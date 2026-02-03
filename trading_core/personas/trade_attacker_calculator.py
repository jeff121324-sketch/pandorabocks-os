from trading_core.personas.base import (
    BaseTradePersonaSentinel,
    BaseTradePersonaExecutor,
)
from trading_core.personas.context_match import score_context
from trading_core.personas.context_profiles import ATTACKER_CONTEXT

from trading_core.personas.experience_memory import PersonaExperienceMemory, make_context_key

MEMORY = PersonaExperienceMemory("attacker")

class TradeAttackerSentinel(BaseTradePersonaSentinel):
    persona_name = "attacker"

    def should_activate(self, payload: dict) -> bool:
        if "close" not in payload:
            return False
        return abs(payload.get("change", 0)) > 0.002

    def create_executor(self):
        return TradeAttackerExecutor()


class TradeAttackerExecutor(BaseTradePersonaExecutor):

    def execute(self, payload: dict):
        confidence = min(abs(payload.get("change", 0)) * 10, 1.0)
        if confidence < 0.4:
            return None

        context_match = score_context(ATTACKER_CONTEXT, payload)
        context_key = make_context_key(payload, context_match)
        experience_acc = MEMORY.get_accuracy(context_key)


        return {
            "stance_hint": "approve",
            "confidence": round(confidence, 3),
            "context_match": context_match,
            "experience_accuracy": experience_acc,
            "context_key": context_key,
            "rationale": "short-term momentum detected",
            "metrics": {
                "price_change": payload.get("change"),
            },
        }