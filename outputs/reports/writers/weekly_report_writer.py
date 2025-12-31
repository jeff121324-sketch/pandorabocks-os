# aisop/outputs/reports/writers/weekly_report_writer.py
from pathlib import Path
from datetime import datetime
import json


class WeeklyReportWriter:
    def __init__(self, base_dir="outputs/reports/weekly"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def send(self, payload: dict):
        week = datetime.utcnow().strftime("%Y-W%U")
        path = self.base_dir / f"weekly_report_{week}.json"

        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
