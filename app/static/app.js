// ── State ─────────────────────────────────────────────────────────
const state = {
  models: [],
  selectedModel: null,
  serverRunning: false,
  mode: 'chat',          // 'chat' | 'agent'
  convId: 'default',
  personalityId: 'default',
  personalities: [],
  streaming: false,
  browserPath: 'C:\\',
  browserSelected: null,
  currentTps: 0,
};

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
    case 'new-skill':      openSkillModal(null); break;
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
      if (tabName === 'memory') loadMemories();
      if (tabName === 'agents') loadAgents();
      if (tabName === 'history') loadHistory();
      if (tabName === 'skills') loadSkills();
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
  }
  document.getElementById('model-quick-info').style.display = 'block';
}

// ── Server ────────────────────────────────────────────────────────
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
      server_name: 'main',
    });
    state.serverRunning = true;
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
    updateServerStatus(s.running);
    if (s.running) {
      updateContextBar();
    }
  } catch (e) { /* silent */ }
}

// ── Context Bar ───────────────────────────────────────────────────
async function updateContextBar() {
  try {
    const info = await API.get(`/api/context?conv_id=${state.convId}`);
    const fill = document.getElementById('ctx-fill');
    const tokens = document.getElementById('ctx-tokens');
    const pct = info.usage_pct;
    fill.style.width = pct + '%';
    fill.className = 'ctx-fill' + (pct > 80 ? ' crit' : pct > 60 ? ' warn' : '');
    tokens.textContent = `${info.total_tokens.toLocaleString()} / ${info.max_tokens.toLocaleString()} tokens`;
    if (info.needs_compaction) {
      toast('Context is nearly full — consider compacting', 'info', 4000);
    }
  } catch (e) { /* silent */ }
}

async function compactContext() {
  if (!state.serverRunning) { toast('Load a model first', 'error'); return; }
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

async function sendMessage() {
  if (state.streaming) return;
  const box = document.getElementById('input-box');
  const msg = box.value.trim();
  if (!msg) return;
  if (!state.serverRunning) { toast('Load a model first', 'error'); return; }

  box.value = '';
  box.style.height = 'auto';

  removeEmptyState();
  appendMessage('user', msg);

  if (state.mode === 'agent') {
    await runAgent(msg);
  } else {
    await streamChat(msg);
  }
}

async function streamChat(msg) {
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
        stream: true,
        conv_id: state.convId,
        server_name: 'main',
        inject_memory: injectMem,
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

  // ── Fenced code blocks — rendered as rich interactive blocks ────
  let html = text.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
    lang = (lang || 'text').toLowerCase();
    code = code.trimEnd();
    const id   = _storeCode(lang, code);
    const esc  = escHtml(code);
    const isRunnable  = ['python', 'py'].includes(lang);
    const isPreviewable = ['html', 'javascript', 'js', 'css', 'jsx', 'tsx', 'svg'].includes(lang);

    return `<div class="code-block" data-cbid="${id}">
      <div class="code-header">
        <span class="code-lang">${escHtml(lang)}</span>
        <div class="code-actions">
          <button class="code-btn" onclick="copyCodeBlock('${id}', this)">📋 Copy</button>
          ${isRunnable  ? `<button class="code-btn code-btn-run"     onclick="runCodeBlock('${id}')">▶ Run</button>` : ''}
          ${isPreviewable ? `<button class="code-btn code-btn-preview" onclick="previewCodeBlock('${id}')">👁 Preview</button>` : ''}
        </div>
      </div>
      <pre><code>${esc}</code></pre>
    </div>`;
  });

  // Inline code
  html = html.replace(/`([^`\n]+)`/g, (_, c) => `<code>${escHtml(c)}</code>`);
  // Bold / italic
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*([^*\n]+)\*/g, '<em>$1</em>');
  // Headers
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
  // Tables (basic)
  html = html.replace(/^\|(.+)\|$/gm, (line) => {
    if (/^[\|\s\-:]+$/.test(line)) return '';
    const cells = line.split('|').slice(1,-1).map(c=>`<td>${c.trim()}</td>`).join('');
    return `<tr>${cells}</tr>`;
  });
  html = html.replace(/(<tr>[\s\S]*?<\/tr>)/g, '<table>$1</table>');
  // Lists
  html = html.replace(/^[-*] (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>[\s\S]*?<\/li>)/g, '<ul>$1</ul>');
  // Paragraphs — skip lines that are already block elements
  const parts = html.split(/\n{2,}/);
  html = parts.map(p => {
    const t = p.trim();
    if (!t) return '';
    if (/^<(div|pre|ul|ol|table|h[1-6]|blockquote)/.test(t)) return t;
    return `<p>${t.replace(/\n/g, '<br>')}</p>`;
  }).join('\n');

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
        <div class="skill-footer">
          <span class="skill-type">${s.action_type}</span>
          <button class="btn btn-ghost btn-sm btn-icon" onclick="openSkillModal(${JSON.stringify(s)})" title="Edit">✏️</button>
          <button class="btn btn-danger btn-sm btn-icon" onclick="deleteSkill('${s.id}')" title="Delete">🗑</button>
        </div>
      `;
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
  const parent = document.getElementById('browser-up').dataset.parent;
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

// ── Textarea auto-resize + Enter to send ─────────────────────────
function initInput() {
  const box = document.getElementById('input-box');
  box.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  box.addEventListener('input', () => {
    box.style.height = 'auto';
    box.style.height = Math.min(box.scrollHeight, 160) + 'px';
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
  setInterval(checkServerStatus, 15000);
  setInterval(() => { if (state.serverRunning) updateContextBar(); }, 10000);
}

// ── Boot ──────────────────────────────────────────────────────────
async function init() {
  initMenuBar();
  initTabs();
  initInput();
  initModelSelect();
  await Promise.all([
    loadHardware(),
    loadModels(),
    loadPersonalities(),
    loadSkills(),
    checkServerStatus(),
  ]);
  startPolling();
}

init();
