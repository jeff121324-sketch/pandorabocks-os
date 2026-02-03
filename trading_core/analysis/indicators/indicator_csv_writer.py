# trading_core/analysis/indicators/indicator_csv_writer.py
import csv
from pathlib import Path


class IndicatorCSVWriter:
    """
    Archive only.
    Writes indicator.snapshot to CSV.
    """

    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._header_written = False
        self._header_written = self.path.exists()

    def on_indicator_snapshot(self, event):
        payload = event.payload
        if "indicators" not in payload:
            return
        indicators = payload["indicators"]

        # 第一次動態寫 header
        if not self._header_written:
            self._write_header(indicators)

        with self.path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    payload.get("timestamp"),
                    payload.get("symbol"),
                    payload.get("interval"),
                ]
                + [indicators.get(k) for k in self._indicator_keys]
            )

    def _write_header(self, indicators: dict):
        self._indicator_keys = sorted(indicators.keys())

        with self.path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["timestamp", "symbol", "interval"] + self._indicator_keys
            )

        self._header_written = True
