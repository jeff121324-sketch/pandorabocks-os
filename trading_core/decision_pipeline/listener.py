# trading_core/decision_pipeline/listener.py

from trading_core.decision_pipeline.run import run_decision_pipeline

MODULE = "DecisionListener"

def on_market_kline(event):
    print("[DECISION] listener triggered")   # ⭐ 驗收用

    decision = run_decision_pipeline(event)

    if decision is None:
        return

    print(f"[DECISION][A-MODE] {decision}")
