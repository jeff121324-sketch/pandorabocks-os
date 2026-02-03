# trading_core/data/raw_loader.py

import json
from pathlib import Path

RAW_DIR = Path("trading_core/data/raw")

def load_latest_kline():
    files = sorted(RAW_DIR.glob("*.jsonl"))
    if not files:
        return None

    latest = files[-1]
    with open(latest, "r", encoding="utf-8") as f:
        last_line = f.readlines()[-1]

    return json.loads(last_line)
