# replay_runtime/reader.py
import json
from pathlib import Path

class RawMarketReader:
    def __init__(self, base_dir):
        self.base = Path(base_dir)

    def iter_records(self, symbol, interval, date):
        file = self.base / symbol / interval / f"{date}.jsonl"
        if not file.exists():
            return

        with file.open("r", encoding="utf-8") as f:
            for line in f:
                yield json.loads(line)
