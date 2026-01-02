# scripts/tests/test_persona_cheating_simulation.py
import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from datetime import datetime, timedelta, timezone

from shared_core.governance.arbiter.schema import PersonaDecisionRecord
from shared_core.governance.arbiter.window_builder import build_performance_window
from shared_core.governance.arbiter.snapshot_builder import build_trust_snapshot
from shared_core.governance.chair.chair_supervisor import ChairSupervisor


def test_cheating_persona_detection():
    now = datetime.now(timezone.utc)

    # High confidence but bad alignment (cheating pattern)
    records = [
        PersonaDecisionRecord(
            persona="attacker",
            agenda_id="cheat-test",
            proposal_id=f"c-{i}",
            stance="approve",
            confidence=0.95,
            final_outcome="approved",
            decided_at=now - timedelta(minutes=i),
            alignment=-0.4,   # consistently wrong
        )
        for i in range(15)
    ]

    window = build_performance_window(
        persona="attacker",
        records=records,
        window_type="mid",
    )

    snapshot = build_trust_snapshot(
        persona="attacker",
        windows=[window],
    )

    chair = ChairSupervisor()
    directive = chair.review(snapshot)

    print("\n=== Cheating Simulation ===")
    print("trust_score:", snapshot.trust_score)
    print("learning_integrity:", snapshot.learning_integrity)
    print("directive:", directive)

    assert directive.action == "request_learning"


if __name__ == "__main__":
    test_cheating_persona_detection()
    print("\n✅ Cheating detection test PASSED")
