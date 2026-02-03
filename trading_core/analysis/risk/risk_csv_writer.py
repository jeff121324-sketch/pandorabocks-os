# trading_core/analysis/risk/risk_csv_writer.py
import csv
from pathlib import Path


class RiskCSVWriter:
    """
    Archive only.
    Deterministic & replayable.
    """

    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_file()

    def _init_file(self):
        if not self.path.exists():
            with self.path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "symbol",
                    "interval",
                    "price",
                    "composite_risk",
                    "rsi_pressure",
                    "atr_pressure",
                    "volatility_pressure",
                    "liquidity_pressure",
                    "structure_tension",
                    "structure_directionality",
                ])

    def on_risk_snapshot(self, event):
        payload = event.payload
        r = payload["risk"]

        with self.path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                payload.get("timestamp"),
                payload["symbol"],
                payload["interval"],
                r.get("price"),
                r.get("composite_risk"),
                r.get("rsi_pressure"),
                r.get("atr_pressure"),
                r.get("volatility_pressure"),
                r.get("liquidity_pressure"),
                r.get("structure_tension"),
                r.get("structure_directionality"),
            ])

