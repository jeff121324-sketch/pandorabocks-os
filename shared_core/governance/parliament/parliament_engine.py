from __future__ import annotations

from dataclasses import asdict
from typing import Dict, Any, List, Tuple
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

from .parliament_schema import Proposal, Vote, Decision


class ParliamentEngine:
    """
    ParliamentEngine v0.1
    - Stateless evaluation: (proposal + votes + rules) -> Decision
    - No EventBus, no execution, no global state
    """

    def __init__(self, rules_path: str | Path | None = None, rules: Dict[str, Any] | None = None):
        if rules is not None:
            self.rules = rules
            return

        if rules_path is None:
            raise ValueError("Provide rules_path or rules dict.")

        self.rules = self._load_rules(rules_path)

    def _load_rules(self, rules_path: str | Path) -> Dict[str, Any]:
        if yaml is None:
            raise RuntimeError("PyYAML is required to load rules.yaml. Install with: pip install pyyaml")
        p = Path(rules_path)
        if not p.exists():
            raise FileNotFoundError(f"rules.yaml not found: {p}")
        with p.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    # -----------------------------
    # Public API
    # -----------------------------
    def evaluate(self, proposal: Proposal, votes: List[Vote]) -> Decision:
        """
        Evaluate a proposal given votes, return Decision.
        This function is deterministic and stateless.
        """
        self._validate_inputs(proposal, votes)

        defaults = self.rules.get("defaults", {})
        weights = self.rules.get("weights", {})
        thresholds = self.rules.get("thresholds", {})

        min_votes = int(defaults.get("min_votes", 2))
        approve_threshold = float(defaults.get("approve_threshold", 0.6))
        defer_if_low_conf = bool(defaults.get("defer_if_low_confidence", True))
        low_conf_threshold = float(defaults.get("low_confidence_threshold", 0.35))

        if len(votes) < min_votes:
            return Decision(
                agenda_id=proposal.agenda_id,
                proposal_id=proposal.proposal_id,
                outcome="deferred",
                votes=votes,
                arbitration_required=True,
                notes=f"insufficient_votes<{min_votes}",
            )

        approve_score, reject_score, total_weighted_conf = self._score_votes(votes, weights)
        total_score = approve_score + reject_score

        # If everyone abstained (or no weight), defer
        if total_score <= 1e-12:
            return Decision(
                agenda_id=proposal.agenda_id,
                proposal_id=proposal.proposal_id,
                outcome="deferred",
                votes=votes,
                arbitration_required=True,
                notes="no_effective_votes",
            )

        approve_ratio = approve_score / total_score

        # Low confidence -> defer + arbitration flag
        if defer_if_low_conf and total_weighted_conf < float(thresholds.get("min_total_confidence", 0.9)):
            return Decision(
                agenda_id=proposal.agenda_id,
                proposal_id=proposal.proposal_id,
                outcome="deferred",
                votes=votes,
                arbitration_required=True,
                notes="low_total_confidence",
            )

        # If many votes have too-low confidence, defer
        if defer_if_low_conf and self._has_too_many_low_confidence(votes, low_conf_threshold):
            return Decision(
                agenda_id=proposal.agenda_id,
                proposal_id=proposal.proposal_id,
                outcome="deferred",
                votes=votes,
                arbitration_required=True,
                notes="many_low_confidence_votes",
            )

        close_margin = float(thresholds.get("close_margin", 0.05))
        arbitration_required = abs(approve_ratio - approve_threshold) <= close_margin

        if approve_ratio >= approve_threshold:
            return Decision(
                agenda_id=proposal.agenda_id,
                proposal_id=proposal.proposal_id,
                outcome="approved",
                votes=votes,
                arbitration_required=arbitration_required,
                notes=f"approve_ratio={approve_ratio:.3f}",
            )
        else:
            return Decision(
                agenda_id=proposal.agenda_id,
                proposal_id=proposal.proposal_id,
                outcome="rejected",
                votes=votes,
                arbitration_required=arbitration_required,
                notes=f"approve_ratio={approve_ratio:.3f}",
            )

    # -----------------------------
    # Internals
    # -----------------------------
    def _validate_inputs(self, proposal: Proposal, votes: List[Vote]) -> None:
        for v in votes:
            if v.agenda_id != proposal.agenda_id:
                raise ValueError("Vote agenda_id mismatch proposal.agenda_id")
            if v.proposal_id != proposal.proposal_id:
                raise ValueError("Vote proposal_id mismatch proposal.proposal_id")

    def _role_weight(self, role: str, weights: Dict[str, Any]) -> float:
        w = weights.get(role, 1.0)
        try:
            return float(w)
        except Exception:
            return 1.0

    def _score_votes(self, votes: List[Vote], weights: Dict[str, Any]) -> Tuple[float, float, float]:
        approve_score = 0.0
        reject_score = 0.0
        total_weighted_conf = 0.0

        for v in votes:
            w = self._role_weight(v.role, weights)
            conf = float(v.confidence)
            total_weighted_conf += conf * w

            if v.stance == "approve":
                approve_score += conf * w
            elif v.stance == "reject":
                reject_score += conf * w
            else:
                # abstain contributes to confidence total but not to decision score
                pass

        return approve_score, reject_score, total_weighted_conf

    def _has_too_many_low_confidence(self, votes: List[Vote], threshold: float) -> bool:
        # v0.1: simple heuristic: if >= half votes are below threshold => defer
        lows = sum(1 for v in votes if float(v.confidence) < threshold)
        return lows >= max(1, len(votes) // 2)
