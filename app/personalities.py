import json, uuid
from pathlib import Path

PDIR = Path(__file__).parent / 'personalities'
PDIR.mkdir(exist_ok=True)

_DEFAULTS = [
    {
        'id': 'default',
        'name': 'Assistant',
        'avatar': '#7c3aed',
        'system_prompt': 'You are a helpful, harmless, and honest AI assistant.',
        'temperature': 0.7,
        'top_p': 0.9,
        'icon': '🤖',
    },
    {
        'id': 'coder',
        'name': 'Coder',
        'avatar': '#0ea5e9',
        'system_prompt': (
            'You are an expert software engineer. '
            'Provide concise, correct code. Use code blocks. '
            'Minimize prose unless the user asks for explanation.'
        ),
        'temperature': 0.2,
        'top_p': 0.95,
        'icon': '💻',
    },
    {
        'id': 'creative',
        'name': 'Creative',
        'avatar': '#f59e0b',
        'system_prompt': (
            'You are a creative writing assistant. '
            'Be imaginative, expressive, and engaging. '
            'Paint vivid pictures with words.'
        ),
        'temperature': 1.1,
        'top_p': 0.95,
        'icon': '✨',
    },
    {
        'id': 'analyst',
        'name': 'Analyst',
        'avatar': '#22c55e',
        'system_prompt': (
            'You are a precise data analyst. '
            'Give structured, factual responses. '
            'Use bullet points and tables where helpful. '
            'Always cite your reasoning.'
        ),
        'temperature': 0.3,
        'top_p': 0.85,
        'icon': '📊',
    },
]

def _seed():
    for p in _DEFAULTS:
        path = PDIR / f"{p['id']}.json"
        if not path.exists():
            path.write_text(json.dumps(p, indent=2))

def list_personalities() -> list[dict]:
    _seed()
    result = []
    for f in sorted(PDIR.glob('*.json')):
        try:
            result.append(json.loads(f.read_text()))
        except Exception:
            pass
    return result

def get_personality(id_: str) -> dict | None:
    path = PDIR / f'{id_}.json'
    return json.loads(path.read_text()) if path.exists() else None

def save_personality(data: dict) -> dict:
    if 'id' not in data or not data['id']:
        data['id'] = str(uuid.uuid4())[:8]
    (PDIR / f"{data['id']}.json").write_text(json.dumps(data, indent=2))
    return data

def delete_personality(id_: str):
    if id_ in ('default', 'coder', 'creative', 'analyst'):
        raise ValueError('Cannot delete built-in personalities')
    path = PDIR / f'{id_}.json'
    if path.exists():
        path.unlink()
