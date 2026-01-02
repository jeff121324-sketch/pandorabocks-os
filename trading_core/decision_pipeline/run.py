# trading_core/decision_pipeline/run.py

def run_decision_pipeline(event):
    """
    A 模式 v0
    - 只根據 market.kline 做最簡單決策
    - 不讀 state
    - 不碰 risk
    """

    payload = event.payload
    close = payload.get("close")

    if close is None:
        return None

    # 🔹 A 模式：極簡決策（只是為了驗證管線）
    decision = {
        "action": "HOLD",
        "confidence": 0.5,
        "reason": "A-mode bootstrap",
        "price": close,
        "symbol": payload.get("symbol"),
        "interval": payload.get("interval"),
    }

    return decision
