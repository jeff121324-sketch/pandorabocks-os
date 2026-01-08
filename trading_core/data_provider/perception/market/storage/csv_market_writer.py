import csv
import os
from pathlib import Path
from datetime import datetime


class MarketCSVWriter:
    def __init__(self, root="data/market_csv"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def write(self, records: list[dict]):
        print("[CSV] write called", len(records))
        if not records:
            return

        r0 = records[0]
        symbol = r0["symbol"].replace("/", "_")
        interval = r0["interval"]

        filename = f"{symbol}_{interval}.csv"
        path = self.root / filename

        write_header = not path.exists()

        with path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=records[0].keys()
            )

            if write_header:
                writer.writeheader()

            for r in records:
                writer.writerow(r)
