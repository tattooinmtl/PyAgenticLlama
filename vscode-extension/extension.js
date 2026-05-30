/**
 * PyAgenticLlama VS Code Extension
 * Listens on localhost:3333 for code blocks sent from the PyAgenticLlama app.
 * Each received code block opens as a new untitled tab in VS Code.
 */

const vscode = require('vscode');
const http   = require('http');
const path   = require('path');

let server    = null;
let statusBar = null;
let _connected = false;
let _receivedCount = 0;

// ── Language maps ────────────────────────────────────────────────────────────

const LANG_ID = {
  python: 'python', py: 'python',
  javascript: 'javascript', js: 'javascript',
  typescript: 'typescript', ts: 'typescript',
  html: 'html', css: 'css', scss: 'scss',
  json: 'json', jsonc: 'jsonc',
  bash: 'shellscript', sh: 'shellscript', shell: 'shellscript',
  sql: 'sql',
  yaml: 'yaml', yml: 'yaml',
  markdown: 'markdown', md: 'markdown',
  rust: 'rust', go: 'go',
  java: 'java', kotlin: 'kotlin',
  cpp: 'cpp', c: 'c', csharp: 'csharp', cs: 'csharp',
  php: 'php', ruby: 'ruby', swift: 'swift',
  xml: 'xml', toml: 'toml', ini: 'ini',
  dockerfile: 'dockerfile', docker: 'dockerfile',
  powershell: 'powershell', ps1: 'powershell',
};

const LANG_EXT = {
  python: '.py', py: '.py',
  javascript: '.js', js: '.js',
  typescript: '.ts', ts: '.ts',
  html: '.html', css: '.css', scss: '.scss',
  json: '.json',
  bash: '.sh', sh: '.sh',
  sql: '.sql',
  yaml: '.yaml', yml: '.yaml',
  markdown: '.md', md: '.md',
  rust: '.rs', go: '.go',
  java: '.java', kotlin: '.kt',
  cpp: '.cpp', c: '.c', csharp: '.cs', cs: '.cs',
  php: '.php', ruby: '.rb', swift: '.swift',
  powershell: '.ps1', ps1: '.ps1',
};

// ── Activation ───────────────────────────────────────────────────────────────

function activate(context) {
  // Status bar
  statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 99);
  statusBar.command = 'pyagenticllama.showStatus';
  setStatus(false);
  statusBar.show();
  context.subscriptions.push(statusBar);

  // Commands
  context.subscriptions.push(
    vscode.commands.registerCommand('pyagenticllama.showStatus',       showStatus),
    vscode.commands.registerCommand('pyagenticllama.openApp',          openApp),
    vscode.commands.registerCommand('pyagenticllama.openWorkspace',    openWorkspace),
    vscode.commands.registerCommand('pyagenticllama.openProjectFolder', openProjectFolder),
  );

  // Start HTTP bridge server
  startServer(context);
}

// ── HTTP bridge server ───────────────────────────────────────────────────────

function startServer(context) {
  const cfg  = vscode.workspace.getConfiguration('pyagenticllama');
  const port = cfg.get('port', 3333);

  server = http.createServer((req, res) => {
    // CORS — allow the PyAgenticLlama browser app to call us
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }

    // ── GET /ping ── heartbeat ───────────────────────────────────────
    if (req.method === 'GET' && req.url === '/ping') {
      setStatus(true);
      respond(res, 200, {
        status: 'ok',
        version: '1.0.0',
        workspace: getWorkspacePath(),
        received: _receivedCount,
      });
      return;
    }

    // ── POST /receive ── inbound code block ─────────────────────────
    if (req.method === 'POST' && req.url === '/receive') {
      readBody(req, async (raw) => {
        try {
          const data = JSON.parse(raw);
          await receiveCode(data);
          respond(res, 200, { status: 'ok', count: ++_receivedCount });
        } catch (e) {
          respond(res, 500, { error: e.message });
        }
      });
      return;
    }

    // ── POST /open-folder ── open project workspace ─────────────────
    if (req.method === 'POST' && req.url === '/open-folder') {
      readBody(req, async (raw) => {
        try {
          const { folder } = JSON.parse(raw);
          if (folder) {
            const uri = vscode.Uri.file(folder);
            await vscode.commands.executeCommand('vscode.openFolder', uri, { forceNewWindow: false });
          }
          respond(res, 200, { status: 'ok' });
        } catch (e) {
          respond(res, 500, { error: e.message });
        }
      });
      return;
    }

    res.writeHead(404); res.end();
  });

  server.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
      vscode.window.showWarningMessage(
        `PyAgenticLlama: Port ${port} is already in use. Another instance may be running.`
      );
    } else {
      vscode.window.showErrorMessage(`PyAgenticLlama server error: ${err.message}`);
    }
    setStatus(false, 'port conflict');
  });

  server.listen(port, '127.0.0.1', () => {
    console.log(`[PyAgenticLlama] Bridge listening on 127.0.0.1:${port}`);
    setStatus(false);  // Listening but not yet pinged
  });

  context.subscriptions.push({ dispose: () => { if (server) server.close(); } });
}

// ── Receive code and open in editor ─────────────────────────────────────────

async function receiveCode(data) {
  const code        = String(data.code || '');
  const lang        = String(data.language || '').toLowerCase();
  const projectPath = String(data.project_path || '');
  const filename    = String(data.filename || '');
  const cfg         = vscode.workspace.getConfiguration('pyagenticllama');
  const autoFocus   = cfg.get('autoFocus', true);

  let doc;

  if (projectPath && filename) {
    // Save as a named file inside the project folder
    const ext     = filename.includes('.') ? '' : (LANG_EXT[lang] || '');
    const safeName = filename.replace(/[<>:"/\\|?*]/g, '_');
    const filePath = path.join(projectPath, safeName + ext);
    const uri      = vscode.Uri.file(filePath);
    await vscode.workspace.fs.writeFile(uri, Buffer.from(code, 'utf8'));
    doc = await vscode.workspace.openTextDocument(uri);
  } else {
    // Create an untitled document — user names it on save
    doc = await vscode.workspace.openTextDocument({
      content: code,
      language: LANG_ID[lang] || undefined,
    });
  }

  await vscode.window.showTextDocument(doc, {
    preview: false,          // Don't reuse the preview tab — always new tab
    preserveFocus: !autoFocus,
  });

  if (autoFocus) {
    // Bring VS Code window to front
    vscode.window.showInformationMessage(
      `📨 Code received from PyAgenticLlama${lang ? ` (${lang})` : ''}`
    );
  }

  setStatus(true);
}

// ── Commands ─────────────────────────────────────────────────────────────────

function showStatus() {
  const cfg  = vscode.workspace.getConfiguration('pyagenticllama');
  const port = cfg.get('port', 3333);
  const info = _connected
    ? `Connected — ${_receivedCount} file(s) received this session`
    : `Listening on port ${port} — waiting for PyAgenticLlama`;
  vscode.window.showInformationMessage(
    `🦙 PyAgenticLlama: ${info}`, 'Open App', 'Open Workspace'
  ).then(choice => {
    if (choice === 'Open App')       openApp();
    if (choice === 'Open Workspace') openWorkspace();
  });
}

function openApp() {
  const url = vscode.workspace.getConfiguration('pyagenticllama').get('appUrl', 'http://localhost:7860');
  vscode.env.openExternal(vscode.Uri.parse(url));
}

/**
 * Open the PyAgenticLlama shared workspace/ folder directly — no file picker.
 * Path is taken from settings (pyagenticllama.workspacePath) or auto-fetched
 * from the running app via GET /api/workspace.
 */
async function openWorkspace() {
  const cfg = vscode.workspace.getConfiguration('pyagenticllama');
  let wsPath = cfg.get('workspacePath', '').trim();

  if (!wsPath) {
    // Auto-detect: ask the running app for the workspace path
    try {
      const appUrl = cfg.get('appUrl', 'http://localhost:7860');
      const res    = await fetch(`${appUrl}/api/workspace`);
      if (res.ok) {
        const data = await res.json();
        wsPath = data.path || '';
      }
    } catch (_) { /* app not running — fall through to error */ }
  }

  if (!wsPath) {
    vscode.window.showErrorMessage(
      'Could not find the PyAgenticLlama workspace folder. ' +
      'Set pyagenticllama.workspacePath in VS Code settings, or make sure the app is running.'
    );
    return;
  }

  const uri = vscode.Uri.file(wsPath);
  await vscode.commands.executeCommand('vscode.openFolder', uri, { forceNewWindow: false });
}

async function openProjectFolder() {
  const folder = await vscode.window.showOpenDialog({
    canSelectFolders: true,
    canSelectFiles: false,
    openLabel: 'Open as Workspace',
  });
  if (folder?.[0]) {
    await vscode.commands.executeCommand('vscode.openFolder', folder[0], { forceNewWindow: false });
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function setStatus(connected, note) {
  _connected = connected;
  if (!statusBar) return;
  if (note) {
    statusBar.text = `$(plug) PyAgenticLlama ⚠`;
    statusBar.tooltip = `PyAgenticLlama — ${note}`;
    statusBar.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
  } else if (connected) {
    statusBar.text = `$(plug) PyAgenticLlama ●`;
    statusBar.tooltip = `PyAgenticLlama connected — ${_receivedCount} received`;
    statusBar.backgroundColor = undefined;
  } else {
    statusBar.text = `$(plug) PyAgenticLlama`;
    statusBar.tooltip = 'PyAgenticLlama — listening, not yet connected';
    statusBar.backgroundColor = undefined;
  }
}

function getWorkspacePath() {
  return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '';
}

function respond(res, code, obj) {
  res.writeHead(code, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(obj));
}

function readBody(req, cb) {
  let buf = '';
  req.on('data', chunk => buf += chunk);
  req.on('end', () => cb(buf));
}

function deactivate() {
  if (server) server.close();
}

module.exports = { activate, deactivate };
