# pb_language/pbschema.py
from typing import TypedDict, List, Optional, Literal


class PBSemanticFeatures(TypedDict, total=False):
    """
    PB-Lang Semantic Schema v1
    語言理解後的結構化語意結果
    """

    # 基本語言層
    language: str
    text_length: int
    tokens: List[str]

    # 情緒層
    sentiment: Literal["positive", "neutral", "negative"]
    sentiment_score: float  # -1.0 ~ 1.0

    # 意圖 / 指令層
    intent: Optional[str]
    command: Optional[str]

    # 語意品質
    confidence: float       # 0.0 ~ 1.0
    ambiguity: float        # 0.0 ~ 1.0

    # 標籤（給 AISOP / 後端用）
    tags: List[str]
