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
        self._last_ingest_ts = 0.0

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
    def anti_poison(self, raw):
        now = time.time()

        # 絕對底線：防止毫秒級無限灌入（系統異常）
        if now - self._last_ingest_ts < 0.001:  # 1ms
            return None

        self._last_ingest_ts = now
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
    # --------------------------------------------------
    # Gateway 專用入口（Adapter × Raw）
    # --------------------------------------------------
    def run_pipeline(self, adapter, raw, *, soft: bool = False):
        """
        統一由 Gateway 呼叫的 pipeline 入口

        adapter: Domain Adapter（如 MarketKlineAdapter）
        raw:     原始 dict
        """
        # 將 adapter 的 domain 行為「暫時掛載」到 core
        self.filter = adapter.filter
        self.auto_fix = adapter.auto_fix
        self.anti_poison = adapter.anti_poison
        self.enrich = adapter.enrich
        self.make_event = adapter.make_event

        return self.to_event(raw)
