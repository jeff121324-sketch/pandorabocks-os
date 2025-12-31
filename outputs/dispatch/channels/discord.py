import os
import requests
from dotenv import load_dotenv

load_dotenv()
WEBHOOK = os.getenv("DC_REPORT_WEBHOOK", "").strip()

def send_discord_message(message: str):
    if not WEBHOOK:
        raise RuntimeError("DC_REPORT_WEBHOOK not set")

    payload = {
        "content": message[:1900]  # Discord safety limit
    }

    r = requests.post(WEBHOOK, json=payload, timeout=10)
    if r.status_code not in (200, 204):
        raise RuntimeError(f"Discord send failed: {r.status_code} {r.text}")
