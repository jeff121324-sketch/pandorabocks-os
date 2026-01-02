# trading_core/data/raw_writer.py
import json
import time
from pathlib import Path

class RawMarketWriter:
    """
    Raw Market Writer (append-only)
    """
    def __init__(self, base_dir: str):
        self.base = Path(base_dir)

    def write(self, record: dict):
        # 使用 market_ts 作為世界時間
        ts = record["market_ts"]
        date = time.strftime("%Y-%m-%d", time.gmtime(ts))

        path = (
            self.base
            / "raw"
            / record["source"]
            / record["symbol"]
            / record["interval"]
        )
        path.mkdir(parents=True, exist_ok=True)

        file = path / f"{date}.jsonl"
        with file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
