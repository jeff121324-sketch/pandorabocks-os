# aisop/learning/trust_builder.py
from collections import defaultdict
from .persona_trust_snapshot import PersonaTrustSnapshot, PersonaTrust


class PersonaTrustBuilder:
    """
    Build PersonaTrustSnapshot from learning metrics.
    Deterministic, replay-safe.
    """

    def build(self, metrics: dict) -> PersonaTrustSnapshot:
        snapshot = PersonaTrustSnapshot()
        persona_stats = metrics.get("persona_stats", {})

        for name, stat in persona_stats.items():
            attempts = stat.get("count", 0)
            approved = stat.get("approved", 0)
            blocked = stat.get("blocked", 0)

            # v0 trust rule：簡單、保守、不爆炸
            if attempts == 0:
                trust = 1.0
            else:
                trust = round(1.0 + (approved - blocked) / max(attempts, 1) * 0.1, 3)

            snapshot.personas[name] = PersonaTrust(
                trust=trust,
                evidence={
                    "attempts": attempts,
                    "approved": approved,
                    "blocked": blocked,
                }
            )

        return snapshot
