# trading_core/decision_pipeline/listener.py
from trading_core.decision_pipeline.run import run_decision_pipeline
from shared_core.event_schema import PBEvent
from trading_core.state.market_regime import build_market_regime


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
        # ⭐⭐⭐ 就是這裡 ⭐⭐⭐
        indicator_snapshot = decision.get("indicator_snapshot")
        perception_health = decision.get("perception_health")

        regime = build_market_regime(
            indicator_snapshot,
            perception_health,
        )

        # 寫入 DecisionGate（世界狀態）
        bus.runtime.decision_gate.update_market_regime(regime)

        print(
            f"[MarketRegime] {regime.regime} | "
            f"tradable={regime.tradable} | "
            f"conf={regime.confidence}"
        )
        
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

