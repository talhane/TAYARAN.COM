import json, os, shutil, tempfile
from pathlib import Path
from datetime import date, datetime, time

def data_dir():
    p=Path(os.environ.get('EA_DATA_DIR', Path(__file__).resolve().parents[1]/'data')); p.mkdir(parents=True,exist_ok=True); return p

def progress_path(user_id=None):
    # Separate progress files keep each student's study records private.
    if user_id:
        import hashlib
        key = hashlib.sha256(str(user_id).strip().lower().encode('utf-8')).hexdigest()[:24]
        return data_dir()/f'progress-{key}.json'
    return data_dir()/'progress.json'
def defaults(): return {'completed_lessons':[],'exercise_results':{},'exam_history':[],'settings':{},'projects':[]}
def load_progress(user_id=None):
    p=progress_path(user_id)
    if not p.exists(): return defaults()
    try:
        with p.open(encoding='utf-8') as f: data=json.load(f)
        d=defaults(); d.update(data if isinstance(data,dict) else {}); return d
    except Exception:
        try: shutil.copy2(p,p.with_name('progress.corrupt-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.json'))
        except Exception: pass
        return defaults()
def _json_default(value):
    """Convert common Python date/time values to portable JSON strings."""
    if isinstance(value, (date, datetime, time)):
        return value.isoformat()
    # Support NumPy scalar values without making NumPy a storage dependency.
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")

def save_progress(data, user_id=None):
    p=progress_path(user_id); p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.progress-',suffix='.tmp',dir=str(p.parent))
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2,default=_json_default); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp): os.remove(tmp)
def export_progress(data): return json.dumps(data,ensure_ascii=False,indent=2,default=_json_default).encode('utf-8')
