import time
from datetime import datetime, timedelta, timezone
from .dispatch_runner import dispatch_daily
from outputs.dispatch.report_closure_manager import (
    check_weekly_closure,
    check_monthly_closure,
)

TZ_TW = timezone(timedelta(hours=8))

def run_daily_scheduler():
    triggered = False

    while True:
        now = datetime.now(TZ_TW)

        if now.hour == 9 and not triggered:
            date_str = now.strftime("%Y-%m-%d")
            dispatch_daily(date_str)
            triggered = True

        if now.hour != 9:
            triggered = False

            check_weekly_closure()
            check_monthly_closure()
            time.sleep(30)

if __name__ == "__main__":
    run_daily_scheduler()
