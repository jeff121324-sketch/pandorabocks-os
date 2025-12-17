# shared_core/perception_core/pipeline_core.py
from typing import Dict, Any, Optional
import time


class PerceptionPipelineCore:
    """
    共同感知核心（所有 Adapter 共用）
    ----------------------------------------------------
    功能：
        1) filter
        2) auto_fix
        3) anti_poison
        4) enrich
        5) make_event（由子類別實作）
        6) validator.validate()
    """

    def __init__(self, validator=None):
        self.validator = validator

    # --------------------------------------------------
    # (1) filter
    # --------------------------------------------------
    def filter(self, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """子類可覆寫"""
        return raw

    # --------------------------------------------------
    # (2) auto_fix
    # --------------------------------------------------
    def auto_fix(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """子類可覆寫"""
        return raw

    # --------------------------------------------------
    # (3) anti_poison
    # --------------------------------------------------
    def anti_poison(self, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """子類可覆寫"""
        return raw

    # --------------------------------------------------
    # (4) enrich
    # --------------------------------------------------
    def enrich(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """子類可覆寫"""
        raw["timestamp"] = raw.get("timestamp", time.time())
        return raw

    # --------------------------------------------------
    # (5) make_event
    # --------------------------------------------------
    def make_event(self, raw: Dict[str, Any]):
        """抽象方法，子類必須實作"""
        raise NotImplementedError

    # --------------------------------------------------
    # (6) validator
    # --------------------------------------------------
    def to_event(self, raw: Dict[str, Any]):
        """完整六階段流程"""
        if raw is None:
            return None

        raw = self.filter(raw)
        if raw is None:
            return None

        raw = self.auto_fix(raw)
        raw = self.anti_poison(raw)
        if raw is None:
            return None

        raw = self.enrich(raw)

        event = self.make_event(raw)

        if self.validator:
            return self.validator.validate(event, soft=True)
        return event
