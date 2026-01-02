import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()
TZ_TW = timezone(timedelta(hours=8))
OWNER_WEBHOOK = os.getenv("DC_GENERAL_WEBHOOK", "").strip()

def notify_owner_error(title: str, detail: str):
    if not OWNER_WEBHOOK:
        return

    msg = (
        "🚨【發送失敗｜需要介入】\n"
        f"時間：{datetime.now(TZ_TW).strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"項目：{title}\n"
        f"說明：{detail}"
    )

    requests.post(OWNER_WEBHOOK, json={"content": msg[:1900]}, timeout=10)
