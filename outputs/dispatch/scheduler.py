import time
from datetime import datetime, timedelta, timezone
from .dispatch_runner import dispatch_daily

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

        time.sleep(30)

if __name__ == "__main__":
    run_daily_scheduler()
