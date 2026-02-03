# trading_core/personas/trade_defender_calculator.py

from trading_core.personas.base import (
    BaseTradePersonaSentinel,
    BaseTradePersonaExecutor,
)
from trading_core.personas.context_match import score_context
from trading_core.personas.context_profiles import DEFENDER_CONTEXT
from trading_core.personas.experience_memory import PersonaExperienceMemory, make_context_key

MEMORY = PersonaExperienceMemory("defender")

class TradeDefenderSentinel(BaseTradePersonaSentinel):
    persona_name = "defender"

    def should_activate(self, payload: dict) -> bool:
        if payload.get("risk_level") == "high":
            return True
        return abs(payload.get("change", 0)) > 0.005

    def create_executor(self):
        return TradeDefenderExecutor()



class TradeDefenderExecutor(BaseTradePersonaExecutor):

    def execute(self, payload: dict):

        risk_level = payload.get("risk_level")
        change = abs(payload.get("change", 0))

        # 明確風險 → 反對交易
        if risk_level == "high" or change > 0.01:
            context_match = score_context(DEFENDER_CONTEXT, payload)
            context_key = make_context_key(payload, context_match)
            experience_acc = MEMORY.get_accuracy(context_key)


            return {
                "stance_hint": "reject",
                "confidence": 0.75,
                "context_match": context_match,
                "experience_accuracy": experience_acc,
                "context_key": context_key,
                "rationale": "elevated risk or abnormal volatility",
                "metrics": {
                    "risk_level": risk_level,
                    "price_change": change,
                },
            }            

        # 沒有強烈風險，不出聲
        return None
