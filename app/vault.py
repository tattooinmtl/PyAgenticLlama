"""
Secure vault using Fernet (AES-128-CBC + HMAC) with a key derived from machine identity.
Keys are never stored on disk — derived at runtime from COMPUTERNAME + USERNAME.
"""
import json, os, base64, hashlib
from pathlib import Path
from cryptography.fernet import Fernet

VAULT_PATH = Path(__file__).parent.parent / 'data' / 'vault.enc'
VAULT_PATH.parent.mkdir(exist_ok=True)

def _derive_key() -> bytes:
    identity = f"{os.environ.get('COMPUTERNAME','PC')}{os.environ.get('USERNAME','user')}localai-v1"
    raw = hashlib.pbkdf2_hmac('sha256', identity.encode(), b'localai-salt-2024', 200_000, dklen=32)
    return base64.urlsafe_b64encode(raw)

def _fernet() -> Fernet:
    return Fernet(_derive_key())

def load_vault() -> dict:
    if not VAULT_PATH.exists():
        return {}
    try:
        return json.loads(_fernet().decrypt(VAULT_PATH.read_bytes()))
    except Exception:
        return {}

def _save_vault(data: dict):
    VAULT_PATH.write_bytes(_fernet().encrypt(json.dumps(data).encode()))

def set_secret(key: str, value: str):
    d = load_vault()
    d[key] = value
    _save_vault(d)

def get_secret(key: str, default: str = '') -> str:
    return load_vault().get(key, default)

def delete_secret(key: str):
    d = load_vault()
    d.pop(key, None)
    _save_vault(d)

def list_keys() -> list[str]:
    return list(load_vault().keys())

def set_env_from_vault():
    for k, v in load_vault().items():
        if not k.startswith('_') and k == k.upper():
            os.environ.setdefault(k, v)
