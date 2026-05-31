import asyncio, json, os, uuid, subprocess, sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import httpx
from pydantic import BaseModel

from .gguf import model_info
from .hardware import system_info, will_fit
from .llama import get_server, stop_all, all_servers
from .context import get_context
from .mcp_client import mcp, PRESETS
from .brain import (remember, recall, all_memories, delete_memory, clear_memories,
                    save_conversation, add_message, list_conversations,
                    get_conversation_messages, delete_conversation)
from .vault import set_secret, get_secret, delete_secret, list_keys, set_env_from_vault
from .personalities import list_personalities, get_personality, save_personality, delete_personality

BASE_DIR      = Path(__file__).parent.parent
MODELS_DIR    = BASE_DIR / 'models'
SKILLS_DIR    = Path(__file__).parent / 'skills'
WORKSPACE_DIR = BASE_DIR / 'workspace'
SKILLS_DIR.mkdir(exist_ok=True)
WORKSPACE_DIR.mkdir(exist_ok=True)

# ── App ───────────────────────────────────────────────────────────

def _autodiscover_py_skills():
    """Scan SKILLS_DIR for .py files that define execute() and register missing ones."""
    import ast, re

    # Collect already-known ids, names, and py_file references
    existing_ids      = set()
    existing_names    = set()
    existing_py_files = set()
    for f in SKILLS_DIR.glob('*.json'):
        try:
            s = json.loads(f.read_text())
            existing_ids.add(s.get('id', '').lower())
            existing_names.add(s.get('name', '').lower().replace(' ', '_'))
            if s.get('py_file'):
                existing_py_files.add(s['py_file'].lower())
        except Exception:
            pass

    registered = 0
    for py_path in sorted(SKILLS_DIR.glob('*.py')):
        stem = py_path.stem

        # Skip if already registered (by id, name, py_file ref, or existing json)
        if (stem.lower() in existing_ids
                or stem.lower() in existing_names
                or py_path.name.lower() in existing_py_files
                or (SKILLS_DIR / f'{stem}.json').exists()):
            continue

        try:
            code = py_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        if 'def execute(' not in code:
            continue   # not a skill file

        # Module docstring → description
        description = f'Auto-discovered skill from {py_path.name}'
        try:
            doc = ast.get_docstring(ast.parse(code))
            if doc:
                description = doc.splitlines()[0].strip()
        except Exception:
            pass

        # Infer parameters from kwargs.get() calls
        type_map = {'int': 'integer', 'float': 'number', 'bool': 'boolean'}
        properties: dict = {}
        for m in re.finditer(
            r'(\w+)\s*=\s*(int|float|bool|str)?\s*\(?kwargs\.get\(["\'](\w+)["\']',
            code
        ):
            cast, param = m.group(2), m.group(3)
            properties[param] = {'type': type_map.get(cast, 'string'), 'description': param}
        if not properties:   # fallback: undecorated kwargs.get
            for m in re.finditer(r'kwargs\.get\(["\'](\w+)["\']', code):
                properties[m.group(1)] = {'type': 'string', 'description': m.group(1)}

        skill = {
            'id': stem,
            'name': stem.replace('_', ' ').title(),
            'description': description,
            'parameters': {
                'type': 'object',
                'properties': properties,
                'required': list(properties)[:1],
            },
            'action_type': 'python',
            'code': '',           # runtime loads from py_file
            'py_file': py_path.name,
            'webhook_url': '',
            'enabled': True,
        }

        (SKILLS_DIR / f'{stem}.json').write_text(json.dumps(skill, indent=2))
        existing_ids.add(stem.lower())
        registered += 1
        print(f'[Skills] Auto-registered: {skill["name"]} ({py_path.name})')

    if registered:
        print(f'[Skills] {registered} new skill(s) discovered and registered.')


@asynccontextmanager
async def lifespan(app):
    set_env_from_vault()       # load vault env vars
    _autodiscover_py_skills()  # register any new .py skills
    yield
    await stop_all()
    await mcp.disconnect_all()

app = FastAPI(lifespan=lifespan, title='PyAgenticLlama')
app.mount('/static', StaticFiles(directory=Path(__file__).parent / 'static'), name='static')

@app.get('/')
def root():
    return FileResponse(Path(__file__).parent / 'static' / 'index.html')

@app.get('/logo.png')
def serve_logo():
    return FileResponse(Path(__file__).parent / 'logo.png', media_type='image/png')

# ── Hardware ──────────────────────────────────────────────────────

@app.get('/api/hardware')
def hardware():
    return system_info()

# ── Models & Filesystem ───────────────────────────────────────────

@app.get('/api/models')
def list_models(extra_paths: str = ''):
    """Scan default models dir + any extra paths for .gguf files."""
    search_dirs: list[Path] = [MODELS_DIR]
    if extra_paths:
        for p in extra_paths.split('|'):
            path = Path(p.strip())
            if path.exists():
                search_dirs.append(path)
    # Also load saved model paths from vault
    saved = get_secret('_model_paths', '')
    if saved:
        for p in saved.split('|'):
            path = Path(p.strip())
            if path.exists() and path not in search_dirs:
                search_dirs.append(path)

    found = {}
    for d in search_dirs:
        for f in sorted(d.glob('*.gguf'), key=lambda x: x.stat().st_size):
            key = str(f)
            if key not in found:
                found[key] = {
                    'path': str(f),
                    'name': f.stem,
                    'size_gb': round(f.stat().st_size / 1024**3, 2),
                    'dir': str(f.parent),
                }
    return list(found.values())

@app.post('/api/models/add-path')
def add_model_path(path: str):
    """Persist an extra model folder to vault."""
    if not Path(path).is_dir():
        raise HTTPException(400, 'Not a valid directory')
    saved = get_secret('_model_paths', '')
    paths = [p for p in saved.split('|') if p] if saved else []
    if path not in paths:
        paths.append(path)
        set_secret('_model_paths', '|'.join(paths))
    return {'paths': paths}

@app.get('/api/models/paths')
def get_model_paths():
    saved = get_secret('_model_paths', '')
    paths = [p for p in saved.split('|') if p] if saved else []
    return {'paths': [str(MODELS_DIR)] + paths}

@app.get('/api/models/info')
def get_model_info(path: str = Query(...)):
    if not Path(path).exists():
        raise HTTPException(404, 'Model file not found')
    info = model_info(path)
    hw = system_info()
    fits, msg = will_fit(info['estimated_ram_gb'])
    return {**info, **hw, 'fits': fits, 'fit_message': msg}

@app.get('/api/filesystem/home')
def filesystem_home():
    """Return user home folder and common shortcuts."""
    home = Path.home()
    shortcuts = []
    for name, folder in [
        ('Desktop',   home / 'Desktop'),
        ('Downloads', home / 'Downloads'),
        ('Documents', home / 'Documents'),
        ('Pictures',  home / 'Pictures'),
        ('Videos',    home / 'Videos'),
    ]:
        if folder.exists():
            shortcuts.append({'name': name, 'path': str(folder)})
    # Add drive roots
    import string
    for drive in string.ascii_uppercase:
        p = Path(f'{drive}:\\')
        if p.exists():
            shortcuts.append({'name': f'{drive}:\\', 'path': str(p)})
    return {'home': str(home), 'shortcuts': shortcuts}

@app.get('/api/filesystem/browse')
def browse_filesystem(path: str = ''):
    """Browse filesystem — returns ALL files and folders like Windows Explorer."""
    if not path:
        path = str(Path.home())
    try:
        p = Path(path)
        if not p.exists():
            raise HTTPException(400, 'Path does not exist')
        entries = []
        try:
            items = list(p.iterdir())
        except PermissionError:
            return {'path': str(p), 'parent': str(p.parent), 'entries': []}
        for item in sorted(items, key=lambda x: (not x.is_dir(), x.name.lower())):
            try:
                if item.name.startswith('.'):
                    continue  # skip hidden files
                is_dir = item.is_dir()
                is_gguf = not is_dir and item.suffix.lower() == '.gguf'
                stat = item.stat()
                size_mb = None if is_dir else round(stat.st_size / 1024**2, 1)
                entries.append({
                    'name': item.name,
                    'path': str(item),
                    'is_dir': is_dir,
                    'is_gguf': is_gguf,
                    'size_mb': size_mb,
                    'size_gb': round(stat.st_size / 1024**3, 2) if is_gguf else None,
                })
            except Exception:
                pass
        return {'path': str(p), 'parent': str(p.parent), 'entries': entries}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e))

# ── Server management ─────────────────────────────────────────────

class StartRequest(BaseModel):
    model_path: str
    context_length: int = 4096
    gpu_layers: int = 20
    server_name: str = 'main'
    mmproj_path: str | None = None

@app.post('/api/server/start')
async def start_server(req: StartRequest):
    if not Path(req.model_path).exists():
        raise HTTPException(404, 'Model file not found')
    srv = get_server(req.server_name)
    try:
        await srv.start(req.model_path, req.context_length, req.gpu_layers, req.mmproj_path)
        ctx = get_context()
        ctx.max_tokens = req.context_length
        ctx.clear()
        return srv.status()
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post('/api/server/stop')
async def stop_server(name: str = 'main'):
    await get_server(name).stop()
    return {'status': 'stopped', 'name': name}

@app.get('/api/server/status')
def server_status(name: str = 'main'):
    return get_server(name).status()

@app.get('/api/server/all')
def server_all():
    return all_servers()

@app.get('/api/server/log')
def server_log(name: str = 'main', lines: int = 80):
    log_path = BASE_DIR / f'llama-{name}.log'
    if not log_path.exists():
        return {'lines': []}
    all_lines = log_path.read_text(errors='replace').splitlines()
    return {'lines': all_lines[-lines:]}

# ── Provider ──────────────────────────────────────────────────────

class ProviderConfig(BaseModel):
    type: str = 'local'          # 'local' | 'external'
    name: str = ''
    base_url: str = ''
    api_key: str = ''
    model: str = ''

def _get_provider() -> dict:
    raw = get_secret('_provider_config', '')
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
    return {'type': 'local'}

def _provider_url_headers(provider: dict, srv) -> tuple[str, dict]:
    """Return (url, auth-headers) for /v1/chat/completions."""
    if provider.get('type') == 'external':
        base = provider['base_url'].rstrip('/')
        return f'{base}/chat/completions', {'Authorization': f"Bearer {provider['api_key']}"}
    return f'{srv.base_url()}/v1/chat/completions', {}

def _infer_provider_name(base_url: str) -> str:
    u = base_url.lower()
    for kw, label in [('nvidia','NVIDIA NIM'), ('openai','OpenAI'),
                       ('anthropic','Anthropic'), ('groq','Groq'),
                       ('together','Together AI'), ('mistral','Mistral AI'),
                       ('cohere','Cohere'), ('deepseek','DeepSeek'),
                       ('gemini','Google AI'), ('google','Google AI')]:
        if kw in u:
            return label
    return 'Custom Provider'

@app.get('/api/provider')
def get_provider():
    return _get_provider()

@app.post('/api/provider')
def set_provider(cfg: ProviderConfig):
    data = cfg.model_dump()
    set_secret('_provider_config', json.dumps(data))
    return data

@app.delete('/api/provider')
def reset_provider():
    set_secret('_provider_config', json.dumps({'type': 'local'}))
    return {'type': 'local'}

@app.post('/api/provider/parse-file')
async def parse_provider_file(file: UploadFile = File(...)):
    """Extract base_url, api_key and model from an OpenAI-compatible .py config file."""
    import ast, re
    content = (await file.read()).decode('utf-8', errors='ignore')

    base_url = api_key = model = ''

    # AST pass — handles OpenAI(base_url=...) and .create(model=...)
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            fn_name = (fn.id if isinstance(fn, ast.Name)
                       else fn.attr if isinstance(fn, ast.Attribute) else '')
            if fn_name in ('OpenAI', 'AsyncOpenAI', 'AzureOpenAI'):
                for kw in node.keywords:
                    if kw.arg == 'base_url' and isinstance(kw.value, ast.Constant):
                        base_url = kw.value.value
                    elif kw.arg == 'api_key' and isinstance(kw.value, ast.Constant):
                        api_key = kw.value.value
            if isinstance(fn, ast.Attribute) and fn.attr == 'create':
                for kw in node.keywords:
                    if kw.arg == 'model' and isinstance(kw.value, ast.Constant) and not model:
                        model = kw.value.value
    except Exception:
        pass

    # Regex fallback
    if not base_url:
        m = re.search(r'base_url\s*=\s*["\']([^"\']+)["\']', content)
        if m: base_url = m.group(1)
    if not api_key:
        m = re.search(r'api_key\s*=\s*["\']([^"\']+)["\']', content)
        if m: api_key = m.group(1)
    if not model:
        m = re.search(r'model\s*=\s*["\']([^"\']+)["\']', content)
        if m: model = m.group(1)

    if not base_url and not api_key:
        raise HTTPException(400, 'Could not find provider configuration in this file. '
                                 'Expected an OpenAI-compatible client with base_url and api_key.')

    return {
        'type': 'external',
        'name': _infer_provider_name(base_url),
        'base_url': base_url,
        'api_key': api_key,
        'model': model,
    }

# ── File upload / attachment extraction ──────────────────────────

@app.post('/api/upload')
async def upload_attachment(file: UploadFile = File(...)):
    """Extract content from an uploaded file. PDFs → text. Images → base64 data-url."""
    import base64
    data = await file.read()
    filename = file.filename or 'file'
    ext = Path(filename).suffix.lower()

    if ext == '.pdf':
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=data, filetype='pdf')
            text = '\n\n'.join(page.get_text() for page in doc)
            doc.close()
            return {'type': 'text', 'filename': filename, 'content': text}
        except ImportError:
            pass
        try:
            from pdfminer.high_level import extract_text
            import io
            text = extract_text(io.BytesIO(data))
            return {'type': 'text', 'filename': filename, 'content': text}
        except ImportError:
            raise HTTPException(400, 'PDF parsing unavailable — install PyMuPDF: pip install pymupdf')

    if ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg'):
        mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
                    '.gif': 'image/gif', '.webp': 'image/webp', '.bmp': 'image/bmp',
                    '.svg': 'image/svg+xml'}
        mime = mime_map.get(ext, file.content_type or 'image/jpeg')
        b64 = base64.b64encode(data).decode()
        return {'type': 'image', 'filename': filename,
                'data_url': f'data:{mime};base64,{b64}', 'mime': mime}

    # Fallback: decode as text
    try:
        return {'type': 'text', 'filename': filename,
                'content': data.decode('utf-8', errors='replace')}
    except Exception:
        raise HTTPException(400, f'Cannot read {filename} as text')

# ── Chat ──────────────────────────────────────────────────────────

class AttachmentItem(BaseModel):
    filename: str = ''
    type: str = 'text'        # 'text' | 'image'
    content: str = ''         # text file content
    data_url: str = ''        # image: 'data:image/png;base64,...'
    mime: str = ''

class ChatRequest(BaseModel):
    message: str
    system: str | None = None
    personality_id: str = 'default'
    stream: bool = True
    conv_id: str = 'default'
    server_name: str = 'main'
    inject_memory: bool = False
    attachments: list[AttachmentItem] = []

def _resolve_persona(pid: str, override_system: str | None) -> tuple[str | None, float, float]:
    p = get_personality(pid)
    if not p:
        return override_system, 0.7, 0.9
    system = override_system or p.get('system_prompt')
    return system, float(p.get('temperature', 0.7)), float(p.get('top_p', 0.9))

def _skills_as_tools() -> list:
    tools = []
    for f in SKILLS_DIR.glob('*.json'):
        try:
            s = json.loads(f.read_text())
            if not s.get('enabled', True):
                continue
            tools.append({
                'type': 'function',
                'function': {
                    'name': s['id'].replace('-', '_'),
                    'description': s['description'],
                    'parameters': s.get('parameters', {'type': 'object', 'properties': {}}),
                }
            })
        except Exception:
            pass
    # Append live MCP tools from all connected servers
    tools.extend(mcp.as_openai_tools())
    return tools

@app.post('/api/chat')
async def chat(req: ChatRequest):
    provider = _get_provider()
    srv = get_server(req.server_name)
    if provider.get('type') != 'external' and not srv.running:
        raise HTTPException(503, 'No model loaded. Load a model first.')

    ctx = get_context(req.conv_id)
    system, temp, top_p = _resolve_persona(req.personality_id, req.system)

    if req.inject_memory and req.message:
        mems = recall(req.message, limit=5)
        if mems:
            mem_text = '\n'.join(f"- {m['content']}" for m in mems)
            system = (system or '') + f'\n\n[Relevant memories]:\n{mem_text}'

    # Build message content — plain text or multimodal list for vision models
    text_parts = [req.message] if req.message else []
    image_parts = []
    for att in req.attachments:
        if att.type == 'text' and att.content:
            text_parts.append(f'\n\n---\n**File: {att.filename}**\n```\n{att.content[:50000]}\n```')
        elif att.type == 'image' and att.data_url:
            image_parts.append({'type': 'image_url', 'image_url': {'url': att.data_url}})
    combined_text = ''.join(text_parts)
    user_content: str | list = (
        [{'type': 'text', 'text': combined_text}] + image_parts
        if image_parts else combined_text
    )

    ctx.add('user', user_content)
    messages = ctx.get_messages(system)
    tools = _skills_as_tools()

    payload: dict = {
        'model': provider.get('model', 'local') if provider.get('type') == 'external' else 'local',
        'messages': messages,
        'stream': req.stream,
        'temperature': temp,
        'top_p': top_p,
    }
    if tools:
        payload['tools'] = tools

    if req.stream:
        return StreamingResponse(
            _stream_response(srv, payload, ctx, req.conv_id, req.message, provider),
            media_type='text/event-stream',
            headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
        )
    return await _blocking_response(srv, payload, ctx, req.conv_id, req.message, provider)

async def _stream_response(srv, payload, ctx, conv_id, user_msg, provider=None):
    provider = provider or {'type': 'local'}
    url, headers = _provider_url_headers(provider, srv)
    model_label = (provider.get('name') or provider.get('model', '')) \
        if provider.get('type') == 'external' else (srv.model_path or '')
    full = ''
    try:
        async with httpx.AsyncClient(timeout=600) as client:
            async with client.stream('POST', url, json=payload, headers=headers) as resp:
                async for raw in resp.aiter_lines():
                    if not raw.startswith('data: '):
                        continue
                    data = raw[6:].strip()
                    if data == '[DONE]':
                        ctx.add('assistant', full)
                        save_conversation(conv_id, user_msg[:60], model_label)
                        add_message(conv_id, 'user', user_msg)
                        add_message(conv_id, 'assistant', full)
                        if ctx.needs_compaction():
                            asyncio.create_task(_compact(srv, ctx))
                        yield 'data: [DONE]\n\n'
                        return
                    try:
                        chunk = json.loads(data)
                        delta = chunk['choices'][0]['delta'].get('content', '')
                        if delta:
                            full += delta
                            yield f'data: {json.dumps({"content": delta})}\n\n'
                        usage = chunk.get('usage') or chunk['choices'][0].get('usage')
                        if usage:
                            ctx.update_tokens(usage.get('total_tokens', 0))
                    except Exception:
                        pass
    except Exception as e:
        yield f'data: {json.dumps({"error": str(e)})}\n\n'

async def _blocking_response(srv, payload, ctx, conv_id, user_msg, provider=None):
    provider = provider or {'type': 'local'}
    url, headers = _provider_url_headers(provider, srv)
    async with httpx.AsyncClient(timeout=600) as client:
        resp = await client.post(url, json=payload, headers=headers)
        data = resp.json()
    content = data['choices'][0]['message']['content']
    ctx.add('assistant', content)
    add_message(conv_id, 'user', user_msg)
    add_message(conv_id, 'assistant', content)
    if 'usage' in data:
        ctx.update_tokens(data['usage'].get('total_tokens', 0))
    return {'content': content}

async def _compact(srv, ctx):
    provider = _get_provider()
    url, headers = _provider_url_headers(provider, srv)
    model_id = provider.get('model', 'local') if provider.get('type') == 'external' else 'local'
    n = max(2, len(ctx.messages) // 2)
    to_sum = ctx.messages[:n]
    def _msg_text(m: dict) -> str:
        c = m.get('content', '')
        if isinstance(c, list):
            return ' '.join(p.get('text', '') for p in c if isinstance(p, dict) and p.get('type') == 'text')
        return str(c)

    prompt = [
        {'role': 'system', 'content': 'Summarize this conversation concisely. Keep all key facts, decisions, and context. Be brief.'},
        {'role': 'user', 'content': '\n'.join(
            f"{m['role'].upper()}: {_msg_text(m)}" for m in to_sum if isinstance(m, dict) and 'content' in m
        )}
    ]
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, headers=headers,
                                     json={'model': model_id, 'messages': prompt, 'stream': False})
            summary = resp.json()['choices'][0]['message']['content']
            ctx.apply_summary(summary, n)
    except Exception:
        pass

@app.get('/api/context')
def get_ctx_info(conv_id: str = 'default'):
    return get_context(conv_id).info()

@app.post('/api/context/compact')
async def compact_ctx(conv_id: str = 'default', server_name: str = 'main'):
    srv = get_server(server_name)
    ctx = get_context(conv_id)
    await _compact(srv, ctx)
    return ctx.info()

@app.post('/api/context/clear')
def clear_ctx(conv_id: str = 'default'):
    get_context(conv_id).clear()
    return {'status': 'cleared'}

# ── Filesystem (general — any path on the user's PC) ─────────────

class FsSave(BaseModel):
    path: str
    content: str

class FsMkdir(BaseModel):
    path: str

_FS_IGNORE = {'.git', '__pycache__', 'node_modules', '.venv', 'venv',
              '.idea', '.mypy_cache', '.pytest_cache', 'dist', 'build'}

def _build_fs_tree(p: Path, depth: int = 0, max_depth: int = 6) -> dict | None:
    if not p.exists() or depth > max_depth:
        return None
    if p.is_file():
        return {'name': p.name, 'path': str(p).replace('\\', '/'),
                'isDir': False, 'ext': p.suffix.lstrip('.').lower()}
    if p.is_dir():
        if depth > 0 and (p.name in _FS_IGNORE or p.name.startswith('.')):
            return None
        children = []
        try:
            for item in sorted(p.iterdir(),
                               key=lambda x: (not x.is_dir(), x.name.lower())):
                node = _build_fs_tree(item, depth + 1, max_depth)
                if node:
                    children.append(node)
        except PermissionError:
            pass
        return {'name': p.name, 'path': str(p).replace('\\', '/'),
                'isDir': True, 'children': children}
    return None

@app.get('/api/fs/tree')
def fs_tree(root: str = Query(...)):
    p = Path(root)
    if not p.exists() or not p.is_dir():
        raise HTTPException(404, 'Directory not found')
    return _build_fs_tree(p)

@app.get('/api/fs/read')
def fs_read(path: str = Query(...)):
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise HTTPException(404, 'File not found')
    return {'content': p.read_text(encoding='utf-8', errors='replace'), 'path': str(p)}

@app.post('/api/fs/save')
def fs_save(req: FsSave):
    p = Path(req.path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(req.content, encoding='utf-8')
    return {'saved': str(p), 'size': len(req.content)}

@app.post('/api/fs/mkdir')
def fs_mkdir(req: FsMkdir):
    p = Path(req.path)
    p.mkdir(parents=True, exist_ok=True)
    return {'created': str(p), 'path': str(p).replace('\\', '/')}

@app.delete('/api/fs/delete')
def fs_delete(path: str = Query(...)):
    import shutil
    p = Path(path)
    if p.is_dir():
        shutil.rmtree(p, ignore_errors=True)
    elif p.exists():
        p.unlink()
    return {'deleted': str(p)}

# ── Workspace ────────────────────────────────────────────────────

class WorkspaceSave(BaseModel):
    path: str       # relative path inside workspace, e.g. "app.py" or "src/main.js"
    content: str

def _safe_ws_path(rel: str) -> Path:
    """Resolve rel to an absolute path guaranteed to stay inside WORKSPACE_DIR."""
    target = (WORKSPACE_DIR / rel).resolve()
    if not str(target).startswith(str(WORKSPACE_DIR.resolve())):
        raise HTTPException(400, 'Path traversal not allowed')
    return target

@app.get('/api/workspace')
def workspace_info():
    return {'path': str(WORKSPACE_DIR), 'name': 'workspace'}

@app.get('/api/workspace/files')
def workspace_files():
    result = []
    for f in sorted(WORKSPACE_DIR.rglob('*')):
        if f.is_file() and not f.name.startswith('.'):
            rel = str(f.relative_to(WORKSPACE_DIR)).replace('\\', '/')
            result.append({'path': rel, 'size': f.stat().st_size,
                           'ext': f.suffix.lstrip('.')})
    return result

@app.post('/api/workspace/save')
def workspace_save(req: WorkspaceSave):
    target = _safe_ws_path(req.path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(req.content, encoding='utf-8')
    return {'saved': req.path, 'size': len(req.content)}

@app.get('/api/workspace/read')
def workspace_read(path: str = Query(...)):
    target = _safe_ws_path(path)
    if not target.exists():
        raise HTTPException(404, 'File not found')
    return {'content': target.read_text(encoding='utf-8', errors='replace'), 'path': path}

@app.delete('/api/workspace/file')
def workspace_delete(path: str = Query(...)):
    target = _safe_ws_path(path)
    if target.exists():
        target.unlink()
    return {'deleted': path}

@app.post('/api/workspace/open-in-vscode')
async def workspace_open_in_vscode():
    """Ask the VS Code extension to open the workspace folder."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.post('http://127.0.0.1:3333/open-folder',
                                  json={'folder': str(WORKSPACE_DIR)})
            return {'status': 'ok' if r.status_code == 200 else 'error'}
    except Exception as e:
        raise HTTPException(503, f'VS Code extension not reachable: {e}')

# ── Skills ────────────────────────────────────────────────────────

class SkillIn(BaseModel):
    name: str
    description: str
    parameters: dict = {}
    action_type: str = 'python'
    code: str = ''
    webhook_url: str = ''
    enabled: bool = True

@app.get('/api/skills/source')
def skill_source(id: str = Query(...)):
    """Return the source code for a skill — also checks for a matching .py file."""
    json_path = SKILLS_DIR / f'{id}.json'
    if json_path.exists():
        s = json.loads(json_path.read_text())
        # Prefer explicit py_file reference
        if s.get('py_file'):
            py_path = SKILLS_DIR / s['py_file']
            if py_path.exists():
                return {'code': py_path.read_text(encoding='utf-8'), 'source': 'file'}
        if s.get('code'):
            return {'code': s['code'], 'source': 'json'}
        # Fallback: .py with same stem
        py_path = SKILLS_DIR / f'{id}.py'
        if py_path.exists():
            return {'code': py_path.read_text(encoding='utf-8'), 'source': 'file'}
    # Last resort: search by stem
    for py_path in SKILLS_DIR.glob('*.py'):
        if py_path.stem.lower() == id.lower():
            return {'code': py_path.read_text(encoding='utf-8'), 'source': 'file'}
    raise HTTPException(404, 'Skill source not found')

@app.get('/api/skills/find')
def find_skill(name: str = Query(...)):
    """Find skills by partial name or exact ID — used by /validate_skill command."""
    needle = name.strip().lower()
    hits = []
    for f in sorted(SKILLS_DIR.glob('*.json')):
        try:
            s = json.loads(f.read_text())
            if needle in s.get('name', '').lower() or needle == s.get('id', '').lower():
                hits.append(s)
        except Exception:
            pass
    return hits

@app.get('/api/skills')
def list_skills():
    result = []
    for f in sorted(SKILLS_DIR.glob('*.json')):
        try:
            result.append(json.loads(f.read_text()))
        except Exception:
            pass
    return result

@app.post('/api/skills')
def create_skill(s: SkillIn):
    skill_id = str(uuid.uuid4())[:8]
    skill = {'id': skill_id, **s.model_dump()}
    (SKILLS_DIR / f'{skill_id}.json').write_text(json.dumps(skill, indent=2))
    return skill

@app.put('/api/skills/{skill_id}')
def update_skill(skill_id: str, s: SkillIn):
    path = SKILLS_DIR / f'{skill_id}.json'
    if not path.exists():
        raise HTTPException(404)
    skill = json.loads(path.read_text())
    skill.update(s.model_dump())
    path.write_text(json.dumps(skill, indent=2))
    return skill

@app.delete('/api/skills/{skill_id}')
def delete_skill_ep(skill_id: str):
    path = SKILLS_DIR / f'{skill_id}.json'
    if path.exists():
        path.unlink()
    return {'status': 'deleted'}

@app.post('/api/skills/{skill_id}/run')
async def run_skill_ep(skill_id: str, kwargs: dict = {}):
    path = SKILLS_DIR / f'{skill_id}.json'
    if not path.exists():
        raise HTTPException(404)
    skill = json.loads(path.read_text())
    result = await _execute_skill(skill, kwargs)
    return {'result': result}

async def _execute_skill(skill: dict, kwargs: dict) -> str:
    if skill['action_type'] == 'python':
        code = (skill.get('code') or '').strip()
        # If no embedded code, load from referenced .py file (auto-discovered skills)
        if not code:
            py_name = skill.get('py_file') or f"{skill['id']}.py"
            py_path = SKILLS_DIR / py_name
            if py_path.exists():
                code = py_path.read_text(encoding='utf-8')
        if not code:
            raise ValueError(f'No code found for skill {skill["id"]!r}')
        ns = {
            '__builtins__': __builtins__,
            'httpx': __import__('httpx'),
            'json': __import__('json'),
            'os': __import__('os'),
            'subprocess': __import__('subprocess'),
            'Path': Path,
            'vault_get': get_secret,
        }
        exec(compile(code, '<skill>', 'exec'), ns)
        fn = ns.get('execute')
        if not fn:
            raise ValueError('Skill must define an execute(**kwargs) function')
        result = fn(**kwargs)
        if asyncio.iscoroutine(result):
            result = await result
        return str(result)
    elif skill['action_type'] == 'webhook':
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(skill['webhook_url'], json=kwargs)
            return resp.text
    return 'Unknown action type'

# ── Agent ─────────────────────────────────────────────────────────

class AgentRequest(BaseModel):
    message: str
    personality_id: str = 'default'
    max_iterations: int = 10
    server_name: str = 'main'
    conv_id: str = 'default'

@app.post('/api/agent')
async def agent_run(req: AgentRequest):
    srv = get_server(req.server_name)
    if not srv.running:
        raise HTTPException(503, 'No model loaded')

    ctx = get_context(req.conv_id)
    system, temp, top_p = _resolve_persona(req.personality_id, None)
    ctx.add('user', req.message)

    tools = _skills_as_tools()
    skills_by_name = {}
    for f in SKILLS_DIR.glob('*.json'):
        try:
            s = json.loads(f.read_text())
            skills_by_name[s['id'].replace('-', '_')] = s
        except Exception:
            pass

    trace = []
    for i in range(req.max_iterations):
        payload = {
            'model': 'local',
            'messages': ctx.get_messages(system),
            'tools': tools,
            'stream': False,
            'temperature': temp,
            'top_p': top_p,
        }
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(f'{srv.base_url()}/v1/chat/completions', json=payload)
        data = resp.json()
        msg = data['choices'][0]['message']

        if not msg.get('tool_calls'):
            content = msg.get('content', '')
            ctx.add('assistant', content)
            add_message(req.conv_id, 'user', req.message)
            add_message(req.conv_id, 'assistant', content)
            return {'content': content, 'trace': trace, 'iterations': i + 1}

        ctx.messages.append(msg)
        for tc in msg['tool_calls']:
            fn_name = tc['function']['name']
            try:
                args = json.loads(tc['function'].get('arguments', '{}'))
            except Exception:
                args = {}
            skill = skills_by_name.get(fn_name)
            mcp_target = mcp.resolve(fn_name)
            if skill:
                try:
                    result = await _execute_skill(skill, args)
                except Exception as e:
                    result = f'Error executing {fn_name}: {e}'
            elif mcp_target:
                srv_name, tool_name = mcp_target
                try:
                    result = await mcp.call(srv_name, tool_name, args)
                except Exception as e:
                    result = f'MCP error ({srv_name}/{tool_name}): {e}'
            else:
                result = f'Unknown tool: {fn_name}'
            trace.append({'tool': fn_name, 'args': args, 'result': result})
            ctx.messages.append({'role': 'tool', 'tool_call_id': tc['id'], 'content': result})

    return {'content': 'Max iterations reached', 'trace': trace, 'iterations': req.max_iterations}

# ── Console log polling ───────────────────────────────────────────

@app.get('/api/console/lines')
def console_lines(name: str = 'main', after: int = 0):
    """Return log lines starting from `after` index. Frontend polls this."""
    log_path = BASE_DIR / f'llama-{name}.log'
    if not log_path.exists():
        return {'lines': [], 'total': 0}
    try:
        lines = log_path.read_text(errors='replace').splitlines()
        return {'lines': lines[after:], 'total': len(lines)}
    except Exception:
        return {'lines': [], 'total': 0}

# ── Terminal ───────────────────────────────────────────────────────

_term_cwd = str(BASE_DIR)   # Persistent working directory across commands
_term_history: list[str] = []  # Keep last 200 lines of session output

class TermCmd(BaseModel):
    command: str

@app.post('/api/terminal/exec')
async def terminal_exec(req: TermCmd):
    global _term_cwd
    cmd = req.command.strip()
    if not cmd:
        return {'output': '', 'cwd': _term_cwd, 'returncode': 0}

    # Handle cd ourselves so directory persists across calls
    if cmd.lower().startswith('cd') and (len(cmd) == 2 or cmd[2] in (' ', '\t')):
        target = cmd[2:].strip() or str(Path.home())
        try:
            new = Path(_term_cwd) / target
            new = new.resolve()
            if new.is_dir():
                _term_cwd = str(new)
                return {'output': '', 'cwd': _term_cwd, 'returncode': 0}
            return {'output': f"cd: path not found: {target}", 'cwd': _term_cwd, 'returncode': 1}
        except Exception as e:
            return {'output': str(e), 'cwd': _term_cwd, 'returncode': 1}

    try:
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(
                cmd, shell=True,
                capture_output=True, text=True,
                timeout=60, cwd=_term_cwd,
                encoding='utf-8', errors='replace',
            )
        )
        out = (result.stdout or '') + (result.stderr or '')
        return {'output': out, 'cwd': _term_cwd, 'returncode': result.returncode}
    except subprocess.TimeoutExpired:
        return {'output': 'Timed out after 60 seconds.', 'cwd': _term_cwd, 'returncode': -1}
    except Exception as e:
        return {'output': str(e), 'cwd': _term_cwd, 'returncode': -1}

@app.get('/api/terminal/cwd')
def get_term_cwd():
    return {'cwd': _term_cwd}

# ── Code runner ───────────────────────────────────────────────────

class RunRequest(BaseModel):
    code: str
    language: str = 'python'

@app.post('/api/run')
async def run_code(req: RunRequest):
    if req.language.lower() not in ('python', 'py'):
        raise HTTPException(400, 'Only Python execution is currently supported')
    try:
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(
                [sys.executable, '-c', req.code],
                capture_output=True, text=True, timeout=30,
                cwd=str(BASE_DIR),
            )
        )
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(408, 'Script timed out after 30 seconds')
    except Exception as e:
        raise HTTPException(500, str(e))

# ── Spawn sub-agents ──────────────────────────────────────────────

class SpawnRequest(BaseModel):
    name: str
    model_path: str
    task: str
    personality_id: str = 'default'
    context_length: int = 2048
    gpu_layers: int = 0

@app.post('/api/agents/spawn')
async def spawn_agent(req: SpawnRequest):
    if not Path(req.model_path).exists():
        raise HTTPException(404, 'Model not found')
    srv = get_server(req.name)
    if not srv.running:
        await srv.start(req.model_path, req.context_length, req.gpu_layers)
    ctx = get_context(f'agent-{req.name}')
    system, temp, top_p = _resolve_persona(req.personality_id, None)
    ctx.clear()
    ctx.add('user', req.task)
    payload = {
        'model': 'local',
        'messages': ctx.get_messages(system),
        'stream': False,
        'temperature': temp,
    }
    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.post(f'{srv.base_url()}/v1/chat/completions', json=payload)
    content = resp.json()['choices'][0]['message']['content']
    ctx.add('assistant', content)
    return {'agent': req.name, 'content': content}

@app.get('/api/agents')
def list_agents():
    return all_servers()

@app.post('/api/agents/{name}/stop')
async def stop_agent(name: str):
    await get_server(name).stop()
    return {'status': 'stopped', 'name': name}

# ── Brain/Memory ──────────────────────────────────────────────────

class MemoryIn(BaseModel):
    content: str
    type_: str = 'fact'
    tags: list[str] = []
    project: str = ''

@app.post('/api/brain/remember')
def brain_remember(m: MemoryIn):
    id_ = remember(m.content, m.type_, m.tags, m.project)
    return {'id': id_, 'status': 'stored'}

@app.get('/api/brain/recall')
def brain_recall(q: str = Query(...), limit: int = 10):
    return recall(q, limit)

@app.get('/api/brain/memories')
def brain_all(limit: int = 100):
    return all_memories(limit)

@app.delete('/api/brain/memories/{id_}')
def brain_delete(id_: int):
    delete_memory(id_)
    return {'status': 'deleted'}

@app.delete('/api/brain/memories')
def brain_clear_all():
    clear_memories()
    return {'status': 'cleared'}

@app.get('/api/brain/conversations')
def get_convs():
    return list_conversations()

@app.get('/api/brain/conversations/{conv_id}')
def get_conv(conv_id: str):
    return get_conversation_messages(conv_id)

@app.delete('/api/brain/conversations/{conv_id}')
def del_conv(conv_id: str):
    delete_conversation(conv_id)
    return {'status': 'deleted'}

# ── Vault ─────────────────────────────────────────────────────────

class SecretIn(BaseModel):
    key: str
    value: str

@app.get('/api/vault/keys')
def vault_keys():
    return [k for k in list_keys() if not k.startswith('_')]

@app.post('/api/vault/set')
def vault_set(s: SecretIn):
    set_secret(s.key, s.value)
    os.environ[s.key] = s.value
    return {'status': 'saved'}

@app.get('/api/vault/get/{key}')
def vault_get_ep(key: str):
    val = get_secret(key)
    return {'key': key, 'exists': bool(val)}

@app.delete('/api/vault/delete/{key}')
def vault_del(key: str):
    delete_secret(key)
    return {'status': 'deleted'}

# ── Personalities ─────────────────────────────────────────────────

@app.get('/api/personalities')
def get_personalities():
    return list_personalities()

@app.post('/api/personalities')
def create_personality(data: dict):
    return save_personality(data)

@app.put('/api/personalities/{id_}')
def update_personality(id_: str, data: dict):
    data['id'] = id_
    return save_personality(data)

@app.delete('/api/personalities/{id_}')
def del_personality(id_: str):
    try:
        delete_personality(id_)
        return {'status': 'deleted'}
    except ValueError as e:
        raise HTTPException(400, str(e))

# ── MCP Server management ──────────────────────────────────────────

class MCPAddRequest(BaseModel):
    name: str
    command: str
    args: list[str] = []
    env: dict = {}
    description: str = ''
    enabled: bool = True

@app.get('/api/mcp/servers')
def mcp_list():
    return mcp.status()

@app.get('/api/mcp/presets')
def mcp_presets():
    return PRESETS

@app.post('/api/mcp/servers')
def mcp_add(req: MCPAddRequest):
    # Substitute vault values into env
    resolved_env = {}
    for k, v in req.env.items():
        resolved_env[k] = v or get_secret(k, v)
    cfg = mcp.add_config(req.name, req.command, req.args, resolved_env, req.description, req.enabled)
    return cfg.to_dict()

@app.delete('/api/mcp/servers/{name}')
async def mcp_remove(name: str):
    await mcp.disconnect(name)
    mcp.remove_config(name)
    return {'status': 'removed'}

@app.post('/api/mcp/servers/{name}/connect')
async def mcp_connect(name: str):
    try:
        conn = await mcp.connect(name)
        return conn.status()
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post('/api/mcp/servers/{name}/disconnect')
async def mcp_disconnect(name: str):
    await mcp.disconnect(name)
    return {'status': 'disconnected', 'name': name}

@app.get('/api/mcp/servers/{name}/tools')
def mcp_tools(name: str):
    status = next((s for s in mcp.status() if s['name'] == name), None)
    if not status:
        raise HTTPException(404, 'Server not found')
    return status['tools']

@app.post('/api/mcp/servers/{name}/call')
async def mcp_call(name: str, body: dict):
    tool_name = body.get('tool')
    args      = body.get('arguments', {})
    if not tool_name:
        raise HTTPException(400, 'Missing tool name')
    try:
        result = await mcp.call(name, tool_name, args)
        return {'result': result}
    except Exception as e:
        raise HTTPException(500, str(e))

# ── VS Code bridge ────────────────────────────────────────────────

VS_CODE_PORT = 3333   # Must match the port in the VS Code extension settings

@app.get('/api/vscode/status')
async def vscode_status():
    """Check whether the VS Code extension bridge is running."""
    try:
        async with httpx.AsyncClient() as c:
            r = await c.get(f'http://127.0.0.1:{VS_CODE_PORT}/ping', timeout=2.0)
            return {'connected': True, **r.json()}
    except Exception:
        return {'connected': False, 'status': 'not running'}

class VSCodeSend(BaseModel):
    code: str
    language: str = ''
    filename: str = ''
    project_path: str = ''

@app.post('/api/vscode/send')
async def vscode_send(req: VSCodeSend):
    """Forward a code block to the VS Code extension."""
    try:
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f'http://127.0.0.1:{VS_CODE_PORT}/receive',
                json=req.model_dump(),
                timeout=5.0,
            )
            r.raise_for_status()
            return {'status': 'sent'}
    except Exception as e:
        raise HTTPException(503,
            f'VS Code not connected — install the PyAgenticLlama extension '
            f'and restart VS Code. ({e})')

@app.post('/api/vscode/open-folder')
async def vscode_open_folder(body: dict):
    """Tell VS Code to open a folder as workspace."""
    folder = body.get('folder', '')
    if not folder:
        raise HTTPException(400, 'folder is required')
    try:
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f'http://127.0.0.1:{VS_CODE_PORT}/open-folder',
                json={'folder': folder},
                timeout=5.0,
            )
            r.raise_for_status()
            return {'status': 'ok'}
    except Exception as e:
        raise HTTPException(503, str(e))

# ── Test Skill ─────────────────────────────────────────────────────

class TestSkillRequest(BaseModel):
    skill_id: str
    kwargs: dict = {}

@app.post('/api/skills/test')
async def test_skill(req: TestSkillRequest):
    path = SKILLS_DIR / f'{req.skill_id}.json'
    if not path.exists():
        raise HTTPException(404, 'Skill not found')
    skill = json.loads(path.read_text())
    try:
        result = await _execute_skill(skill, req.kwargs)
        return {'result': result, 'status': 'ok'}
    except Exception as e:
        raise HTTPException(500, str(e))
