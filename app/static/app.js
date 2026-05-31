// ── State ─────────────────────────────────────────────────────────
const state = {
  models: [],
  selectedModel: null,
  serverRunning: false,
  externalProvider: false,   // true when an external API provider is active
  modelInfo: null,           // full info object from /api/models/info for loaded model
  provider: null,            // current provider config
  csOpen: false,             // CodingSpace panel open
  mode: 'chat',              // 'chat' | 'agent'
  convId: 'default',
  personalityId: 'default',
  personalities: [],
  streaming: false,
  browserPath: 'C:\\',
  browserSelected: null,
  currentTps: 0,
  contextLength: 0,          // set when model loads; drives live context bar
};

// True when something can handle a chat request (local server OR external provider)
function _canChat() { return state.serverRunning || state.externalProvider; }

// ── API ───────────────────────────────────────────────────────────
const API = {
  async get(path) {
    const r = await fetch(path);
    if (!r.ok) { const t = await r.text(); throw new Error(t); }
    return r.json();
  },
  async post(path, body = {}) {
    const r = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) { const t = await r.text(); throw new Error(t); }
    return r.json();
  },
  async put(path, body) {
    const r = await fetch(path, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) { const t = await r.text(); throw new Error(t); }
    return r.json();
  },
  async del(path) {
    const r = await fetch(path, { method: 'DELETE' });
    if (!r.ok) { const t = await r.text(); throw new Error(t); }
    return r.json();
  },
};

// ── Toast ─────────────────────────────────────────────────────────
function toast(msg, type = 'info', ms = 3500) {
  const c = document.getElementById('toasts');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  c.appendChild(el);
  setTimeout(() => el.remove(), ms);
}

// ── Modal helpers ─────────────────────────────────────────────────
function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

// ── Menu bar ──────────────────────────────────────────────────────
function initMenuBar() {
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.menu-item')) {
      document.querySelectorAll('.menu-item.open').forEach(el => el.classList.remove('open'));
    }
  });
  document.querySelectorAll('.menu-trigger').forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.stopPropagation();
      const item = trigger.closest('.menu-item');
      const wasOpen = item.classList.contains('open');
      document.querySelectorAll('.menu-item.open').forEach(el => el.classList.remove('open'));
      if (!wasOpen) item.classList.add('open');
    });
  });
  document.querySelectorAll('[data-action]').forEach(el => {
    el.addEventListener('click', (e) => {
      e.stopPropagation();
      document.querySelectorAll('.menu-item.open').forEach(i => i.classList.remove('open'));
      handleAction(el.dataset.action);
    });
  });
}

function handleAction(action) {
  switch (action) {
    case 'new-chat':       newChat(); break;
    case 'save-chat':      saveChat(); break;
    case 'open-browser':   openFileBrowser(); break;
    case 'add-model-path': promptAddModelPath(); break;
    case 'exit':           window.close(); break;
    case 'compact-ctx':    compactContext(); break;
    case 'clear-ctx':      clearContext(); break;
    case 'clear-memories': if (confirm('Clear all memories?')) clearAllMemories(); break;
    case 'toggle-left':    document.getElementById('left-panel').classList.toggle('hidden'); break;
    case 'toggle-right':   document.getElementById('right-panel').classList.toggle('hidden'); break;
    case 'scroll-bottom':  scrollToBottom(); break;
    case 'load-model':     loadModel(); break;
    case 'stop-server':    stopServer(); break;
    case 'model-inspector': openInspector(); break;
    case 'server-log':     openLogModal(); break;
    case 'open-vault':     openVaultModal(); break;
    case 'open-personalities': openPersonalitiesModal(); break;
    case 'open-mcp':       switchRightTab('mcp'); loadMcpServers(); break;
    case 'new-skill':      openSkillModal(null); break;
    case 'test-skill':     switchRightTab('skills'); loadSkills(); toast('Pick a skill from the Skills tab and click Run', 'info', 4000); break;
    case 'toggle-agent-mode': setMode(state.mode === 'agent' ? 'chat' : 'agent'); break;
    case 'spawn-agent':    openSpawnModal(); break;
    case 'view-agents':    switchRightTab('agents'); loadAgents(); break;
    case 'show-shortcuts': toast('Enter=Send, Shift+Enter=Newline, Ctrl+N=New chat', 'info', 5000); break;
    case 'about':          toast('PyAgenticLlama — Advanced llama.cpp interface', 'info', 4000); break;
  }
}

// ── Panel tabs ────────────────────────────────────────────────────
function initTabs() {
  document.querySelectorAll('.panel-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const panel = tab.closest('.left-panel, .right-panel');
      const tabName = tab.dataset.tab;
      panel.querySelectorAll('.panel-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tabName));
      panel.querySelectorAll('.panel-content').forEach(c => c.classList.toggle('active', c.dataset.tab === tabName));
      // Lazy load when tab activated
      if (tabName === 'memory')  loadMemories();
      if (tabName === 'agents')  loadAgents();
      if (tabName === 'history') loadHistory();
      if (tabName === 'skills')  loadSkills();
      if (tabName === 'mcp')     loadMcpServers();
    });
  });
}

function switchRightTab(name) {
  const rp = document.getElementById('right-panel');
  rp.querySelectorAll('.panel-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === name));
  rp.querySelectorAll('.panel-content').forEach(c => c.classList.toggle('active', c.dataset.tab === name));
}

// ── Hardware ──────────────────────────────────────────────────────
async function loadHardware() {
  try {
    const hw = await API.get('/api/hardware');
    const el = document.getElementById('hw-info');
    el.innerHTML = `
      <div class="hw-row"><span class="hw-label">RAM</span><span class="hw-val">${hw.ram_available_gb} / ${hw.ram_total_gb} GB free</span></div>
      <div class="hw-row"><span class="hw-label">VRAM</span><span class="hw-val">${hw.vram_gb} GB</span></div>
      <div class="hw-row" style="margin-top:4px"><span class="hw-label" style="color:var(--text2);font-size:11px">${hw.gpu_name}</span></div>
      <div class="hw-row"><span class="hw-label" style="color:var(--text2);font-size:11px">${hw.cpu_name}</span></div>
    `;
  } catch (e) {
    document.getElementById('hw-info').innerHTML = '<span style="color:var(--text3);font-size:12px">Could not read hardware info</span>';
  }
}

// ── Models ────────────────────────────────────────────────────────
async function loadModels() {
  try {
    state.models = await API.get('/api/models');
    const sel = document.getElementById('model-select');
    sel.innerHTML = '<option value="">— select a model —</option>';
    state.models.forEach(m => {
      const opt = document.createElement('option');
      opt.value = m.path;
      opt.textContent = `${m.name} (${m.size_gb} GB)`;
      sel.appendChild(opt);
    });
    // Also populate spawn model list
    const spawnSel = document.getElementById('spawn-model');
    if (spawnSel) {
      spawnSel.innerHTML = '';
      state.models.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m.path;
        opt.textContent = m.name;
        spawnSel.appendChild(opt);
      });
    }
  } catch (e) {
    toast('Failed to load models: ' + e.message, 'error');
  }
}

async function onModelSelect() {
  const path = document.getElementById('model-select').value;
  if (!path) {
    document.getElementById('model-quick-info').style.display = 'none';
    return;
  }
  state.selectedModel = path;
  try {
    const info = await API.get('/api/models/info?path=' + encodeURIComponent(path));
    state.modelInfo = info;
    showModelQuickInfo(info);
    // Default to 4096 — do NOT auto-fill the model's max context (e.g. 131072 for Llama 3.1).
    // llama-server pre-allocates the FULL KV cache for whatever -c you pass.
    // 131072 × 32 layers × fp16 = ~64 GB. Let the user raise it manually.
    const safeDefault = Math.min(info.context_length || 4096, 4096);
    document.getElementById('ctx-length').value = safeDefault;
  } catch (e) {
    toast('Could not read model info: ' + e.message, 'error');
  }
}

function showModelQuickInfo(info) {
  const grid = document.getElementById('model-info-grid');
  grid.innerHTML = `
    <div class="info-item"><div class="info-item-label">Architecture</div><div class="info-item-val">${info.architecture || '?'}</div></div>
    <div class="info-item"><div class="info-item-label">Max Context</div><div class="info-item-val">${(info.context_length||0).toLocaleString()}</div></div>
    <div class="info-item"><div class="info-item-label">Layers</div><div class="info-item-val">${info.n_layers || '?'}</div></div>
    <div class="info-item"><div class="info-item-label">Heads</div><div class="info-item-val">${info.n_heads || '?'}</div></div>
    <div class="info-item"><div class="info-item-label">File</div><div class="info-item-val">${info.file_size_gb} GB</div></div>
    <div class="info-item"><div class="info-item-label">Est. RAM</div><div class="info-item-val">${info.estimated_ram_gb} GB</div></div>
  `;
  const fitBadge = document.getElementById('fit-badge');
  if (info.fits !== undefined) {
    fitBadge.innerHTML = `<span class="badge ${info.fits ? 'badge-green' : 'badge-red'}">${info.fit_message}</span>`;
    fitBadge.innerHTML += `&nbsp;<span class="badge badge-blue">${info.chat_template_format || 'unknown'} template</span>`;
    if (info.is_vision) {
      fitBadge.innerHTML += `&nbsp;<span class="badge badge-green">👁 Vision</span>`;
    }
  }
  document.getElementById('model-quick-info').style.display = 'block';
}

// ── Server ────────────────────────────────────────────────────────
function freeRam() {
  floatWins.terminal.open();
  floatWins.terminal.exec('powershell -ExecutionPolicy Bypass -File "C:\\AIFreeRam\\Clear-RAM.ps1"');
}

async function _applyStartupConfig() {
  try {
    const cfg = await API.get('/api/startup-config');
    if (cfg.gpu_layers !== undefined)
      document.getElementById('gpu-layers').value = cfg.gpu_layers;
    if (cfg.context)
      document.getElementById('ctx-length').value = cfg.context;
    // Store flash_attn for use when loading
    state._flashAttn = cfg.flash_attn;
    state._backend   = cfg.backend;
  } catch (_) {}
}

function applyPreset(preset) {
  const gpuEl = document.getElementById('gpu-layers');
  const ctxEl = document.getElementById('ctx-length');
  if (preset === 'cpu') {
    gpuEl.value = 0;
    ctxEl.value = 16384;
    toast('CPU Only preset — gpu_layers=0, context=16K. Best for integrated GPU.', 'info', 4000);
  } else if (preset === 'balanced') {
    gpuEl.value = 8;
    ctxEl.value = 8192;
    toast('Balanced preset — 8 GPU layers, 8K context. Good for 4–6GB VRAM.', 'info', 4000);
  }
}

async function loadModel() {
  const path = document.getElementById('model-select').value || state.selectedModel;
  if (!path) { toast('Select a model first', 'error'); return; }
  const ctx = parseInt(document.getElementById('ctx-length').value) || 4096;
  const gpu = parseInt(document.getElementById('gpu-layers').value) || 0;

  document.getElementById('load-btn').disabled = true;
  document.getElementById('server-loading').style.display = 'block';
  document.getElementById('load-status').textContent = 'Starting llama-server... (may take 30–120s for large models)';

  try {
    await API.post('/api/server/start', {
      model_path: path,
      context_length: ctx,
      gpu_layers: gpu,
      // Use startup config flash_attn if set; otherwise only enable for GPU mode
      flash_attn: state._flashAttn !== undefined ? state._flashAttn : gpu > 0,
      server_name: 'main',
      mmproj_path: state.modelInfo?.mmproj_path || null,
    });
    state.serverRunning = true;
    state.contextLength = ctx;   // remember for live bar updates
    updateServerStatus(true);
    toast('Model loaded and ready', 'success');
    updateContextBar();
    newChat();
  } catch (e) {
    toast('Failed to load model: ' + e.message, 'error');
  } finally {
    document.getElementById('load-btn').disabled = false;
    document.getElementById('server-loading').style.display = 'none';
    document.getElementById('stop-btn').style.display = state.serverRunning ? '' : 'none';
  }
}

async function stopServer() {
  try {
    await API.post('/api/server/stop');
    state.serverRunning = false;
    updateServerStatus(false);
    toast('Server stopped', 'info');
  } catch (e) {
    toast('Error stopping server: ' + e.message, 'error');
  }
}

function updateServerStatus(running) {
  const dot = document.getElementById('server-dot');
  const txt = document.getElementById('server-status-text');
  const stopBtn = document.getElementById('stop-btn');
  dot.className = 'dot' + (running ? ' green' : '');
  if (running) {
    const sel = document.getElementById('model-select');
    const name = sel.options[sel.selectedIndex]?.text?.split(' (')[0] || 'Model';
    txt.textContent = name;
  } else {
    txt.textContent = 'No model loaded';
  }
  if (stopBtn) stopBtn.style.display = running ? '' : 'none';
}

async function checkServerStatus() {
  try {
    const s = await API.get('/api/server/status');
    state.serverRunning = s.running;
    if (s.running && s.context_length) state.contextLength = s.context_length;
    updateServerStatus(s.running);
    if (s.running) {
      updateContextBar();
    }
  } catch (e) { /* silent */ }
}

// ── Context Bar ───────────────────────────────────────────────────
function _setContextBar(usedTokens, maxTokens) {
  const fill   = document.getElementById('ctx-fill');
  const tokens = document.getElementById('ctx-tokens');
  if (!fill || !tokens) return;
  const pct = maxTokens > 0 ? Math.min((usedTokens / maxTokens) * 100, 100) : 0;
  fill.style.width = pct + '%';
  fill.className = 'ctx-fill' + (pct > 80 ? ' crit' : pct > 60 ? ' warn' : '');
  tokens.textContent = `${Math.round(usedTokens).toLocaleString()} / ${maxTokens.toLocaleString()} tokens`;
}

async function updateContextBar() {
  try {
    const info = await API.get(`/api/context?conv_id=${state.convId}`);
    _setContextBar(info.total_tokens, info.max_tokens);
    if (info.needs_compaction) {
      toast('Context is nearly full — consider compacting', 'info', 4000);
    }
  } catch (e) { /* silent */ }
}

async function compactContext() {
  if (!_canChat()) { toast('Load a model or set an AI provider (/provider)', 'error'); return; }
  try {
    await API.post(`/api/context/compact?conv_id=${state.convId}&server_name=main`);
    addSystemMessage('Context compacted — old messages summarized');
    updateContextBar();
    toast('Context compacted', 'success');
  } catch (e) {
    toast('Compact failed: ' + e.message, 'error');
  }
}

async function clearContext() {
  await API.post(`/api/context/clear?conv_id=${state.convId}`);
  newChat();
}

// ── Chat ──────────────────────────────────────────────────────────
function newChat() {
  state.convId = 'conv-' + Date.now();
  const msgs = document.getElementById('messages');
  msgs.innerHTML = `<div class="empty-chat" id="empty-chat">
    <div class="empty-chat-icon">🧠</div>
    <div class="empty-chat-title">PyAgenticLlama</div>
    <div class="empty-chat-sub">${state.serverRunning ? 'Ready — type a message to begin' : 'Load a model from the left panel'}</div>
  </div>`;
  updateContextBar();
}

function setMode(mode) {
  state.mode = mode;
  document.getElementById('mode-chat').classList.toggle('active', mode === 'chat');
  document.getElementById('mode-agent').classList.toggle('active', mode === 'agent');
}

function toggleMemoryMode(btn) {
  btn.classList.toggle('active');
}

// ── Attachments ──────────────────────────────────────────────────
let _attachments = []; // [{name, type, content?, dataUrl?, mime?}]

function _modelAcceptsImages() {
  if (state.modelInfo?.is_vision) return true;
  if (state.externalProvider) return true;  // let provider reject if unsupported
  return false;
}

function openAttachPicker() {
  const input = document.getElementById('attach-input');
  const imgTypes = _modelAcceptsImages() ? '.jpg,.jpeg,.png,.gif,.webp,.bmp,' : '';
  input.accept = imgTypes + '.txt,.md,.py,.js,.ts,.jsx,.tsx,.json,.csv,.html,.css,.xml,.yaml,.yml,.sh,.bat,.c,.cpp,.h,.java,.rs,.go,.rb,.php,.pdf';
  input.click();
}

async function handleAttachFiles(files) {
  for (const file of files) {
    const ext = file.name.split('.').pop().toLowerCase();
    const isImage = ['jpg','jpeg','png','gif','webp','bmp'].includes(ext);
    if (isImage) {
      try {
        const dataUrl = await _readAsDataUrl(file);
        _attachments.push({ name: file.name, type: 'image', dataUrl, mime: file.type || 'image/jpeg' });
      } catch (e) { toast('Could not read image: ' + file.name, 'error'); }
    } else if (ext === 'pdf') {
      try {
        const fd = new FormData();
        fd.append('file', file);
        const r = await fetch('/api/upload', { method: 'POST', body: fd });
        const d = await r.json();
        if (d.content !== undefined) {
          _attachments.push({ name: file.name, type: 'text', content: d.content });
        } else {
          toast('Could not extract PDF text: ' + (d.detail || 'unknown error'), 'error');
        }
      } catch (e) { toast('PDF upload failed: ' + e.message, 'error'); }
    } else {
      try {
        const text = await _readAsText(file);
        _attachments.push({ name: file.name, type: 'text', content: text });
      } catch (e) { toast('Could not read file: ' + file.name, 'error'); }
    }
  }
  document.getElementById('attach-input').value = '';
  renderAttachBar();
}

function removeAttachment(i) {
  _attachments.splice(i, 1);
  renderAttachBar();
}

function renderAttachBar() {
  const bar = document.getElementById('attach-bar');
  const btn = document.getElementById('attach-btn');
  if (_attachments.length === 0) {
    bar.style.display = 'none';
    bar.innerHTML = '';
    btn.classList.remove('has-files');
    return;
  }
  btn.classList.add('has-files');
  bar.style.display = 'flex';
  bar.innerHTML = _attachments.map((att, i) => {
    if (att.type === 'image') {
      return `<div class="attach-chip attach-chip-img">
        <img src="${att.dataUrl}" class="attach-thumb" alt="${escHtml(att.name)}">
        <span class="attach-chip-name">${escHtml(att.name)}</span>
        <button class="attach-chip-rm" onclick="removeAttachment(${i})" title="Remove">×</button>
      </div>`;
    }
    return `<div class="attach-chip">
      <span class="attach-chip-icon">📄</span>
      <span class="attach-chip-name">${escHtml(att.name)}</span>
      <button class="attach-chip-rm" onclick="removeAttachment(${i})" title="Remove">×</button>
    </div>`;
  }).join('');
}

function _readAsDataUrl(file) {
  return new Promise((res, rej) => {
    const fr = new FileReader();
    fr.onload = e => res(e.target.result);
    fr.onerror = () => rej(new Error('FileReader error'));
    fr.readAsDataURL(file);
  });
}

function _readAsText(file) {
  return new Promise((res, rej) => {
    const fr = new FileReader();
    fr.onload = e => res(e.target.result);
    fr.onerror = () => rej(new Error('FileReader error'));
    fr.readAsText(file, 'utf-8');
  });
}

async function sendMessage() {
  if (state.streaming) return;
  const box = document.getElementById('input-box');
  const msg = box.value.trim();
  if (!msg && _attachments.length === 0) return;

  _hideCmdDropdown();
  box.value = '';
  box.style.height = 'auto';

  // Intercept slash commands (attachments are ignored for slash commands)
  if (msg.startsWith('/')) {
    removeEmptyState();
    await handleSlashCommand(msg);
    return;
  }

  if (!_canChat()) { toast('Load a model or set an AI provider (/provider)', 'error'); return; }

  removeEmptyState();

  // Snapshot and clear attachments before sending
  const attachSnapshot = [..._attachments];
  _attachments = [];
  renderAttachBar();

  appendUserMessage(msg, attachSnapshot);

  if (state.mode === 'agent') {
    await runAgent(msg);
  } else {
    await streamChat(msg, null, attachSnapshot);
  }
}

async function streamChat(msg, systemOverride = null, attachments = []) {
  state.streaming = true;
  _abortCtrl = new AbortController();
  _setGenerating(true);

  const injectMem = document.getElementById('mode-memory').classList.contains('active');
  const { bubble, thinking } = createAssistantBubble();
  const cursor = document.createElement('span');
  cursor.className = 'cursor';
  bubble.appendChild(cursor);

  let fullText = '';
  let thinkText = '';
  let inThink = false;
  let firstTokenTime = null;
  let tokenCount = 0;

  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      signal: _abortCtrl.signal,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: msg,
        personality_id: state.personalityId,
        system: systemOverride || undefined,   // overrides personality for validate/fix commands
        stream: true,
        conv_id: state.convId,
        server_name: 'main',
        inject_memory: injectMem,
        attachments: attachments.map(a => ({
          filename: a.name,
          type: a.type,
          content: a.content || '',
          data_url: a.dataUrl || '',
          mime: a.mime || '',
        })),
      }),
    });

    const reader = resp.body.getReader();
    const dec = new TextDecoder();
    let buf = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const lines = buf.split('\n');
      buf = lines.pop();

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const data = line.slice(6).trim();
        if (data === '[DONE]') {
          cursor.remove();
          renderFinalBubble(bubble, fullText);
          if (thinkText) renderThinking(thinking, thinkText);
          updateContextBar();
          updateTps(0, true);
          await saveConversationTitle(msg);
          break;
        }
        try {
          const chunk = JSON.parse(data);
          if (chunk.error) { toast('Error: ' + chunk.error, 'error'); break; }
          const delta = chunk.content || '';
          if (!delta) continue;

          if (!firstTokenTime) firstTokenTime = Date.now();
          tokenCount += delta.length / 4;  // ~4 chars per token
          const elapsed = (Date.now() - firstTokenTime) / 1000;
          if (elapsed > 0) updateTps(tokenCount / elapsed);
          // Live bar: use frontend counter so the bar moves as tokens arrive
          if (state.contextLength) _setContextBar(tokenCount, state.contextLength);

          // Parse <think> tags
          let remaining = delta;
          while (remaining.length > 0) {
            if (!inThink) {
              const tStart = remaining.indexOf('<think>');
              if (tStart === -1) {
                fullText += remaining;
                remaining = '';
              } else {
                fullText += remaining.slice(0, tStart);
                remaining = remaining.slice(tStart + 7);
                inThink = true;
              }
            } else {
              const tEnd = remaining.indexOf('</think>');
              if (tEnd === -1) {
                thinkText += remaining;
                remaining = '';
              } else {
                thinkText += remaining.slice(0, tEnd);
                remaining = remaining.slice(tEnd + 8);
                inThink = false;
              }
            }
          }

          // Display during streaming
          const displayText = (thinkText && fullText === '') ? '' : fullText;
          if (displayText) {
            bubble.textContent = displayText;
            bubble.appendChild(cursor);
          }
          if (thinkText && thinking) {
            thinking.querySelector('.think-body').textContent = thinkText;
          }
          scrollToBottom();
        } catch (e) { /* skip bad JSON */ }
      }
    }
  } catch (e) {
    cursor.remove();
    if (e.name === 'AbortError') {
      // User hit Stop — render whatever arrived so far
      if (fullText) renderFinalBubble(bubble, fullText);
      else bubble.innerHTML = '<em style="color:var(--text3)">Generation stopped.</em>';
    } else {
      bubble.innerHTML = `<span style="color:var(--red)">Error: ${escHtml(e.message)}</span>`;
      toast('Request failed: ' + e.message, 'error');
    }
  } finally {
    _abortCtrl = null;
    state.streaming = false;
    _setGenerating(false);
  }
}

async function runAgent(msg) {
  state.streaming = true;
  _setGenerating(true);

  const { bubble } = createAssistantBubble();
  bubble.textContent = '⚙️ Working...';

  try {
    const result = await API.post('/api/agent', {
      message: msg,
      personality_id: state.personalityId,
      max_iterations: 10,
      server_name: 'main',
      conv_id: state.convId,
    });

    bubble.innerHTML = '';
    if (result.trace && result.trace.length > 0) {
      const traceEl = document.createElement('div');
      traceEl.style.cssText = 'margin-bottom:8px; border:1px solid var(--border); border-radius:6px; overflow:hidden;';
      traceEl.innerHTML = result.trace.map(t => `
        <div style="padding:6px 10px; background:var(--surface3); border-bottom:1px solid var(--border); font-size:11px;">
          <span style="color:var(--accent)">▶ ${t.tool}</span>
          <span style="color:var(--text3); margin-left:8px">${JSON.stringify(t.args).slice(0, 60)}</span>
          <div style="color:var(--text2); margin-top:3px; font-family:var(--mono)">${String(t.result).slice(0, 200)}</div>
        </div>
      `).join('');
      bubble.appendChild(traceEl);
    }
    renderFinalBubble(bubble, result.content);
    const meta = bubble.closest('.msg').querySelector('.msg-tps');
    if (meta) meta.textContent = `${result.iterations} steps`;
    updateContextBar();
  } catch (e) {
    bubble.innerHTML = `<span style="color:var(--red)">Agent error: ${e.message}</span>`;
    toast('Agent failed: ' + e.message, 'error');
  } finally {
    state.streaming = false;
    _setGenerating(false);
  }
}

function updateTps(tps, final = false) {
  const el = document.getElementById('tps-badge');
  if (final || tps === 0) {
    if (tps === 0) { el.style.display = 'none'; return; }
    el.textContent = `${tps.toFixed(1)} t/s`;
    el.style.display = '';
    setTimeout(() => { el.style.display = 'none'; }, 4000);
  } else {
    el.textContent = `${tps.toFixed(1)} t/s`;
    el.style.display = '';
    // Update the last message meta
    const msgs = document.getElementById('messages');
    const lastTps = msgs.querySelector('.msg.assistant:last-child .msg-tps');
    if (lastTps) lastTps.textContent = `${tps.toFixed(1)} t/s`;
  }
}

// ── Message rendering ─────────────────────────────────────────────
function removeEmptyState() {
  const e = document.getElementById('empty-chat');
  if (e) e.remove();
}

function appendMessage(role, content) {
  const msgs = document.getElementById('messages');
  const wrap = document.createElement('div');
  wrap.className = `msg ${role}`;
  const persona = state.personalities.find(p => p.id === state.personalityId);
  const roleLabel = role === 'user' ? 'You' : (persona?.name || 'Assistant');
  wrap.innerHTML = `
    <div class="msg-meta">
      ${role === 'assistant' ? `<div class="persona-avatar" style="background:${persona?.avatar || '#7c3aed'}">${persona?.icon || '🤖'}</div>` : ''}
      <span class="msg-role">${roleLabel}</span>
      ${role === 'assistant' ? '<span class="msg-tps"></span>' : ''}
    </div>
    <div class="msg-bubble">${role === 'user' ? escHtml(content) : ''}</div>
  `;
  msgs.appendChild(wrap);
  scrollToBottom();
  return wrap;
}

function appendUserMessage(msg, attachments = []) {
  const wrap = appendMessage('user', msg);
  if (attachments.length === 0) return wrap;
  const bubble = wrap.querySelector('.msg-bubble');
  const bar = document.createElement('div');
  bar.className = 'msg-attach-bar';
  for (const att of attachments) {
    if (att.type === 'image' && att.dataUrl) {
      const img = document.createElement('img');
      img.className = 'msg-attach-img';
      img.src = att.dataUrl;
      img.alt = att.name;
      img.onclick = () => window.open(att.dataUrl, '_blank');
      bar.appendChild(img);
    } else {
      const chip = document.createElement('span');
      chip.className = 'msg-attach-file';
      chip.textContent = `📄 ${att.name}`;
      bar.appendChild(chip);
    }
  }
  bubble.insertBefore(bar, bubble.firstChild);
  return wrap;
}

function createAssistantBubble() {
  const wrap = appendMessage('assistant', '');
  const bubble = wrap.querySelector('.msg-bubble');

  // Thinking block (hidden until content arrives)
  const thinking = document.createElement('div');
  thinking.className = 'think-block';
  thinking.innerHTML = `
    <div class="think-header" onclick="this.closest('.think-block').classList.toggle('open')">
      <span class="think-toggle">▶</span>
      <span>Thinking</span>
    </div>
    <div class="think-body"></div>
  `;
  thinking.style.display = 'none';
  wrap.insertBefore(thinking, bubble);

  return { bubble, thinking };
}

function renderThinking(thinkEl, text) {
  if (!text || !thinkEl) return;
  thinkEl.style.display = '';
  thinkEl.querySelector('.think-body').innerHTML = escHtml(text).replace(/\n/g, '<br>');
}

function renderFinalBubble(bubble, text) {
  bubble.innerHTML = renderMarkdown(text || '');
}

function addSystemMessage(text) {
  const msgs = document.getElementById('messages');
  const wrap = document.createElement('div');
  wrap.className = 'msg system';
  wrap.innerHTML = `<div class="msg-bubble">${escHtml(text)}</div>`;
  msgs.appendChild(wrap);
  scrollToBottom();
}

function scrollToBottom() {
  const msgs = document.getElementById('messages');
  msgs.scrollTop = msgs.scrollHeight;
}

// ── Stop generation ───────────────────────────────────────────────
let _abortCtrl = null;

function stopGeneration() {
  if (_abortCtrl) {
    _abortCtrl.abort();
    _abortCtrl = null;
  }
}

function _setGenerating(on) {
  document.getElementById('send-btn').style.display     = on ? 'none' : '';
  document.getElementById('stop-gen-btn').style.display = on ? '' : 'none';
}

// ── Code block IDs & storage ──────────────────────────────────────
let _codeBlockStore = {};
let _codeBlockCounter = 0;

function _storeCode(lang, code) {
  const id = 'cb' + (++_codeBlockCounter);
  _codeBlockStore[id] = { lang, code };
  return id;
}

// ── Markdown renderer ─────────────────────────────────────────────
function renderMarkdown(text) {
  if (!text) return '';

  // ── Step 1: Extract fenced code blocks → null-byte placeholders ──
  // Handles 3+ backticks; optional trailing text on opening line.
  // Code is escaped here; the rest of the text is escaped in step 2.
  const _blocks = [];
  let html = text.replace(/`{3,}(\w*)[^\n]*\n([\s\S]*?)\n?`{3,}/g, (_, rawLang, rawCode) => {
    const lang = (rawLang || 'text').toLowerCase();
    const code = rawCode.trimEnd();
    const id   = _storeCode(lang, code);
    const esc  = escHtml(code);
    const isRunnable    = ['python', 'py'].includes(lang);
    const isPreviewable = ['html', 'javascript', 'js', 'css', 'jsx', 'tsx', 'svg'].includes(lang);
    _blocks.push(`<div class="code-block" data-cbid="${id}">
      <div class="code-header">
        <span class="code-lang">${escHtml(lang)}</span>
        <div class="code-actions">
          <button class="code-btn" onclick="copyCodeBlock('${id}', this)">📋 Copy</button>
          ${isRunnable    ? `<button class="code-btn code-btn-run"     onclick="runCodeBlock('${id}')">▶ Run</button>` : ''}
          ${isPreviewable ? `<button class="code-btn code-btn-preview" onclick="previewCodeBlock('${id}')">👁 Preview</button>` : ''}
          <button class="code-btn code-btn-cs"    onclick="sendToCS('${id}')"    title="Open in CodingSpace as new file">Code Space</button>
          <button class="code-btn code-btn-apply" onclick="applyToCS('${id}')"   title="Apply to currently open CS file">Apply</button>
          <button class="code-btn code-btn-vscode" onclick="sendToVSCode('${id}')" title="Send to VS Code as new tab">⌗ VS Code</button>
        </div>
      </div>
      <pre><code>${esc}</code></pre>
    </div>`);
    return `\x00BLOCK${_blocks.length - 1}\x00`;
  });

  // ── Step 2: Escape ALL remaining text ─────────────────────────────
  // Prevents model-output HTML from being injected into the page.
  // Placeholders use \x00 which is unaffected by escHtml.
  html = escHtml(html);

  // ── Step 3: Apply inline markdown (on already-escaped text) ───────
  // Captured groups are already escaped — do NOT call escHtml() again.
  html = html.replace(/`([^`\n]+)`/g, (_, c) => `<code>${c}</code>`);
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*([^*\n]+)\*/g, '<em>$1</em>');
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm,  '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm,   '<h1>$1</h1>');
  html = html.replace(/^\|(.+)\|$/gm, (line) => {
    if (/^[\|\s\-:]+$/.test(line)) return '';
    const cells = line.split('|').slice(1, -1).map(c => `<td>${c.trim()}</td>`).join('');
    return `<tr>${cells}</tr>`;
  });
  html = html.replace(/(<tr>[\s\S]*?<\/tr>)/g, '<table>$1</table>');
  html = html.replace(/^[-*] (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>[\s\S]*?<\/li>)/g, '<ul>$1</ul>');

  // Paragraphs — skip block elements and placeholders
  const parts = html.split(/\n{2,}/);
  html = parts.map(p => {
    const t = p.trim();
    if (!t) return '';
    if (/^<(div|pre|ul|ol|table|h[1-6]|blockquote)/.test(t)) return t;
    if (t.includes('\x00BLOCK')) return t;
    return `<p>${t.replace(/\n/g, '<br>')}</p>`;
  }).join('\n');

  // ── Step 4: Restore code block HTML ───────────────────────────────
  html = html.replace(/\x00BLOCK(\d+)\x00/g, (_, i) => _blocks[+i]);

  return html;
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ── Copy code block ────────────────────────────────────────────────
function copyCodeBlock(id, btn) {
  const entry = _codeBlockStore[id];
  if (!entry) return;
  navigator.clipboard.writeText(entry.code).then(() => {
    const orig = btn.textContent;
    btn.textContent = '✓ Copied';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = orig; btn.classList.remove('copied'); }, 2000);
  }).catch(() => {
    // Fallback for browsers without clipboard API
    const ta = document.createElement('textarea');
    ta.value = entry.code;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    ta.remove();
    btn.textContent = '✓ Copied';
    setTimeout(() => btn.textContent = '📋 Copy', 2000);
  });
}

// ── Run Python code ────────────────────────────────────────────────
async function runCodeBlock(id) {
  const entry = _codeBlockStore[id];
  if (!entry) return;

  // Find or create the output panel below this code block
  const blockEl = document.querySelector(`.code-block[data-cbid="${id}"]`);
  let out = blockEl?.nextElementSibling;
  if (!out || !out.classList.contains('code-output')) {
    out = document.createElement('div');
    out.className = 'code-output';
    out.innerHTML = `
      <div class="code-output-header"><span class="spinner"></span> Running...</div>
      <div class="code-output-body"></div>`;
    blockEl?.insertAdjacentElement('afterend', out);
  }
  const header = out.querySelector('.code-output-header');
  const body   = out.querySelector('.code-output-body');
  header.innerHTML = '<span class="spinner"></span> Running...';
  body.textContent = '';
  body.className   = 'code-output-body';

  try {
    const result = await API.post('/api/run', { code: entry.code, language: entry.lang });
    const hasErr = result.returncode !== 0 || result.stderr;
    header.innerHTML = hasErr
      ? `<span style="color:var(--red)">✗ Error (exit ${result.returncode})</span>`
      : `<span style="color:var(--green)">✓ Finished</span>`;
    body.textContent = (result.stdout || '') + (result.stderr ? '\n' + result.stderr : '') || '(no output)';
    body.className   = 'code-output-body' + (hasErr ? ' err' : ' ok');
  } catch (e) {
    header.innerHTML = `<span style="color:var(--red)">✗ Failed</span>`;
    body.textContent = e.message;
    body.className   = 'code-output-body err';
  }
}

// ── Preview HTML/JS/CSS ────────────────────────────────────────────
let _previewBlobUrl = null;

function previewCodeBlock(id) {
  const entry = _codeBlockStore[id];
  if (!entry) return;
  openPreviewModal(entry.code, entry.lang, id);
}

function openPreviewModal(code, lang, id) {
  const title = document.getElementById('preview-modal-title');
  const tabs  = document.getElementById('preview-tabs');
  const content = document.getElementById('preview-content');

  title.textContent = `👁 Preview — ${lang}`;
  tabs.innerHTML = '';
  content.innerHTML = '';

  if (['html', 'svg'].includes(lang)) {
    // Render directly in iframe
    _showHtmlPreview(content, code);
    document.getElementById('preview-open-btn').style.display = '';
  } else if (['css'].includes(lang)) {
    // Wrap in minimal HTML to preview CSS
    const wrapped = `<!DOCTYPE html><html><head><style>${code}</style></head><body>
      <h1>Heading</h1><p>Paragraph text.</p><a href="#">Link</a>
      <button>Button</button><input placeholder="Input"><ul><li>Item 1</li><li>Item 2</li></ul>
    </body></html>`;
    _showHtmlPreview(content, wrapped);
  } else if (['javascript', 'js'].includes(lang)) {
    // Wrap JS in a page with a console capture
    const wrapped = `<!DOCTYPE html><html><head><style>body{font-family:monospace;background:#0a0c10;color:#c9d1d9;padding:12px}</style></head><body>
      <div id="output"></div>
      <script>
        const _out = document.getElementById('output');
        const _log = console.log.bind(console);
        console.log = (...args) => { _out.innerHTML += '<div>' + args.map(a=>JSON.stringify(a)??String(a)).join(' ') + '</div>'; _log(...args); };
        try { ${code} } catch(e) { _out.innerHTML += '<div style="color:red">Error: ' + e.message + '</div>'; }
      <\/script></body></html>`;
    _showHtmlPreview(content, wrapped);
  } else {
    content.innerHTML = `<pre style="background:var(--bg);padding:12px;border-radius:6px;font-family:var(--mono);font-size:12px;overflow-x:auto;max-height:400px">${escHtml(code)}</pre>`;
    document.getElementById('preview-open-btn').style.display = 'none';
  }

  openModal('preview-modal');
}

function _showHtmlPreview(container, html) {
  if (_previewBlobUrl) URL.revokeObjectURL(_previewBlobUrl);
  const blob = new Blob([html], { type: 'text/html' });
  _previewBlobUrl = URL.createObjectURL(blob);
  const iframe = document.createElement('iframe');
  iframe.className = 'preview-iframe';
  iframe.src = _previewBlobUrl;
  iframe.sandbox = 'allow-scripts';
  container.appendChild(iframe);
}

function openPreviewExternal() {
  if (_previewBlobUrl) window.open(_previewBlobUrl, '_blank');
}

// ── Skills ────────────────────────────────────────────────────────
const _PERSONALITY_BADGES = {
  general:  '🌐 General',
  default:  '🤖 Assistant',
  coder:    '💻 Coder',
  creative: '✨ Creative',
  analyst:  '📊 Analyst',
};
function _personalityBadge(p) {
  return _PERSONALITY_BADGES[p] || `🏷 ${escHtml(p || 'general')}`;
}

async function loadSkills() {
  try {
    const skills = await API.get('/api/skills');
    const list = document.getElementById('skills-list');
    list.innerHTML = '';
    if (!skills.length) {
      list.innerHTML = '<div style="color:var(--text3);font-size:12px;text-align:center;padding:16px">No skills yet.<br>Create one to give the AI tools.</div>';
      return;
    }
    skills.forEach(s => {
      const card = document.createElement('div');
      card.className = 'skill-card';
      card.innerHTML = `
        <div class="skill-card-top">
          <span class="skill-name">${escHtml(s.name)}</span>
          <label class="switch"><input type="checkbox" ${s.enabled ? 'checked' : ''} onchange="toggleSkill('${s.id}', this.checked)"><span class="slider"></span></label>
        </div>
        <div class="skill-desc">${escHtml(s.description)}</div>
        <div class="skill-footer" data-skillid="${s.id}">
          <span class="skill-type">${s.action_type}</span>
          <span class="skill-personality-badge" title="Available when using this personality">${_personalityBadge(s.personality)}</span>
          <button class="btn btn-ghost btn-sm btn-icon" title="Test skill">▶</button>
          <button class="btn btn-ghost btn-sm btn-icon" title="Edit">✏️</button>
          <button class="btn btn-danger btn-sm btn-icon" title="Delete">🗑</button>
        </div>
      `;
      // Attach all button handlers via closure — never JSON in onclick attrs
      const footer = card.querySelector('.skill-footer');
      const [runBtn, editBtn, delBtn] = footer.querySelectorAll('button');
      runBtn.onclick  = () => openTestSkillModal(s.id, s.name);
      editBtn.onclick = () => openSkillModal(s);
      delBtn.onclick  = () => deleteSkill(s.id);

      list.appendChild(card);
    });
  } catch (e) {
    toast('Failed to load skills: ' + e.message, 'error');
  }
}

function openSkillModal(skill) {
  document.getElementById('skill-id').value = skill?.id || '';
  document.getElementById('skill-name').value = skill?.name || '';
  document.getElementById('skill-desc').value = skill?.description || '';
  document.getElementById('skill-type').value = skill?.action_type || 'python';
  document.getElementById('skill-code').value = skill?.code || 'def execute(**kwargs):\n    # vault_get("MY_API_KEY") to read stored keys\n    return "result"';
  document.getElementById('skill-webhook').value = skill?.webhook_url || '';
  document.getElementById('skill-params').value = skill?.parameters ? JSON.stringify(skill.parameters, null, 2) : '';
  document.getElementById('skill-enabled').checked = skill?.enabled !== false;
  document.getElementById('skill-personality').value = skill?.personality || 'general';
  toggleSkillType();
  openModal('skill-modal');
}

function toggleSkillType() {
  const type = document.getElementById('skill-type').value;
  document.getElementById('skill-code-group').style.display = type === 'python' ? '' : 'none';
  document.getElementById('skill-webhook-group').style.display = type === 'webhook' ? '' : 'none';
}

async function saveSkill() {
  const id = document.getElementById('skill-id').value;
  let params = {};
  try {
    const raw = document.getElementById('skill-params').value.trim();
    if (raw) params = JSON.parse(raw);
  } catch (e) {
    toast('Parameters must be valid JSON', 'error'); return;
  }
  const data = {
    name: document.getElementById('skill-name').value,
    description: document.getElementById('skill-desc').value,
    parameters: params,
    action_type: document.getElementById('skill-type').value,
    code: document.getElementById('skill-code').value,
    webhook_url: document.getElementById('skill-webhook').value,
    enabled: document.getElementById('skill-enabled').checked,
    personality: document.getElementById('skill-personality').value,
  };
  try {
    if (id) {
      await API.put(`/api/skills/${id}`, data);
    } else {
      await API.post('/api/skills', data);
    }
    closeModal('skill-modal');
    toast('Skill saved', 'success');
    loadSkills();
  } catch (e) {
    toast('Save failed: ' + e.message, 'error');
  }
}

async function deleteSkill(id) {
  if (!confirm('Delete this skill?')) return;
  await API.del(`/api/skills/${id}`);
  toast('Skill deleted', 'info');
  loadSkills();
}

async function toggleSkill(id, enabled) {
  try {
    // Load full skill, update enabled, save
    const skills = await API.get('/api/skills');
    const skill = skills.find(s => s.id === id);
    if (skill) {
      skill.enabled = enabled;
      await API.put(`/api/skills/${id}`, skill);
    }
  } catch (e) { /* silent */ }
}

// ── Vault ─────────────────────────────────────────────────────────
async function openVaultModal() {
  await loadVaultKeys();
  openModal('vault-modal');
}

async function loadVaultKeys() {
  try {
    const keys = await API.get('/api/vault/keys');
    const list = document.getElementById('vault-list');
    list.innerHTML = '';
    if (!keys.length) {
      list.innerHTML = '<div style="color:var(--text3);font-size:12px">No secrets stored yet.</div>';
      return;
    }
    keys.forEach(k => {
      const row = document.createElement('div');
      row.style.cssText = 'display:flex;align-items:center;gap:6px;padding:5px 0;border-bottom:1px solid var(--border)';
      row.innerHTML = `
        <span style="font-family:var(--mono);font-size:12px;flex:1">${escHtml(k)}</span>
        <span style="font-size:11px;color:var(--text3)">●●●●●●●●</span>
        <button class="btn btn-danger btn-sm" onclick="deleteVaultKey('${k}')">Delete</button>
      `;
      list.appendChild(row);
    });
  } catch (e) { /* silent */ }
}

async function saveVaultEntry() {
  const key = document.getElementById('vault-key').value.trim();
  const val = document.getElementById('vault-value').value.trim();
  if (!key || !val) { toast('Key and value required', 'error'); return; }
  try {
    await API.post('/api/vault/set', { key, value: val });
    document.getElementById('vault-key').value = '';
    document.getElementById('vault-value').value = '';
    toast(`"${key}" saved to vault`, 'success');
    loadVaultKeys();
  } catch (e) {
    toast('Failed to save: ' + e.message, 'error');
  }
}

async function deleteVaultKey(key) {
  if (!confirm(`Delete secret "${key}"?`)) return;
  await API.del(`/api/vault/delete/${key}`);
  toast(`"${key}" deleted`, 'info');
  loadVaultKeys();
}

// ── Brain / Memory ────────────────────────────────────────────────
async function loadMemories() {
  try {
    const mems = await API.get('/api/brain/memories?limit=50');
    renderMemoryList(mems);
  } catch (e) { /* silent */ }
}

async function searchMemory() {
  const q = document.getElementById('memory-search').value.trim();
  if (!q) { loadMemories(); return; }
  try {
    const results = await API.get(`/api/brain/recall?q=${encodeURIComponent(q)}`);
    renderMemoryList(results);
  } catch (e) { toast('Search failed', 'error'); }
}

function renderMemoryList(mems) {
  const list = document.getElementById('memory-list');
  list.innerHTML = '';
  if (!mems.length) {
    list.innerHTML = '<div style="color:var(--text3);font-size:12px;text-align:center">No memories yet.</div>';
    return;
  }
  mems.forEach(m => {
    const tags = JSON.parse(m.tags || '[]');
    const card = document.createElement('div');
    card.className = 'memory-card';
    card.innerHTML = `
      <div class="memory-content">${escHtml(m.content)}</div>
      <div class="memory-meta">
        <span class="badge badge-blue" style="font-size:9px">${m.type}</span>
        ${tags.map(t => `<span class="memory-tag">${escHtml(t)}</span>`).join('')}
        <button class="btn btn-danger btn-sm btn-icon" style="margin-left:auto;padding:1px 5px" onclick="deleteMemory(${m.id})">✕</button>
      </div>
    `;
    list.appendChild(card);
  });
}

function openRememberModal() { openModal('remember-modal'); }

async function saveMemory() {
  const content = document.getElementById('mem-content').value.trim();
  if (!content) { toast('Enter something to remember', 'error'); return; }
  const tags = document.getElementById('mem-tags').value.split(',').map(t => t.trim()).filter(Boolean);
  const type_ = document.getElementById('mem-type').value;
  try {
    await API.post('/api/brain/remember', { content, type_, tags });
    closeModal('remember-modal');
    document.getElementById('mem-content').value = '';
    document.getElementById('mem-tags').value = '';
    toast('Remembered!', 'success');
    loadMemories();
  } catch (e) {
    toast('Failed: ' + e.message, 'error');
  }
}

async function deleteMemory(id) {
  await API.del(`/api/brain/memories/${id}`);
  toast('Memory deleted', 'info');
  loadMemories();
}

async function clearAllMemories() {
  await API.del('/api/brain/memories');
  toast('All memories cleared', 'info');
  loadMemories();
}

// ── Conversation History ──────────────────────────────────────────
async function loadHistory() {
  try {
    const convs = await API.get('/api/brain/conversations');
    const list = document.getElementById('history-list');
    list.innerHTML = '';
    if (!convs.length) {
      list.innerHTML = '<div style="color:var(--text3);font-size:12px;text-align:center;padding:12px">No saved conversations yet.</div>';
      return;
    }
    convs.forEach(c => {
      const d = new Date(c.ts * 1000);
      const card = document.createElement('div');
      card.style.cssText = 'background:var(--surface2);border:1px solid var(--border);border-radius:6px;padding:8px 10px;cursor:pointer;';
      card.innerHTML = `
        <div style="font-size:12px;font-weight:600;margin-bottom:2px">${escHtml(c.title)}</div>
        <div style="font-size:10px;color:var(--text3)">${d.toLocaleDateString()} ${d.toLocaleTimeString()}</div>
      `;
      list.appendChild(card);
    });
  } catch (e) { /* silent */ }
}

function saveConversationTitle(_msg) {
  // Conversations are saved automatically in the backend streaming handler.
  // Nothing to do here — kept as a no-op so call sites don't need to change.
}

// ── Personalities ─────────────────────────────────────────────────
async function loadPersonalities() {
  try {
    state.personalities = await API.get('/api/personalities');
    const sel = document.getElementById('personality-select');
    sel.innerHTML = '';
    state.personalities.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = `${p.icon || '🤖'} ${p.name}`;
      sel.appendChild(opt);
    });
    sel.value = state.personalityId;
    sel.onchange = () => { state.personalityId = sel.value; };
  } catch (e) { /* silent */ }
}

async function openPersonalitiesModal() {
  await renderPersonalitiesList();
  openModal('personalities-modal');
}

async function renderPersonalitiesList() {
  const list = document.getElementById('personalities-list');
  list.innerHTML = '';
  state.personalities.forEach(p => {
    const card = document.createElement('div');
    card.style.cssText = 'display:flex;align-items:center;gap:8px;padding:8px;background:var(--surface2);border:1px solid var(--border);border-radius:6px';
    card.innerHTML = `
      <div class="persona-avatar" style="background:${escHtml(p.avatar || '#7c3aed')}">${escHtml(p.icon || '🤖')}</div>
      <div style="flex:1">
        <div style="font-weight:600;font-size:13px">${escHtml(p.name)}</div>
        <div style="font-size:11px;color:var(--text3)">T=${p.temperature}</div>
      </div>
      <button class="btn btn-ghost btn-sm">Edit</button>
    `;
    // Attach handler via closure — avoids JSON serialization in onclick attribute
    card.querySelector('button').onclick = () => editPersonality(p);
    list.appendChild(card);
  });
}

function openNewPersonality() {
  editPersonality({ id: '', name: '', avatar: '#7c3aed', system_prompt: '', temperature: 0.7, top_p: 0.9, icon: '🤖' });
}

function editPersonality(p) {
  document.getElementById('p-id').value = p.id || '';
  document.getElementById('p-name').value = p.name || '';
  document.getElementById('p-color').value = p.avatar || '#7c3aed';
  document.getElementById('p-system').value = p.system_prompt || '';
  document.getElementById('p-temp').value = p.temperature || 0.7;
  document.getElementById('p-top_p').value = p.top_p || 0.9;
  document.getElementById('personality-editor').style.display = '';
}

async function savePersonality() {
  const id = document.getElementById('p-id').value;
  const data = {
    id,
    name: document.getElementById('p-name').value,
    avatar: document.getElementById('p-color').value,
    system_prompt: document.getElementById('p-system').value,
    temperature: parseFloat(document.getElementById('p-temp').value),
    top_p: parseFloat(document.getElementById('p-top_p').value),
  };
  try {
    if (id) {
      await API.put(`/api/personalities/${id}`, data);
    } else {
      await API.post('/api/personalities', data);
    }
    document.getElementById('personality-editor').style.display = 'none';
    toast('Personality saved', 'success');
    await loadPersonalities();
    await renderPersonalitiesList();
  } catch (e) {
    toast('Save failed: ' + e.message, 'error');
  }
}

// ── Model Inspector ───────────────────────────────────────────────
async function openInspector() {
  const path = document.getElementById('model-select').value || state.selectedModel;
  if (!path) { toast('Select a model first', 'error'); return; }
  try {
    const info = await API.get('/api/models/info?path=' + encodeURIComponent(path));
    const c = document.getElementById('inspector-content');
    c.innerHTML = `
      <div style="font-weight:700;font-size:16px;margin-bottom:8px">${escHtml(info.name)}</div>
      <div class="inspector-grid" style="margin-bottom:12px">
        <div class="inspector-stat"><div class="inspector-stat-val">${info.n_layers}</div><div class="inspector-stat-label">Layers</div></div>
        <div class="inspector-stat"><div class="inspector-stat-val">${info.n_heads}</div><div class="inspector-stat-label">Att. Heads</div></div>
        <div class="inspector-stat"><div class="inspector-stat-val">${info.n_kv_heads}</div><div class="inspector-stat-label">KV Heads</div></div>
        <div class="inspector-stat"><div class="inspector-stat-val">${info.embedding_size?.toLocaleString()}</div><div class="inspector-stat-label">Embed Dim</div></div>
        <div class="inspector-stat"><div class="inspector-stat-val">${(info.context_length/1000).toFixed(0)}K</div><div class="inspector-stat-label">Max Context</div></div>
        <div class="inspector-stat"><div class="inspector-stat-val">${info.vocab_size?.toLocaleString() || '?'}</div><div class="inspector-stat-label">Vocab Size</div></div>
        <div class="inspector-stat"><div class="inspector-stat-val">${info.file_size_gb} GB</div><div class="inspector-stat-label">File Size</div></div>
        <div class="inspector-stat"><div class="inspector-stat-val">${info.estimated_ram_gb} GB</div><div class="inspector-stat-label">Est. RAM</div></div>
        <div class="inspector-stat"><div class="inspector-stat-val">${info.rope_freq_base?.toLocaleString() || '?'}</div><div class="inspector-stat-label">RoPE Base</div></div>
      </div>
      <div style="display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap">
        <span class="badge badge-blue">${info.architecture}</span>
        <span class="badge badge-yellow">${info.chat_template_format || 'unknown'} template</span>
        <span class="badge ${info.fits ? 'badge-green' : 'badge-red'}">${info.fits ? 'Fits in RAM' : 'May not fit'}</span>
      </div>
      ${info.chat_template ? `
        <div style="font-size:11px;color:var(--text3);margin-bottom:4px">Chat Template (first 500 chars):</div>
        <div class="template-box">${escHtml(info.chat_template)}</div>
      ` : ''}
    `;
    openModal('inspector-modal');
  } catch (e) {
    toast('Failed to load info: ' + e.message, 'error');
  }
}

// ── File Browser ──────────────────────────────────────────────────
async function openFileBrowser() {
  state.browserSelected = null;
  document.getElementById('browser-select-btn').disabled = true;
  document.getElementById('browser-selected').textContent = '';
  // Load shortcuts first, then navigate to home
  try {
    const home = await API.get('/api/filesystem/home');
    const sc = document.getElementById('browser-shortcuts');
    sc.innerHTML = '';
    home.shortcuts.forEach(s => {
      const btn = document.createElement('div');
      btn.style.cssText = 'padding:5px 8px;border-radius:5px;cursor:pointer;font-size:12px;color:var(--text2);display:flex;align-items:center;gap:6px;';
      btn.innerHTML = `<span>${s.name.includes(':\\') ? '💾' : '📁'}</span><span>${escHtml(s.name)}</span>`;
      btn.onmouseenter = () => btn.style.background = 'var(--surface3)';
      btn.onmouseleave = () => btn.style.background = '';
      btn.onclick = () => browseTo(s.path);
      sc.appendChild(btn);
    });
    await browseTo(home.home);
  } catch (e) {
    await browseTo('C:\\');
  }
  openModal('browser-modal');
}

async function browseTo(path) {
  state.browserPath = path;
  document.getElementById('browser-list').innerHTML = '<div style="padding:12px;color:var(--text3);font-size:12px">Loading...</div>';
  try {
    const data = await API.get('/api/filesystem/browse?path=' + encodeURIComponent(path));
    document.getElementById('browser-path').textContent = data.path;
    document.getElementById('browser-up').dataset.parent = data.parent;

    const list = document.getElementById('browser-list');
    list.innerHTML = '';

    if (!data.entries.length) {
      list.innerHTML = '<div style="padding:12px;color:var(--text3);font-size:12px">Empty folder</div>';
      return;
    }

    data.entries.forEach(e => {
      const row = document.createElement('div');
      let icon = e.is_dir ? '📁' : '📄';
      if (e.is_gguf) icon = '🧠';
      row.className = `file-entry${e.is_gguf ? ' gguf' : ''}`;
      if (!e.is_dir && !e.is_gguf) row.style.color = 'var(--text3)';
      row.innerHTML = `
        <span class="file-icon">${icon}</span>
        <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escHtml(e.name)}</span>
        ${e.is_gguf ? `<span class="file-size">${e.size_gb} GB</span>` :
          (e.size_mb && !e.is_dir ? `<span class="file-size">${e.size_mb < 1024 ? e.size_mb + ' MB' : (e.size_mb/1024).toFixed(1) + ' GB'}</span>` : '')}
      `;
      if (e.is_dir) {
        row.style.cursor = 'pointer';
        row.ondblclick = () => browseTo(e.path);
        row.onclick = () => {
          list.querySelectorAll('.file-entry').forEach(r => r.style.background = '');
          row.style.background = 'var(--surface3)';
        };
      } else if (e.is_gguf) {
        row.style.cursor = 'pointer';
        row.onclick = () => {
          state.browserSelected = e.path;
          document.getElementById('browser-selected').textContent = '✓ ' + e.path;
          document.getElementById('browser-select-btn').disabled = false;
          list.querySelectorAll('.file-entry').forEach(r => r.style.background = '');
          row.style.background = 'var(--accent-dim)';
        };
        row.ondblclick = () => { row.click(); selectBrowserModel(); };
      }
      list.appendChild(row);
    });
  } catch (e) {
    document.getElementById('browser-list').innerHTML =
      `<div style="padding:12px;color:var(--red);font-size:12px">Error: ${escHtml(e.message)}</div>`;
  }
}

function browserUp() {
  const { parent } = document.getElementById('browser-up').dataset;
  if (parent) browseTo(parent);
}

function selectBrowserModel() {
  if (!state.browserSelected) return;
  // Add to model dropdown
  const sel = document.getElementById('model-select');
  let found = false;
  for (const opt of sel.options) {
    if (opt.value === state.browserSelected) { found = true; sel.value = state.browserSelected; break; }
  }
  if (!found) {
    const opt = document.createElement('option');
    opt.value = state.browserSelected;
    opt.textContent = state.browserSelected.split('\\').pop();
    sel.appendChild(opt);
    sel.value = state.browserSelected;
  }
  state.selectedModel = state.browserSelected;
  closeModal('browser-modal');
  onModelSelect();
}

function addCurrentBrowserFolder() {
  const path = state.browserPath;
  fetch('/api/models/add-path?path=' + encodeURIComponent(path), { method: 'POST' })
    .then(r => r.json())
    .then(() => { toast('Folder added to model list', 'success'); loadModels(); })
    .catch(e => toast('Failed: ' + e.message, 'error'));
}

async function promptAddModelPath() {
  const path = prompt('Enter folder path containing .gguf files:');
  if (!path) return;
  try {
    await fetch('/api/models/add-path?path=' + encodeURIComponent(path), { method: 'POST' });
    toast('Folder added', 'success');
    await loadModels();
  } catch (e) {
    toast('Failed: ' + e.message, 'error');
  }
}

// ── Agents ────────────────────────────────────────────────────────
async function loadAgents() {
  try {
    const agents = await API.get('/api/agents');
    const list = document.getElementById('agents-list');
    list.innerHTML = '';
    if (!agents.length) {
      list.innerHTML = '<div style="color:var(--text3);font-size:12px;text-align:center;padding:12px">No agents running.</div>';
      return;
    }
    agents.forEach(a => {
      const card = document.createElement('div');
      card.className = 'agent-card';
      card.innerHTML = `
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
          <div class="dot ${a.running ? 'green' : ''}"></div>
          <span class="agent-name">${escHtml(a.name)}</span>
          ${a.running ? `<button class="btn btn-danger btn-sm" onclick="stopAgent('${a.name}')">Stop</button>` : ''}
        </div>
        <div class="agent-model" style="font-size:11px;color:var(--text3)">${a.model ? a.model.split('\\').pop() : 'no model'}</div>
        <div style="font-size:10px;color:var(--text3)">port ${a.port} · ctx ${a.context_length}</div>
      `;
      list.appendChild(card);
    });
  } catch (e) { /* silent */ }
}

function openSpawnModal() {
  loadModels();
  openModal('spawn-modal');
}

async function spawnAgent() {
  const name = document.getElementById('spawn-name').value.trim();
  const model = document.getElementById('spawn-model').value;
  const task = document.getElementById('spawn-task').value.trim();
  if (!name || !model || !task) { toast('Fill all fields', 'error'); return; }
  const btn = document.querySelector('#spawn-modal .btn-primary');
  btn.textContent = 'Working...';
  btn.disabled = true;
  try {
    const result = await API.post('/api/agents/spawn', {
      name, model_path: model, task,
      context_length: parseInt(document.getElementById('spawn-ctx').value) || 2048,
      gpu_layers: parseInt(document.getElementById('spawn-gpu').value) || 0,
    });
    closeModal('spawn-modal');
    removeEmptyState();
    const wrap = document.createElement('div');
    wrap.className = 'msg tool-call';
    wrap.innerHTML = `
      <div class="msg-meta"><span class="msg-role">Agent: ${escHtml(name)}</span></div>
      <div class="msg-bubble">
        <div style="font-size:11px;color:var(--text3);margin-bottom:4px">Task: ${escHtml(task)}</div>
        ${renderMarkdown(result.content)}
      </div>
    `;
    document.getElementById('messages').appendChild(wrap);
    scrollToBottom();
    toast(`Agent "${name}" completed task`, 'success');
    loadAgents();
  } catch (e) {
    toast('Agent failed: ' + e.message, 'error');
  } finally {
    btn.textContent = 'Spawn Agent';
    btn.disabled = false;
  }
}

async function stopAgent(name) {
  await API.post(`/api/agents/${name}/stop`);
  toast(`Agent "${name}" stopped`, 'info');
  loadAgents();
}

// ── Server Log ────────────────────────────────────────────────────
async function openLogModal() {
  openModal('log-modal');
  loadServerLog();
}

async function loadServerLog() {
  try {
    const data = await API.get('/api/server/log?lines=80');
    document.getElementById('log-content').textContent = data.lines.join('\n') || '(empty log)';
  } catch (e) {
    document.getElementById('log-content').textContent = 'Could not load log';
  }
}

// ── Save chat ─────────────────────────────────────────────────────
function saveChat() {
  const msgs = document.getElementById('messages');
  const text = Array.from(msgs.querySelectorAll('.msg')).map(m => {
    const role = m.querySelector('.msg-role')?.textContent || '';
    const content = m.querySelector('.msg-bubble')?.textContent || '';
    return `${role}: ${content}`;
  }).join('\n\n');
  const blob = new Blob([text], { type: 'text/plain' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `chat-${Date.now()}.txt`;
  a.click();
}

// ═══════════════════════════════════════════════════════════════════
// ── VS Code Bridge ────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════

const vsCode = {
  connected: false,
  workspace: '',
};

async function checkVSCode() {
  try {
    const data = await API.get('/api/vscode/status');
    vsCode.connected = data.connected;
    vsCode.workspace = data.workspace || '';
    updateVSCodeStatus(data);
    return data.connected;
  } catch (e) {
    vsCode.connected = false;
    updateVSCodeStatus({ connected: false });
    return false;
  }
}

function updateVSCodeStatus(data) {
  const dot  = document.getElementById('vscode-dot');
  const txt  = document.getElementById('vscode-status-text');
  const ind  = document.getElementById('vscode-indicator');
  if (!dot) return;
  dot.className = 'dot' + (data.connected ? ' green' : '');
  txt.textContent = data.connected ? 'VS Code ●' : 'VS Code';
  ind.title = data.connected
    ? `VS Code connected${data.workspace ? ' — ' + data.workspace : ''} (${data.received ?? 0} sent)`
    : 'VS Code not connected — run install.bat in vscode-extension/';
}

async function sendToVSCode(cbId) {
  const entry = _codeBlockStore[cbId];
  if (!entry) return;

  const ok = await checkVSCode();
  if (!ok) {
    toast('VS Code not connected. Run vscode-extension/install.bat then restart VS Code.', 'error', 6000);
    return;
  }

  try {
    await API.post('/api/vscode/send', {
      code: entry.code,
      language: entry.lang,
      project_path: state.codingSession?.folder || '',
      filename: '',
    });
    toast(`Sent to VS Code ✓ (${entry.lang || 'text'})`, 'success');
  } catch (e) {
    toast('VS Code send failed: ' + e.message, 'error', 5000);
  }
}

async function openFolderInVSCode() {
  const folder = document.getElementById('cs-folder').value.trim();
  if (!folder) { toast('Enter a folder path first', 'error'); return; }
  try {
    await API.post('/api/vscode/open-folder', { folder });
    toast('Sent folder to VS Code', 'success');
  } catch (e) {
    toast('Could not open in VS Code: ' + e.message, 'error');
  }
}

// ═══════════════════════════════════════════════════════════════════
// ── Coding Session ────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════

// Extend state with coding session
state.codingSession = null;  // null = no active session

const CODING_SYSTEM_TEMPLATE = (s) => `You are an expert coding assistant working on a specific project.

PROJECT CONTEXT:
  Name: ${s.name}
  Folder: ${s.folder || 'not specified'}
  Type: ${s.type || 'not specified'}
  Description: ${s.description || 'not specified'}

CODING RULES:
1. Every code block must start with a filename comment on the first line:
   Python → # filename: main.py
   JS/TS  → // filename: index.js
   HTML   → <!-- filename: index.html -->
   Other  → # filename: script.ext
2. Each file gets its own separate code block — never combine multiple files in one block
3. When creating a project, output the complete file tree first (use \`\`\`text), then each file
4. Code must be complete and runnable — no "..." placeholders, no TODO stubs
5. Imports, dependencies, requirements.txt/package.json must be included when needed
6. After sending all code blocks, give a brief "How to run" section`;

// ── CodingSpace ───────────────────────────────────────────────────

const LANG_EXT = { python:'py',js:'js',javascript:'js',typescript:'ts',html:'html',
  css:'css',bash:'sh',sql:'sql',json:'json',yaml:'yaml',rust:'rs',go:'go',
  java:'java',cpp:'cpp',csharp:'cs',ruby:'rb',php:'php',markdown:'md',text:'txt' };
const EXT_LANG = Object.fromEntries(
  Object.entries(LANG_EXT).map(([l,e])=>[e,l]).concat([['py','python'],['sh','bash'],['md','markdown'],['yml','yaml']])
);
const PREVIEWABLE_EXT = new Set(['html','htm','svg','css','js']);

let _csRoot     = '';          // absolute path of the CodingSpace root dir
let _csFile     = null;        // { path (abs), name, ext }
let _csModified = false;
let _csCreating = null;        // 'file' | 'dir' | null
let _csSelDir   = '';          // last selected directory (for new file placement)
let _csPreviewing = false;

// ── Open / close ──────────────────────────────────────────────────

async function toggleCodingSpace(rootOverride) {
  const panel = document.getElementById('cs-panel');
  if (rootOverride) _csRoot = rootOverride;
  if (!_csRoot) {
    const info = await API.get('/api/workspace').catch(() => null);
    _csRoot = info?.path || '';
  }
  state.csOpen = !state.csOpen;
  if (rootOverride) state.csOpen = true;
  panel.classList.toggle('cs-open', state.csOpen);
  if (state.csOpen) {
    _csUpdateHeader();
    await csRefreshTree();
    _csStatus('Ready');
  }
}

function _csUpdateHeader() {
  const el = document.getElementById('cs-root-label');
  if (el) {
    const short = _csRoot ? _csRoot.split(/[\\/]/).pop() : 'workspace';
    el.textContent = `🗂 ${short}`;
    el.title = _csRoot;
  }
}

// ── Tree ──────────────────────────────────────────────────────────

async function csRefreshTree() {
  if (!_csRoot) return;
  const list = document.getElementById('cs-tree-list');
  list.innerHTML = '<div style="padding:8px 10px;font-size:11px;color:var(--text3)">Loading…</div>';
  try {
    const tree = await API.get(`/api/fs/tree?root=${encodeURIComponent(_csRoot)}`);
    list.innerHTML = '';
    if (!tree?.children?.length) {
      list.innerHTML = '<div style="padding:8px 10px;font-size:11px;color:var(--text3)">Empty folder — create a file to start</div>';
      return;
    }
    _csSelDir = _csRoot;
    tree.children.forEach(node => _csRenderNode(node, list, 0));
  } catch (e) { list.innerHTML = `<div style="padding:8px 10px;font-size:11px;color:var(--red)">Error: ${escHtml(e.message)}</div>`; }
}

function _csRenderNode(node, container, depth) {
  const row = document.createElement('div');
  row.className = 'cs-node';
  row.style.paddingLeft = (8 + depth * 14) + 'px';
  row.dataset.path = node.path;

  if (node.isDir) {
    const toggle = document.createElement('span');
    toggle.className = 'cs-node-toggle'; toggle.textContent = '▶';
    const icon = document.createElement('span');
    icon.className = 'cs-node-icon'; icon.textContent = '📁';
    const name = document.createElement('span');
    name.className = 'cs-node-name'; name.textContent = node.name;
    row.append(toggle, icon, name);
    container.appendChild(row);

    const childWrap = document.createElement('div');
    childWrap.className = 'cs-children'; childWrap.style.display = 'none';
    container.appendChild(childWrap);

    row.onclick = () => {
      const open = childWrap.style.display !== 'none';
      childWrap.style.display = open ? 'none' : '';
      toggle.textContent = open ? '▶' : '▼';
      icon.textContent   = open ? '📁' : '📂';
      _csSelDir = node.path;
    };

    if (node.children) node.children.forEach(c => _csRenderNode(c, childWrap, depth + 1));
  } else {
    const icon = document.createElement('span');
    icon.className = 'cs-node-icon'; icon.textContent = '📄';
    const name = document.createElement('span');
    name.className = 'cs-node-name'; name.textContent = node.name;
    const del = document.createElement('span');
    del.className = 'cs-node-del'; del.textContent = '×'; del.title = 'Delete';
    del.onclick = e => { e.stopPropagation(); _csDeletePath(node.path, node.name); };
    row.append(icon, name, del);
    row.onclick = () => csOpenByPath(node.path, node.name, node.ext || '');
    if (_csFile?.path === node.path) row.classList.add('cs-active');
    container.appendChild(row);
  }
}

// ── File operations ───────────────────────────────────────────────

async function csOpenByPath(absPath, name, ext) {
  try {
    const data = await API.get(`/api/fs/read?path=${encodeURIComponent(absPath)}`);
    _csFile = { path: absPath, name, ext: ext || absPath.split('.').pop() };
    _csModified = false;
    _csPreviewing = false;

    document.getElementById('cs-editor').value         = data.content;
    document.getElementById('cs-editor').style.display = '';
    document.getElementById('cs-preview-frame').style.display = 'none';
    document.getElementById('cs-editor-filename').textContent = name;
    document.getElementById('cs-delete-btn').style.display    = '';

    const prevBtn = document.getElementById('cs-preview-btn');
    prevBtn.style.display = PREVIEWABLE_EXT.has(_csFile.ext) ? '' : 'none';

    _csStatus(`${name} — ${data.content.split('\n').length} lines`);
    _csHighlightActive(absPath);
  } catch (e) { _csStatus(`Cannot open: ${e.message}`, true); }
}

async function csSave() {
  if (!_csFile) { _csStatus('No file open', true); return; }
  const content = document.getElementById('cs-editor').value;
  try {
    await API.post('/api/fs/save', { path: _csFile.path, content });
    _csModified = false;
    _csStatus(`Saved: ${_csFile.name}`);
    await csRefreshTree();
  } catch (e) { _csStatus('Save failed: ' + e.message, true); }
}

async function csDeleteCurrent() {
  if (!_csFile) return;
  if (!confirm(`Delete ${_csFile.name}?`)) return;
  await _csDeletePath(_csFile.path, _csFile.name);
}

async function _csDeletePath(absPath, name) {
  if (!confirm(`Delete ${name}?`)) return;
  try {
    await API.del(`/api/fs/delete?path=${encodeURIComponent(absPath)}`);
    if (_csFile?.path === absPath) {
      _csFile = null; _csModified = false;
      document.getElementById('cs-editor').value            = '';
      document.getElementById('cs-editor-filename').textContent = '—';
      document.getElementById('cs-delete-btn').style.display = 'none';
      document.getElementById('cs-preview-btn').style.display = 'none';
    }
    _csStatus(`Deleted: ${name}`);
    await csRefreshTree();
  } catch (e) { _csStatus('Delete failed: ' + e.message, true); }
}

// ── Inline create (+ File / + Dir) ───────────────────────────────

function csStartCreate(type) {
  _csCreating = type;
  document.getElementById('cs-create-icon').textContent = type === 'dir' ? '📁' : '📄';
  document.getElementById('cs-create-name').value       = '';
  document.getElementById('cs-create-row').style.display = '';
  document.getElementById('cs-create-name').focus();
}

async function csConfirmCreate() {
  const name = document.getElementById('cs-create-name').value.trim();
  if (!name) { csCancelCreate(); return; }
  const dir  = _csSelDir || _csRoot;
  const full = dir.replace(/[\\/]+$/, '') + '/' + name;
  try {
    if (_csCreating === 'dir') {
      await API.post('/api/fs/mkdir', { path: full });
      _csStatus(`Folder created: ${name}`);
    } else {
      await API.post('/api/fs/save', { path: full, content: '' });
      await csOpenByPath(full, name, name.split('.').pop());
      _csStatus(`Created: ${name}`);
    }
    await csRefreshTree();
  } catch (e) { _csStatus('Create failed: ' + e.message, true); }
  csCancelCreate();
}

function csCancelCreate() {
  _csCreating = null;
  document.getElementById('cs-create-row').style.display = 'none';
}

// ── Preview (HTML/CSS/JS) ─────────────────────────────────────────

function csTogglePreview() {
  if (!_csFile) return;
  _csPreviewing = !_csPreviewing;
  const editor = document.getElementById('cs-editor');
  const frame  = document.getElementById('cs-preview-frame');
  const btn    = document.getElementById('cs-preview-btn');
  if (_csPreviewing) {
    const content = editor.value;
    const blob    = new Blob([content], { type: _csFile.ext === 'css' ? 'text/css' : 'text/html' });
    frame.src = URL.createObjectURL(blob);
    frame.style.display = ''; editor.style.display = 'none';
    btn.textContent = '✏ Edit';
  } else {
    frame.style.display = 'none'; editor.style.display = '';
    btn.textContent = '👁 Preview';
  }
}

// ── VS Code integration ───────────────────────────────────────────

async function csOpenInVSCode() {
  const root = _csRoot;
  try {
    await API.post('/api/workspace/open-in-vscode', {});
    toast('Opened in VS Code', 'success');
  } catch {
    const uri = 'vscode://file/' + (root || '').replace(/\\/g, '/');
    window.open(uri, '_blank');
  }
}

async function csSendToVSCode() {
  if (!_csFile) { toast('No file open in CodingSpace', 'error'); return; }
  const code = document.getElementById('cs-editor').value;
  const ok   = await checkVSCode();
  if (!ok) { toast('VS Code not connected', 'error'); return; }
  try {
    await API.post('/api/vscode/send', {
      code, language: EXT_LANG[_csFile.ext] || _csFile.ext || 'text',
      project_path: _csRoot, filename: _csFile.name,
    });
    toast(`Sent ${_csFile.name} to VS Code ✓`, 'success');
  } catch (e) { toast('VS Code send failed', 'error'); }
}

// ── Code block buttons ────────────────────────────────────────────

// "Code Space" button — creates a new ai-gen file and opens it
async function sendToCS(cbId) {
  const entry = _codeBlockStore[cbId];
  if (!entry) return;
  if (!_csRoot) {
    const info = await API.get('/api/workspace').catch(() => null);
    _csRoot = info?.path || '';
  }
  const ext      = LANG_EXT[entry.lang] || entry.lang || 'txt';
  const filename = `ai-gen-${Date.now()}.${ext}`;
  const absPath  = _csRoot.replace(/[\\/]+$/, '') + '/' + filename;
  try {
    await API.post('/api/fs/save', { path: absPath, content: entry.code });
    if (!state.csOpen) await toggleCodingSpace(_csRoot);
    await csOpenByPath(absPath, filename, ext);
    await csRefreshTree();
    _csStatus(`New file: ${filename}`);
  } catch (e) { toast('Could not create file: ' + e.message, 'error'); }
}

// "Apply" button — writes code to the currently open CS file
function applyToCS(cbId) {
  const entry = _codeBlockStore[cbId];
  if (!entry) return;
  if (!_csFile) {
    toast('No file open in CodingSpace — use "Code Space" first', 'error', 4000); return;
  }
  document.getElementById('cs-editor').value = entry.code;
  _csModified = true;
  _csStatus(`Applied to ${_csFile.name} — click Save when ready`);
  if (!state.csOpen) toggleCodingSpace(_csRoot);
}

// ── Helpers ───────────────────────────────────────────────────────

function _csStatus(msg, isError) {
  const el = document.getElementById('cs-editor-status');
  if (!el) return;
  el.textContent = msg;
  el.style.color = isError ? 'var(--red)' : 'var(--text3)';
}

function _csHighlightActive(absPath) {
  document.querySelectorAll('.cs-node').forEach(el => {
    el.classList.toggle('cs-active', el.dataset.path === absPath);
  });
}

function _langToExt(lang) { return LANG_EXT[lang] || lang || 'txt'; }
function _extToLang(ext)  { return EXT_LANG[ext]  || ext  || 'text'; }

// ── Provider ──────────────────────────────────────────────────────

let _parsedProviderCfg = null;

async function openProviderModal() {
  _parsedProviderCfg = null;
  document.getElementById('prov-preview').style.display = 'none';
  document.getElementById('prov-confirm-btn').style.display = 'none';
  document.getElementById('prov-dropzone-icon').textContent = '📄';

  // Fetch current config and server status in parallel
  const [cfg, srv] = await Promise.all([
    fetch('/api/provider').then(r => r.json()).catch(() => ({ type: 'local' })),
    fetch('/api/server/status').then(r => r.json()).catch(() => ({})),
  ]);

  // Update local-tab status pill
  const localEl = document.getElementById('local-provider-status');
  if (srv.running) {
    localEl.innerHTML = `<span style="color:var(--green)">●</span> llama.cpp running — <strong>${escHtml(srv.model || 'model loaded')}</strong>`;
  } else {
    localEl.innerHTML = `<span style="color:var(--text3)">○</span> No local model loaded`;
  }

  // Pre-fill manual fields if currently on an external provider
  if (cfg.type === 'external') {
    document.getElementById('prov-name').value  = cfg.name      || '';
    document.getElementById('prov-url').value   = cfg.base_url  || '';
    document.getElementById('prov-key').value   = cfg.api_key   || '';
    document.getElementById('prov-model').value = cfg.model     || '';
    setProviderTab('manual');
  } else {
    setProviderTab('local');
  }

  openModal('provider-modal');
}

function setProviderTab(tab) {
  ['local', 'manual', 'upload'].forEach(t => {
    document.getElementById(`ptab-${t}`).classList.toggle('active', t === tab);
    document.getElementById(`ppanel-${t}`).style.display = t === tab ? '' : 'none';
  });
}

async function resetToLocalProvider() {
  await fetch('/api/provider', { method: 'DELETE' });
  _updateProviderBadge({ type: 'local' });
  closeModal('provider-modal');
  toast('Switched back to local llama.cpp', 'success');
}

async function saveManualProvider() {
  const name  = document.getElementById('prov-name').value.trim();
  const url   = document.getElementById('prov-url').value.trim();
  const key   = document.getElementById('prov-key').value.trim();
  const model = document.getElementById('prov-model').value.trim();
  if (!url || !key) { toast('Base URL and API Key are required', 'error'); return; }
  const cfg = { type: 'external', name: name || 'Custom Provider', base_url: url, api_key: key, model };
  await fetch('/api/provider', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cfg),
  });
  _updateProviderBadge(cfg);
  closeModal('provider-modal');
  toast(`Provider set to ${cfg.name}`, 'success');
}

function handleProviderFileDrop(e) {
  e.preventDefault();
  document.getElementById('prov-dropzone').classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) _parseProviderFile(file);
}

function handleProviderFileInput(input) {
  const file = input.files[0];
  if (file) _parseProviderFile(file);
}

async function _parseProviderFile(file) {
  try {
    const fd = new FormData();
    fd.append('file', file);
    const resp = await fetch('/api/provider/parse-file', { method: 'POST', body: fd });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || 'Could not parse file');
    }
    const cfg = await resp.json();
    _parsedProviderCfg = cfg;

    document.getElementById('prev-name').textContent  = cfg.name  || '—';
    document.getElementById('prev-url').textContent   = cfg.base_url || '—';
    document.getElementById('prev-key').textContent   = cfg.api_key
      ? cfg.api_key.slice(0, 8) + '••••••••' : '(not found)';
    document.getElementById('prev-model').textContent = cfg.model || '(not specified)';
    document.getElementById('prov-preview').style.display      = '';
    document.getElementById('prov-confirm-btn').style.display  = '';
    document.getElementById('prov-dropzone-icon').textContent  = '✅';
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function confirmProviderFile() {
  if (!_parsedProviderCfg) return;
  await fetch('/api/provider', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(_parsedProviderCfg),
  });
  _updateProviderBadge(_parsedProviderCfg);
  closeModal('provider-modal');
  toast(`Provider set to ${_parsedProviderCfg.name}`, 'success');
  _parsedProviderCfg = null;
}

function _updateProviderBadge(cfg) {
  state.provider = cfg || null;
  state.externalProvider = !!(cfg && cfg.type === 'external');
  const badge = document.getElementById('provider-badge');
  if (!badge) return;
  if (state.externalProvider) {
    badge.textContent = `🔌 ${cfg.name || 'External API'}`;
    badge.style.display = '';
  } else {
    badge.style.display = 'none';
  }
}

async function _loadProviderBadge() {
  const cfg = await fetch('/api/provider').then(r => r.json()).catch(() => ({ type: 'local' }));
  _updateProviderBadge(cfg);
}

async function openCodingModal() {
  const vsStatus = document.getElementById('cs-vscode-status');
  const connected = await checkVSCode().catch(() => false);
  vsStatus.innerHTML = connected
    ? '<span style="color:var(--green)">✅ VS Code connected</span>'
    : '<span style="color:var(--text3)">○ VS Code not connected — install <code>vscode-extension/install.bat</code></span>';

  // Pre-fill from active session only (never from vsCode.workspace — that caused the PyAgenticLlama lock-in bug)
  if (state.codingSession) {
    document.getElementById('cs-name').value   = state.codingSession.name   || '';
    document.getElementById('cs-folder').value = state.codingSession.folder || '';
    document.getElementById('cs-type').value   = state.codingSession.type   || '';
    document.getElementById('cs-desc').value   = state.codingSession.description || '';
  } else {
    // Default folder = workspace/ path as a suggestion
    if (!document.getElementById('cs-folder').value && state.workspacePath) {
      document.getElementById('cs-folder').placeholder = state.workspacePath + '\\MyProject';
    }
  }

  openModal('coding-modal');
}

async function startCodingSession() {
  const name   = document.getElementById('cs-name').value.trim();
  const folder = document.getElementById('cs-folder').value.trim();
  const type   = document.getElementById('cs-type').value;
  const desc   = document.getElementById('cs-desc').value.trim();

  if (!name) { toast('Project name is required', 'error'); return; }

  state.codingSession = { name, folder, type, description: desc };

  // Update context bar badge
  const badge = document.getElementById('coding-session-badge');
  badge.className = 'coding-session-badge';
  badge.innerHTML = `💻 ${escHtml(name)}`;
  badge.style.display = '';

  // Always try to sync VS Code with the project folder
  if (folder) {
    _csRoot = folder;
    API.post('/api/vscode/open-folder', { folder }).catch(() => {});
  } else {
    _csRoot = state.workspacePath || '';
  }

  closeModal('coding-modal');
  newChat();

  // Auto-open CodingSpace with the project folder as root
  if (!state.csOpen) toggleCodingSpace(_csRoot || undefined);

  // Build the opening message
  let intro = `I'm starting a coding session for **${name}**`;
  if (type) intro += ` — a **${type}** project`;
  if (folder) intro += `\nProject folder: \`${folder}\``;
  if (desc) intro += `\n\nWhat to build: ${desc}`;
  intro += `\n\nPlease start by asking any clarifying questions you need, then output the project structure and first files.`;

  // Inject the coding system prompt for this session
  removeEmptyState();
  appendMessage('user', intro);
  await streamChat(intro, CODING_SYSTEM_TEMPLATE(state.codingSession));
}

function browseCodingFolder() {
  window._codingFolderPick = true;
  openFileBrowser();
}

async function csCreateProjectFolder() {
  const path = document.getElementById('cs-folder').value.trim();
  if (!path) { toast('Enter a folder path first', 'error'); return; }
  try {
    await API.post('/api/fs/mkdir', { path });
    toast(`Folder created: ${path}`, 'success');
    document.getElementById('cs-vscode-open').style.display = '';
  } catch (e) { toast('Could not create folder: ' + e.message, 'error'); }
}

// Override selectBrowserModel when in coding folder-pick mode
const _origSelectBrowserModel = window.selectBrowserModel;
function selectBrowserModel() {
  if (window._codingFolderPick) {
    document.getElementById('cs-folder').value = state.browserPath;
    document.getElementById('cs-vscode-open').style.display = '';
    window._codingFolderPick = false;
    closeModal('browser-modal');
  } else if (_origSelectBrowserModel) {
    _origSelectBrowserModel();
  }
}

// Clear the folder-pick flag if the browser modal is closed without selecting
// (e.g. user clicks the backdrop or the X button)
function _onBrowserModalClose() {
  window._codingFolderPick = false;
}
document.addEventListener('DOMContentLoaded', () => {
  const bm = document.getElementById('browser-modal');
  if (bm) bm.addEventListener('click', e => {
    if (e.target === bm) _onBrowserModalClose();
  });
});

// ═══════════════════════════════════════════════════════════════════
// ── Slash Commands ────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════

const SLASH_COMMANDS = [
  { cmd: '/CodingSpace',    desc: 'Toggle split-screen coding panel (chat left, editor + files right)', usage: '/CodingSpace' },
  { cmd: '/provider',       desc: 'Switch AI provider (local, API key, or upload config file)', usage: '/provider' },
  { cmd: '/coding',         desc: 'Start a coding session with project context', usage: '/coding' },
  { cmd: '/validate_skill', desc: 'Validate a skill with AI',                   usage: '/validate_skill <name>' },
  { cmd: '/fix_skill',      desc: 'Ask AI to rewrite a broken skill',            usage: '/fix_skill <name>' },
  { cmd: '/list_skills',    desc: 'Show all registered skills',                  usage: '/list_skills' },
  { cmd: '/compact',        desc: 'Summarize + compact context',                 usage: '/compact' },
  { cmd: '/clear',          desc: 'Clear chat history',                          usage: '/clear' },
  { cmd: '/remember',       desc: 'Save a fact to memory',                       usage: '/remember <text>' },
  { cmd: '/recall',         desc: 'Search memory',                               usage: '/recall <query>' },
  { cmd: '/help',           desc: 'Show all slash commands',                     usage: '/help' },
  { cmd: '/bookcontext',    desc: 'Build Book Bible from book.json — full novel awareness in small context', usage: '/bookcontext [path/to/book.json]' },
];

let _cmdSelectedIdx = -1;

function _cmdDropdown()  { return document.getElementById('cmd-dropdown'); }
function _cmdInput()     { return document.getElementById('input-box'); }

function _showCmdDropdown(filter) {
  const dd = _cmdDropdown();
  const matches = filter
    ? SLASH_COMMANDS.filter(c => c.cmd.startsWith(filter.toLowerCase()))
    : SLASH_COMMANDS;

  if (!matches.length) { _hideCmdDropdown(); return; }

  _cmdSelectedIdx = 0;
  dd.innerHTML = matches.map((c, i) => `
    <div class="cmd-item${i === 0 ? ' selected' : ''}" data-cmd="${c.cmd}">
      <span class="cmd-name">${c.cmd}</span>
      <span class="cmd-desc">${c.desc}</span>
      <span class="cmd-usage">${c.usage}</span>
    </div>`).join('');

  dd.querySelectorAll('.cmd-item').forEach((el, i) => {
    el.onmouseenter = () => {
      dd.querySelectorAll('.cmd-item').forEach(e => e.classList.remove('selected'));
      el.classList.add('selected');
      _cmdSelectedIdx = i;
    };
    el.onclick = () => _selectCmd(el.dataset.cmd);
  });

  dd.classList.add('open');
}

function _hideCmdDropdown() {
  _cmdDropdown().classList.remove('open');
  _cmdSelectedIdx = -1;
}

function _selectCmd(cmd) {
  const box = _cmdInput();
  // Replace current /... text with the chosen command + space
  box.value = cmd + ' ';
  _hideCmdDropdown();
  box.focus();
}

function _cmdNavKey(dir) {
  const dd = _cmdDropdown();
  const items = dd.querySelectorAll('.cmd-item');
  if (!items.length) return false;
  items[_cmdSelectedIdx]?.classList.remove('selected');
  _cmdSelectedIdx = (_cmdSelectedIdx + dir + items.length) % items.length;
  items[_cmdSelectedIdx]?.classList.add('selected');
  return true;
}

// ── Slash command router ───────────────────────────────────────────
async function handleSlashCommand(raw) {
  const parts  = raw.trim().split(/\s+/);
  const cmd    = parts[0].toLowerCase();
  const args   = parts.slice(1).join(' ').trim();

  switch (cmd) {
    case '/codingspace':    return toggleCodingSpace();
    case '/provider':       return openProviderModal();
    case '/coding':         return openCodingModal();
    case '/validate_skill': return runValidateSkill(args, false);
    case '/fix_skill':      return runValidateSkill(args, true);
    case '/list_skills':    return listSkillsInChat();
    case '/compact':        return compactContext();
    case '/clear':          return clearContext();
    case '/remember':       return quickRemember(args);
    case '/recall':         return quickRecall(args);
    case '/help':           return showHelp();
    case '/bookcontext':    return runBookContext(args);
    default:
      addSystemMessage(`Unknown command: ${cmd}. Type /help for the list.`);
  }
}

// ── /bookcontext ──────────────────────────────────────────────────
async function runBookContext(args) {
  if (!_canChat()) { toast('Load a model first (use Creative personality for best results)', 'error'); return; }

  // Switch to Creative personality automatically
  const sel = document.getElementById('personality-select');
  if (sel && sel.value !== 'creative') {
    sel.value = 'creative';
    state.personalityId = 'creative';
    addSystemMessage('Switched to Creative personality for book writing.');
  }

  const pathHint = args ? `Use book_json_path="${args}".` : 'Auto-detect book.json in workspace.';
  addSystemMessage('📖 Building Book Bible — reading each chapter sequentially…');

  const msg = (
    `You are a book editor. Use the book_writer_skill to build a complete Book Bible.\n\n` +
    `Steps:\n` +
    `1. Call book_writer_skill with action="list_chapters" to see all chapters. ${pathHint}\n` +
    `2. For each chapter (by index), call book_writer_skill with action="summarize_chapter" and chapter_index=N.\n` +
    `   For each chapter you read, write a structured summary:\n` +
    `   ## Chapter N: [Title]\n` +
    `   **Characters present:** [name — role, arc note]\n` +
    `   **Key events:** bullet list\n` +
    `   **Plot threads opened/closed:** ...\n` +
    `   **Tone/style:** ...\n` +
    `   **Ending state:** ...\n\n` +
    `3. After all chapters, append two master sections:\n` +
    `   ## Master Character Sheet\n` +
    `   (each named character, role, arc across all chapters)\n` +
    `   ## Timeline\n` +
    `   (chronological events with chapter references)\n` +
    `   ## Open Threads\n` +
    `   (unresolved plot points for next chapter)\n\n` +
    `4. Call book_writer_skill with action="save_bible" and content="[the full markdown]".\n\n` +
    `Be thorough. Each chapter summary should be ~150-200 words.`
  );

  try {
    _setGenerating(true);
    const { bubble } = createAssistantBubble();
    const result = await API.post('/api/agent', {
      message: msg,
      personality_id: 'creative',
      max_iterations: 25,
      server_name: 'main',
      conv_id: state.convId,
    });
    renderFinalBubble(bubble, result.content || 'Book Bible built.');
    updateContextBar();
    // Check if book-bible.md now exists in workspace
    _checkBookMode();
    toast('Book Bible complete — switch to Creative personality and ask AI to continue your story!', 'success', 5000);
  } catch (e) {
    toast('Book Bible failed: ' + e.message, 'error');
  } finally {
    _setGenerating(false);
  }
}

// ── Book Mode badge ───────────────────────────────────────────────
let _bookModeActive = false;

async function _checkBookMode() {
  try {
    const files = await API.get('/api/workspace/files');
    const hasBook = files.some(f => f.path === 'book.json' || f.path.endsWith('/book.json'));
    const hasBible = files.some(f => f.path === 'book-bible.md' || f.path.endsWith('/book-bible.md'));
    const badge = document.getElementById('book-mode-badge');
    if (!badge) return;
    _bookModeActive = hasBook;
    badge.style.display = hasBook ? '' : 'none';
    badge.title = hasBible
      ? 'Book Bible ready — use Creative personality to write chapters'
      : 'book.json detected — run /bookcontext to build the Book Bible';
    badge.textContent = hasBible ? '📖 Book Mode ✓' : '📖 Book Mode';
    badge.style.opacity = hasBible ? '1' : '0.6';
  } catch (_) {}
}

// ── /validate_skill & /fix_skill ──────────────────────────────────

const SKILL_TEMPLATE = `\`\`\`python
def execute(**kwargs):
    # 1. Read your arguments
    param = kwargs.get("param_name", "default")

    # 2. Install dependencies inside execute() (auto-installs on first run)
    try:
        import requests
    except ImportError:
        import subprocess, sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests

    # 3. Use vault for secrets — never hardcode API keys
    # api_key = vault_get("MY_API_KEY")

    # 4. Do the work
    result = f"Result for: {param}"

    # 5. Always return a STRING
    return result
\`\`\``;

const VALIDATE_SYSTEM = `You are a skill validator for PyAgenticLlama.

A "skill" is a Python snippet stored in a JSON file. The app calls \`execute(**kwargs)\` from it.

RULES a valid skill must follow:
1. Must define \`def execute(**kwargs)\`
2. Must RETURN a string (not print, not yield — return)
3. All imports must be inside execute() or inside a helper function — never at module level (skills are exec'd, not imported)
4. Use \`kwargs.get("param", default)\` to read arguments
5. Use \`vault_get("KEY")\` to read stored secrets — never hardcode keys
6. If deps need installing, use subprocess.check_call inside the function

CORRECT TEMPLATE:
${SKILL_TEMPLATE}

Your task:
1. ✅ List what is CORRECT
2. ⚠️ List every PROBLEM with line references if possible
3. 🔧 Show the FULLY CORRECTED skill code in a complete \`\`\`python block
4. Final verdict on its own line: VALID ✅ / FIXABLE ⚠️ / BROKEN ❌`;

const FIX_SYSTEM = `You are a skill repair tool for PyAgenticLlama.
Rewrite the following skill so it is fully correct and working.
Output ONLY the corrected skill in a single \`\`\`python code block — no explanation outside the block.
Follow these rules:
1. Function must be named \`execute(**kwargs)\`
2. Must return a string
3. All imports inside execute() or helper functions (never module-level)
4. Use vault_get("KEY") for secrets
5. Handle the case where required args are missing`;

async function runValidateSkill(skillName, fixMode) {
  if (!_canChat()) { toast('Load a model or set an AI provider (/provider)', 'error'); return; }

  if (!skillName) {
    // Show list of skills to choose from
    const skills = await API.get('/api/skills').catch(() => []);
    if (!skills.length) { addSystemMessage('No skills found. Create one first.'); return; }
    addSystemMessage('Available skills:\n' + skills.map(s => `  • ${s.name}  (id: ${s.id})`).join('\n')
      + `\n\nUsage: /validate_skill <name>`);
    return;
  }

  // Find skill(s) matching the name
  let hits = [];
  try {
    hits = await API.get('/api/skills/find?name=' + encodeURIComponent(skillName));
  } catch (e) { /* fallback: scan all */ }

  if (!hits.length) {
    // Fallback: try to read the .py file directly if name matches a file
    addSystemMessage(`No skill found matching "${skillName}". Check the skill name in the Skills tab.`);
    return;
  }

  const skill = hits[0];

  // Build the context block the AI will see
  let skillContext = `Skill name: ${skill.name}\nAction type: ${skill.action_type}\nDescription: ${skill.description}\n`;
  if (skill.parameters && Object.keys(skill.parameters).length) {
    skillContext += `Parameters schema:\n${JSON.stringify(skill.parameters, null, 2)}\n`;
  }

  if (skill.action_type === 'python' && skill.code) {
    skillContext += `\nSkill code:\n\`\`\`python\n${skill.code}\n\`\`\``;
  } else if (skill.action_type === 'webhook') {
    skillContext += `\nWebhook URL: ${skill.webhook_url}`;
  } else {
    skillContext += `\n(No code found — skill may be stored as a .py file)`;

    // Try to load the .py file
    try {
      const pyPath = `app/skills/${skill.name}.py`;
      const res = await fetch(`/api/skills/source?id=${skill.id}`).catch(() => null);
      if (res?.ok) {
        const src = await res.json();
        skillContext += `\n\`\`\`python\n${src.code}\n\`\`\``;
      }
    } catch (e) { /* skip */ }
  }

  const userMsg = fixMode
    ? `Please rewrite and fix this skill completely:\n\n${skillContext}`
    : `Please validate this skill and tell me what is correct, what is wrong, and show the fixed version:\n\n${skillContext}`;

  // Show in chat as a user message with a header indicating this is a validation request
  removeEmptyState();
  const wrap = document.createElement('div');
  wrap.className = 'msg user';
  wrap.innerHTML = `
    <div class="msg-meta"><span class="msg-role">You</span></div>
    <div class="msg-bubble">
      <div class="validate-header">
        ${fixMode ? '🔧 Fix Skill' : '🔍 Validate Skill'} — <strong>${escHtml(skill.name)}</strong>
      </div>
      <div class="validate-code">${escHtml(skill.code || '(no inline code)')}</div>
      <em style="font-size:12px;color:rgba(255,255,255,0.7)">Asking AI to ${fixMode ? 'rewrite' : 'review'} this skill…</em>
    </div>`;
  document.getElementById('messages').appendChild(wrap);
  scrollToBottom();

  // Stream the AI response with the validation system prompt
  await streamChat(userMsg, fixMode ? FIX_SYSTEM : VALIDATE_SYSTEM);
}

// ── /list_skills ──────────────────────────────────────────────────

async function listSkillsInChat() {
  const skills = await API.get('/api/skills').catch(() => []);
  if (!skills.length) { addSystemMessage('No skills registered yet.'); return; }
  const lines = ['**Registered Skills**\n'];
  skills.forEach(s => {
    const status = s.enabled ? '✅' : '⛔';
    lines.push(`${status} **${s.name}** (${s.action_type}) — ${s.description}`);
  });
  addSystemMessage(lines.join('\n'));
}

// ── /remember & /recall ───────────────────────────────────────────

async function quickRemember(text) {
  if (!text) { addSystemMessage('Usage: /remember <what to remember>'); return; }
  await API.post('/api/brain/remember', { content: text, type_: 'fact', tags: [] });
  addSystemMessage(`✅ Remembered: "${text}"`);
}

async function quickRecall(query) {
  if (!query) { addSystemMessage('Usage: /recall <search query>'); return; }
  const results = await API.get('/api/brain/recall?q=' + encodeURIComponent(query) + '&limit=5').catch(() => []);
  if (!results.length) { addSystemMessage(`No memories found for: "${query}"`); return; }
  const lines = [`**Memory recall for: ${query}**\n`];
  results.forEach((m, i) => lines.push(`${i+1}. [${m.type}] ${m.content}`));
  addSystemMessage(lines.join('\n'));
}

// ── /help ─────────────────────────────────────────────────────────

function showHelp() {
  const lines = ['**Slash Commands**\n'];
  SLASH_COMMANDS.forEach(c => lines.push(`\`${c.usage}\` — ${c.desc}`));
  addSystemMessage(lines.join('\n'));
}

// ── Textarea auto-resize + Enter to send ─────────────────────────
function initInput() {
  const box = document.getElementById('input-box');

  box.addEventListener('keydown', (e) => {
    const dd = _cmdDropdown();

    // Navigate autocomplete with arrow keys
    if (dd.classList.contains('open')) {
      if (e.key === 'ArrowUp')   { e.preventDefault(); _cmdNavKey(-1); return; }
      if (e.key === 'ArrowDown') { e.preventDefault(); _cmdNavKey(+1); return; }
      if (e.key === 'Tab' || (e.key === 'Enter' && _cmdSelectedIdx >= 0)) {
        e.preventDefault();
        const sel = dd.querySelector('.cmd-item.selected');
        if (sel) _selectCmd(sel.dataset.cmd);
        return;
      }
      if (e.key === 'Escape') { _hideCmdDropdown(); return; }
    }

    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  box.addEventListener('input', () => {
    box.style.height = 'auto';
    box.style.height = Math.min(box.scrollHeight, 160) + 'px';

    const val = box.value;
    // Show ALL commands when just "/" is typed; filter as user continues typing
    if (val.startsWith('/') && !val.includes(' ')) {
      _showCmdDropdown(val === '/' ? null : val);
    } else {
      _hideCmdDropdown();
    }
  });

  // Hide dropdown when clicking outside
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.input-area')) _hideCmdDropdown();
  });

  document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'n') { e.preventDefault(); newChat(); }
  });
}

// ── Model select change ───────────────────────────────────────────
function initModelSelect() {
  document.getElementById('model-select').addEventListener('change', onModelSelect);
}

// ── Periodic status refresh ───────────────────────────────────────
function startPolling() {
  checkServerStatus();
  checkVSCode();
  setInterval(checkServerStatus, 15000);
  setInterval(checkVSCode, 8000);
  setInterval(() => { if (state.serverRunning) updateContextBar(); }, 10000);
}

// ═══════════════════════════════════════════════════════════════════
// ── MCP Servers ───────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════

async function loadMcpServers() {
  try {
    const servers = await API.get('/api/mcp/servers');
    const list = document.getElementById('mcp-list');
    list.innerHTML = '';

    if (!servers.length) {
      list.innerHTML = `<div style="color:var(--text3);font-size:12px;text-align:center;padding:14px">
        No MCP servers configured.<br>Click <strong>+ Add Server</strong> to connect one.
      </div>`;
      return;
    }

    servers.forEach(s => {
      const card = document.createElement('div');
      card.className = 'mcp-card';
      const toolChips = s.tools.slice(0, 6).map(t =>
        `<span class="mcp-tool-chip">${escHtml(t.name)}</span>`).join('');
      const moreTools = s.tool_count > 6 ? `<span class="mcp-tool-chip">+${s.tool_count - 6}</span>` : '';
      card.innerHTML = `
        <div class="mcp-card-top">
          <span class="mcp-status-dot ${s.connected ? 'on' : ''}"></span>
          <span class="mcp-name">${escHtml(s.name)}</span>
          <span class="badge ${s.connected ? 'badge-green' : 'badge-yellow'}">${s.connected ? `${s.tool_count} tools` : 'offline'}</span>
        </div>
        ${s.description ? `<div class="mcp-desc">${escHtml(s.description)}</div>` : ''}
        ${s.tools.length ? `<div class="mcp-tools">${toolChips}${moreTools}</div>` : ''}
        ${s.error ? `<div style="font-size:11px;color:var(--red);margin-bottom:5px">${escHtml(s.error)}</div>` : ''}
        <div class="mcp-actions">
          ${s.connected
            ? `<button class="btn btn-danger btn-sm" onclick="mcpDisconnect('${s.name}')">Disconnect</button>`
            : `<button class="btn btn-success btn-sm" onclick="mcpConnect('${s.name}')">Connect</button>`
          }
          <button class="btn btn-ghost btn-sm" onclick="openMcpAddModal(${JSON.stringify(s).replace(/"/g,'&quot;')})">Edit</button>
          <button class="btn btn-danger btn-sm btn-icon" onclick="mcpRemove('${s.name}')" title="Remove">🗑</button>
        </div>
      `;
      list.appendChild(card);
    });
  } catch (e) {
    toast('MCP load failed: ' + e.message, 'error');
  }
}

async function mcpConnect(name) {
  try {
    toast(`Connecting to ${name}…`, 'info', 2000);
    await API.post(`/api/mcp/servers/${encodeURIComponent(name)}/connect`);
    toast(`${name} connected`, 'success');
    loadMcpServers();
  } catch (e) {
    toast(`Connect failed: ${e.message}`, 'error', 5000);
  }
}

async function mcpDisconnect(name) {
  await API.post(`/api/mcp/servers/${encodeURIComponent(name)}/disconnect`);
  toast(`${name} disconnected`, 'info');
  loadMcpServers();
}

async function mcpRemove(name) {
  if (!confirm(`Remove MCP server "${name}"?`)) return;
  await API.del(`/api/mcp/servers/${encodeURIComponent(name)}`);
  toast(`${name} removed`, 'info');
  loadMcpServers();
}

async function openMcpAddModal(existing) {
  // Load presets into modal
  try {
    const presets = await API.get('/api/mcp/presets');
    const pc = document.getElementById('mcp-presets');
    pc.innerHTML = '';
    presets.forEach(p => {
      const btn = document.createElement('button');
      btn.className = 'mcp-preset-btn';
      btn.textContent = p.name;
      btn.title = p.description;
      btn.onclick = () => {
        document.getElementById('mcp-name').value    = p.name;
        document.getElementById('mcp-desc').value    = p.description || '';
        document.getElementById('mcp-command').value = p.command;
        document.getElementById('mcp-args').value    = (p.args || []).join('\n');
        document.getElementById('mcp-env').value     = Object.entries(p.env || {}).map(([k,v]) => `${k}=${v}`).join('\n');
      };
      pc.appendChild(btn);
    });
  } catch (e) { /* silent */ }

  if (existing) {
    document.getElementById('mcp-edit-name').value  = existing.name || '';
    document.getElementById('mcp-name').value        = existing.name || '';
    document.getElementById('mcp-desc').value        = existing.description || '';
    document.getElementById('mcp-command').value     = existing.command || '';
    document.getElementById('mcp-args').value        = (existing.args || []).join('\n');
    document.getElementById('mcp-env').value         = (existing.env_keys || []).map(k => `${k}=`).join('\n');
    document.getElementById('mcp-enabled').checked   = existing.enabled !== false;
  } else {
    ['mcp-edit-name','mcp-name','mcp-desc','mcp-command','mcp-args','mcp-env'].forEach(id => {
      document.getElementById(id).value = '';
    });
    document.getElementById('mcp-enabled').checked = true;
  }
  openModal('mcp-modal');
}

async function saveMcpServer() {
  const name    = document.getElementById('mcp-name').value.trim();
  const command = document.getElementById('mcp-command').value.trim();
  if (!name || !command) { toast('Name and command are required', 'error'); return; }

  const args = document.getElementById('mcp-args').value.split('\n').map(l => l.trim()).filter(Boolean);
  const env  = {};
  document.getElementById('mcp-env').value.split('\n').forEach(line => {
    const eq = line.indexOf('=');
    if (eq > 0) env[line.slice(0, eq).trim()] = line.slice(eq + 1).trim();
  });

  try {
    await API.post('/api/mcp/servers', {
      name, command, args, env,
      description: document.getElementById('mcp-desc').value,
      enabled: document.getElementById('mcp-enabled').checked,
    });
    closeModal('mcp-modal');
    toast(`Saved — connecting to ${name}…`, 'info', 2000);
    await mcpConnect(name);
  } catch (e) {
    toast('Save failed: ' + e.message, 'error');
  }
}

// ═══════════════════════════════════════════════════════════════════
// ── Test Skill ────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════

let _testSkillId = null;

async function openTestSkillModal(skillId, skillName) {
  _testSkillId = skillId;
  document.getElementById('test-skill-name').textContent = skillName;
  document.getElementById('test-skill-output').style.display = 'none';

  // Build a filled argument template from the skill's parameter schema
  try {
    const skills = await API.get('/api/skills');
    const skill  = skills.find(s => s.id === skillId);
    const schema = skill?.parameters || {};
    const props  = schema.properties || {};
    const required = schema.required || [];

    // Auto-fill each property with a sensible placeholder value
    const template = {};
    for (const [key, def] of Object.entries(props)) {
      if (def.type === 'string')  template[key] = def.example ?? (required.includes(key) ? `your ${key} here` : '');
      else if (def.type === 'integer' || def.type === 'number') template[key] = def.default ?? 5;
      else if (def.type === 'boolean') template[key] = def.default ?? true;
      else if (def.type === 'array')   template[key] = [];
      else template[key] = null;
    }

    const argsEl    = document.getElementById('test-skill-args');
    const hintsEl   = document.getElementById('test-skill-hints');

    argsEl.value = JSON.stringify(template, null, 2);

    // Show parameter hints (name: description)
    if (Object.keys(props).length && hintsEl) {
      hintsEl.innerHTML = Object.entries(props).map(([k, d]) => {
        const req = required.includes(k) ? '<span style="color:var(--red)"> *</span>' : '';
        const desc = d.description ? ` — ${escHtml(d.description)}` : '';
        return `<div><code style="color:var(--cyan)">${escHtml(k)}</code>${req}<span style="color:var(--text3)">${desc}</span></div>`;
      }).join('');
      hintsEl.style.display = '';
    } else if (hintsEl) {
      hintsEl.style.display = 'none';
    }
  } catch (e) {
    document.getElementById('test-skill-args').value = '{}';
  }

  openModal('test-skill-modal');
}

async function runTestSkill() {
  if (!_testSkillId) return;
  let kwargs = {};
  try {
    kwargs = JSON.parse(document.getElementById('test-skill-args').value || '{}');
  } catch (e) {
    toast('Arguments must be valid JSON', 'error'); return;
  }

  const runBtn = document.getElementById('test-skill-run-btn');
  const status = document.getElementById('test-skill-status');
  const result = document.getElementById('test-skill-result');
  const out    = document.getElementById('test-skill-output');

  runBtn.disabled = true;
  runBtn.textContent = '⏳ Running…';
  out.style.display = '';
  status.innerHTML = '<span class="spinner"></span> Running…';
  result.textContent = '';
  result.className = 'code-output-body';

  try {
    const data = await API.post('/api/skills/test', { skill_id: _testSkillId, kwargs });
    status.innerHTML = '<span style="color:var(--green)">✓ OK</span>';
    result.textContent = String(data.result);
    result.className = 'code-output-body ok';
  } catch (e) {
    status.innerHTML = '<span style="color:var(--red)">✗ Error</span>';
    result.textContent = e.message;
    result.className = 'code-output-body err';
  } finally {
    runBtn.disabled = false;
    runBtn.textContent = '▶ Run';
  }
}

// ═══════════════════════════════════════════════════════════════════
// ── Floating Windows ──────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════

class FloatWin {
  constructor({ id, btnId, defaultRight, defaultBottom, defaultWidth, defaultHeight }) {
    this.el      = document.getElementById(id);
    this.btnEl   = document.getElementById(btnId);
    this.body    = this.el.querySelector('.float-body');
    this._docked = false;
    this._minimized = false;

    // Set default position via CSS vars already on the element
    this._initDrag();
    this._initResize();
  }

  // ── Visibility ─────────────────────────────────────────────────
  toggle() {
    const on = this.el.classList.toggle('visible');
    this.btnEl?.classList.toggle('win-btn-on', on);
    if (on) this._onOpen();
  }

  open() {
    if (!this.visible) {
      this.el.classList.add('visible');
      this.btnEl?.classList.add('win-btn-on');
      this._onOpen();
    }
  }

  get visible() { return this.el.classList.contains('visible'); }

  // ── Minimize ───────────────────────────────────────────────────
  minimize() {
    this._minimized = !this._minimized;
    this.el.classList.toggle('minimized', this._minimized);
    const btn = this.el.querySelector('[id$="-min-btn"]') ||
                this.el.querySelectorAll('.float-btn')[1];
    if (btn) btn.textContent = this._minimized ? '□' : '─';
  }

  // ── Clear body ─────────────────────────────────────────────────
  clearBody() {
    this.body.innerHTML = '';
  }

  // ── Dock / Undock ──────────────────────────────────────────────
  toggleDock() {
    const area   = document.getElementById('float-dock-area');
    const dockBtn = this.el.querySelector('[id$="-dock-btn"]') ||
                    this.el.querySelectorAll('.float-btn')[2];

    if (!this._docked) {
      // Move into dock area
      this._savedStyle = {
        left: this.el.style.left, top: this.el.style.top,
        right: this.el.style.right, bottom: this.el.style.bottom,
        width: this.el.style.width, height: this.el.style.height,
      };
      this.el.classList.add('docked');
      area.appendChild(this.el);
      area.style.display = 'flex';
      this.el.style.cssText = '';   // let .docked class take over
      this.el.classList.add('docked', 'visible');
      if (dockBtn) { dockBtn.textContent = '⊟'; dockBtn.title = 'Undock'; }
      this._docked = true;
    } else {
      // Return to floating
      this.el.classList.remove('docked');
      document.body.appendChild(this.el);
      const s = this._savedStyle || {};
      this.el.style.right  = s.right  || '20px';
      this.el.style.bottom = s.bottom || '20px';
      this.el.style.left   = s.left   || '';
      this.el.style.top    = s.top    || '';
      this.el.style.width  = s.width  || '600px';
      this.el.style.height = s.height || '320px';
      if (dockBtn) { dockBtn.textContent = '⊞'; dockBtn.title = 'Dock'; }
      this._docked = false;
      // Hide area if empty
      if (!area.children.length) area.style.display = 'none';
    }
  }

  // ── Drag ───────────────────────────────────────────────────────
  _initDrag() {
    const handle = this.el.querySelector('.float-title');
    let sx, sy, sl, st;
    handle.addEventListener('mousedown', (e) => {
      if (e.target.closest('button') || this._docked) return;
      // Convert right/bottom to left/top for easier math
      const rect = this.el.getBoundingClientRect();
      this.el.style.left   = rect.left + 'px';
      this.el.style.top    = rect.top  + 'px';
      this.el.style.right  = 'auto';
      this.el.style.bottom = 'auto';
      sx = e.clientX; sy = e.clientY;
      sl = rect.left;  st = rect.top;
      this.el.style.transition = 'none';
      this.el.style.zIndex = '460';

      const move = (e) => {
        let nx = sl + e.clientX - sx;
        let ny = st + e.clientY - sy;
        // Clamp to viewport
        nx = Math.max(0, Math.min(nx, window.innerWidth  - 60));
        ny = Math.max(0, Math.min(ny, window.innerHeight - 40));
        this.el.style.left = nx + 'px';
        this.el.style.top  = ny + 'px';
      };
      const up = () => {
        this.el.style.transition = '';
        this.el.style.zIndex = '450';
        document.removeEventListener('mousemove', move);
        document.removeEventListener('mouseup', up);
      };
      document.addEventListener('mousemove', move);
      document.addEventListener('mouseup', up);
      e.preventDefault();
    });
  }

  // ── Native resize (HTML resize attr) ──────────────────────────
  _initResize() {
    if (!this._docked) this.el.style.overflow = 'hidden';
    this.el.style.resize = 'both';
  }

  // Override in subclasses
  _onOpen() {}

  // ── Append line to body, auto-scroll ──────────────────────────
  appendLine(html) {
    const atBottom = this.body.scrollHeight - this.body.scrollTop <= this.body.clientHeight + 4;
    const line = document.createElement('div');
    line.innerHTML = html;
    this.body.appendChild(line);
    if (atBottom) this.body.scrollTop = this.body.scrollHeight;
  }

  appendText(text) {
    this.appendLine(escHtml(text));
  }
}

// ── Console window ─────────────────────────────────────────────────
class ConsoleWin extends FloatWin {
  constructor(opts) {
    super(opts);
    this._pollIdx  = 0;
    this._pollTimer = null;
  }

  _onOpen() {
    this._startPolling();
  }

  _startPolling() {
    if (this._pollTimer) return;
    this._pollTimer = setInterval(() => this._poll(), 1500);
    this._poll();  // immediate first fetch
  }

  _stopPolling() {
    clearInterval(this._pollTimer);
    this._pollTimer = null;
  }

  toggle() {
    super.toggle();
    if (!this.visible) this._stopPolling();
  }

  clearBody() {
    super.clearBody();
    this._pollIdx = 0;
  }

  async _poll() {
    if (!this.visible) return;
    try {
      const data = await API.get(`/api/console/lines?after=${this._pollIdx}`);
      if (data.lines && data.lines.length) {
        data.lines.forEach(line => this.appendLine(this._colorLine(line)));
        this._pollIdx = data.total;
      }
    } catch (e) { /* silent */ }
  }

  _colorLine(raw) {
    const e = escHtml(raw);
    if (/error|fail|fatal/i.test(raw))   return `<span class="log-err">${e}</span>`;
    if (/warn/i.test(raw))               return `<span class="log-warn">${e}</span>`;
    if (/loaded|ready|success|ok/i.test(raw)) return `<span class="log-ok">${e}</span>`;
    if (/^[.\s]*$/.test(raw) || raw.length < 3) return `<span class="log-dim">${e}</span>`;
    return `<span class="log-info">${e}</span>`;
  }
}

// ── Terminal window ────────────────────────────────────────────────
class TerminalWin extends FloatWin {
  constructor(opts) {
    super(opts);
    this._cwd     = '';
    this._history = [];   // command history
    this._histIdx = -1;   // arrow-key position
    this._busy    = false;

    const inp = document.getElementById('terminal-input');
    inp.addEventListener('keydown', (e) => {
      if (e.key === 'Enter')      { e.preventDefault(); terminalRun(); }
      if (e.key === 'ArrowUp')    { e.preventDefault(); this._histNav(-1); }
      if (e.key === 'ArrowDown')  { e.preventDefault(); this._histNav(+1); }
    });
  }

  _histNav(dir) {
    const inp = document.getElementById('terminal-input');
    this._histIdx = Math.max(-1, Math.min(this._history.length - 1, this._histIdx + dir));
    inp.value = this._histIdx >= 0 ? this._history[this._histIdx] : '';
  }

  _onOpen() {
    // Load current working directory on first open
    if (!this._cwd) {
      API.get('/api/terminal/cwd')
        .then(d => this._setCwd(d.cwd))
        .catch(() => {});
    }
    document.getElementById('terminal-input').focus();
  }

  _setCwd(cwd) {
    this._cwd = cwd;
    // Show only last 2 path segments for brevity
    const parts = cwd.replace(/\\/g, '/').split('/').filter(Boolean);
    const short = parts.slice(-2).join('/');
    document.getElementById('terminal-cwd-label').textContent = cwd;
    document.getElementById('terminal-prompt').textContent = `${short}>`;
  }

  async exec(cmd) {
    if (this._busy || !cmd.trim()) return;
    this._busy = true;

    // Add to history (skip duplicates at top)
    if (cmd.trim() && this._history[0] !== cmd) this._history.unshift(cmd);
    if (this._history.length > 100) this._history.pop();
    this._histIdx = -1;

    // Echo the command
    const parts = this._cwd.replace(/\\/g, '/').split('/').filter(Boolean);
    const short = parts.slice(-2).join('/');
    this.appendLine(`<span class="term-prompt">${escHtml(short)}&gt;</span> <span class="term-cmd">${escHtml(cmd)}</span>`);

    // Show a running indicator for commands that may take a while
    const runningId = 'term-running-' + Date.now();
    this.appendLine(`<span class="term-dim" id="${runningId}">running…</span>`);

    try {
      const res = await API.post('/api/terminal/exec', { command: cmd, timeout: 300 });
      // Remove the running indicator
      document.getElementById(runningId)?.remove();
      if (res.output) {
        const cls = res.returncode !== 0 ? 'term-err' : 'term-out';
        res.output.split('\n').forEach(l => {
          if (l !== '') this.appendLine(`<span class="${cls}">${escHtml(l)}</span>`);
        });
      }
      if (res.cwd) this._setCwd(res.cwd);
    } catch (e) {
      document.getElementById(runningId)?.remove();
      this.appendLine(`<span class="term-err">Error: ${escHtml(e.message)}</span>`);
    } finally {
      this._busy = false;
      document.getElementById('terminal-input').focus();
    }
  }
}

// ── Instantiate windows ────────────────────────────────────────────
const floatWins = {
  console:  new ConsoleWin({ id: 'float-console',  btnId: 'console-btn' }),
  terminal: new TerminalWin({ id: 'float-terminal', btnId: 'terminal-btn' }),
};

// ── Global terminal run helper (called by button + Enter key) ────
async function terminalRun() {
  const inp = document.getElementById('terminal-input');
  const cmd = inp.value;
  inp.value = '';
  await floatWins.terminal.exec(cmd);
}

// ── Right panel collapse ──────────────────────────────────────────

function toggleRightPanel() {
  const rp        = document.getElementById('right-panel');
  const workspace = rp?.closest('.workspace');
  const btn       = document.getElementById('rp-toggle-btn');
  const collapsed = rp.classList.toggle('rp-collapsed');
  workspace?.classList.toggle('rp-collapsed', collapsed);
  if (btn) btn.textContent = collapsed ? '›' : '‹';
}

async function _loadWorkspacePath() {
  const info = await API.get('/api/workspace').catch(() => null);
  if (info?.path) state.workspacePath = info.path;
}

// ── Boot ──────────────────────────────────────────────────────────

function _splashLog(msg, status = 'ok') {
  const lines = document.getElementById('splash-lines');
  if (!lines) return;
  const tag = status === 'ok'   ? '<span class="s-ok">[  OK  ]</span>'
             : status === 'warn' ? '<span class="s-warn">[ WARN ]</span>'
             :                    '<span class="s-info">[ INFO ]</span>';
  const el = document.createElement('div');
  el.className = 'splash-line';
  el.innerHTML = `${tag} ${msg}`;
  lines.appendChild(el);
  // Keep scroll at bottom so latest line is always visible
  const term = document.getElementById('splash-terminal');
  if (term) term.scrollTop = term.scrollHeight;
}

function _splashWrap(promise, doneMsg, warnMsg) {
  return promise
    .then(r  => { _splashLog(doneMsg, 'ok');   return r; })
    .catch(e => { _splashLog(warnMsg || doneMsg + ' — skipped', 'warn'); });
}

async function init() {
  _splashLog('PyAgenticLlama initializing…', 'info');
  _splashLog('uvicorn ASGI server running on port 7860', 'ok');
  _splashLog('FastAPI lifespan: vault env loaded', 'ok');
  _splashLog('Skill auto-discovery complete', 'ok');

  initMenuBar();
  initTabs();
  initInput();
  initModelSelect();
  _splashLog('UI shell mounted', 'ok');

  await Promise.all([
    _splashWrap(loadHardware(),         'Hardware info loaded'),
    _splashWrap(loadModels(),           'Model directory scanned'),
    _splashWrap(loadPersonalities(),    'Personalities registered'),
    _splashWrap(loadSkills(),           'Skills indexed'),
    _splashWrap(checkServerStatus(),    'Inference server checked'),
    _splashWrap(_loadProviderBadge(),   'Provider config loaded'),
    _splashWrap(_loadWorkspacePath(),   'Workspace path resolved'),
    _splashWrap(_checkBookMode(),       'Book mode checked'),
    _splashWrap(_applyStartupConfig(), 'Launch mode applied'),
  ]);

  startPolling();
  _splashLog('All systems nominal — welcome!', 'ok');

  // Short pause so the user can read the last line, then fade out
  await new Promise(r => setTimeout(r, 750));
  const splash = document.getElementById('splash-screen');
  if (splash) {
    splash.classList.add('fade-out');
    splash.addEventListener('transitionend', () => splash.remove(), { once: true });
  }
}

init();
