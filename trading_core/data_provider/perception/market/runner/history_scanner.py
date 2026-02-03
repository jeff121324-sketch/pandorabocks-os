import csv
import os

def scan_last_kline_ts(csv_path: str) -> int | None:
    """
    Scan legacy Binance CSV and return last kline_open_ts (epoch sec).
    """
    if not os.path.exists(csv_path):
        return None

    last_ts = None
    with open(csv_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # 跳過 header
            if "kline_open_ts" in line:
                continue

            parts = line.split(",")
            if len(parts) < 6:
                continue

            try:
                last_ts = int(float(parts[4]))
            except Exception:
                continue

    return last_ts
