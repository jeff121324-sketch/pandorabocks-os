class GovernanceRuntime:
    def __init__(self, engine, snapshot_handler, decision_persistence_handler):
        self.engine = engine
        self.snapshot_handler = snapshot_handler
        self.decision_persistence_handler = decision_persistence_handler

    def on_load(self, bus):
        # 1️⃣ 治理快照 → 議會
        bus.subscribe(
            "system.governance.snapshot.created",
            self.snapshot_handler.handle,
        )

        # 2️⃣ 議會決策 → Library
        bus.subscribe(
            "system.governance.decision.created",
            self.decision_persistence_handler.handle,
        )

        print("[GovernanceRuntime] 🔔 subscribed governance events")
