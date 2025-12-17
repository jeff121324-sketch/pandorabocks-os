# shared_core/foundation/event_bus.py
"""
⚠ Deprecated Module (Legacy EventBus)

這是 AISOP v0.5 / 舊版工具使用的事件匯流排，
已被 Pandora Core EventBus 取代。

禁止 TradingRuntime / TradingBridge 使用這個模組。
只允許舊版 AISOP perception/core 引用。
"""
from __future__ import annotations

import fnmatch
from threading import RLock
from typing import Callable, Dict, List, Optional

from shared_core.event_schema import PBEvent


EventHandler = Callable[[PBEvent], None]


class EventBus:
    """
    🌐 EventBus v1 — 文明級外部事件神經系統（完整版骨架）
    
    目標（v1）：
    - thread-safe
    - wildcard routing (market.* / ai.* / system.* / *)
    - 多訂閱者
    - 不會阻塞 PB-Lang event flow
    - 留好 v2 插槽（priority / filter-chain）
    """

    def __init__(self):
        # key = pattern: str (e.g. "market.*", "ai.signal")
        # value = list of handlers
        self._subscribers: Dict[str, List[EventHandler]] = {}

        # v2 預留：priority handler queues
        self._priority_handlers: Dict[int, List[EventHandler]] = {}

        # v2 預留：filter chain
        self._filters: List[Callable[[PBEvent], Optional[PBEvent]]] = []

        self._lock = RLock()

    # ============================================================
    # v1: 訂閱 / 取消訂閱
    # ============================================================

    def subscribe(self, pattern: str, handler: EventHandler) -> None:
        """
        例：
        subscribe("market.kline", on_kline)
        subscribe("market.*", on_market)
        subscribe("*", on_everything)
        """
        with self._lock:
            handlers = self._subscribers.setdefault(pattern, [])
            if handler not in handlers:
                handlers.append(handler)

    def unsubscribe(self, pattern: str, handler: EventHandler) -> None:
        with self._lock:
            handlers = self._subscribers.get(pattern, [])
            if handler in handlers:
                handlers.remove(handler)
            if not handlers and pattern in self._subscribers:
                del self._subscribers[pattern]

    # ============================================================
    # v1: 發布事件（骨架）
    # ============================================================

    def publish(self, event: PBEvent) -> None:
        """
        發布 PBEvent 到所有符合 pattern 的 handler。
        """

        # --------------------------------------------------------
        # v2 插槽：filter-chain（目前不啟動，只預留）
        # --------------------------------------------------------
        filtered_event = event
        for f in self._filters:
            filtered_event = f(filtered_event)
            if filtered_event is None:
                # event 被 filter 丟掉
                return

        event = filtered_event

        # --------------------------------------------------------
        # v1 核心：wildcard routing
        # --------------------------------------------------------
        with self._lock:
            subscribers_snapshot = list(self._subscribers.items())

        for pattern, handlers in subscribers_snapshot:
            if fnmatch.fnmatch(event.type, pattern):
                for handler in handlers:
                    try:
                        handler(event)
                    except Exception as e:
                        # v1: 先簡單 console 錯誤（之後交給 PBsystem.error）
                        print(f"[EventBus] handler error for pattern={pattern}: {e}")

    # ============================================================
    # v2: 預留 API（未啟用，但骨架已固定）
    # ============================================================

    def add_filter(self, f: Callable[[PBEvent], Optional[PBEvent]]) -> None:
        """之後用於毒資料清洗、PB-Lang validator"""
        with self._lock:
            self._filters.append(f)

    def add_priority_handler(self, priority: int, handler: EventHandler) -> None:
        """預留未來 AI 決策優先權、RTS routing 用"""
        with self._lock:
            self._priority_handlers.setdefault(priority, []).append(handler)

