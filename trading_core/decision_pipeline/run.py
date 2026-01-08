# trading_core/decision_pipeline/run.py

def run_decision_pipeline(event):
    """
    A-MODE Decision Pipeline (A+B schema, v1)

    A 層（core）：
    - 100% deterministic
    - 僅依賴 event.payload
    - 可被 replay / hash / snapshot

    B 層（extension）：
    - 目前為結構占位
    - 不使用 random / time
    - 不影響一致性驗證
    """

    payload = event.payload
    close = payload.get("close")

    if close is None:
        return None

    decision = {
        # ==========================
        # A 層：Deterministic Core
        # ==========================
        "core": {
            "action": "HOLD",
            "price": close,
            "symbol": payload.get("symbol"),
            "interval": payload.get("interval"),
        },

        # ==========================
        # B 層：Extension（占位）
        # ==========================
        "extension": {
            "mode": "bootstrap",
            "note": "A-mode deterministic core (no exploration)"
        }
    }

    return decision
