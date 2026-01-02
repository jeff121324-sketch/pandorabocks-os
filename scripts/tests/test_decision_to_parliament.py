import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# =========================================
# Minimal Decision → Parliament Integration Test
# =========================================

from shared_core.governance.decision_api import DecisionAPI
from shared_core.governance.parliament_adapter import ParliamentAdapter
from shared_core.governance.parliament.context import GovernanceContext
from shared_core.governance.decision_personas.schema import DecisionSummary
from shared_core.governance.parliament.parliament_engine import ParliamentEngine


def main():
    # -------------------------
    # Setup
    # -------------------------
    decision_api = DecisionAPI()

    engine = ParliamentEngine(
        rules={
            "defaults": {
                "min_votes": 2,
                "approve_threshold": 0.6,
            }
        }
    )

    adapter = ParliamentAdapter(engine)

    context = GovernanceContext(
        world_capabilities=["HOTPLUG", "MULTI_RUNTIME"]
    )

    summary = DecisionSummary(
        source_project="aisop-hotel",
        subject="front_desk_staffing",
        intent="increase_staff",
        time_scope="short",
        risk_flags=[],
        confidence_hint=0.7,
    )

    # -------------------------
    # Decision Flow
    # -------------------------
    opinions = decision_api.request_opinions(
        summary=summary,
        context=context,
    )

    print("\n=== Persona Opinions ===")
    for op in opinions:
        print(op)

    decision = adapter.submit_decision(
        summary=summary,
        opinions=opinions,
        context=context,
    )

    # -------------------------
    # Result
    # -------------------------
    print("\n=== Parliament Decision ===")
    print(decision)
    print("\n=== Decision Dict ===")
    print(decision.to_dict())


if __name__ == "__main__":
    main()
