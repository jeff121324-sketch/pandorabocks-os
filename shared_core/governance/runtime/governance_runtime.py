from shared_core.event_schema import PBEvent
from pandora_core.event_bus import EventBus

class GovernanceRuntime:
    def __init__(
        self,
        engine,
        snapshot_handler,
        decision_persistence_handler,
        parliament,
    ):
        self.engine = engine
        self.snapshot_handler = snapshot_handler
        self.decision_persistence_handler = decision_persistence_handler
        self.parliament = parliament

        # 🚫 注意：這裡「不能」建立 TradeSignalHandler
        self.trade_signal_handler = None

    def on_load(self, bus):
        from shared_core.governance.handlers.trade_signal_handler import (
            TradeSignalHandler,
        )

        # ✅ 在這裡才有 bus，可以安全建立 handler
        self.trade_signal_handler = TradeSignalHandler(
            bus,
            self.parliament,
        )

        # 1️⃣ 治理快照 → 議會
        bus.subscribe(
            "system.governance.snapshot.created",
            self.snapshot_handler.handle,
        )

        # 2️⃣ 交易人格訊號 → 議會（關鍵）
        bus.subscribe(
            "persona.signal.trade",
            self.trade_signal_handler.handle,
        )

        # 3️⃣ 議會決策 → Library
        bus.subscribe(
            "system.governance.decision.created",
            self.decision_persistence_handler.handle,
        )

        print("[GovernanceRuntime] 🔔 subscribed governance events")

