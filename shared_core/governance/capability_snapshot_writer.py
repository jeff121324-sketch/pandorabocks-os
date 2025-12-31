# shared_core/governance/capability_snapshot_writer.py

from __future__ import annotations
from typing import Optional

from shared_core.governance.capability_snapshot import CapabilitySnapshot


class CapabilitySnapshotWriter:
    """
    Append-only writer for governance capability snapshots.
    """

    def __init__(self, library):
        """
        library: 你現有的 Library 實例
        """
        self.library = library

    def write(self, snapshot: CapabilitySnapshot) -> None:
        """
        Append snapshot to library.
        MUST be append-only.
        """

        record = {
            "type": "world.capability.snapshot",
            "snapshot": snapshot.to_dict(),
        }

        # ⚠️ 關鍵：只 append
        self.library.append(record)
