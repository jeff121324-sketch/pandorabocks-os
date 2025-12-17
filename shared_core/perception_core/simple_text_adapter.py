# shared_core/perception_core/simple_text_adapter.py

from typing import Optional, Dict, Any
from pandora_core.event_bus import EventBus
from shared_core.pb_lang.pb_event_validator import PBEventValidator
import re
import time
from shared_core.event_schema import PBEvent


class SimpleTextInputAdapter:
    """
    SimpleTextInputAdapter v1
    -------------------------
    將任意文字 → 轉成 PBEvent(text.input)

    pipeline:
        1) filter        - 移除空字串、惡意輸入
        2) auto_fix      - 修復破損格式、strip
        3) anti_poison   - prompt injection/攻擊文字偵測
        4) enrich        - 增加 timestamp, source
        5) make_event    - 統一產生 PBEvent
    """

    def __init__(self, validator: Optional[PBEventValidator] = None):
        self.validator = validator or PBEventValidator(strict=False, soft=True)

    # --------------------------------------------------
    # 1) filter
    # --------------------------------------------------
    def filter(self, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        txt = raw.get("text", "")
        if not isinstance(txt, str):
            return None
        if txt.strip() == "":
            return None
        return raw

    # --------------------------------------------------
    # 2) auto_fix
    # --------------------------------------------------
    def auto_fix(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        raw["text"] = raw["text"].strip()
        return raw

    # --------------------------------------------------
    # 3) anti_poison
    # --------------------------------------------------
    def anti_poison(self, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        txt = raw["text"]

        # 最基本的攻擊詞偵測（可以之後擴充）
        block = [
            r"DROP TABLE", r"SELECT \*", r"system\(",
            r"hack", r"malware", r"rm -rf",
        ]
        for bad in block:
            if re.search(bad, txt, flags=re.IGNORECASE):
                return None

        return raw

    # --------------------------------------------------
    # 4) enrich（timestamp + source）
    # --------------------------------------------------
    def enrich(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        raw["timestamp"] = raw.get("timestamp") or time.time()
        raw["source"] = raw.get("source", "text.input")
        return raw

    # --------------------------------------------------
    # 5) make_event 產生 PBEvent
    # --------------------------------------------------
    def make_event(self, raw: Dict[str, Any]) -> PBEvent:
        """
        把文字 raw 轉成 PBEvent（不加 meta，因為 PBEvent 自己會生成）
        """
        payload = {"text": raw["text"]}

        return PBEvent(
            type="text.input",
            source="text.input",
            payload=payload,
        )

    # --------------------------------------------------
    # * Main entry *
    # 完整管線
    # --------------------------------------------------
    def to_event(self, raw: Dict[str, Any]) -> Optional[PBEvent]:
        raw = self.filter(raw)
        if raw is None:
            return None

        raw = self.auto_fix(raw)
        raw = self.anti_poison(raw)
        if raw is None:
            return None

        raw = self.enrich(raw)

        event = self.make_event(raw)

        return self.validator.validate(event, soft=True)
