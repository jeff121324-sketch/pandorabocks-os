# aisop/outputs/narrators/stub_narrator.py
from typing import Dict, Any

class StubNarrator:
    def narrate(self, decision: Dict[str, Any]) -> str:
        return (
            "This decision was generated based on current market signals. "
            "No anomalies were detected and risk remains within acceptable range."
        )
