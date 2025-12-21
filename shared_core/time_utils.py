# shared_core/time_utils.py

from datetime import datetime, timezone
from typing import Optional


# =============================
# Core UTC Time Providers
# =============================

def utc_now() -> datetime:
    """
    Return timezone-aware UTC datetime.
    This is the ONLY recommended way to get 'now' in the system.
    """
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """
    Return ISO8601 string of current UTC time.
    Example: '2025-12-18T13:04:38.537876+00:00'
    """
    return utc_now().isoformat()


# =============================
# Parsing / Normalization
# =============================

def parse_iso(ts: str) -> datetime:
    """
    Parse ISO8601 string into timezone-aware datetime.
    """
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        # Assume UTC if missing timezone
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def ensure_utc(dt: datetime) -> datetime:
    """
    Ensure a datetime is timezone-aware and in UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


# =============================
# Human Friendly (Optional)
# =============================

def format_human(dt: Optional[datetime] = None) -> str:
    """
    Format datetime into human-readable UTC string.
    Example: '2025-12-18 13:04:38 UTC'
    """
    if dt is None:
        dt = utc_now()
    dt = ensure_utc(dt)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
