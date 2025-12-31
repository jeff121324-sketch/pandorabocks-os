from pathlib import Path
from formatter.zh_TW import format_daily_report_zh
from channels.discord import send_discord_message
from dispatch_log import log_dispatch

BASE_DIR = Path(__file__).resolve().parents[1]
REPORT_DIR = BASE_DIR / "reports" / "daily"

def dispatch_daily(date_str: str):
    """
    Phase 1：
    - 只處理 daily
    - 只處理 zh_TW
    """
    report_file = REPORT_DIR / f"daily_report_{date_str}.json"

    if not report_file.exists():
        raise FileNotFoundError(f"Daily report not found: {report_file}")

    message = format_daily_report_zh(report_file)
    send_discord_message(message)
    log_dispatch("daily", date_str, "discord", "success")

def get_latest_daily_date():
    files = list(REPORT_DIR.glob("daily_report_*.json"))
    if not files:
        raise RuntimeError("No daily_report found in outputs/reports/daily")

    latest = sorted(files)[-1]
    return latest.stem.replace("daily_report_", "")

if __name__ == "__main__":
    date = get_latest_daily_date()
    dispatch_daily(date)
