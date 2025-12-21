"""
Decision Library Writer
-----------------------
Append-only writer for governance decisions.

Design principles:
- Write-only (no read, no inference)
- Immutable input (Decision is frozen)
- Side-effect limited to LibraryWriter
- Governance-safe (no feedback to decision layer)
"""

from datetime import datetime
from typing import Optional, Dict, Any

from shared_core.governance.parliament.parliament_schema import Decision
from library.library_writer import LibraryWriter
from library.library_event import LibraryEvent
from shared_core.time_utils import utc_now_iso
import uuid

class DecisionLibraryWriter:
    """
    Persist governance decisions into Library system.

    This writer is intentionally:
    - Dumb
    - Deterministic
    - Append-only

    It exists to guarantee:
    - Auditability
    - Replayability
    - Historical accountability
    """

    RECORD_TYPE = "governance_decision"
    VERSION = "v0"

    def __init__(self, library_writer: LibraryWriter):
        """
        Parameters
        ----------
        library_writer : LibraryWriter
            Existing library writer instance (JSONL / storage backend)
        """
        self._writer = library_writer

    def write(self, decision: Decision) -> None:
        """
        Write a Decision into Library.

        This method:
        - Does NOT return anything
        - Does NOT mutate decision
        - Does NOT perform validation or inference
        """

        event = self._build_record(decision)
        self._writer.write_event(event)


    # -----------------------------
    # internal helpers
    # -----------------------------

    def _build_record(self, decision: Decision) -> LibraryEvent:
        payload = decision.to_dict()
        """
        Build a stable, versioned library record.

        Separated for:
        - Testability
        - Future schema evolution
        """

        return LibraryEvent(
            event_id=str(uuid.uuid4()),
            event_type="governance.decision",
            source="parliament",
            ts=payload.get("decided_at") or utc_now_iso(),
            payload=payload,
            meta={
                "agenda_id": decision.agenda_id,
                "proposal_id": decision.proposal_id,
                "outcome": decision.outcome,
            },
        )

