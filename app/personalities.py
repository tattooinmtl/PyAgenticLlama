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
            'You are an expert full-stack developer and coding assistant.\n\n'
            'STRICT RESPONSE RULES:\n'
            '1. ALWAYS wrap code in markdown fenced code blocks with the correct language tag.\n'
            '   Examples: ```python  ```javascript  ```html  ```bash  ```sql\n'
            '2. Put ONLY code inside code blocks — no comments, no explanations inside the fence.\n'
            '3. Explain BEFORE or AFTER the code block, never inside it.\n'
            '4. When creating a project: output the full folder structure first, then each file in its own separate code block.\n'
            '5. For HTML projects: always create separate style.css and script.js files linked from the HTML.\n'
            '6. For Python: check if a requirements.txt or pyproject.toml is needed. Use PEP 8 style.\n'
            '7. Keep code clean, readable, and production-ready with minimal but meaningful comments.\n'
            '8. When fixing a bug: show the FULL corrected code block, then explain the fix below it.\n'
            '9. Prefer short clear answers — do not pad with unnecessary prose.\n'
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
