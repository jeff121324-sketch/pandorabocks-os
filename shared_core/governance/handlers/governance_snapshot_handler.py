from uuid import uuid4
from datetime import datetime, timezone

from shared_core.event_schema import PBEvent
from shared_core.governance.parliament.parliament_engine import ParliamentEngine
from shared_core.governance.parliament.parliament_schema import Proposal, Vote


class GovernanceSnapshotHandler:
    def __init__(self, engine: ParliamentEngine, event_bus):
        self.engine = engine
        self.event_bus = event_bus

    def handle(self, event: PBEvent):
        payload = event.payload

        agenda_id = f"governance-{payload['snapshot_id']}"

        proposal = Proposal(
            agenda_id=agenda_id,
            proposal_id=str(uuid4()),
            proposer_role="governance",
            action={
                "intent": "acknowledge_governance_snapshot",
                "snapshot_id": payload["snapshot_id"],
            },
            constraints={
                "world_count": payload["world_count"],
            },
        )

        votes = [
            Vote(
                agenda_id=agenda_id,
                proposal_id=proposal.proposal_id,
                role="chair",
                stance="approve",
                confidence=0.9,
                rationale="snapshot structurally valid",
            ),
            Vote(
                agenda_id=agenda_id,
                proposal_id=proposal.proposal_id,
                role="arbiter",
                stance="approve",
                confidence=0.8,
                rationale="no conflict detected",
            ),
        ]

        # 🧠 議會決策
        decision = self.engine.evaluate(proposal, votes)

        # 📣 發出治理決策事件（關鍵）
        decision_event = PBEvent(
            type="system.governance.decision.created",
            source="governance.parliament",
            payload={
                "agenda_id": agenda_id,
                "decision": {
                    **decision.to_dict(),

                    # 👇 新增這兩個（文明級關鍵）
                    "report_type": "daily",        # daily / weekly / monthly
                    "narration_cost": "low",       # low / high
                },
                "ts": datetime.now(timezone.utc).isoformat(),
            },
        )

        self.event_bus.publish(decision_event)

        return decision
