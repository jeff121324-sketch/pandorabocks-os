from dataclasses import dataclass
from typing import Optional, Dict


@dataclass(frozen=True)
class WorldContext:
    """
    描述一個「世界」的靜態身分資訊。
    v1.1：允許攜帶描述性 domain / market metadata
    """
    world_id: str                  # 全域唯一識別
    world_type: str                # e.g. pandora, aisop, trading
    owner: str                     # e.g. system, human, org

    # ⬇️ 新增（描述性，不影響 runtime）
    domain: Optional[str] = None   # trading / hospitality / healthcare
    market: Optional[Dict] = None  # {symbol, exchange, asset_type}

    description: Optional[str] = None
    meta: Optional[Dict] = None