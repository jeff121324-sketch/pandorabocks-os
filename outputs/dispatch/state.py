from pathlib import Path
from datetime import datetime, timedelta, timezone
import json

TZ_TW = timezone(timedelta(hours=8))
STATE_DIR = Path(__file__).resolve().parent / "state"
STATE_DIR.mkdir(exist_ok=True)
STATE_FILE = STATE_DIR / "dispatch_state.json"

def _load():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}

def _save(state):
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def has_sent_today():
    state = _load()
    today = datetime.now(TZ_TW).strftime("%Y-%m-%d")
    return state.get("last_sent_date") == today

def mark_sent_today():
    state = _load()
    today = datetime.now(TZ_TW).strftime("%Y-%m-%d")
    state["last_sent_date"] = today
    state["last_sent_at"] = datetime.now(TZ_TW).isoformat()
    _save(state)
