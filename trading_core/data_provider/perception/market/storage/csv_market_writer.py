import csv
import os
from pathlib import Path
from datetime import datetime

# ======================================================
# 🔒 Final canonical market CSV schema（必須在這裡定義）
# ======================================================
MARKET_CSV_FIELDS = [
    "source",
    "market",
    "symbol",
    "interval",
    "kline_open_ts",
    "kline_close_ts",
    "fetch_ts",
    "human_open_time",
    "human_open_time_local",
    "open",
    "high",
    "low",
    "close",
    "volume",
]

class MarketCSVWriter:
    def __init__(self, root="data/market_csv"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def write(self, records: list[dict], *, symbol: str, interval: str):
        print("[CSV] write called", len(records))
        if not records:
            return

        if not symbol or not interval:
            raise ValueError(
                "MarketCSVWriter.write requires explicit symbol and interval"
            )

        symbol_safe = symbol.replace("/", "_")
        filename = f"{symbol_safe}_{interval}.csv"
        path = self.root / filename

        write_header = not path.exists()

        with path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=MARKET_CSV_FIELDS,
                extrasaction="ignore",   # 🔒 關鍵：多的欄位直接丟掉
            )

            if write_header:
                writer.writeheader()

            for r in records:
                # 🔒 缺欄位補 None，避免 writer 崩
                row = {k: r.get(k) for k in MARKET_CSV_FIELDS}
                writer.writerow(row)
