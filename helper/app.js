// ── Scroll progress bar ───────────────────────────────────────────
window.addEventListener('scroll', () => {
  const max = document.documentElement.scrollHeight - window.innerHeight;
  const pct = max > 0 ? (window.scrollY / max) * 100 : 0;
  document.getElementById('progress-bar').style.width = pct + '%';
});

// ── Copy to clipboard ─────────────────────────────────────────────
function copyCode(btn) {
  const pre = btn.closest('.code-wrap').querySelector('pre');
  const text = pre.innerText || pre.textContent;
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 2000);
  }).catch(() => {
    // Fallback for non-secure context
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 2000);
  });
}

// ── Builder ───────────────────────────────────────────────────────
let _paramCount = 0;

function addParam(name = '', type = 'string', desc = '') {
  _paramCount++;
  const id = _paramCount;
  const row = document.createElement('div');
  row.className = 'param-row';
  row.id = `pr-${id}`;
  row.innerHTML = `
    <input type="text"   id="pn-${id}" placeholder="param_name"   value="${esc(name)}" oninput="buildOutput()">
    <select              id="pt-${id}" onchange="buildOutput()">
      ${['string','integer','number','boolean','array'].map(t =>
        `<option value="${t}"${t === type ? ' selected' : ''}>${t}</option>`
      ).join('')}
    </select>
    <input type="text"   id="pd-${id}" placeholder="What this does" value="${esc(desc)}" oninput="buildOutput()">
    <button class="param-rm" onclick="removeParam(${id})" title="Remove">×</button>
  `;
  document.getElementById('param-rows').appendChild(row);
  buildOutput();
}

function removeParam(id) {
  const el = document.getElementById(`pr-${id}`);
  if (el) el.remove();
  buildOutput();
}

function resetBuilder() {
  document.getElementById('b-name').value = '';
  document.getElementById('b-desc').value = '';
  document.getElementById('b-webhook').value = '';
  document.getElementById('b-action').value = 'python';
  document.getElementById('param-rows').innerHTML = '';
  document.getElementById('webhook-row').style.display = 'none';
  _paramCount = 0;
  buildOutput();
}

document.getElementById('b-action').addEventListener('change', function () {
  document.getElementById('webhook-row').style.display =
    this.value === 'webhook' ? '' : 'none';
});

function _getParams() {
  const rows = document.querySelectorAll('.param-row');
  const params = [];
  rows.forEach(row => {
    const id = row.id.replace('pr-', '');
    const name = (document.getElementById(`pn-${id}`)?.value || '').trim();
    const type = document.getElementById(`pt-${id}`)?.value || 'string';
    const desc = (document.getElementById(`pd-${id}`)?.value || '').trim();
    if (name) params.push({ name, type, desc });
  });
  return params;
}

function _slugify(str) {
  return str.trim().toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '') || 'my_skill';
}

function buildOutput() {
  const name    = (document.getElementById('b-name').value || '').trim();
  const desc    = (document.getElementById('b-desc').value || '').trim();
  const action  = document.getElementById('b-action').value;
  const webhook = (document.getElementById('b-webhook').value || '').trim();
  const params  = _getParams();
  const slug    = _slugify(name);

  // ── JSON ───────────────────────────────────────────────────────
  const properties = {};
  const required = [];
  params.forEach(p => {
    properties[p.name] = { type: p.type, description: p.desc || p.name };
    required.push(p.name);
  });

  const json = {
    id: slug,
    name: name || 'My Skill',
    description: desc || 'Describe what this skill does.',
    parameters: {
      type: 'object',
      properties,
      required,
    },
    action_type: action,
    code: '',
    webhook_url: action === 'webhook' ? webhook : '',
    enabled: true,
  };

  document.getElementById('out-json').innerHTML =
    '<code>' + syntaxJson(JSON.stringify(json, null, 2)) + '</code>';

  // ── Python ─────────────────────────────────────────────────────
  const paramLines = params.map(p => {
    const cast = p.type === 'integer' ? 'int(' : p.type === 'number' ? 'float(' : '';
    const close = cast ? ')' : '';
    return `    ${p.name} = ${cast}kwargs.get('${p.name}', ${p.type === 'boolean' ? 'False' : p.type === 'integer' || p.type === 'number' ? '0' : "''"})${close}`;
  });

  const checkLines = params
    .filter(p => p.type === 'string')
    .map(p => `    if not ${p.name}:\n        return 'Missing required parameter: ${p.name}'`);

  const bodyHint = action === 'webhook'
    ? `    # Webhook mode — body is sent as JSON by the engine\n    # This code won't run for webhook skills\n    pass`
    : `    # ── Your logic here ──────────────────────────────────────\n    # Use httpx, json, os, subprocess, Path, vault_get freely\n    result = f'${name || "Skill"} called${params.length ? ' with: ' + params.map(p => `{${p.name}}`).join(', ') : ''}'\n    return str(result)`;

  const py = [
    `def execute(**kwargs):`,
    `    """${desc || (name ? name + ' skill' : 'My skill')}."""`,
    ...(paramLines.length ? ['    # Read parameters', ...paramLines] : []),
    ...(checkLines.length ? ['', ...checkLines] : []),
    '',
    bodyHint,
  ].join('\n');

  document.getElementById('out-py').innerHTML =
    '<code>' + syntaxPy(py) + '</code>';
}

// ── Tab switcher ──────────────────────────────────────────────────
function switchTab(el, panelId) {
  document.querySelectorAll('.out-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.out-panel').forEach(p => p.classList.remove('active'));
  el.classList.add('active');
  document.getElementById(panelId).classList.add('active');
}

// ── Examples ─────────────────────────────────────────────────────
const EXAMPLES = {
  calculator: {
    name: 'Calculator',
    desc: 'Evaluate a safe math expression and return the numeric result.',
    params: [{ name: 'expression', type: 'string', desc: 'Math expression to evaluate, e.g. "2 ** 10 + 5"' }],
    code: `import ast, operator

_SAFE_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg,
}

def _safe_eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError(f'Unsupported operation: {ast.dump(node)}')

def execute(**kwargs):
    expr = kwargs.get('expression', '').strip()
    if not expr:
        return 'No expression provided.'
    try:
        tree = ast.parse(expr, mode='eval')
        result = _safe_eval(tree.body)
        return f'{expr} = {result}'
    except Exception as e:
        return f'Error: {e}'`,
  },

  'fetch-url': {
    name: 'Fetch URL',
    desc: 'Fetch a webpage and return its plain-text content (strips HTML tags).',
    params: [
      { name: 'url', type: 'string', desc: 'Full URL to fetch, including https://' },
      { name: 'max_chars', type: 'integer', desc: 'Maximum characters to return (default 3000)' },
    ],
    code: `import httpx, re

def execute(**kwargs):
    url = kwargs.get('url', '').strip()
    max_chars = int(kwargs.get('max_chars', 3000))
    if not url:
        return 'No URL provided.'
    try:
        r = httpx.get(url, timeout=10, follow_redirects=True,
                      headers={'User-Agent': 'Mozilla/5.0'})
        r.raise_for_status()
        # Strip HTML tags and collapse whitespace
        text = re.sub(r'<[^>]+>', ' ', r.text)
        text = re.sub(r'\\s+', ' ', text).strip()
        return text[:max_chars] + ('...' if len(text) > max_chars else '')
    except httpx.HTTPStatusError as e:
        return f'HTTP error {e.response.status_code}: {url}'
    except Exception as e:
        return f'Error fetching URL: {e}'`,
  },

  'read-file': {
    name: 'Read File',
    desc: 'Read a text file from the server filesystem and return its contents.',
    params: [
      { name: 'path', type: 'string', desc: 'Absolute or relative file path to read' },
      { name: 'max_lines', type: 'integer', desc: 'Maximum lines to return (default 100)' },
    ],
    code: `from pathlib import Path

def execute(**kwargs):
    path = kwargs.get('path', '').strip()
    max_lines = int(kwargs.get('max_lines', 100))
    if not path:
        return 'No path provided.'
    p = Path(path)
    if not p.exists():
        return f'File not found: {path}'
    if not p.is_file():
        return f'Not a file: {path}'
    try:
        lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
        truncated = len(lines) > max_lines
        result = '\\n'.join(lines[:max_lines])
        if truncated:
            result += f'\\n... ({len(lines) - max_lines} more lines)'
        return result
    except PermissionError:
        return f'Permission denied: {path}'
    except Exception as e:
        return f'Error reading file: {e}'`,
  },

  'run-python': {
    name: 'Run Python',
    desc: 'Execute a Python code snippet in a subprocess and return its stdout/stderr.',
    params: [
      { name: 'code', type: 'string', desc: 'Python code to execute' },
      { name: 'timeout', type: 'integer', desc: 'Timeout in seconds (default 10)' },
    ],
    code: `import subprocess, sys

def execute(**kwargs):
    code = kwargs.get('code', '').strip()
    timeout = int(kwargs.get('timeout', 10))
    if not code:
        return 'No code provided.'
    try:
        result = subprocess.run(
            [sys.executable, '-c', code],
            capture_output=True, text=True,
            timeout=timeout
        )
        out = result.stdout.strip()
        err = result.stderr.strip()
        parts = []
        if out: parts.append(out)
        if err: parts.append('STDERR:\\n' + err)
        if result.returncode != 0:
            parts.append(f'Exit code: {result.returncode}')
        return '\\n'.join(parts) if parts else '(no output)'
    except subprocess.TimeoutExpired:
        return f'Timed out after {timeout}s'
    except Exception as e:
        return f'Error: {e}'`,
  },
};

let _activeExample = null;

function showExample(key) {
  const cards = document.querySelectorAll('.example-card');
  cards.forEach((c, i) => {
    const keys = Object.keys(EXAMPLES);
    c.classList.toggle('active', keys[i] === key);
  });

  if (_activeExample === key) {
    document.getElementById('example-detail').classList.remove('visible');
    document.getElementById('example-detail').innerHTML = '';
    _activeExample = null;
    return;
  }
  _activeExample = key;

  const ex = EXAMPLES[key];
  const detail = document.getElementById('example-detail');

  const paramRows = ex.params.map(p =>
    `<tr><td class="param-name">${esc(p.name)}</td><td class="param-type">${esc(p.type)}</td><td class="param-desc">${esc(p.desc)}</td></tr>`
  ).join('');

  detail.innerHTML = `
    <div style="padding:18px 22px; background:var(--surface2); border-bottom:1px solid var(--border)">
      <div style="font-weight:700;font-size:16px;color:var(--text);margin-bottom:4px">${esc(ex.name)}</div>
      <div style="font-size:13px;color:var(--text2)">${esc(ex.desc)}</div>
      ${ex.params.length ? `
        <table class="param-table" style="margin-top:14px">
          <thead><tr><th>Parameter</th><th>Type</th><th>Description</th></tr></thead>
          <tbody>${paramRows}</tbody>
        </table>` : ''}
    </div>
    <div class="code-wrap" style="border-radius:0;border:none;border-top:1px solid var(--border)">
      <div class="code-header">
        <span class="code-lang">Python</span>
        <button class="btn-copy" onclick="copyCode(this)">Copy</button>
      </div>
      <pre><code>${syntaxPy(ex.code)}</code></pre>
    </div>
    <div style="padding:12px 20px;border-top:1px solid var(--border);background:var(--surface2)">
      <button class="btn btn-ghost btn-sm" onclick="loadIntoBuilder('${key}')">Load into Builder ↑</button>
    </div>
  `;
  detail.classList.add('visible');
  setTimeout(() => detail.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 50);
}

function loadIntoBuilder(key) {
  const ex = EXAMPLES[key];
  document.getElementById('b-name').value = ex.name;
  document.getElementById('b-desc').value = ex.desc;
  document.getElementById('param-rows').innerHTML = '';
  _paramCount = 0;
  ex.params.forEach(p => addParam(p.name, p.type, p.desc));
  buildOutput();
  // Switch to Python tab and scroll up
  const pyTab = document.querySelector('.out-tab:last-of-type');
  if (pyTab) switchTab(pyTab, 'tab-py');
  document.getElementById('builder').scrollIntoView({ behavior: 'smooth' });
}

// ── Minimal syntax highlighters ───────────────────────────────────
function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function syntaxJson(raw) {
  return esc(raw)
    .replace(/(&quot;)([^&]+)(&quot;)(\s*:)/g,
      '<span class="key">$1$2$3</span>$4')
    .replace(/:\s*(&quot;)([^&]*)(&quot;)/g,
      ': <span class="str">$1$2$3</span>')
    .replace(/:\s*(true|false)/g,
      ': <span class="kw">$1</span>')
    .replace(/:\s*(\d+\.?\d*)/g,
      ': <span class="num">$1</span>');
}

function syntaxPy(raw) {
  return esc(raw)
    // strings (single and double quoted, one-line)
    .replace(/(&#39;[^&#]*&#39;|&quot;[^&]*&quot;)/g, '<span class="str">$1</span>')
    // comments
    .replace(/(#[^\n]*)/g, '<span class="cmt">$1</span>')
    // keywords
    .replace(/\b(def|return|import|from|if|elif|else|for|while|in|not|and|or|is|try|except|raise|with|as|class|True|False|None|pass)\b/g,
      '<span class="kw">$1</span>')
    // function calls
    .replace(/\b([a-zA-Z_]\w*)\(/g, '<span class="fn">$1</span>(')
    // numbers
    .replace(/\b(\d+\.?\d*)\b/g, '<span class="num">$1</span>');
}

// ── Init ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  addParam('query', 'string', 'The search term or input');
  buildOutput();
});
