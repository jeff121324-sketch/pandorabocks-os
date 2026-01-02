# shared_core/governance/arbiter/snapshot_builder.py

from datetime import datetime
from statistics import mean
from typing import List

from .schema import (
    PersonaPerformanceWindow,
    PersonaTrustSnapshot,
)


def build_trust_snapshot(
    *,
    persona: str,
    windows: List[PersonaPerformanceWindow],
) -> PersonaTrustSnapshot:
    """
    Build a long-term trust snapshot for ONE persona.

    This function:
    - Aggregates multiple performance windows
    - Describes long-term tendencies
    - Marks structural risk signals

    It MUST NOT:
    - Adjust weights
    - Trigger learning
    - Influence decisions
    """

    if not windows:
        return PersonaTrustSnapshot(
            persona=persona,
            snapshot_at=datetime.utcnow(),
            trust_score=0.5,
            stability_score=0.0,
            learning_integrity=0.5,
            status_flags=["no_windows"],
            notes="insufficient data for trust evaluation",
        )

    # -------------------------
    # Aggregate metrics
    # -------------------------
    alignment_scores = [w.alignment_score for w in windows]
    confidence_levels = [w.average_confidence for w in windows]

    trust_score = mean(alignment_scores)
    stability_score = 1.0 - (max(alignment_scores) - min(alignment_scores)) \
        if len(alignment_scores) > 1 else 0.5

    # Clamp to 0.0 ~ 1.0
    trust_score = max(0.0, min(1.0, trust_score))
    stability_score = max(0.0, min(1.0, stability_score))

    # -------------------------
    # Learning integrity
    # -------------------------
    learning_integrity = 1.0

    for w in windows:
        if "confidence_outpaces_accuracy" in w.warning_flags:
            learning_integrity -= 0.2
        if "random_stance_pattern" in w.warning_flags:
            learning_integrity -= 0.3

    learning_integrity = max(0.0, min(1.0, learning_integrity))

    # -------------------------
    # Status flags
    # -------------------------
    status_flags = []

    if trust_score < 0.3:
        status_flags.append("low_trust_level")

    if stability_score < 0.3:
        status_flags.append("behavior_drift_detected")

    if learning_integrity < 0.4:
        status_flags.append("learning_exploitation_suspected")

    return PersonaTrustSnapshot(
        persona=persona,
        snapshot_at=datetime.utcnow(),
        trust_score=round(trust_score, 4),
        stability_score=round(stability_score, 4),
        learning_integrity=round(learning_integrity, 4),
        status_flags=status_flags,
        notes="auto-generated trust snapshot",
    )
