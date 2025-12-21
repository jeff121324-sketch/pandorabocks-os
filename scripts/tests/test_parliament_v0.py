import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pathlib import Path
from shared_core.governance.parliament import Proposal, Vote, ParliamentEngine

rules_path = Path("shared_core/governance/parliament/rules.yaml")
engine = ParliamentEngine(rules_path=rules_path)

proposal = Proposal(
    agenda_id="A-001",
    proposal_id="P-001",
    proposer_role="Proposer",
    action={"intent": "open_position", "symbol": "BTC/USDT"},
    constraints={"max_risk": 0.01},
)

votes = [
    Vote(agenda_id="A-001", proposal_id="P-001", role="Proposer", stance="approve", confidence=0.70, rationale="signal ok"),
    Vote(agenda_id="A-001", proposal_id="P-001", role="RiskExaminer", stance="approve", confidence=0.55, rationale="risk acceptable"),
    Vote(agenda_id="A-001", proposal_id="P-001", role="StabilityGuard", stance="abstain", confidence=0.40, rationale="needs more data"),
]

decision = engine.evaluate(proposal, votes)
print("DECISION:", decision.outcome, decision.arbitration_required, decision.notes)
