from shared_core.governance.parliament.parliament_schema import (
    Proposal,
    Vote,
)
from shared_core.event_schema import PBEvent
import uuid


class TradeSignalHandler:
    """
    Bridge: persona.signal.trade → governance decision personas
    """

    def __init__(self, bus, parliament):
        self.bus = bus
        self.parliament = parliament

        bus.subscribe("persona.signal.trade", self.on_trade_signal)
        
    def handle(self, event):
        return self.on_trade_signal(event)

    def on_trade_signal(self, event):
        # -------------------------
        # 1️⃣ 事件正規化
        # -------------------------
        if isinstance(event, dict):
            payload = event
        else:
            payload = event.payload

        signal = payload["signal"]

        # -------------------------
        # 2️⃣ 建立 Proposal（議程）
        # -------------------------
        proposal = Proposal(
            agenda_id="trade.decision",
            proposal_id=str(uuid.uuid4()),
            proposer_role=payload.get("target_persona", "unknown"),
            action=payload["signal"]["stance_hint"],   # buy / sell / abstain
            constraints={},
        )
        # -------------------------
        # 3️⃣ 建立 Vote（人格投票）
        # -------------------------
        vote = Vote(
            agenda_id=proposal.agenda_id,
            proposal_id=proposal.proposal_id,
            role=payload.get("target_persona", "unknown"),
            stance=signal.get("stance_hint", "abstain"),
            confidence=float(signal.get("confidence", 0.0)),
            rationale=signal.get("rationale", ""),
        )

        # =====================================================
        # 4️⃣ 呼叫 ParliamentEngine（純治理）
        # =====================================================
        decision = self.parliament.evaluate(
            proposal=proposal,
            votes=[vote],
        )

        if not decision:
            return

        # =====================================================
        # 5️⃣ 決策結果 → PBEvent（⚠️ 一定要是 PBEvent）
        # =====================================================
        if hasattr(decision, "outcome"):
            result = decision.outcome
        elif hasattr(decision, "result"):
            result = decision.result
        elif hasattr(decision, "action"):
            result = decision.action
        elif hasattr(decision, "stance"):
            result = decision.stance
        else:
            raise AttributeError(
                f"Decision missing result field: {decision.__dict__}"
            )

        decision_payload = {
            "agenda_id": decision.agenda_id,
            "result": result,   # ← 這一行你現在缺的就是它
            "proposal_id": decision.proposal_id,

            # 🟢 Business-level（給 persistence / narration / output 用）
            "decision": {
                "decision": result,
                "confidence": getattr(decision, "confidence", 0.0),
                "notes": getattr(decision, "notes", None),
                "arbitration_required": getattr(decision, "arbitration_required", False),
            },
        }


        # 附加資訊（可有可無）
        if hasattr(decision, "notes"):
            decision_payload["notes"] = decision.notes
        if hasattr(decision, "arbitration_required"):
            decision_payload["arbitration_required"] = decision.arbitration_required

        # 🔴 關鍵：payload 外面一定要包一層 decision
        self.bus.publish(
            PBEvent(
                type="system.governance.decision.created",
                payload=decision_payload,
                source="governance.parliament",
            )
        )

