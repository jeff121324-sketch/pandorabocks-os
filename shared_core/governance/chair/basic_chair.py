# shared_core/governance/chair/basic_chair.py

from shared_core.governance.parliament.parliament_schema import Decision
from shared_core.governance.chair.chair_strategy import ChairStrategy

class BasicChairStrategy(ChairStrategy):

    def review(self, proposal, context):
        # 1️⃣ 程序正確性
        if not proposal.is_procedurally_valid():
            return Decision(
                agenda_id=proposal.agenda_id,
                proposal_id=proposal.proposal_id,
                outcome="rejected",
                votes=[],
                notes="procedural_invalid",
            )

        # 2️⃣ 能力邊界
        if proposal.requires_capability_not_in(context.world_capabilities):
            return Decision(
                agenda_id=proposal.agenda_id,
                proposal_id=proposal.proposal_id,
                outcome="rejected",
                votes=[],
                notes="capability_violation",
            )

        # 3️⃣ 系統穩定性（治理節奏）
        if context.is_flapping(proposal.proposal_id):
            return Decision(
                agenda_id=proposal.agenda_id,
                proposal_id=proposal.proposal_id,
                outcome="deferred",
                votes=[],
                arbitration_required=True,
                notes="proposal_flapping_cooldown",
            )

        # ✅ 放行
        return None
