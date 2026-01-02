from datetime import datetime, timedelta, timezone
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TZ_TW = timezone(timedelta(hours=8))
OWNER_WEBHOOK = os.getenv("DC_GENERAL_WEBHOOK", "").strip()


def notify_startup_ok():
    if not OWNER_WEBHOOK:
        return

    msg = (
        "🟢【Dispatch 啟動完成】\n"
        f"時間：{datetime.now(TZ_TW).strftime('%Y-%m-%d %H:%M:%S')}\n"
        "模組：Daily Report Dispatcher\n"
        "時區：Asia/Taipei\n"
        "狀態：Healthy"
    )

    try:
        requests.post(
            OWNER_WEBHOOK,
            json={"content": msg[:1900]},
            timeout=10
        )
    except Exception:
        pass


def notify_startup_error(err: Exception):
    if not OWNER_WEBHOOK:
        return

    msg = (
        "🚨【Dispatch 啟動失敗｜需要介入】\n"
        f"時間：{datetime.now(TZ_TW).strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"錯誤：{type(err).__name__}\n"
        f"說明：{str(err)}"
    )

    try:
        requests.post(
            OWNER_WEBHOOK,
            json={"content": msg[:1900]},
            timeout=10
        )
    except Exception:
        pass
