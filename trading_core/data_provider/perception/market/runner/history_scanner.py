import csv
import os

def scan_last_kline_ts(csv_path: str) -> int | None:
    """
    Scan CSV and return last kline_open_ts.
    """
    if not os.path.exists(csv_path):
        return None

    last_ts = None
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            last_ts = int(float(row["kline_open_ts"]))

    return last_ts
