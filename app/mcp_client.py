"""
MCP (Model Context Protocol) client — stdio transport.
Connects to any MCP server via subprocess stdin/stdout using JSON-RPC 2.0.
"""
import asyncio, json, re, os
from pathlib import Path
from dataclasses import dataclass, field

CONFIG_PATH = Path(__file__).parent.parent / 'data' / 'mcp_servers.json'
CONFIG_PATH.parent.mkdir(exist_ok=True)

MCP_PROTOCOL_VERSION = '2024-11-05'

def _safe_fn(s: str) -> str:
    """Sanitize to OpenAI function-name rules: [a-zA-Z0-9_], max 64 chars."""
    return re.sub(r'[^a-zA-Z0-9_]', '_', s)[:64]


@dataclass
class MCPConfig:
    name: str
    command: str
    args: list = field(default_factory=list)
    env: dict = field(default_factory=dict)
    enabled: bool = True
    description: str = ''

    def to_dict(self):
        return {
            'name': self.name, 'command': self.command, 'args': self.args,
            'env': self.env, 'enabled': self.enabled, 'description': self.description,
        }


class MCPConnection:
    """Manages a single connected MCP server."""

    def __init__(self, cfg: MCPConfig):
        self.cfg = cfg
        self._proc: asyncio.subprocess.Process | None = None
        self._reader_task: asyncio.Task | None = None
        self._pending: dict[int, asyncio.Future] = {}
        self._id = 0
        self.tools: list[dict] = []
        self.resources: list[dict] = []
        self.connected = False
        self.error = ''

    # ── Internal helpers ────────────────────────────────────────────

    def _next_id(self) -> int:
        self._id += 1
        return self._id

    async def _send(self, msg: dict):
        data = json.dumps(msg) + '\n'
        self._proc.stdin.write(data.encode())
        await self._proc.stdin.drain()

    async def _notify(self, method: str, params: dict | None = None):
        await self._send({'jsonrpc': '2.0', 'method': method, 'params': params or {}})

    async def _request(self, method: str, params: dict | None = None, timeout: float = 30) -> dict:
        req_id = self._next_id()
        loop = asyncio.get_event_loop()
        fut: asyncio.Future = loop.create_future()
        self._pending[req_id] = fut
        await self._send({'jsonrpc': '2.0', 'id': req_id, 'method': method, 'params': params or {}})
        try:
            return await asyncio.wait_for(asyncio.shield(fut), timeout=timeout)
        finally:
            self._pending.pop(req_id, None)

    async def _read_loop(self):
        while True:
            try:
                line = await self._proc.stdout.readline()
                if not line:
                    break
                text = line.decode('utf-8', errors='replace').strip()
                if not text:
                    continue
                msg = json.loads(text)
                req_id = msg.get('id')
                if req_id is not None and req_id in self._pending:
                    fut = self._pending.pop(req_id)
                    if not fut.done():
                        if 'error' in msg:
                            fut.set_exception(Exception(str(msg['error'])))
                        else:
                            fut.set_result(msg.get('result', {}))
            except asyncio.CancelledError:
                break
            except json.JSONDecodeError:
                pass  # ignore non-JSON lines (server startup messages)
            except Exception:
                break

    # ── Public API ──────────────────────────────────────────────────

    async def connect(self):
        env = {**os.environ, **self.cfg.env}
        self._proc = await asyncio.create_subprocess_exec(
            self.cfg.command, *self.cfg.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            env=env,
        )
        self._reader_task = asyncio.create_task(self._read_loop())

        # MCP handshake
        await self._request('initialize', {
            'protocolVersion': MCP_PROTOCOL_VERSION,
            'capabilities': {'tools': {}, 'resources': {}},
            'clientInfo': {'name': 'PyAgenticLlama', 'version': '1.0'},
        })
        await self._notify('notifications/initialized')

        # Discover tools
        try:
            resp = await self._request('tools/list')
            self.tools = resp.get('tools', [])
        except Exception:
            self.tools = []

        # Discover resources (optional — not all servers have them)
        try:
            resp = await self._request('resources/list')
            self.resources = resp.get('resources', [])
        except Exception:
            self.resources = []

        self.connected = True
        self.error = ''

    async def disconnect(self):
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
        if self._proc and self._proc.returncode is None:
            try:
                self._proc.terminate()
                await asyncio.wait_for(self._proc.wait(), timeout=5)
            except Exception:
                pass
        self.connected = False
        self.tools = []
        self.resources = []
        self._pending.clear()

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        resp = await self._request('tools/call', {'name': tool_name, 'arguments': arguments}, timeout=60)
        content = resp.get('content', [])
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get('type') == 'text':
                        parts.append(item.get('text', ''))
                    elif item.get('type') == 'image':
                        parts.append('[image data]')
                    elif item.get('type') == 'resource':
                        parts.append(item.get('text', str(item)))
                    else:
                        parts.append(str(item))
                else:
                    parts.append(str(item))
            return '\n'.join(p for p in parts if p)
        return str(content)

    def status(self) -> dict:
        return {
            'name': self.cfg.name,
            'command': self.cfg.command,
            'args': self.cfg.args,
            'env_keys': list(self.cfg.env.keys()),
            'enabled': self.cfg.enabled,
            'description': self.cfg.description,
            'connected': self.connected,
            'error': self.error,
            'tool_count': len(self.tools),
            'tools': [{'name': t['name'], 'description': t.get('description', '')} for t in self.tools],
            'resource_count': len(self.resources),
        }


class MCPManager:
    """Manages multiple MCP server connections and their configs."""

    def __init__(self):
        self._configs: dict[str, MCPConfig] = {}
        self._conns:   dict[str, MCPConnection] = {}
        self._load()

    # ── Persistence ─────────────────────────────────────────────────

    def _load(self):
        if CONFIG_PATH.exists():
            try:
                items = json.loads(CONFIG_PATH.read_text())
                for item in items:
                    cfg = MCPConfig(**{k: v for k, v in item.items() if k in MCPConfig.__dataclass_fields__})
                    self._configs[cfg.name] = cfg
            except Exception:
                pass

    def _save(self):
        CONFIG_PATH.write_text(json.dumps([c.to_dict() for c in self._configs.values()], indent=2))

    # ── Config management ────────────────────────────────────────────

    def add_config(self, name: str, command: str, args: list,
                   env: dict | None = None, description: str = '', enabled: bool = True) -> MCPConfig:
        cfg = MCPConfig(name=name, command=command, args=args,
                        env=env or {}, description=description, enabled=enabled)
        self._configs[name] = cfg
        self._save()
        return cfg

    def update_config(self, name: str, **kwargs) -> MCPConfig:
        if name not in self._configs:
            raise KeyError(f'No server named {name!r}')
        cfg = self._configs[name]
        for k, v in kwargs.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)
        self._save()
        return cfg

    def remove_config(self, name: str):
        self._configs.pop(name, None)
        self._save()

    # ── Connection management ────────────────────────────────────────

    async def connect(self, name: str) -> MCPConnection:
        if name not in self._configs:
            raise KeyError(f'No config for {name!r}')
        # Disconnect old connection if any
        if name in self._conns:
            await self._conns[name].disconnect()
        conn = MCPConnection(self._configs[name])
        self._conns[name] = conn
        try:
            await conn.connect()
        except Exception as e:
            conn.error = str(e)
            conn.connected = False
            raise
        return conn

    async def disconnect(self, name: str):
        if name in self._conns:
            await self._conns[name].disconnect()
            del self._conns[name]

    async def disconnect_all(self):
        for conn in list(self._conns.values()):
            await conn.disconnect()
        self._conns.clear()

    # ── Tool integration ─────────────────────────────────────────────

    def as_openai_tools(self) -> list[dict]:
        """All MCP tools as OpenAI-compatible function specs."""
        tools = []
        for srv_name, conn in self._conns.items():
            if not conn.connected:
                continue
            for tool in conn.tools:
                fn_name = _safe_fn(f'mcp_{_safe_fn(srv_name)}_{_safe_fn(tool["name"])}')
                tools.append({
                    'type': 'function',
                    'function': {
                        'name': fn_name,
                        'description': f'[MCP:{srv_name}] {tool.get("description", "")}',
                        'parameters': tool.get('inputSchema', {'type': 'object', 'properties': {}}),
                    }
                })
        return tools

    def resolve(self, fn_name: str) -> tuple[str, str] | None:
        """Resolve a prefixed fn_name back to (server_name, original_tool_name)."""
        for srv_name, conn in self._conns.items():
            if not conn.connected:
                continue
            prefix = _safe_fn(f'mcp_{_safe_fn(srv_name)}_')
            if fn_name.startswith(prefix):
                original_safe = fn_name[len(prefix):]
                # Find the matching tool by its sanitized name
                for tool in conn.tools:
                    if _safe_fn(tool['name']) == original_safe:
                        return srv_name, tool['name']
        return None

    async def call(self, srv_name: str, tool_name: str, args: dict) -> str:
        if srv_name not in self._conns or not self._conns[srv_name].connected:
            raise RuntimeError(f'MCP server not connected: {srv_name}')
        return await self._conns[srv_name].call_tool(tool_name, args)

    def status(self) -> list[dict]:
        result = []
        for name, cfg in self._configs.items():
            conn = self._conns.get(name)
            if conn:
                result.append(conn.status())
            else:
                result.append({
                    'name': name, 'command': cfg.command, 'args': cfg.args,
                    'env_keys': list(cfg.env.keys()), 'enabled': cfg.enabled,
                    'description': cfg.description, 'connected': False,
                    'error': '', 'tool_count': 0, 'tools': [], 'resource_count': 0,
                })
        return result


# Singleton
mcp = MCPManager()

# Preset templates users can install quickly
PRESETS = [
    {
        'name': 'filesystem',
        'description': 'Read/write files on your PC',
        'command': 'npx',
        'args': ['-y', '@modelcontextprotocol/server-filesystem', 'C:\\Users'],
    },
    {
        'name': 'memory',
        'description': 'Persistent key-value memory store',
        'command': 'npx',
        'args': ['-y', '@modelcontextprotocol/server-memory'],
    },
    {
        'name': 'brave-search',
        'description': 'Web search via Brave Search API (needs BRAVE_API_KEY in vault)',
        'command': 'npx',
        'args': ['-y', '@modelcontextprotocol/server-brave-search'],
        'env': {'BRAVE_API_KEY': ''},
    },
    {
        'name': 'puppeteer',
        'description': 'Browser automation and web scraping',
        'command': 'npx',
        'args': ['-y', '@modelcontextprotocol/server-puppeteer'],
    },
    {
        'name': 'sqlite',
        'description': 'Query and manage a local SQLite database',
        'command': 'npx',
        'args': ['-y', '@modelcontextprotocol/server-sqlite', '--db-path', 'C:\\data\\app.db'],
    },
]
