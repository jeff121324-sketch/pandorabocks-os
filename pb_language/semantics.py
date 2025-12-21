# pb_language/semantics.py
from pb_language.pbschema import PBSemanticFeatures


def analyze(text: str) -> PBSemanticFeatures:
    tokens = text.strip().split()

    return PBSemanticFeatures(
        language="en",
        text_length=len(text),
        tokens=tokens,
        intent="statement",
        confidence=0.7,
        ambiguity=0.2,
        tags=[],
    )


