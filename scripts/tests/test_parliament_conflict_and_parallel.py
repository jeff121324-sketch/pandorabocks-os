# scripts/tests/test_parliament_governance_v0.py

import sys
from pathlib import Path
from datetime import datetime
from pprint import pprint

# -------------------------------------------------
# Path bootstrap（與你現有測試一致）
# -------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared_core.governance.parliament.parliament_engine import ParliamentEngine
from shared_core.governance.parliament.parliament_schema import Proposal, Vote


# -------------------------------------------------
# helpers
# -------------------------------------------------
def make_proposal(aid, pid):
    return Proposal(
        agenda_id=aid,
        proposal_id=pid,
        proposer_role="tester",
        action={"type": "noop"},
    )


def make_vote(aid, pid, role, stance):
    return Vote(
        agenda_id=aid,
        proposal_id=pid,
        role=role,
        stance=stance,
        confidence=1.0,
        rationale=f"{role} says {stance}",
    )


def run():
    engine = ParliamentEngine(
        rules_path="shared_core/governance/parliament/rules.yaml"
    )

    # ==================================================
    # Test 1: 分歧測試（制度門檻）
    # ==================================================
    proposal_a = make_proposal("agenda-A", "proposal-A1")
    votes_a = [
        make_vote("agenda-A", "proposal-A1", "role_approve", "approve"),
        make_vote("agenda-A", "proposal-A1", "role_reject", "reject"),
    ]

    decision_a = engine.evaluate(proposal_a, votes_a)

    print("\n[Test 1 - Conflict]")
    print(
        f"agenda={decision_a.agenda_id} "
        f"outcome={decision_a.outcome} "
        f"arbitration_required={decision_a.arbitration_required} "
        f"notes={decision_a.notes}"
    )

    # ==================================================
    # Test 2: 多 Agenda 並行（不串線）
    # ==================================================
    proposal_b = make_proposal("agenda-B", "proposal-B1")
    proposal_c = make_proposal("agenda-C", "proposal-C1")

    decision_b = engine.evaluate(
        proposal_b,
        [
            make_vote("agenda-B", "proposal-B1", "r1", "approve"),
            make_vote("agenda-B", "proposal-B1", "r2", "approve"),
        ],
    )

    decision_c = engine.evaluate(
        proposal_c,
        [
            make_vote("agenda-C", "proposal-C1", "r1", "reject"),
            make_vote("agenda-C", "proposal-C1", "r2", "reject"),
        ],
    )

    print("\n[Test 2 - Parallel Agendas]")
    print(f"agenda-B outcome={decision_b.outcome} notes={decision_b.notes}")
    print(f"agenda-C outcome={decision_c.outcome} notes={decision_c.notes}")

    # ==================================================
    # Test 3: Decision → dict（治理輸出）
    # ==================================================
    print("\n[Test 3 - Decision Serialization]")
    decision_dict = decision_b.to_dict()
    pprint(decision_dict)

    assert decision_dict["agenda_id"] == "agenda-B"
    assert decision_dict["outcome"] == "approved"
    assert "votes" in decision_dict
    assert isinstance(decision_dict["votes"], list)

    print("\n✅ Governance v0 ALL TESTS PASSED")


if __name__ == "__main__":
    run()

