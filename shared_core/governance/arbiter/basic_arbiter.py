# shared_core/governance/arbiter/basic_arbiter.py

from shared_core.governance.parliament.parliament_schema import Decision
from shared_core.governance.arbiter.arbiter_strategy import ArbiterStrategy

class StabilityFirstArbiter(ArbiterStrategy):

    def arbitrate(self, votes, context):
        total = len(votes)
        approve = [v for v in votes if v.stance == "approve"]
        reject = [v for v in votes if v.stance == "reject"]

        # -------------------------------------------------
        # 0️⃣ 推導議題識別（治理 v0.5 正確來源）
        # -------------------------------------------------
        proposal_id = votes[0].proposal_id if votes else None
        agenda_id = votes[0].agenda_id if votes else "unknown"

        # -------------------------------------------------
        # 1️⃣ 系統抖動（flapping）→ 絕對優先、直接鎖死
        # -------------------------------------------------
        if proposal_id and context.is_flapping(proposal_id):
            return Decision(
                agenda_id=agenda_id,
                proposal_id=proposal_id,
                outcome="rejected",
                votes=votes,
                arbitration_required=True,
                notes="arbiter_flapping_guard",
            )

        # -------------------------------------------------
        # 2️⃣ 無投票資料 → 延後（保守）
        # -------------------------------------------------
        if total == 0:
            return Decision(
                agenda_id=agenda_id,
                proposal_id=proposal_id or "unknown",
                outcome="deferred",
                votes=votes,
                arbitration_required=True,
                notes="arbiter_no_votes",
            )

        approve_ratio = len(approve) / total

        # -------------------------------------------------
        # 3️⃣ 明確強共識（>= 70%）
        # -------------------------------------------------
        if approve_ratio >= 0.7:
            return Decision(
                agenda_id=agenda_id,
                proposal_id=proposal_id,
                outcome="approved",
                votes=votes,
                arbitration_required=False,
                notes="arbiter_strong_majority",
            )

        # -------------------------------------------------
        # 4️⃣ 接近門檻 → 延後（需要更多訊號）
        # -------------------------------------------------
        if 0.45 <= approve_ratio < 0.7:
            return Decision(
                agenda_id=agenda_id,
                proposal_id=proposal_id,
                outcome="deferred",
                votes=votes,
                arbitration_required=True,
                notes="arbiter_close_margin",
            )

        # -------------------------------------------------
        # 5️⃣ 高風險世界 → 保守否決
        # -------------------------------------------------
        if context.is_high_risk_world():
            return Decision(
                agenda_id=agenda_id,
                proposal_id=proposal_id,
                outcome="rejected",
                votes=votes,
                arbitration_required=False,
                notes="arbiter_risk_guard",
            )

        # -------------------------------------------------
        # 6️⃣ 其他情況 → 延後
        # -------------------------------------------------
        return Decision(
            agenda_id=agenda_id,
            proposal_id=proposal_id,
            outcome="deferred",
            votes=votes,
            arbitration_required=True,
            notes="arbiter_no_consensus",
        )

