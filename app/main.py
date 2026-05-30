import asyncio, json, os, uuid, subprocess, sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
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

BASE_DIR  = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / 'models'
SKILLS_DIR = Path(__file__).parent / 'skills'
SKILLS_DIR.mkdir(exist_ok=True)

# ── App ───────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app):
    set_env_from_vault()   # Load vault env vars on startup
    yield
    await stop_all()
    await mcp.disconnect_all()

app = FastAPI(lifespan=lifespan, title='LocalAI')
app.mount('/static', StaticFiles(directory=Path(__file__).parent / 'static'), name='static')

@app.get('/')
def root():
    return FileResponse(Path(__file__).parent / 'static' / 'index.html')

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

@app.post('/api/server/start')
async def start_server(req: StartRequest):
    if not Path(req.model_path).exists():
        raise HTTPException(404, 'Model file not found')
    srv = get_server(req.server_name)
    try:
        await srv.start(req.model_path, req.context_length, req.gpu_layers)
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

# ── Chat ──────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    system: str | None = None
    personality_id: str = 'default'
    stream: bool = True
    conv_id: str = 'default'
    server_name: str = 'main'
    inject_memory: bool = False

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
    srv = get_server(req.server_name)
    if not srv.running:
        raise HTTPException(503, 'No model loaded. Load a model first.')

    ctx = get_context(req.conv_id)
    system, temp, top_p = _resolve_persona(req.personality_id, req.system)

    # Optionally inject relevant memories into system prompt
    if req.inject_memory and req.message:
        mems = recall(req.message, limit=5)
        if mems:
            mem_text = '\n'.join(f"- {m['content']}" for m in mems)
            system = (system or '') + f'\n\n[Relevant memories]:\n{mem_text}'

    ctx.add('user', req.message)
    messages = ctx.get_messages(system)
    tools = _skills_as_tools()

    payload: dict = {
        'model': 'local',
        'messages': messages,
        'stream': req.stream,
        'temperature': temp,
        'top_p': top_p,
    }
    if tools:
        payload['tools'] = tools

    if req.stream:
        return StreamingResponse(
            _stream_response(srv, payload, ctx, req.conv_id, req.message),
            media_type='text/event-stream',
            headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
        )
    return await _blocking_response(srv, payload, ctx, req.conv_id, req.message)

async def _stream_response(srv, payload, ctx, conv_id, user_msg):
    full = ''
    try:
        async with httpx.AsyncClient(timeout=600) as client:
            async with client.stream('POST', f'{srv.base_url()}/v1/chat/completions',
                                     json=payload) as resp:
                async for raw in resp.aiter_lines():
                    if not raw.startswith('data: '):
                        continue
                    data = raw[6:].strip()
                    if data == '[DONE]':
                        ctx.add('assistant', full)
                        save_conversation(conv_id, user_msg[:60], srv.model_path or '')
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

async def _blocking_response(srv, payload, ctx, conv_id, user_msg):
    async with httpx.AsyncClient(timeout=600) as client:
        resp = await client.post(f'{srv.base_url()}/v1/chat/completions', json=payload)
        data = resp.json()
    content = data['choices'][0]['message']['content']
    ctx.add('assistant', content)
    add_message(conv_id, 'user', user_msg)
    add_message(conv_id, 'assistant', content)
    if 'usage' in data:
        ctx.update_tokens(data['usage'].get('total_tokens', 0))
    return {'content': content}

async def _compact(srv, ctx):
    n = max(2, len(ctx.messages) // 2)
    to_sum = ctx.messages[:n]
    prompt = [
        {'role': 'system', 'content': 'Summarize this conversation concisely. Keep all key facts, decisions, and context. Be brief.'},
        {'role': 'user', 'content': '\n'.join(f"{m['role'].upper()}: {m['content']}" for m in to_sum if isinstance(m, dict) and 'content' in m)}
    ]
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f'{srv.base_url()}/v1/chat/completions',
                json={'model': 'local', 'messages': prompt, 'stream': False}
            )
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
    # Check JSON skill first
    json_path = SKILLS_DIR / f'{id}.json'
    if json_path.exists():
        s = json.loads(json_path.read_text())
        if s.get('code'):
            return {'code': s['code'], 'source': 'json'}
        # Try a matching .py by name
        py_name = s.get('name', '').replace(' ', '_') + '.py'
        py_path = SKILLS_DIR / py_name
        if py_path.exists():
            return {'code': py_path.read_text(), 'source': 'file'}
    # Fallback: look for .py with matching name/id
    for py_path in SKILLS_DIR.glob('*.py'):
        if py_path.stem.lower() == id.lower():
            return {'code': py_path.read_text(), 'source': 'file'}
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
        ns = {
            '__builtins__': __builtins__,
            'httpx': __import__('httpx'),
            'json': __import__('json'),
            'os': __import__('os'),
            'subprocess': __import__('subprocess'),
            'Path': Path,
            'vault_get': get_secret,
        }
        exec(compile(skill['code'], '<skill>', 'exec'), ns)
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
