# shared_core/pblang_core/semantics.py
from pb_language.schema import PBSemanticFeatures
import re

class PBLangSentiment:
    """
    PB-Lang Sentiment Analyzer v1
    單一職責：文字 → 情緒特徵
    """

    @staticmethod
    def analyze(text: str) -> PBSemanticFeatures:
        sentiment = "neutral"
        score = 0.0

        low = text.lower()

        # === Negative signals ===
        if "崩" in text or "dump" in low or "crash" in low:
            sentiment = "negative"
            score = -0.7

        # === Positive signals ===
        elif "噴" in text or "moon" in low or "pump" in low:
            sentiment = "positive"
            score = 0.7

        return PBSemanticFeatures(
            sentiment=sentiment,
            sentiment_score=score,
        )
