from datetime import datetime
from pathlib import Path
import json


class DailyReportWriter:
    """
    Write one daily decision report per run.
    """

    def __init__(self, base_dir="outputs/reports"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def send(self, payload: dict):
        date = datetime.utcnow().strftime("%Y-%m-%d")
        path = self.base_dir / f"daily_report_{date}.json"

        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
