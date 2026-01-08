"""
Decision Fingerprint Utility
----------------------------
- 僅對 decision.core 計算 fingerprint
- 作為一致性驗證、治理快照的基礎工具
"""

import json
import hashlib
from typing import Dict


def fingerprint_core(core: Dict) -> str:
    """
    Generate deterministic fingerprint for decision core.

    Rules:
    - key order independent
    - value stable
    - no randomness
    """

    # 1️⃣ 強制排序 + 緊湊序列化
    payload = json.dumps(
        core,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    # 2️⃣ SHA-256（夠用、可審計、穩定）
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
