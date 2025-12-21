from typing import List, Literal, Dict, Any
from dataclasses import dataclass, field


RiskLevel = Literal["low", "medium", "high"]


@dataclass
class AdvisorConstraints:
    """
    顧問模式的硬性邊界
    """
    no_decision: bool = True
    no_execution: bool = True
    no_external_action: bool = True


@dataclass
class AdvisorOutput:
    """
    Advisor Output Schema v1
    AI 在 A 模式下「唯一合法」的輸出格式
    """

    summary: str
    interpreted_intent: str
    confidence: float                # 0.0 ~ 1.0
    risk_level: RiskLevel
    risk_notes: List[str] = field(default_factory=list)
    suggested_next_steps: List[str] = field(default_factory=list)
    constraints: AdvisorConstraints = field(default_factory=AdvisorConstraints)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "advisor_output": {
                "summary": self.summary,
                "interpreted_intent": self.interpreted_intent,
                "confidence": round(float(self.confidence), 3),
                "risk_level": self.risk_level,
                "risk_notes": self.risk_notes,
                "suggested_next_steps": self.suggested_next_steps,
                "constraints": {
                    "no_decision": self.constraints.no_decision,
                    "no_execution": self.constraints.no_execution,
                    "no_external_action": self.constraints.no_external_action,
                },
            }
        }
