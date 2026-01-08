# outputs/dispatch/health.py

from datetime import datetime, timedelta, timezone

from .state import has_sent_today
from outputs.dispatch.channels.discord import send_status_message
from outputs.dispatch.owner_notify import notify_owner_error

TZ_TW = timezone(timedelta(hours=8))

# 簡單 cooldown，避免洗版
_last_sent = {}

COOLDOWN_SECONDS = 60 * 10  # 10 分鐘


def dispatch_health_warning(event):
    """
    Handle world.health.warning
    - 有 cooldown
    - 不吵人
    """
    payload = event 

    reason = payload.get("reason", "unknown")
    interval = payload.get("interval", "N/A")
    world_id = payload.get("world_id", "unknown")

    key = f"{world_id}:{reason}:{interval}"
    now = datetime.now(TZ_TW).timestamp()

    last = _last_warning_sent.get(key)
    if last and now - last < COOLDOWN_SECONDS:
        return  # ⛔ 冷卻中，直接吞掉

    _last_warning_sent[key] = now

    msg = (
        "⚠️ **AISOP 世界健康警告**\n\n"
        f"**世界**：{world_id}\n"
        f"**原因**：{reason}\n"
        f"**週期**：{interval}\n"
        f"**時間**：{datetime.now(TZ_TW).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        "狀態：系統尚可運作，但存在風險。\n"
        "請留意資料完整性與外部服務狀態。"
    )

    send_status_message(msg)

def dispatch_health_error(event):
    """
    Handle world.health.error
    - ❌ 無 cooldown
    - 🚨 一定通知
    - 🔔 可升級通知 owner
    """
    payload = event 

    world_id = payload.get("world_id", "unknown")
    reason = payload.get("reason", "unknown")
    detail = payload.get("detail", "")

    msg = (
        "🚨 **AISOP 世界嚴重錯誤（ERROR）**\n\n"
        f"**世界**：{world_id}\n"
        f"**原因**：{reason}\n"
        f"**細節**：{detail}\n"
        f"**時間**：{datetime.now(TZ_TW).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        "⚠️ 系統已標記為異常狀態。\n"
        "建議立即檢查並評估是否需要 Freeze 該世界。"
    )

    # 1️⃣ 一定送 status（這是你現在看到的 #status）
    send_status_message(msg)

    # 2️⃣ 如果你要「真的吵你」，走 owner notify
    notify_owner_error(
        title="AISOP World Health ERROR",
        detail=msg
    )
