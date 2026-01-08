# shared_core/world/world_state.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Iterable, Any
from datetime import datetime

from shared_core.event_schema import PBEvent


@dataclass
class WorldStateConfig:
    """
    WorldState 行為設定（v1 極薄）
    """
    enable_persistence: bool = True
    enable_debug_log: bool = False


class WorldState:
    """
    WorldState v1
    ----------------
    世界級狀態容器（append-only）

    職責：
    - 接收世界中發生的事件（通常來自 Perception）
    - 將事件正式承認為「世界經驗」
    - 委派給既有 writer / storage / log system

    嚴格不做：
    - 不推論
    - 不決策
    - 不計算
    """

    def __init__(
        self,
        world_id: str,
        writer: Any,
        config: Optional[WorldStateConfig] = None,
    ):
        self.world_id = world_id
        self.writer = writer
        self.config = config or WorldStateConfig()

    # =========================================================
    # Core API
    # =========================================================

    def append(self, event: PBEvent) -> None:
        """
        世界正式承認一個事件已經發生
        """
        if not self.config.enable_persistence:
            return

        # 強制補齊世界語意（但不修改原事件語意）
        event.meta.setdefault("world_id", self.world_id)
        event.meta.setdefault("ack_ts", self._now())

        self.writer.write(event)

        if self.config.enable_debug_log:
            print(
                f"[WorldState] 🧠 world={self.world_id} "
                f"ack event={event.type}"
            )

    def append_many(self, events: Iterable[PBEvent]) -> None:
        for e in events:
            self.append(e)

    # =========================================================
    # Utilities
    # =========================================================

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"
