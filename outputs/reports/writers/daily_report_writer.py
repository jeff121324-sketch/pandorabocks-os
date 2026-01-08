from datetime import datetime
from pathlib import Path
import json
from datetime import datetime, timedelta, timezone
from outputs.dispatch.report_sender import send_daily_report

TZ_TW = timezone(timedelta(hours=8))

class DailyReportWriter:
    """
    Write one daily decision report per run.
    """

    def __init__(self, base_dir="outputs/reports"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def send(self, payload: dict):
        # 1️⃣ 使用台灣時區，避免跨日錯誤
        date = datetime.now(TZ_TW).strftime("%Y-%m-%d")
        path = self.base_dir / f"daily_report_{date}.json"

        # 2️⃣ 寫入日報（你原本就在做的事）
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

        # 3️⃣ ✅ 寫完日報 → 正式送出報表
        send_daily_report(date)
