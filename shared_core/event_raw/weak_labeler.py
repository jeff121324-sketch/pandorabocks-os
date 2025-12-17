# weak_labeler.py
from typing import Dict, Any, List

class WeakLabeler:
    """
    WeakLabeler v1 — 輕量弱語義標籤器
    ✔ 不做深度 NLP
    ✔ 僅依照 event type、payload 特徵建立初步標籤
    ✔ 供日後 Library System 做「人類審核 + 強標籤」的前置版本
    """

    def __init__(self):
        # 可擴充字典（未來可由外部 plugin 增加）
        self.rules = {
            "market.kline": self._label_kline,
        }

    # -----------------------------------------------------
    # 主入口
    # -----------------------------------------------------
    def label_event(self, event_dict: Dict[str, Any]) -> List[str]:
        """
        使用 event["type"] 找對應的弱標籤方法
        若無對應 → 回傳空 list
        """
        etype = event_dict.get("type")

        if etype in self.rules:
            try:
                return self.rules[etype](event_dict)
            except Exception:
                return []

        return []

    # -----------------------------------------------------
    # market.kline 的弱標籤
    # -----------------------------------------------------
    def _label_kline(self, ev: Dict[str, Any]) -> List[str]:
        payload = ev.get("payload", {})
        o = payload.get("open")
        c = payload.get("close")
        h = payload.get("high")
        l = payload.get("low")
        vol = payload.get("volume", 0)

        tags = ["kline"]

        # 漲跌
        if o is not None and c is not None:
            if c > o:
                tags.append("bull")
            elif c < o:
                tags.append("bear")

        # 波動
        if h is not None and l is not None:
            if (h - l) / max(1e-9, o) > 0.02:
                tags.append("high_volatility")

        # 爆量判斷
        if vol > 0:
            if vol > 5000:
                tags.append("high_volume")
            elif vol < 10:
                tags.append("low_volume")

        return tags