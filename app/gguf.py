import struct, os
from pathlib import Path

MAGIC = b'GGUF'
_SCALAR = {
    0: ('B', 1), 1: ('b', 1), 2: ('H', 2), 3: ('h', 2),
    4: ('I', 4), 5: ('i', 4), 6: ('f', 4), 7: ('?', 1),
    10: ('Q', 8), 11: ('q', 8), 12: ('d', 8),
}

def _str(f):
    n = struct.unpack('<Q', f.read(8))[0]
    return f.read(n).decode('utf-8', 'replace')

def _val(f, t):
    if t == 8:
        return _str(f)
    if t == 9:
        et = struct.unpack('<I', f.read(4))[0]
        n  = struct.unpack('<Q', f.read(8))[0]
        cap = min(n, 32)
        vals = [_val(f, et) for _ in range(cap)]
        return vals
    if t in _SCALAR:
        fmt, sz = _SCALAR[t]
        return struct.unpack(f'<{fmt}', f.read(sz))[0]
    raise ValueError(f'unknown gguf type {t}')

def metadata(path: str) -> dict:
    kv = {}
    with open(path, 'rb') as f:
        if f.read(4) != MAGIC:
            raise ValueError('not a gguf file')
        f.read(4)   # version
        f.read(8)   # n_tensors
        n = struct.unpack('<Q', f.read(8))[0]
        for _ in range(n):
            try:
                k = _str(f)
                t = struct.unpack('<I', f.read(4))[0]
                kv[k] = _val(f, t)
            except Exception:
                break
    return kv

def _infer_template_format(template: str) -> str:
    t = template.lower()
    if 'llama-3' in t or '<|start_header_id|>' in t:
        return 'llama-3'
    if '<|im_start|>' in t:
        return 'chatml'
    if '<start_of_turn>' in t:
        return 'gemma'
    if '[inst]' in t:
        return 'llama-2'
    if '<|user|>' in t or '<|assistant|>' in t:
        return 'phi'
    if '{% for message' in t:
        return 'jinja2'
    return 'custom'

def model_info(path: str) -> dict:
    size_bytes = os.path.getsize(path)
    gb = size_bytes / 1024**3
    stem = Path(path).stem

    try:
        m = metadata(path)
    except Exception as e:
        return {
            'path': path, 'name': stem, 'architecture': 'unknown',
            'context_length': 4096, 'n_layers': 0, 'n_heads': 0, 'n_kv_heads': 0,
            'embedding_size': 0, 'vocab_size': 0, 'rope_freq_base': 0,
            'file_size_gb': round(gb, 2), 'estimated_ram_gb': round(gb * 1.12, 2),
            'chat_template': None, 'chat_template_format': 'unknown',
            'quantization': 'unknown', 'error': str(e),
        }

    arch = m.get('general.architecture', 'llama')

    def _get(*keys, default=0):
        for k in keys:
            v = m.get(k)
            if v is not None:
                return v
        return default

    ctx      = int(_get(f'{arch}.context_length', 'llama.context_length', default=4096))
    layers   = int(_get(f'{arch}.block_count',    'llama.block_count',    default=0))
    emb      = int(_get(f'{arch}.embedding_length','llama.embedding_length',default=4096))
    heads    = int(_get(f'{arch}.attention.head_count', 'llama.attention.head_count', default=0))
    kv_heads = int(_get(f'{arch}.attention.head_count_kv', 'llama.attention.head_count_kv', default=heads))
    rope     = float(_get(f'{arch}.rope.freq_base', 'llama.rope.freq_base', default=10000))
    ff_size  = int(_get(f'{arch}.feed_forward_length', 'llama.feed_forward_length', default=0))
    vocab    = int(_get(f'{arch}.vocab_size', default=0))

    # Chat template
    tmpl = m.get('tokenizer.chat_template', '')
    tmpl_format = _infer_template_format(tmpl) if tmpl else 'none'

    # Quant info
    quant_ver = m.get('general.quantization_version', '')
    file_type = m.get('general.file_type', '')

    # KV cache estimate using correct GQA formula:
    # seq_len × n_layers × 2 (K+V) × n_kv_heads × head_dim × fp16_bytes
    # Cap estimated context at 8192 — using the model's MAX context (e.g. 128K for Llama 3.1)
    # would massively inflate the estimate; users rarely fill it.
    est_ctx = min(ctx, 8192)
    head_dim = (emb // heads) if heads else 128
    kv_gb = (est_ctx * layers * 2 * (kv_heads or heads or 1) * head_dim * 2) / 1024**3 if layers else 0

    # Vision / multimodal detection
    _VISION_ARCH = {'mllama', 'llava', 'clip', 'internvl', 'cogvlm', 'idefics', 'flamingo',
                    'qwen2_vl', 'qwenvl', 'internvl2', 'minicpmv'}
    _VISION_NAMES = ('llava', 'vision', '-vl', 'vl-', 'moondream', 'bakllava',
                     'minicpm-v', 'cogvlm', 'internvl', 'qwen-vl', 'pixtral', 'phi-3-vision')
    _SELF_CONTAINED_VISION = {'mllama', 'qwen2_vl', 'qwenvl'}  # vision encoder bundled in one file

    is_vision = (
        arch.lower() in _VISION_ARCH
        or any(k.startswith(('clip.', 'vision.', 'mllama.')) for k in m)
        or any(kw in stem.lower() for kw in _VISION_NAMES)
    )
    mmproj_needed = is_vision and arch.lower() not in _SELF_CONTAINED_VISION
    mmproj_path = None
    if mmproj_needed:
        for f in Path(path).parent.glob('*.gguf'):
            if 'mmproj' in f.name.lower():
                mmproj_path = str(f)
                break

    return {
        'path': path,
        'name': m.get('general.name', stem),
        'architecture': arch,
        'context_length': ctx,
        'n_layers': layers,
        'n_heads': heads,
        'n_kv_heads': kv_heads,
        'embedding_size': emb,
        'feed_forward_size': ff_size,
        'vocab_size': vocab,
        'rope_freq_base': rope,
        'file_size_gb': round(gb, 2),
        'estimated_ram_gb': round(gb + max(kv_gb, gb * 0.08), 2),
        'chat_template': tmpl[:500] if tmpl else None,
        'chat_template_format': tmpl_format,
        'quantization': str(quant_ver or file_type or 'unknown'),
        'has_bos': bool(m.get('tokenizer.ggml.add_bos_token', True)),
        'has_eos': bool(m.get('tokenizer.ggml.add_eos_token', True)),
        'is_vision': is_vision,
        'mmproj_needed': mmproj_needed,
        'mmproj_path': mmproj_path,
    }
