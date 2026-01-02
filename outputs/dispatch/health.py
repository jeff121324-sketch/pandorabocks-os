# outputs/dispatch/health.py

from .state import has_sent_today

def dispatch_daily_health():
    """
    Dispatch Daily 履約健康狀態
    """
    return {
        "sent_today": has_sent_today()
    }