# trading_core/personas/trade_balancer_calculator.py

from trading_core.personas.base import (
    BaseTradePersonaSentinel,
    BaseTradePersonaExecutor,
)
from trading_core.personas.context_match import score_context
from trading_core.personas.context_profiles import BALANCER_CONTEXT  # ✅ 改這裡
from trading_core.personas.experience_memory import PersonaExperienceMemory, make_context_key

MEMORY = PersonaExperienceMemory("balancer")


class TradeBalancerSentinel(BaseTradePersonaSentinel):
    persona_name = "balancer"

    def should_activate(self, payload: dict) -> bool:
        change = abs(payload.get("change", 0))
        return 0.002 <= change <= 0.008

    def create_executor(self):
        return TradeBalancerExecutor()


class TradeBalancerExecutor(BaseTradePersonaExecutor):
    def execute(self, payload: dict):
        change = abs(payload.get("change", 0))
        confidence = max(0.3, 1.0 - abs(change - 0.005) * 50)

        context_match = score_context(BALANCER_CONTEXT, payload)  # ✅ 改這裡
        context_key = make_context_key(payload, context_match)
        experience_acc = MEMORY.get_accuracy(context_key)
        return {
            "stance_hint": "abstain",
            "confidence": round(confidence, 3),
            "context_match": context_match,
            "experience_accuracy": experience_acc,
            "context_key": context_key,
            "rationale": "market in neutral or transitional state",
            "metrics": {"price_change": change},
        }
