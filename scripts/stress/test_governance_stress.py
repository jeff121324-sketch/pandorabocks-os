import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

"""
test_governance_stress.py

Purpose:
- System Health Test for Governance v0.5
- Validate stability under stress (many proposals, flapping, low confidence)
- NO trading, NO AISOP, NO EventBus dependency
"""

from datetime import datetime, timezone
from shared_core.governance.parliament.parliament_schema import Proposal
from shared_core.governance.parliament.parliament_engine import ParliamentEngine
from shared_core.governance.parliament.context import GovernanceContext
from shared_core.governance.chair.basic_chair import BasicChairStrategy
from shared_core.governance.arbiter.basic_arbiter import StabilityFirstArbiter
from shared_core.governance.parliament.parliament_schema import (
    Proposal,
    Vote,
    Decision,
)

# -------------------------------------------------
# Default rules for stress testing
# -------------------------------------------------
DEFAULT_RULES = {
    "defaults": {
        "min_votes": 2,
        "approve_threshold": 0.6,
        "defer_if_low_confidence": True,
    },
    "thresholds": {
        "min_total_confidence": 0.9,
        "low_confidence_threshold": 0.35,
        "close_margin": 0.05,
    },
    "weights": {
        "member_a": 1.0,
        "member_b": 1.0,
        "member_c": 1.0,
    },
}

# =================================================
# Test 1: Many proposals (system stability)
# =================================================
def test_governance_many_proposals():
    print("\n=== STRESS TEST: many proposals ===")

    context = GovernanceContext(
        world_capabilities=["HOTPLUG", "MULTI_RUNTIME"]
    )

    chair = BasicChairStrategy()
    arbiter = StabilityFirstArbiter()
    parliament = ParliamentEngine(rules=DEFAULT_RULES)

    for i in range(50):
        proposal = Proposal(
            agenda_id="stress-test",
            proposal_id=f"proposal-{i}",
            proposer_role="system",
            action={"enable_feature": f"feature_{i}"},
            constraints={},
        )

        # Chair gate
        chair_decision = chair.review(proposal, context)
        assert chair_decision is None, f"Chair rejected proposal-{i}"

        votes = [
            Vote(
                agenda_id=proposal.agenda_id,   # ✅ 一律從 proposal 取
                proposal_id=proposal.proposal_id,
                role="member_a",
                stance="approve",
                confidence=0.9,
                rationale="meets system expansion requirements",
            ),
            Vote(
                agenda_id=proposal.agenda_id,   # ✅
                proposal_id=proposal.proposal_id,
                role="member_b",
                stance="approve",
                confidence=0.8,
                rationale="no conflict detected",
            ),
            Vote(
                agenda_id=proposal.agenda_id,   # ✅
                proposal_id=proposal.proposal_id,
                role="member_c",
                stance="reject",
                confidence=0.6,
                rationale="potential edge case risk",
            ),
        ]

        decision = parliament.evaluate(
            proposal=proposal,
            votes=votes,
        )

        if decision.arbitration_required:
            decision = arbiter.arbitrate(votes, context)

        context.record_decision(decision)

    assert len(context.recent_decisions(limit=100)) <= 20

    print("✅ many proposals stress passed")


# =================================================
# Test 2: Flapping stress (decision oscillation)
# =================================================
def test_governance_flapping_stress():
    print("\n=== STRESS TEST: flapping ===")

    context = GovernanceContext(
        world_capabilities=["HOTPLUG", "MULTI_RUNTIME"]
    )

    arbiter = StabilityFirstArbiter()

    proposal_id = "enable_feature_x"
    agenda_id = "flap-test"

    # -------------------------------------------------
    # Proposal object (IMPORTANT: is_flapping eats Proposal)
    # -------------------------------------------------
    proposal = Proposal(
        agenda_id=agenda_id,
        proposal_id=proposal_id,
        proposer_role="system",
        action={"enable_feature": proposal_id},
        constraints={},
    )

    # -------------------------------------------------
    # Stub votes（最小合法投票，用於審計與追溯）
    # -------------------------------------------------
    stub_votes = [
        Vote(
            agenda_id=agenda_id,
            proposal_id=proposal_id,
            role="arbiter",
            stance="abstain",
            confidence=0.5,
            rationale="synthetic vote for flapping stress test",
        )
    ]

    # -------------------------------------------------
    # Artificial flapping decisions
    # -------------------------------------------------
    decisions = [
        Decision(
            agenda_id=agenda_id,
            proposal_id=proposal_id,
            outcome="approved",
            votes=stub_votes,
            notes="manual_override",
        ),
        Decision(
            agenda_id=agenda_id,
            proposal_id=proposal_id,
            outcome="rejected",
            votes=stub_votes,
            notes="manual_override",
        ),
        Decision(
            agenda_id=agenda_id,
            proposal_id=proposal_id,
            outcome="approved",
            votes=stub_votes,
            notes="manual_override",
        ),
        Decision(
            agenda_id=agenda_id,
            proposal_id=proposal_id,
            outcome="rejected",
            votes=stub_votes,
            notes="manual_override",
        ),
    ]

    # -------------------------------------------------
    # Record decisions into governance context
    # -------------------------------------------------
    for d in decisions:
        context.record_decision(d)

    # Flapping must be detected (USE Proposal, NOT string)
    assert context.is_flapping(proposal.proposal_id) is True

    # Arbiter must stabilize the system
    final = arbiter.arbitrate(
        votes=stub_votes,
        context=context,
    )

    assert final.outcome in ("rejected", "deferred")
    print("✅ flapping stress passed")




# =================================================
# Test 3: Low confidence voting storm
# =================================================
def test_governance_low_confidence_votes():
    print("\n=== STRESS TEST: low confidence votes ===")

    parliament = ParliamentEngine(rules=DEFAULT_RULES)

    proposal = Proposal(
        agenda_id="low-conf-test",
        proposal_id="risk_feature",
        proposer_role="system",
        action={"enable_feature": "risk_feature"},
        constraints={},
    )

    votes = [
        Vote(
            agenda_id=proposal.agenda_id,
            proposal_id=proposal.proposal_id,
            role="member_a",
            stance="approve",
            confidence=0.2,
            rationale="insufficient confidence",
        ),
        Vote(
            agenda_id=proposal.agenda_id,
           proposal_id=proposal.proposal_id,
            role="member_b",
            stance="approve",
            confidence=0.1,
            rationale="speculative benefit",
        ),
        Vote(
            agenda_id=proposal.agenda_id,
            proposal_id=proposal.proposal_id,
            role="member_c",
            stance="reject",
            confidence=0.3,
            rationale="risk unclear",
        ),
    ]

    decision = parliament.evaluate(
        proposal=proposal,
        votes=votes,
    )

    assert decision.outcome == "deferred"
    assert decision.arbitration_required is True
    print("✅ low confidence stress passed")


# =================================================
# Entry
# =================================================
if __name__ == "__main__":
    print("\n=== GOVERNANCE STRESS TEST v0.5 ===")

    test_governance_many_proposals()
    test_governance_flapping_stress()
    test_governance_low_confidence_votes()

    print("\n🎉 GOVERNANCE STRESS TEST PASSED")
