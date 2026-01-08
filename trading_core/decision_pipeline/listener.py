# trading_core/decision_pipeline/listener.py
from trading_core.decision_pipeline.run import run_decision_pipeline
from shared_core.event_schema import PBEvent
MODULE = "DecisionListener"

def make_on_market_kline(bus, observer=None):
    """
    Factory: create a market.kline listener bound to a specific bus.

    Why:
    - Replay events do NOT carry event.bus
    - Decision must be published to a known, deterministic bus
    """

    def on_market_kline(event):
        print("[DECISION] listener triggered")

        decision = run_decision_pipeline(event)
        if decision is None:
            return

         # 👁️ 側錄給 verifier（不走 bus）
        if observer:
            observer(decision)

        # 🏛️ 正式交給治理系統
        bus.publish(
            PBEvent(
                type="system.decision.proposed",
                payload={"decision": decision},
            )
        )


        print(f"[DECISION][A-MODE] proposed -> {decision}")

    return on_market_kline

