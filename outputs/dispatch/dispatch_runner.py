from pathlib import Path
from datetime import datetime, timedelta, timezone

from .formatter.zh_TW import format_daily_report_zh
from .channels.discord import send_report_message
from .dispatch_log import log_dispatch
from .startup_notify import notify_startup_ok
from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()

# ==================================================
# 基本路徑設定
# ==================================================
BASE_DIR = Path(__file__).resolve().parents[1]
REPORT_DIR = BASE_DIR / "reports" / "daily"

# ==================================================
# 時區
# ==================================================
TZ_TW = timezone(timedelta(hours=8))

# ==================================================
# 狀態鎖（一天只送一次）
# ==================================================
STATE_DIR = Path(__file__).resolve().parent / "state"
STATE_DIR.mkdir(exist_ok=True)
STATE_FILE = STATE_DIR / "dispatch_state.json"

def _load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}

def _save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def has_sent_today():
    state = _load_state()
    today = datetime.now(TZ_TW).strftime("%Y-%m-%d")
    return state.get("last_sent_date") == today

def mark_sent_today():
    state = _load_state()
    today = datetime.now(TZ_TW).strftime("%Y-%m-%d")
    state["last_sent_date"] = today
    state["last_sent_at"] = datetime.now(TZ_TW).isoformat()
    _save_state(state)

# ==================================================
# Owner 錯誤通知（只在真的失敗）
# ==================================================
OWNER_WEBHOOK = os.getenv("DC_GENERAL_WEBHOOK", "").strip()

def notify_owner_error(title: str, detail: str):
    if not OWNER_WEBHOOK:
        return

    msg = (
        "🚨【發送失敗｜需要人工介入】\n"
        f"時間：{datetime.now(TZ_TW).strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"項目：{title}\n"
        f"說明：{detail}"
    )

    try:
        requests.post(
            OWNER_WEBHOOK,
            json={"content": msg[:1900]},
            timeout=10
        )
    except Exception:
        pass

# ==================================================
# 核心發送邏輯（daily only）
# ==================================================
def dispatch_daily(date_str: str):
    report_file = REPORT_DIR / f"daily_report_{date_str}.json"

    if not report_file.exists():
        raise FileNotFoundError(f"Daily report not found: {report_file}")

    try:
        message = format_daily_report_zh(report_file)
        send_report_message(message)
        log_dispatch("daily", date_str, "discord", "success")
        mark_sent_today()

    except Exception as e:
        log_dispatch("daily", date_str, "discord", f"failed: {e}")
        notify_owner_error(
            title=f"Daily Report {date_str}",
            detail=str(e)
        )
        raise

# ==================================================
# 取得最新 daily report（忽略 decision）
# ==================================================
def get_latest_daily_date():
    files = list(REPORT_DIR.glob("daily_report_*.json"))
    if not files:
        raise RuntimeError("No daily_report found in outputs/reports/daily")

    latest = sorted(files)[-1]
    return latest.stem.replace("daily_report_", "")

# ==================================================
# 排程入口（09:00 or 補送）
# ==================================================
def dispatch_check_once():
    """
    單次檢查：
    - 已過 09:00
    - 今天尚未送
    就送 daily report
    """
    now = datetime.now(TZ_TW)
    today = now.strftime("%Y-%m-%d")

    if now.hour >= 9 and not has_sent_today():
        report_file = REPORT_DIR / f"daily_report_{today}.json"
        if not report_file.exists():
            raise RuntimeError(f"Today's daily report not generated yet: {today}")

        dispatch_daily(today)

# ==================================================
# Attach dispatch system to EventBus (OS-level)
# ==================================================
def attach_dispatch(bus):
    from outputs.dispatch.health import dispatch_health_warning
    from outputs.dispatch.owner_notify import notify_owner_error
    from outputs.dispatch.startup_notify import on_startup_event
    from outputs.dispatch.health import dispatch_health_warning, dispatch_health_error

    # World health → Discord #status
    bus.subscribe(
        "world.health.warning",
        dispatch_health_warning
    )

    bus.subscribe("world.health.error", dispatch_health_error)

    # System startup → Discord
    bus.subscribe(
        "system.startup",
        on_startup_event
    )

    # Owner critical notify（如果你有）
    bus.subscribe(
        "owner.notify",
        notify_owner_error
    )

    print("[Dispatch] 📣 Dispatch system attached")

