# outputs/dispatch/channels/discord.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# === Report channels ===
_DAILY_WEBHOOK = os.getenv("DC_REPORT_WEBHOOK", "").strip()
_INSIGHT_WEBHOOK = os.getenv("DC_REPORT_INSIGHT_WEBHOOK", "").strip()

# === Status channel ===
_STATUS_WEBHOOK = os.getenv("DC_STATUS_WEBHOOK", "").strip()


def send_report_message(message: str, *, scope: str):
    """
    Send report message to Discord.

    scope:
        - daily      -> #report
        - insight    -> #report-insight
    """
    if scope == "daily":
        webhook = _DAILY_WEBHOOK
    elif scope == "insight":
        webhook = _INSIGHT_WEBHOOK or _DAILY_WEBHOOK
    else:
        raise ValueError(f"Unknown report scope: {scope}")

    if not webhook:
        raise RuntimeError(f"Webhook not set for scope: {scope}")

    requests.post(
        webhook,
        json={"content": message[:1900]},
        timeout=10,
    )


def send_status_message(message: str):
    if not _STATUS_WEBHOOK:
        return

    requests.post(
        _STATUS_WEBHOOK,
        json={"content": message[:1900]},
        timeout=5,
    )
