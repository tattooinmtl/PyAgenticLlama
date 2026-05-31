import asyncio, contextlib, httpx
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
SERVER_EXE = BASE_DIR / 'llama_exec' / 'llama-server.exe'

class LlamaServer:
    def __init__(self, port: int = 8080, name: str = 'main'):
        self.port = port
        self.name = name
        self.model_path: str | None = None
        self.context_length: int = 4096
        self.gpu_layers: int = 0
        self.mmproj_path: str | None = None
        self._proc: asyncio.subprocess.Process | None = None
        self._log_fh = None
        self._log_path = BASE_DIR / f'llama-{name}.log'

    @property
    def running(self) -> bool:
        return self._proc is not None and self._proc.returncode is None

    async def start(self, model_path: str, context_length: int = 16384, gpu_layers: int = 0,
                    mmproj_path: str | None = None, flash_attn: bool = False,
                    sleep_idle_seconds: int = 300):
        if self.running:
            await self.stop()
        self.model_path = model_path
        self.context_length = context_length
        self.gpu_layers = gpu_layers
        self.mmproj_path = mmproj_path
        cmd = [
            str(SERVER_EXE),
            '-m', model_path,
            '-c', str(context_length),
            '--gpu-layers', str(gpu_layers),
            '--port', str(self.port),
            '--host', '127.0.0.1',
            '--parallel', '1',
            '--sleep-idle-seconds', str(sleep_idle_seconds),
        ]
        if flash_attn:
            cmd += ['--flash-attn', 'on']
        if mmproj_path:
            cmd += ['--mmproj', mmproj_path]
        self._log_fh = open(self._log_path, 'w', encoding='utf-8', errors='replace')
        self._proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=self._log_fh, stderr=self._log_fh
        )
        await self._wait_ready()

    async def _wait_ready(self, timeout: int = 300):
        for _ in range(timeout * 2):
            if not self.running:
                tail = ''
                with contextlib.suppress(Exception):
                    lines = self._log_path.read_text(errors='replace').splitlines()
                    tail = '\n'.join(lines[-5:])
                raise RuntimeError(f'llama-server ({self.name}) crashed.\n{tail}')
            with contextlib.suppress(Exception):
                async with httpx.AsyncClient() as c:
                    r = await c.get(f'http://127.0.0.1:{self.port}/health', timeout=1.0)
                    if r.status_code == 200 and r.json().get('status') == 'ok':
                        return
            await asyncio.sleep(0.5)
        raise TimeoutError(f'Server ({self.name}) not ready after {timeout}s')

    async def stop(self):
        if self._proc and self._proc.returncode is None:
            self._proc.terminate()
            try:
                await asyncio.wait_for(self._proc.wait(), timeout=10)
            except asyncio.TimeoutError:
                self._proc.kill()
        self._proc = None
        self.model_path = None
        if self._log_fh:
            with contextlib.suppress(Exception):
                self._log_fh.close()
            self._log_fh = None

    def base_url(self) -> str:
        return f'http://127.0.0.1:{self.port}'

    def status(self) -> dict:
        return {
            'name': self.name,
            'running': self.running,
            'model': self.model_path,
            'context_length': self.context_length,
            'gpu_layers': self.gpu_layers,
            'mmproj': self.mmproj_path,
            'port': self.port,
        }

# ── Registry ──────────────────────────────────────────────────────

_registry: dict[str, LlamaServer] = {}
_next_port = 8081

def get_server(name: str = 'main') -> LlamaServer:
    if name not in _registry:
        global _next_port
        port = 8080 if name == 'main' else _next_port
        if name != 'main':
            _next_port += 1
        _registry[name] = LlamaServer(port=port, name=name)
    return _registry[name]

def all_servers() -> list[dict]:
    return [s.status() for s in _registry.values()]

async def stop_all():
    for s in _registry.values():
        if s.running:
            await s.stop()
