# trading_core/data_provider/perception/market/runner/live_csv_watcher.py

import time
import csv
from pathlib import Path

class LiveCSVWatcher:
    """
    LiveCSVWatcher v1
    - 監聽 CSV append
    - 轉交給 LiveMarketTickProvider
    """

    def __init__(self, csv_path: Path, provider, *, symbol: str, interval: str):
        self.csv_path = csv_path
        self.provider = provider
        self.symbol = symbol
        self.interval = interval

        self._last_size = 0

    def start(self):
        print(f"[LiveCSVWatcher] 👀 watching {self.csv_path}")

        while True:
            self._poll_once()
            time.sleep(0.5)

    def _poll_once(self):
        if not self.csv_path.exists():
            return

        size = self.csv_path.stat().st_size
        if size <= self._last_size:
            return

        with open(self.csv_path, encoding="utf-8") as f:
            f.seek(self._last_size)

            reader = csv.reader(f)

            # === 1️⃣ 讀 header，建立 index map ===
            header = next(reader, None)
            if not header:
                return

            idx = {name: i for i, name in enumerate(header)}

            required = [
                "kline_open_ts",
                "kline_close_ts",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ]

            if not all(k in idx for k in required):
                return  # ❗ schema 不符，直接拒收

            # === 2️⃣ 讀資料列 ===
            for parts in reader:
                try:
                    open_time_ms  = int(float(parts[idx["kline_open_ts"]]) * 1000)
                    close_time_ms = int(float(parts[idx["kline_close_ts"]]) * 1000)

                    self.provider.emit_kline(
                        symbol=self.symbol,
                        interval=self.interval,
                        open_time_ms=open_time_ms,
                        close_time_ms=close_time_ms,
                        open_price=float(parts[idx["open"]]),
                        high_price=float(parts[idx["high"]]),
                        low_price=float(parts[idx["low"]]),
                        close_price=float(parts[idx["close"]]),
                        volume=float(parts[idx["volume"]]),
                        source="csv_watcher",
                    )

                except Exception:
                    continue

        self._last_size = size
