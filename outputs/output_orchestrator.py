"""
Decision Output Orchestrator

This module is the single exit point for finalized decisions.

Responsibilities:
- Apply locale formatting
- Dispatch payloads to output channels

Non-responsibilities:
- No decision making
- No retries or fallbacks
- No routing or policy logic
- No mutation of decision payload
"""
from outputs.output_schema import build_canonical
from typing import Dict, List, Any


class DecisionOutputOrchestrator:
    """
    Orchestrates finalized decisions to multiple output channels
    with locale-aware formatting.
    """

    def __init__(
        self,
        *,
        formatter,
        outputs: List[Any],
        metadata: Dict[str, Any] | None = None,
    ):
        """
        Args:
            formatter:
                Locale formatter instance (e.g. ZhTWFormatter, EnFormatter)
            outputs:
                List of output channel instances (must implement send(payload))
            metadata:
                Optional static metadata appended to every output
                (e.g. system version, environment)
        """
        self.formatter = formatter
        self.outputs = outputs
        self.metadata = metadata or {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def dispatch(self, decision: Dict[str, Any]) -> None:
        """
        Dispatch a finalized decision.

        Args:
            decision:
                Finalized decision payload from governance layer.
        """
        payload = self._build_payload(decision)

        for output in self.outputs:
            output.emit(payload)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_payload(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build the final output payload.

        This method MUST NOT modify the decision itself.
        """
        formatted = self.formatter.format(decision)

        if not self.metadata:
            return formatted

        # Metadata is appended, not merged destructively
        return {
            "meta": self.metadata,
            "data": build_canonical(formatted),
        }