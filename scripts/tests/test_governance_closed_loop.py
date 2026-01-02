import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# scripts/tests/test_governance_closed_loop.py

from datetime import datetime, timedelta

from shared_core.governance.arbiter.schema import (
    PersonaDecisionRecord,
)
from shared_core.governance.arbiter.window_builder import (
    build_performance_window,
)
from shared_core.governance.arbiter.snapshot_builder import (
    build_trust_snapshot,
)
from shared_core.governance.chair.chair_supervisor import (
    ChairSupervisor,
)


def test_governance_closed_loop():
    # -------------------------
    # Step 1: fake decision records
    # -------------------------
    now = datetime.utcnow()

    records = [
        PersonaDecisionRecord(
            persona="attacker",
            agenda_id="agenda-1",
            proposal_id=f"p-{i}",
            stance="approve",
            confidence=0.7,
            final_outcome="approved",
            decided_at=now - timedelta(minutes=i * 10),
            alignment=0.6,
        )
        for i in range(12)
    ]

    # -------------------------
    # Step 2: build performance window
    # -------------------------
    window = build_performance_window(
        persona="attacker",
        records=records,
        window_type="mid",
    )

    assert window.persona == "attacker"
    assert window.window_type == "mid"
    assert len(window.records) == 12

    # -------------------------
    # Step 3: build trust snapshot
    # -------------------------
    snapshot = build_trust_snapshot(
        persona="attacker",
        windows=[window],
    )

    assert snapshot.persona == "attacker"
    assert 0.0 <= snapshot.trust_score <= 1.0
    assert 0.0 <= snapshot.stability_score <= 1.0
    assert 0.0 <= snapshot.learning_integrity <= 1.0

    # -------------------------
    # Step 4: chair review
    # -------------------------
    chair = ChairSupervisor()
    directive = chair.review(snapshot)

    print("\n=== Chair Directive ===")
    print("persona:", directive.persona)
    print("action:", directive.action)
    print("reasons:", directive.reasons)

    assert directive.persona == "attacker"
    assert directive.action in ("continue", "request_learning")


if __name__ == "__main__":
    test_governance_closed_loop()
    print("\n✅ Governance closed-loop test PASSED")
