# shared_core/foundation/json_utils.py
import json
from datetime import datetime
from pathlib import Path
from decimal import Decimal

def _default_encoder(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, Decimal):
        return float(obj)
    return str(obj)

def safe_json_dump(data, *, ensure_ascii=False, indent=None) -> str:
    """
    Deterministic JSON dump with safe fallback encoder.
    Never raises TypeError due to unknown objects.
    """
    return json.dumps(
        data,
        default=_default_encoder,
        ensure_ascii=ensure_ascii,
        indent=indent,
    )

def safe_json_load(text: str):
    """
    Safe JSON load. Raises ValueError only if JSON is malformed.
    """
    return json.loads(text)
