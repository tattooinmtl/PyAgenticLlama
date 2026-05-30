# PyAgenticLlama

**Advanced local AI interface built on top of llama.cpp** — a full-featured Python web app with agent orchestration, persistent memory, secure secret storage, and a rich chat UI with streaming, code execution, and live preview.

---

## Features

### Chat & Inference
- **Streaming chat** with real-time token/sec display
- **Collapsible thinking blocks** — models like Qwen3 that emit `<think>` tags show a collapsible reasoning panel per message
- **Stop generation** button — cancel mid-stream, keeps whatever arrived
- **Auto context compaction** — when context hits 80%, old messages are summarized automatically so conversation never cuts off
- **Context bar** — live token usage progress bar with color (green → yellow → red)

### Code Blocks
- Every code fence renders with a **language badge**, **📋 Copy** button, **▶ Run** (Python), and **👁 Preview** (HTML/JS/CSS)
- **Run** executes Python locally and shows stdout/stderr inline below the block
- **Preview** renders HTML/JS/CSS in a sandboxed iframe popup with an "Open in Browser" button
- JavaScript preview captures `console.log` output inside the iframe

### Models
- Load any `.gguf` model from the built-in `models/` folder **or anywhere on your PC** via the filesystem browser
- **Hardware check on load** — reads GGUF metadata to show architecture, layers, attention heads, context length, chat template format, and estimated RAM needed
- Correct KV-cache estimation using the GQA formula (not the inflated max-context formula)
- Context length defaults to **4096** — never blindly uses the model's max (e.g. 131K for Llama 3.1 would allocate 64 GB of KV cache)
- **Model Inspector** modal shows full architecture details from GGUF metadata
- Pin extra model folders so they appear in the dropdown permanently

### Personalities
Four built-in, fully customizable:

| Name | Use case | Temp |
|------|----------|------|
| 🤖 Assistant | General chat | 0.7 |
| 💻 Coder | Code generation with strict formatting rules | 0.2 |
| ✨ Creative | Writing, storytelling | 1.1 |
| 📊 Analyst | Structured, factual responses | 0.3 |

Create unlimited custom personalities with avatar color, icon, system prompt, temperature, and top-p.

### Agent Mode
- **Agent loop** — the AI calls your skills as tools, checks results, and loops up to 10 iterations autonomously
- **Sub-agent spawning** — spawn a separate llama-server instance on a new port and dispatch a task to it; results appear in the main chat
- Agent trace panel shows each tool call and its output

### Skills (Tool System)
- Create **Python skills** — define an `execute(**kwargs)` function; use `vault_get("KEY")` to access stored secrets
- Create **Webhook skills** — POST to any HTTP endpoint
- Toggle skills on/off; enabled skills are injected as tools into every request
- AI calls skills automatically in Agent mode

### Brain / Memory
- **Persistent memory** stored in SQLite — remember facts, preferences, project context, notes
- **Full-text search** across all memories
- Conversation history saved per session and browsable in the History tab
- Toggle **🧠 Memory** mode to inject relevant memories into every message automatically

### Secure Vault
- API keys and environment variables stored encrypted with **AES-256 (Fernet)**
- Encryption key derived from your Windows machine identity — no master password needed, access is machine-locked
- Keys are never stored in plaintext, never committed to git
- Variables marked in ALL_CAPS are auto-loaded into the environment on startup
- Access keys inside skills: `vault_get("OPENAI_API_KEY")`

### UI
- **App menu bar** — File, Edit, View, Model, Settings, Tools, Agent, Help (like a real desktop app)
- Dark theme with tabbed left panel (Model / Memory) and right panel (Skills / Agents / History)
- Filesystem browser with quick-access shortcuts (Desktop, Downloads, Documents, Drives)
- Server log viewer, model inspector, vault manager, personality editor all accessible from menus

---

## Requirements

- **Windows 10/11**
- **Python 3.10+** (tested on 3.14)
- **llama.cpp binaries** — place in `llamaVulkan/` (Vulkan build recommended for AMD/Intel GPUs)
- At least one `.gguf` model

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/tattooinmtl/PyAgenticLlama.git
cd PyAgenticLlama

# 2. Add your llama.cpp binaries
#    Copy llama-server.exe and its DLLs into llamaVulkan/

# 3. Add a model
#    Copy any .gguf file into models/
#    Or use File → Browse for Model to load from anywhere

# 4. Launch
start-app.bat
```

Then open **http://localhost:7860** in your browser.

---

## Getting llama.cpp Binaries

Download a pre-built release from [llama.cpp releases](https://github.com/ggerganov/llama.cpp/releases).

- **AMD GPU (Vulkan):** download the `vulkan` build
- **NVIDIA GPU (CUDA):** download the `cuda` build
- **CPU only:** download the `win-noavx` or `avx2` build

Extract and place all files (`llama-server.exe`, `*.dll`) into the `llamaVulkan/` folder.

---

## GPU Layers (GPU Offloading)

The **GPU Layers** setting controls how many model layers run on GPU vs CPU:

| Setting | Effect |
|---------|--------|
| `0` | CPU only — safe default, works everywhere |
| `1–10` | Light GPU offload — good for integrated GPUs (AMD/Intel) with 2–4 GB VRAM |
| `20–32` | Heavy GPU offload — for dedicated GPUs with 6+ GB VRAM |
| `99` | All layers on GPU — only if model fits entirely in VRAM |

> **Tip:** For AMD integrated graphics (shared VRAM), keep GPU Layers at 0–5. Setting it too high will crash.

---

## Recommended Models

With 32 GB RAM, these run well at CPU-only (GPU Layers = 0):

| Model | Size | Quality | Use case |
|-------|------|---------|----------|
| Llama 3.1 8B Q4_K_M | 4.6 GB | Great | General chat, coding |
| Qwen2.5 14B Q4_K_M | ~9 GB | Excellent | Coding, reasoning |
| Qwen3 27B Q4_K_M | ~17 GB | Outstanding | Best quality on 32 GB |
| Mistral 22B Q4_K_M | ~14 GB | Excellent | Fast reasoning |

For context length: the default **4096 tokens** is safe. Raising it increases RAM usage proportionally.

---

## Project Structure

```
PyAgenticLlama/
├── app/
│   ├── main.py           # FastAPI backend — all routes
│   ├── gguf.py           # GGUF metadata reader (architecture, heads, chat template)
│   ├── hardware.py       # RAM/VRAM detection via WMI
│   ├── llama.py          # llama-server process manager (multi-instance registry)
│   ├── context.py        # Context tracking and auto-compaction
│   ├── brain.py          # SQLite memory — remember/recall/conversations
│   ├── vault.py          # AES-256 encrypted secret storage
│   ├── personalities.py  # Personality definitions and management
│   ├── skills/           # User skill definitions (JSON)
│   ├── personalities/    # Personality files (JSON, gitignored)
│   └── static/
│       ├── index.html    # Single-page app
│       ├── style.css     # Dark theme
│       └── app.js        # All frontend logic
├── data/                 # Runtime data (gitignored)
│   ├── brain.db          # SQLite memory database
│   └── vault.enc         # Encrypted secrets
├── llamaVulkan/          # llama.cpp binaries (gitignored — add your own)
├── models/               # GGUF model files (gitignored — add your own)
├── requirements.txt
└── start-app.bat
```

---

## API Endpoints

The backend exposes a REST API you can call directly:

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/server/start` | Load a model and start llama-server |
| `POST` | `/api/server/stop` | Stop the server |
| `GET`  | `/api/server/status` | Server running state |
| `POST` | `/api/chat` | Chat (streaming SSE) |
| `POST` | `/api/agent` | Agentic tool-calling loop |
| `GET`  | `/api/models` | List available GGUF files |
| `GET`  | `/api/models/info?path=` | Full model metadata + RAM estimate |
| `GET`  | `/api/filesystem/browse?path=` | Filesystem browser |
| `POST` | `/api/run` | Execute Python code |
| `POST` | `/api/brain/remember` | Store a memory |
| `GET`  | `/api/brain/recall?q=` | Search memories |
| `GET`  | `/api/vault/keys` | List vault key names |
| `POST` | `/api/vault/set` | Store encrypted secret |
| `POST` | `/api/skills` | Create a skill |
| `POST` | `/api/agents/spawn` | Spawn a sub-agent |

---

## License

MIT
