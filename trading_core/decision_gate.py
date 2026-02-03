# trading_core/decision_gate.py

class TradingDecisionGate:
    def __init__(self):
        self.latest_governance = None
        self.latest_market_regime = None
        
    def update_market_regime(self, regime_snapshot):
        self.latest_market_regime = regime_snapshot

    def update_governance(self, payload: dict):
        self.latest_governance = payload

    def evaluate(self, persona_signal: dict):
        # 🌍 世界狀態優先
        if self.latest_market_regime and not self.latest_market_regime.tradable:
            return "BLOCK", "market_not_tradable"
        
        if not self.latest_governance:
            return "BLOCK", "no_governance_decision"

        result = self.latest_governance.get("result")
        if result != "approve":
            return "BLOCK", result

        decision_block = self.latest_governance.get("decision", {})
        gov_conf = decision_block.get("confidence", 1.0)

        adjusted = persona_signal.get("confidence", 0.0) * gov_conf
        return "ALLOW", adjusted
