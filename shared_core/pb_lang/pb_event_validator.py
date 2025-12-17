# shared_core/pb_lang/pb_event_validator.py

from typing import Any, Dict, Callable, Optional
from shared_core.event_schema import PBEvent


Number = (int, float)


class PBEventValidator:
    """
    PB-Lang v2 事件驗證器：
    - 檢查 PBEvent
    - 支援 soft-drop（批次模式不丟例外）
    """

    def __init__(self, strict: bool = True, soft: bool = False) -> None:
        self.strict = strict
        self.soft = soft
        self.type_validators: Dict[str, Callable[[PBEvent], None]] = {}
        self._register_default_validators() 


    # ------------------------------
    # 公開 API
    # ------------------------------
    def validate(self, event: PBEvent, soft: bool = False) -> PBEvent | None:
        """
        PBEvent 主驗證入口
        soft=True：錯誤不丟 exception → 回傳 None（讓上層丟棄事件）
        soft=False：維持原本行為 → 錯誤直接 raise
        """

        try:
            # 1) 型別檢查
            if not isinstance(event, PBEvent):
                raise TypeError(f"PBEventValidator 只接受 PBEvent，收到 {type(event)}")
    
            # 2) 基本欄位檢查
            if not isinstance(event.type, str) or not event.type.strip():
                raise ValueError("PBEvent.type 必須是非空字串")

            if event.payload is None or not isinstance(event.payload, dict):
                raise ValueError("PBEvent.payload 必須是 dict")

            if not isinstance(event.source, str):
                raise ValueError("PBEvent.source 必須是字串")

            if not isinstance(event.priority, int) or event.priority < 0:
                raise ValueError("PBEvent.priority 必須是非負整數")

            if event.tags is not None and not isinstance(event.tags, list):
                raise ValueError("PBEvent.tags 必須是 list[str] 或 None")

            # 3) 型別專屬 validator（例如 market.kline）
            validator = self.type_validators.get(event.type)
            if validator:
                validator(event)
            elif self.strict:
                # 嚴格模式 → 未註冊的型別拒收
                raise ValueError(f"未註冊的事件型別：{event.type}")

            return event  # 🔥 最終通過

        except Exception as e:
            if soft:
                # ⭐ 軟驗證模式：錯誤時不噴錯 → 直接丟棄事件
                return None
            else:
                # ⭐ 嚴格模式：正常噴錯
                raise
    
    # ------------------------------
    # 內部：註冊預設事件驗證器
    # ------------------------------
    def _register_default_validators(self) -> None:
        self.type_validators["market.kline"] = self._validate_market_kline

        # ⭐ 新增：文字事件型別驗證器
        self.type_validators["text.input"] = self._validate_text_input
    # ------------------------------
    # 各事件型別的細部檢查
    # ------------------------------
    def _validate_market_kline(self, event: PBEvent) -> None:
        """
        market.kline 事件驗證器（v2 強化版）
        - 欄位檢查
        - 型別檢查
        - 數值 sanity check（新版）
        """
        p = event.payload

        # ---------------------------
        # ① 欄位是否存在
        # ---------------------------
        required_keys = ["symbol", "open", "high", "low", "close", "volume", "interval"]
        for key in required_keys:
            if key not in p:
                raise ValueError(f"market.kline 缺少欄位：{key}")

        # ---------------------------
        # ② 基本型別檢查
        # ---------------------------
        if not isinstance(p["symbol"], str):
            raise ValueError("market.kline.symbol 必須是字串")

        numeric_keys = ["open", "high", "low", "close", "volume"]
        for key in numeric_keys:
            if not isinstance(p[key], (int, float)):
                raise ValueError(f"market.kline.{key} 必須是數值")

        if not isinstance(p["interval"], str):
            raise ValueError("market.kline.interval 必須是字串")

        # ---------------------------
        # ③ v2: 數值 sanity check（新增）
        # ---------------------------

        o = p["open"]
        h = p["high"]
        l = p["low"]
        c = p["close"]
        v = p["volume"]

        # 3-1 所有價格必須 >= 0
        for key, val in [("open", o), ("high", h), ("low", l), ("close", c)]:
            if val < 0:
                raise ValueError(f"market.kline.{key} 不能是負數（收到 {val}）")

        # 3-2 high >= low
        if h < l:
            raise ValueError(f"market.kline.high < low（high={h}, low={l}）數據不合理")

        # 3-3 volume >= 0
        if v < 0:
            raise ValueError(f"market.kline.volume 不能是負數（收到 {v}）")

        # ---------------------------
        # optional / extra 欄位（保持 v1）
        # ---------------------------
        if "extra" in p and not isinstance(p["extra"], dict):
            raise ValueError("market.kline.extra 必須是 dict")

        if "meta" in p and not isinstance(p["meta"], dict):
            raise ValueError("market.kline.meta 必須是 dict")
    def _validate_text_input(self, event: PBEvent) -> None:
        """
        text.input 事件驗證器
        - payload 必須是 dict
        - text 必須是非空字串
        """
        p = event.payload

        if not isinstance(p, dict):
            raise ValueError("text.input.payload 必須是 dict")

        if "text" not in p:
            raise ValueError("text.input 缺少欄位：text")

        if not isinstance(p["text"], str) or not p["text"].strip():
            raise ValueError("text.input.text 必須是非空字串")
