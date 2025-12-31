# shared_core/governance/capability_snapshot.py

from __future__ import annotations

import json
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Dict, Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_from_dict(data: Dict[str, Any]) -> str:
    """
    IMPORTANT:
    - 使用 sort_keys=True
    - 使用固定 separators
    - 確保 checksum 穩定、可重現
    """
    raw = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class CapabilitySnapshot:
    """
    Governance-level immutable snapshot.
    This object MUST NOT contain:
    - runtime state
    - plugin instances
    - live references

    It records ONLY governance facts.
    """

    def __init__(
        self,
        *,
        source: str,
        worlds: Dict[str, Dict[str, Any]],
        timestamp: str | None = None,
        snapshot_id: str | None = None,
    ):
        self.snapshot_id = snapshot_id or str(uuid.uuid4())
        self.timestamp = timestamp or _utc_now_iso()
        self.source = source

        # Defensive copy: prevent external mutation
        self.worlds = json.loads(json.dumps(worlds))

        # checksum is computed AFTER all fields are ready
        self.checksum = self._compute_checksum()

    def _compute_checksum(self) -> str:
        payload = {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "source": self.source,
            "worlds": self.worlds,
        }
        return _sha256_from_dict(payload)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "source": self.source,
            "worlds": self.worlds,
            "checksum": self.checksum,
        }

    def to_json(self, *, pretty: bool = False) -> str:
        if pretty:
            return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
        return json.dumps(self.to_dict(), ensure_ascii=False)

    def to_yaml(self) -> str:
        try:
            import yaml
        except ImportError as e:
            raise RuntimeError(
                "PyYAML is required for YAML export: pip install pyyaml"
            ) from e

        return yaml.safe_dump(
            self.to_dict(),
            sort_keys=False,
            allow_unicode=True,
        )

    def __repr__(self) -> str:
        return (
            f"<CapabilitySnapshot "
            f"id={self.snapshot_id} "
            f"worlds={len(self.worlds)} "
            f"checksum={self.checksum[:8]}…>"
        )
