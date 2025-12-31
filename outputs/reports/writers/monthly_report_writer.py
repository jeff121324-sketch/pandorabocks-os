# aisop/outputs/reports/writers/monthly_report_writer.py
from pathlib import Path
from datetime import datetime
import json


class MonthlyReportWriter:
    def __init__(self, base_dir="outputs/reports/monthly"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def send(self, payload: dict):
        month = datetime.utcnow().strftime("%Y-%m")
        path = self.base_dir / f"monthly_report_{month}.json"

        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
