/**
 * PyAgenticLlama VS Code Extension
 * Listens on localhost:3333 for code blocks sent from the PyAgenticLlama app.
 * Provides a status bar item and a sidebar panel in the activity bar.
 */

const vscode = require('vscode');
const http   = require('http');
const path   = require('path');

let server        = null;
let statusBar     = null;
let _connected    = false;
let _receivedCount = 0;
let _statusProvider = null;
let _actionsProvider = null;

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

// ── Tree data providers ──────────────────────────────────────────────────────

class StatusItem extends vscode.TreeItem {
  constructor(label, description, icon, command) {
    super(label, vscode.TreeItemCollapsibleState.None);
    this.description = description;
    if (icon) this.iconPath = new vscode.ThemeIcon(icon);
    if (command) this.command = command;
  }
}

class StatusProvider {
  constructor() {
    this._onDidChangeTreeData = new vscode.EventEmitter();
    this.onDidChangeTreeData = this._onDidChangeTreeData.event;
  }
  refresh() { this._onDidChangeTreeData.fire(); }
  getTreeItem(el) { return el; }
  getChildren() {
    const cfg  = vscode.workspace.getConfiguration('pyagenticllama');
    const port = cfg.get('port', 3333);
    const url  = cfg.get('appUrl', 'http://localhost:7860');
    return [
      new StatusItem(
        _connected ? 'Connected' : 'Waiting',
        _connected ? `${_receivedCount} file(s) received` : 'app not yet pinged',
        _connected ? 'circle-filled' : 'circle-outline'
      ),
      new StatusItem('Port', String(port), 'plug'),
      new StatusItem('App URL', url, 'link'),
    ];
  }
}

class ActionsProvider {
  constructor() {
    this._onDidChangeTreeData = new vscode.EventEmitter();
    this.onDidChangeTreeData = this._onDidChangeTreeData.event;
  }
  refresh() { this._onDidChangeTreeData.fire(); }
  getTreeItem(el) { return el; }
  getChildren() {
    return [
      new StatusItem('Open App in Browser', '', 'globe', {
        command: 'pyagenticllama.openApp', title: 'Open App'
      }),
      new StatusItem('Open Workspace Folder', '', 'folder-opened', {
        command: 'pyagenticllama.openWorkspace', title: 'Open Workspace'
      }),
      new StatusItem('Browse Project Folder…', '', 'folder', {
        command: 'pyagenticllama.openProjectFolder', title: 'Browse Folder'
      }),
      new StatusItem('Settings', '', 'settings-gear', {
        command: 'workbench.action.openSettings',
        title: 'Open Settings',
        arguments: ['pyagenticllama']
      }),
    ];
  }
}

// ── Activation ───────────────────────────────────────────────────────────────

function activate(context) {
  // Status bar
  statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 99);
  statusBar.command = 'pyagenticllama.showStatus';
  setStatus(false);
  statusBar.show();
  context.subscriptions.push(statusBar);

  // Sidebar tree views
  _statusProvider  = new StatusProvider();
  _actionsProvider = new ActionsProvider();
  context.subscriptions.push(
    vscode.window.registerTreeDataProvider('pyagenticllama.statusView',  _statusProvider),
    vscode.window.registerTreeDataProvider('pyagenticllama.actionsView', _actionsProvider),
  );

  // Commands
  context.subscriptions.push(
    vscode.commands.registerCommand('pyagenticllama.showStatus',        showStatus),
    vscode.commands.registerCommand('pyagenticllama.openApp',           openApp),
    vscode.commands.registerCommand('pyagenticllama.openWorkspace',     openWorkspace),
    vscode.commands.registerCommand('pyagenticllama.openProjectFolder', openProjectFolder),
    vscode.commands.registerCommand('pyagenticllama.refreshView',       () => {
      _statusProvider.refresh();
      _actionsProvider.refresh();
    }),
  );

  startServer(context);
}

// ── HTTP bridge server ───────────────────────────────────────────────────────

function startServer(context) {
  const cfg  = vscode.workspace.getConfiguration('pyagenticllama');
  const port = cfg.get('port', 3333);

  server = http.createServer((req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }

    if (req.method === 'GET' && req.url === '/ping') {
      setStatus(true);
      respond(res, 200, {
        status: 'ok', version: '1.0.0',
        workspace: getWorkspacePath(), received: _receivedCount,
      });
      return;
    }

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

    if (req.method === 'POST' && req.url === '/open-folder') {
      readBody(req, async (raw) => {
        try {
          const { folder } = JSON.parse(raw);
          if (folder) {
            await vscode.commands.executeCommand(
              'vscode.openFolder', vscode.Uri.file(folder), { forceNewWindow: false }
            );
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
    setStatus(false);
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
    const ext      = filename.includes('.') ? '' : (LANG_EXT[lang] || '');
    const safeName = filename.replace(/[<>:"/\\|?*]/g, '_');
    const filePath = path.join(projectPath, safeName + ext);
    const uri      = vscode.Uri.file(filePath);
    await vscode.workspace.fs.writeFile(uri, Buffer.from(code, 'utf8'));
    doc = await vscode.workspace.openTextDocument(uri);
  } else {
    doc = await vscode.workspace.openTextDocument({
      content: code,
      language: LANG_ID[lang] || undefined,
    });
  }

  await vscode.window.showTextDocument(doc, { preview: false, preserveFocus: !autoFocus });

  if (autoFocus) {
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

async function openWorkspace() {
  const cfg = vscode.workspace.getConfiguration('pyagenticllama');
  let wsPath = cfg.get('workspacePath', '').trim();

  if (!wsPath) {
    try {
      const appUrl = cfg.get('appUrl', 'http://localhost:7860');
      const res    = await fetch(`${appUrl}/api/workspace`);
      if (res.ok) {
        const data = await res.json();
        wsPath = data.path || '';
      }
    } catch (_) {}
  }

  if (!wsPath) {
    vscode.window.showErrorMessage(
      'Could not find the PyAgenticLlama workspace folder. ' +
      'Set pyagenticllama.workspacePath in VS Code settings, or make sure the app is running.'
    );
    return;
  }

  await vscode.commands.executeCommand(
    'vscode.openFolder', vscode.Uri.file(wsPath), { forceNewWindow: false }
  );
}

async function openProjectFolder() {
  const folder = await vscode.window.showOpenDialog({
    canSelectFolders: true, canSelectFiles: false, openLabel: 'Open as Workspace',
  });
  if (folder?.[0]) {
    await vscode.commands.executeCommand('vscode.openFolder', folder[0], { forceNewWindow: false });
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function setStatus(connected, note) {
  _connected = connected;
  if (_statusProvider) _statusProvider.refresh();
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
