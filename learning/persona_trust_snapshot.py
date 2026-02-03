# aisop/learning/persona_trust_snapshot.py
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class PersonaTrust:
    trust: float
    evidence: Dict[str, int]


@dataclass
class PersonaTrustSnapshot:
    personas: Dict[str, PersonaTrust] = field(default_factory=dict)

    def get_trust(self, persona_name: str) -> float:
        p = self.personas.get(persona_name)
        return p.trust if p else 1.0
