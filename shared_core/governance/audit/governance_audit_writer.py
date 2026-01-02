# shared_core/governance/audit/governance_audit_writer.py

import json
from pathlib import Path
from datetime import datetime
from typing import Any

from shared_core.governance.arbiter.schema import PersonaTrustSnapshot
from shared_core.governance.chair.chair_supervisor import ChairDirective


class GovernanceAuditWriter:
    """
    Write-only audit log.
    No read, no side effect.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _write(self, name: str, payload: Any):
        ts = datetime.now().strftime("%Y%m%d")
        path = self.base_dir / f"{name}_{ts}.jsonl"

        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, default=str) + "\n")

    def record_snapshot(self, snapshot: PersonaTrustSnapshot):
        self._write("trust_snapshot", snapshot.__dict__)

    def record_chair_directive(self, directive: ChairDirective):
        self._write("chair_directive", directive.__dict__)
