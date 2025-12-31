from __future__ import annotations

from dataclasses import asdict
from typing import Dict, Any, List, Tuple
from pathlib import Path
from collections import deque
try:
    import yaml  # type: ignore
except Exception:
    yaml = None

from .parliament_schema import Proposal, Vote, Decision
from shared_core.governance.parliament.context import GovernanceContext
from shared_core.governance.chair.basic_chair import BasicChairStrategy
from shared_core.governance.arbiter.basic_arbiter import StabilityFirstArbiter


class ParliamentEngine:
    """
    ParliamentEngine v0.1
    - Stateless evaluation: (proposal + votes + rules) -> Decision
    - No EventBus, no execution, no global state
    """

    def __init__(self, rules_path: str | Path | None = None, rules: Dict[str, Any] | None = None):

        # ✅ 永遠先初始化內部狀態
        self._decision_history = deque(maxlen=10)
        
        # v0.5 governance actors
        self._chair = BasicChairStrategy()
        self._arbiter = StabilityFirstArbiter()
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
        Deterministic voting + governance guards (v0.5).
        """
        self._validate_inputs(proposal, votes)

        defaults = self.rules.get("defaults", {})
        weights = self.rules.get("weights", {})
        thresholds = self.rules.get("thresholds", {})

        min_votes = int(defaults.get("min_votes", 2))
        approve_threshold = float(defaults.get("approve_threshold", 0.6))
        defer_if_low_conf = bool(defaults.get("defer_if_low_confidence", True))
        low_conf_threshold = float(defaults.get("low_confidence_threshold", 0.35))

        # -----------------------------
        # Governance Context (v0.5)
        # -----------------------------
        context = GovernanceContext(
            world_capabilities=proposal.constraints.get("world_capabilities", []),
            decision_history=list(self._decision_history),
        )

        # -----------------------------
        # Chair pre-review (procedural / capability / stability)
        # -----------------------------
        chair_decision = self._chair.review(proposal, context)
        if chair_decision is not None:
            self._decision_history.append(chair_decision)
            return chair_decision

        # -----------------------------
        # Voting phase (原本邏輯)
        # -----------------------------
        if len(votes) < min_votes:
            decision = Decision(
                agenda_id=proposal.agenda_id,
                proposal_id=proposal.proposal_id,
                outcome="deferred",
                votes=votes,
                arbitration_required=True,
                notes=f"insufficient_votes<{min_votes}",
            )
            self._decision_history.append(decision)
            return decision

        approve_score, reject_score, total_weighted_conf = self._score_votes(votes, weights)
        total_score = approve_score + reject_score

        if total_score <= 1e-12:
            decision = Decision(
                agenda_id=proposal.agenda_id,
                proposal_id=proposal.proposal_id,
                outcome="deferred",
                votes=votes,
                arbitration_required=True,
                notes="no_effective_votes",
            )
            self._decision_history.append(decision)
            return decision

        approve_ratio = approve_score / total_score

        if defer_if_low_conf and total_weighted_conf < float(thresholds.get("min_total_confidence", 0.9)):
            decision = Decision(
                agenda_id=proposal.agenda_id,
                proposal_id=proposal.proposal_id,
                outcome="deferred",
                votes=votes,
                arbitration_required=True,
                notes="low_total_confidence",
            )
            self._decision_history.append(decision)
            return decision

        if defer_if_low_conf and self._has_too_many_low_confidence(votes, low_conf_threshold):
            decision = Decision(
                agenda_id=proposal.agenda_id,
                proposal_id=proposal.proposal_id,
                outcome="deferred",
                votes=votes,
                arbitration_required=True,
                notes="many_low_confidence_votes",
            )
            self._decision_history.append(decision)
            return decision

        close_margin = float(thresholds.get("close_margin", 0.05))
        arbitration_required = abs(approve_ratio - approve_threshold) <= close_margin

        # -----------------------------
        # Final outcome
        # -----------------------------
        if approve_ratio >= approve_threshold:
            decision = Decision(
                agenda_id=proposal.agenda_id,
                proposal_id=proposal.proposal_id,
                outcome="approved",
                votes=votes,
                arbitration_required=arbitration_required,
                notes=f"approve_ratio={approve_ratio:.3f}",
            )
        else:
            decision = Decision(
                agenda_id=proposal.agenda_id,
                proposal_id=proposal.proposal_id,
                outcome="rejected",
                votes=votes,
                arbitration_required=arbitration_required,
                notes=f"approve_ratio={approve_ratio:.3f}",
            )

        # -----------------------------
        # Arbiter (only if needed)
        # -----------------------------
        if decision.arbitration_required:
            arbiter_decision = self._arbiter.arbitrate(decision, context)
            if arbiter_decision is not None:
                self._decision_history.append(arbiter_decision)
                return arbiter_decision

        self._decision_history.append(decision)
        return decision

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
