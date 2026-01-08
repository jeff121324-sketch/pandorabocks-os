from datetime import datetime, timedelta, timezone
from pathlib import Path

from outputs.dispatch.channels.discord import send_report_message
from outputs.dispatch.dispatch_log import log_dispatch
from outputs.dispatch.state import has_sent_today, mark_sent_today
from outputs.dispatch.formatter.zh_TW import format_daily_report_zh

TZ_TW = timezone(timedelta(hours=8))
BASE_DIR = Path(__file__).resolve().parents[2]
REPORT_DIR = BASE_DIR / "reports" / "daily"


def send_daily_report(date: str):
    """
    正常每日報表發送（不處理 error escalation）
    """
    report_file = REPORT_DIR / f"daily_report_{date}.json"

    if not report_file.exists():
        raise FileNotFoundError(f"Daily report not found: {report_file}")

    message = format_daily_report_zh(report_file)
    send_report_message(message, scope="daily")

    log_dispatch("daily", date, "discord", "success")
    mark_sent_today()
# ========= WEEKLY =========

def send_weekly_report(week: str):
    path = REPORT_DIR / "weekly" / f"weekly_report_{week}.json"
    if not path.exists():
        raise FileNotFoundError(path)
    
    msg = f"📘【週報】\n週期：{week}"
    send_report_message(msg, scope="insight")
    log_dispatch("weekly", week, "discord", "success")


# ========= MONTHLY =========

def send_monthly_report(month: str):
    path = REPORT_DIR / "monthly" / f"monthly_report_{month}.json"
    if not path.exists():
        raise FileNotFoundError(path)

    msg = f"📕【月報】\n月份：{month}"
    send_report_message(msg, scope="insight")
    log_dispatch("monthly", month, "discord", "success")