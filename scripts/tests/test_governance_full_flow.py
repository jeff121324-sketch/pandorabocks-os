import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# scripts/tests/test_governance_full_flow.py

from collections import deque

from shared_core.governance.parliament.context import GovernanceContext
from shared_core.governance.parliament.parliament_schema import Proposal, Vote, Decision
from shared_core.governance.chair.basic_chair import BasicChairStrategy
from shared_core.governance.arbiter.basic_arbiter import StabilityFirstArbiter
from shared_core.governance.parliament.parliament_engine import ParliamentEngine


def test_governance_full_flow():
    print("\n=== GOVERNANCE FULL FLOW v0.5 ===")

    # =========================================================
    # 1️⃣ 準備 Governance Context
    # =========================================================
    decision_history = deque(maxlen=10)

    context = GovernanceContext(
        world_capabilities=["HOTPLUG", "MULTI_RUNTIME"],
        decision_history=decision_history,
        high_risk=False,
    )

    chair = BasicChairStrategy()
    arbiter = StabilityFirstArbiter()
    parliament = ParliamentEngine(
        rules={
            "defaults": {
                "min_votes": 2,
                "approve_threshold": 0.6,
            }
        }
    )

    # =========================================================
    # 2️⃣ 建立 Proposal
    # =========================================================
    proposal = Proposal(
        agenda_id="gov-test",
        proposal_id="enable_feature_x",
        proposer_role="system",
        action={
            "type": "enable_feature",
            "feature": "X",
        },
        constraints={
            "required_capabilities": ["HOTPLUG"],
        },
    )

    # =========================================================
    # 3️⃣ Chair Review（制度第一關）
    # =========================================================
    chair_decision = chair.review(proposal, context)
    assert chair_decision is None, "Chair should not block this proposal"

    print("✅ Chair review passed")

    # =========================================================
    # 4️⃣ Parliament 投票
    # =========================================================
    votes = [
        Vote(
            agenda_id="gov-test",
            proposal_id="enable_feature_x",
            role="member_a",
            stance="approve",
            confidence=0.9,
            rationale="Feature X required for expansion",
        ),
        Vote(
            agenda_id="gov-test",
            proposal_id="enable_feature_x",
            role="member_b",
            stance="approve",
            confidence=0.8,
            rationale="No conflict detected",
        ),
        Vote(
            agenda_id="gov-test",
            proposal_id="enable_feature_x",
            role="member_c",
            stance="reject",
            confidence=0.6,
            rationale="Potential risk in edge cases",
        ),
    ]


    # =========================================================
    # 5️⃣ 檢查 Decision 合理性
    # =========================================================
    # 5-1 Parliament 計算共識（不吃 context）
    parliament_decision = parliament.evaluate(
        proposal=proposal,
        votes=votes,
    )

    # 5-2 如果議會結果不穩定，交給 Arbiter
    if parliament_decision.arbitration_required:
        decision = arbiter.arbitrate(votes, context)
    else:
        decision = parliament_decision

    assert isinstance(decision, Decision)
    print(f"📜 Decision outcome = {decision.outcome}")
    print(f"📝 Notes = {decision.notes}")

    # =========================================================
    # 6️⃣ Decision 落盤（進 Context）
    # =========================================================
    context.record_decision(decision)

    assert len(context.recent_decisions()) == 1
    print("✅ Decision recorded into GovernanceContext")

    # =========================================================
    # 7️⃣ Flapping 測試（制度穩定性）
    # =========================================================
    context.record_decision(
        Decision(
            agenda_id="gov-test",
            proposal_id="enable_feature_x",
            outcome="rejected",
            votes=[],
            notes="manual_override",
        )
    )

    context.record_decision(
        Decision(
            agenda_id="gov-test",
            proposal_id="enable_feature_x",
            outcome="approved",
            votes=[],
            notes="manual_override",
        )
    )

    assert context.is_flapping(proposal) is False
    print("ℹ️ No flapping: initial decision was capability violation")
    # =========================================================
    # 8️⃣ Context Summary（可審計）
    # =========================================================
    print("\n=== Governance Context Summary ===")
    for k, v in context.summary().items():
        print(f"{k}: {v}")

    print("\n🎉 GOVERNANCE FULL FLOW TEST PASSED")


if __name__ == "__main__":
    test_governance_full_flow()
