from datetime import datetime, timedelta, timezone

from outputs.dispatch.report_sender import (
    send_weekly_report,
    send_monthly_report,
)

TZ_TW = timezone(timedelta(hours=8))


def check_weekly_closure():
    now = datetime.now(TZ_TW)

    # 週一 00:00 → 送「上週」
    if now.weekday() == 0 and now.hour == 0:
        last_week = (now - timedelta(days=7)).strftime("%Y-W%U")
        send_weekly_report(last_week)


def check_monthly_closure():
    now = datetime.now(TZ_TW)

    # 每月 1 號 00:00 → 送「上個月」
    if now.day == 1 and now.hour == 0:
        last_month = (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        send_monthly_report(last_month)
