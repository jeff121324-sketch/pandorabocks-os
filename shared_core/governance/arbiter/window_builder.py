# shared_core/governance/arbiter/window_builder.py

from typing import List
from statistics import mean

from .schema import (
    PersonaDecisionRecord,
    PersonaPerformanceWindow,
)


def build_performance_window(
    *,
    persona: str,
    records: List[PersonaDecisionRecord],
    window_type: str,  # short / mid / long
) -> PersonaPerformanceWindow:
    """
    Build an aggregated performance window for ONE persona.

    Responsibilities:
    - Aggregate decision behavior
    - Describe patterns
    - Flag suspicious signals (no judgement)

    This function MUST NOT:
    - Adjust weights
    - Trigger learning
    - Influence decisions
    """

    if not records:
        # Defensive: empty window is allowed but explicit
        return PersonaPerformanceWindow(
            persona=persona,
            window_type=window_type,
            records=[],
            average_confidence=0.0,
            alignment_score=0.0,
            abstain_rate=0.0,
            execution_rate=0.0,
            warning_flags=["no_records"],
        )

    total = len(records)

    confidences = [r.confidence for r in records]
    alignments = [r.alignment for r in records if r.alignment is not None]

    abstain_count = sum(1 for r in records if r.stance == "abstain")
    execution_count = sum(1 for r in records if r.stance in ("approve", "reject"))

    average_confidence = mean(confidences) if confidences else 0.0
    alignment_score = mean(alignments) if alignments else 0.0

    abstain_rate = abstain_count / total
    execution_rate = execution_count / total

    # -------------------------
    # Warning flag detection
    # -------------------------
    warning_flags: List[str] = []

    # High confidence but poor alignment
    if average_confidence >= 0.7 and alignment_score < 0.0:
        warning_flags.append("confidence_outpaces_accuracy")

    # Very low abstain rate (over participation)
    if abstain_rate < 0.05 and total >= 10:
        warning_flags.append("over_participation")

    # Very high abstain rate (under participation)
    if abstain_rate > 0.8 and total >= 10:
        warning_flags.append("under_participation")

    # Alignment highly unstable
    if len(alignments) >= 5:
        max_align = max(alignments)
        min_align = min(alignments)
        if max_align - min_align > 1.5:
            warning_flags.append("unstable_alignment_pattern")

    return PersonaPerformanceWindow(
        persona=persona,
        window_type=window_type,
        records=records,
        average_confidence=round(average_confidence, 4),
        alignment_score=round(alignment_score, 4),
        abstain_rate=round(abstain_rate, 4),
        execution_rate=round(execution_rate, 4),
        warning_flags=warning_flags,
    )
