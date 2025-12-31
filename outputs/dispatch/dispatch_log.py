from datetime import datetime
from pathlib import Path
import json

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "dispatch.jsonl"

def log_dispatch(report_type, date, channel, status):
    record = {
        "report_type": report_type,
        "date": date,
        "channel": channel,
        "status": status,
        "timestamp": datetime.utcnow().isoformat()
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
