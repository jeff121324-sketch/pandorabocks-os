"""
AIManager v3 — 專管 AI plugin（Attacker / Defender / Arbiter / AISOPRuntime）
不負責 TradingRuntime、DataRuntime、SystemRuntime。
"""

from llm_registry import LLMRegistry

class AIManager:
    def __init__(self, bus):
        self.bus = bus
        self.plugins = []
        self.llm_registry = LLMRegistry()

    def register(self, plugin):
        self.plugins.append(plugin)
        print(f"[AIManager] 🔌 Registered plugin: {plugin.__class__.__name__}")

    def tick_all(self):
        for p in self.plugins:
            try:
                if hasattr(p, "tick"):
                    p.tick()
            except Exception as e:
                print(f"[AIManager] ❌ Plugin error in {p.__class__.__name__}: {e}")

    # === 對外統一介面 ===

    def get_llm(self, *, role: str, requirement: dict):
        return self.llm_registry.get(role=role, requirement=requirement)

    # === 便利方法（可選） ===

    def get_auditor_llm(self):
        return self.get_llm(
            role="auditor",
            requirement={
                "latency": "low",
                "reasoning": "shallow",
                "cost": "low",
                "risk": "low"
            }
        )
