# trading_core/personas/experience_memory.py

from dataclasses import dataclass
from collections import defaultdict
from typing import Dict


@dataclass
class ExperienceStat:
    total: int = 0
    positive: int = 0
    negative: int = 0

    @property
    def accuracy(self) -> float:
        if self.total == 0:
            return 0.5  # unknown -> neutral
        return self.positive / self.total


def bucket_change(change_abs: float) -> str:
    # 依你目前 persona 的 change 門檻設計桶（可 audit、可調）
    if change_abs < 0.002:
        return "chg_tiny"
    if change_abs < 0.005:
        return "chg_small"
    if change_abs < 0.01:
        return "chg_mid"
    return "chg_big"


def bucket_context_match(cm: float) -> str:
    if cm >= 0.8:
        return "cm_high"
    if cm >= 0.5:
        return "cm_mid"
    return "cm_low"


def make_context_key(payload: dict, context_match: float) -> str:
    risk = payload.get("risk_level", "low")
    change_abs = abs(payload.get("change", 0.0))
    return "|".join(
        [
            f"risk={risk}",
            bucket_change(change_abs),
            bucket_context_match(context_match),
        ]
    )


class PersonaExperienceMemory:
    """
    One persona -> one memory.
    Keyed by (context buckets), stores accuracy stats.
    """

    def __init__(self, persona_name: str):
        self.persona_name = persona_name
        self._stats: Dict[str, ExperienceStat] = defaultdict(ExperienceStat)

    def record(self, context_key: str, outcome: bool) -> None:
        stat = self._stats[context_key]
        stat.total += 1
        if outcome:
            stat.positive += 1
        else:
            stat.negative += 1

    def get_accuracy(self, context_key: str) -> float:
        return round(self._stats[context_key].accuracy, 3)

    def snapshot(self) -> dict:
        # 讓你可以寫進 attempts / report（可審計）
        return {
            "persona": self.persona_name,
            "contexts": {
                k: {
                    "total": v.total,
                    "positive": v.positive,
                    "negative": v.negative,
                    "accuracy": round(v.accuracy, 3),
                }
                for k, v in self._stats.items()
            },
        }
