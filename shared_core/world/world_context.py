from dataclasses import dataclass
from typing import Optional, Dict


@dataclass(frozen=True)
class WorldContext:
    """
    描述一個「世界」的靜態身分資訊。
    v0：不包含狀態、不包含生命週期、不包含健康判斷
    """
    world_id: str                  # 全域唯一識別
    world_type: str                # e.g. pandora, aisop, trading
    owner: str                     # e.g. system, human, org
    description: Optional[str] = None
    meta: Optional[Dict] = None
