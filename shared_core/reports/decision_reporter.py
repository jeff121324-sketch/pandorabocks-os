"""
Decision Reporter
-----------------
Render governance decisions into human-readable reports.

Design principles:
- Read-only
- No side effects
- No feedback to governance
- Deterministic output
"""

from typing import Dict, List


class DecisionReporter:
    """
    Translate a decision dict into human-readable text.

    This class:
    - Does NOT know Decision object
    - Only consumes dict (Decision.to_dict output)
    """

    def render(self, decision: Dict) -> str:
        lines: List[str] = []

        lines.append(f"Agenda: {decision.get('agenda_id')}")
        lines.append(f"Proposal: {decision.get('proposal_id')}")
        lines.append(f"Outcome: {decision.get('outcome').upper()}")
        lines.append("")

        # Reasoning
        if decision.get("notes"):
            lines.append("Reason:")
            lines.append(f"- {decision.get('notes')}")
            lines.append("")

        # Votes
        lines.append("Votes:")
        for v in decision.get("votes", []):
            role = v.get("role")
            stance = v.get("stance")
            confidence = v.get("confidence")
            lines.append(f"- {role}: {stance} (confidence={confidence})")

        lines.append("")
        lines.append(
            f"Arbitration required: "
            f"{'Yes' if decision.get('arbitration_required') else 'No'}"
        )

        return "\n".join(lines)
