from typing import Optional
from datetime import datetime, timezone
import re

from .time_utils import parse_iso

FILENAME_TS_PATTERN = re.compile(r"decision_(\d{8})_(\d{6})")

def extract_event_time(
    data: dict,
    *,
    filename: Optional[str] = None
) -> Optional[datetime]:
    """
    Extract event time from various schema forms.
    Always return timezone-aware UTC datetime.
    """

    # 1️⃣ filename fallback (legacy / guaranteed)
    if filename:
        m = FILENAME_TS_PATTERN.search(filename)
        if m:
            date_part, time_part = m.groups()
            iso = (
                f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
                f"T{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}+00:00"
            )
            return parse_iso(iso)

    # 2️⃣ data["timestamp"]
    ts = data.get("timestamp")
    if isinstance(ts, str):
        return parse_iso(ts)

    # 3️⃣ data["meta"]["timestamp"]
    meta = data.get("meta")
    if isinstance(meta, dict) and isinstance(meta.get("timestamp"), str):
        return parse_iso(meta["timestamp"])

    # 4️⃣ data["payload"]["meta"]["timestamp"]
    payload = data.get("payload")
    if isinstance(payload, dict):
        meta2 = payload.get("meta")
        if isinstance(meta2, dict) and isinstance(meta2.get("timestamp"), str):
            return parse_iso(meta2["timestamp"])

    return None