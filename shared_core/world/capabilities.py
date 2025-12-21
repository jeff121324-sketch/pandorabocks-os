from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class WorldCapabilities:
    """
    描述一個世界「理論上支援哪些能力」
    v0：純宣告，不等於已啟用
    """
    world_id: str
    supports_hotplug: bool = False
    supports_multi_runtime: bool = False
    supports_external_tick: bool = False
