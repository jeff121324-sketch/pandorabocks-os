"""
perception_gateway.py
統一感知層入口（Perception Gateway）

設計目標：
1. 任何來源的 raw 資料（dict）都先進來這裡。
2. 透過對應的 Adapter 做：
   - filter        → 黑名單 / 基本欄位 / 數值合法性
   - auto_fix      → 修復 high/low / close 跳動 / volume=0 等
   - anti_poison   → 高頻垃圾 / 重複事件防護
   - enrich        → 補 interval / ts 等「中間語」
   - make_event    → 轉成 PBEvent
3. 最後由 PBEventValidator 做型別與欄位檢查。
4. 可以選擇 soft 模式：驗證失敗就回傳 None（不丟例外），方便壓力測試 / 批次處理。

使用方式（例）：
    from shared_core.perception_core.perception_gateway import PerceptionGateway
    from trading_core.perception.market_adapter import MarketKlineAdapter
    from shared_core.pb_lang.pb_event_validator import PBEventValidator

    validator = PBEventValidator(strict=True)
    gateway = PerceptionGateway(validator=validator)

    adapter = MarketKlineAdapter(mode="realtime", validator=validator)
    gateway.register_adapter("market.kline", adapter)

    raw = {...}  # 一筆來自 Binance 的 K 線 dict
    event = gateway.process("market.kline", raw, soft=False)
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, Optional

from shared_core.event_schema import PBEvent
from shared_core.pb_lang.pb_event_validator import PBEventValidator
from shared_core.perception_core.simple_text_adapter import SimpleTextInputAdapter


class PerceptionGateway:
    """
    通用感知層入口（新版）
    - 不再依賴 adapter.to_event()
    - 改用 PerceptionCore 統一跑 filter / auto_fix / anti_poison / enrich / make_event
    """

    def __init__(
        self,
        core,   # ⭐ 新必填：PerceptionCore
        validator: Optional[PBEventValidator] = None,
        *,
        strict: bool = True,
    ) -> None:
        self.core = core
        self.validator = validator or PBEventValidator(strict=strict)
        self.adapters: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Adapter 管理
    # ------------------------------------------------------------------
    def register_adapter(self, key: str, adapter: Any) -> None:
        self.adapters[key] = adapter

    def get_adapter(self, key: str) -> Any:
        if key not in self.adapters:
            raise KeyError(f"[Gateway] 找不到 adapter: {key}")
        return self.adapters[key]

    # ------------------------------------------------------------------
    # 單筆處理（新版：走 PerceptionCore）
    # ------------------------------------------------------------------
    def process(
        self,
        key: str,
        raw: Dict[str, Any],
        *,
        soft: bool = False,
    ) -> Optional[PBEvent]:

        adapter = self.get_adapter(key)

        # ⭐⭐ 新流程：用 Core 執行完整六階段 pipeline
        event = self.core.run_pipeline(adapter, raw, soft=soft)
        if event is None:
            return None
        # library.event 是歷史事件，不做 domain-level 驗證
        if key == "library.event":
            return event
        # ⭐ Gateway 仍保留最後 PBEventValidator 防線
        return self.validator.validate(event, soft=soft)

    # ------------------------------------------------------------------
    # 批次處理
    # ------------------------------------------------------------------
    def process_many(
        self,
        key: str,
        raws: Iterable[Dict[str, Any]],
        *,
        soft: bool = True,
    ) -> Iterator[PBEvent]:

        for raw in raws:
            ev = self.process(key, raw, soft=soft)
            if ev is not None:
                yield ev

    # ------------------------------------------------------------------
    # Publish 工具
    # ------------------------------------------------------------------
    def process_and_publish(
        self,
        key: str,
        raw: Dict[str, Any],
        bus: Any,
        *,
        topic: Optional[str] = None,
        soft: bool = False,
    ) -> bool:

        event = self.process(key, raw, soft=soft)
        if event is None:
            return False

        bus.publish(event)
        print(f"[EVENT-PUBLISH] type={event.type}")
        return True