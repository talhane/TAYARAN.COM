"""Local account system for Engineering Academy.
Passwords are PBKDF2-hashed; raw passwords are never stored or displayed.
"""
from __future__ import annotations
import hashlib, hmac, json, os, secrets, tempfile
from datetime import datetime, timezone
from pathlib import Path


def data_dir():
    p = Path(os.environ.get('EA_DATA_DIR', Path(__file__).resolve().parents[1] / 'data'))
    p.mkdir(parents=True, exist_ok=True)
    return p

def accounts_path(): return data_dir() / 'accounts.json'

def _read():
    p = accounts_path()
    if not p.exists(): return {}
    try:
        obj = json.loads(p.read_text(encoding='utf-8'))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}

def _write(accounts):
    p = accounts_path(); fd, tmp = tempfile.mkstemp(prefix='.accounts-', suffix='.tmp', dir=str(p.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(accounts, f, ensure_ascii=False, indent=2); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp): os.remove(tmp)

def normalize_email(email): return (email or '').strip().lower()
def password_ok(password): return isinstance(password, str) and len(password) >= 10 and any(c.isalpha() for c in password) and any(c.isdigit() for c in password)
def _hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), 310_000).hex()
    return {'salt': salt, 'password_hash': digest}
def _verify(password, record):
    try: return hmac.compare_digest(_hash(password, record['salt'])['password_hash'], record['password_hash'])
    except Exception: return False

def account_exists(email): return normalize_email(email) in _read()
def register(email, password, display_name, rules_accepted=False):
    email = normalize_email(email); accounts = _read()
    if '@' not in email or '.' not in email.split('@')[-1]: return False, 'Inserisci un indirizzo email valido.'
    if email in accounts: return False, 'Esiste già un account con questa email.'
    if not password_ok(password): return False, 'La password deve avere almeno 10 caratteri, una lettera e un numero.'
    if not rules_accepted: return False, 'Devi accettare le regole e l’informativa privacy.'
    role = 'admin' if not accounts else 'student'
    record = {'email': email, 'display_name': (display_name or email.split('@')[0]).strip()[:80], 'role': role,
              **_hash(password), 'created_at': datetime.now(timezone.utc).isoformat(), 'last_login': None,
              'rules_accepted': True, 'consents': {'study_progress': True, 'uploaded_files': False, 'location': False, 'device_sharing': False},
              'consent_updated_at': datetime.now(timezone.utc).isoformat(), 'disabled': False}
    accounts[email] = record; _write(accounts)
    return True, role

def authenticate(email, password):
    email = normalize_email(email); accounts = _read(); record = accounts.get(email)
    if not record or record.get('disabled') or not _verify(password, record): return None
    record['last_login'] = datetime.now(timezone.utc).isoformat(); accounts[email] = record; _write(accounts)
    return {'email': email, 'display_name': record.get('display_name', email), 'role': record.get('role', 'student')}

def change_password(email, old_password, new_password):
    accounts = _read(); record = accounts.get(normalize_email(email))
    if not record or not _verify(old_password, record): return False, 'La password attuale non è corretta.'
    if not password_ok(new_password): return False, 'La nuova password deve avere almeno 10 caratteri, una lettera e un numero.'
    record.update(_hash(new_password)); record['password_changed_at'] = datetime.now(timezone.utc).isoformat(); accounts[email] = record; _write(accounts)
    return True, 'Password aggiornata.'

def update_consents(email, consents):
    accounts = _read(); key = normalize_email(email)
    if key not in accounts: return
    allowed = {'study_progress', 'uploaded_files', 'location', 'device_sharing'}
    old = accounts[key].get('consents', {})
    for name in allowed: old[name] = bool(consents.get(name, False))
    accounts[key]['consents'] = old; accounts[key]['consent_updated_at'] = datetime.now(timezone.utc).isoformat(); _write(accounts)

def list_accounts():
    result=[]
    for email, record in _read().items():
        result.append({k: record.get(k) for k in ('email','display_name','role','created_at','last_login','rules_accepted','consents','consent_updated_at','disabled')})
    return sorted(result, key=lambda r: (r.get('role') != 'admin', r.get('email') or ''))

def set_disabled(email, disabled):
    accounts = _read(); key=normalize_email(email)
    if key in accounts and accounts[key].get('role') != 'admin':
        accounts[key]['disabled'] = bool(disabled); _write(accounts)

def account_record(email): return _read().get(normalize_email(email), {})

def user_key(email): return hashlib.sha256(normalize_email(email).encode('utf-8')).hexdigest()[:24]
