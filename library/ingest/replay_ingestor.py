# library/library_ingestor.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Any
from pathlib import Path

from library.library_event import LibraryEvent
from library.library_writer import LibraryWriter


@dataclass
class LibraryIngestStats:
    def __init__(self):
        self.total = 0
        self.ok = 0
        self.errors = 0

    def snapshot(self):
        return {
            "total": self.total,
            "ok": self.ok,
            "errors": self.errors,
        }



class LibraryIngestor:
    """
    LibraryIngestor v1 (Full Capability, Clean Responsibility)

    職責：
    - 接收 PBEvent / PBEvent-like
    - 轉換為 LibraryEvent
    - 寫入 LibraryWriter
    - 收集 ingest 統計資訊

    ❌ 不碰 EventBus
    ❌ 不處理 replay 時間
    ❌ 不知道 ReplayEngine / Runtime
    """

    def __init__(self, writer: LibraryWriter):
        self.writer = writer
        self.stats = LibraryIngestStats()

    def ingest_event(self, ev: Any) -> bool:
        """
        ev: PBEvent 或具有 event_id / event_type / ts / source / payload / meta 的物件
        return: 是否成功寫入
        """
        self.stats.total += 1

        try:
            lib_event = LibraryEvent.from_pbevent(ev)
            self.writer.write_event(lib_event)
            self.stats.ok += 1
            return True

        except Exception:
            self.stats.errors += 1
            return False

    def get_stats(self):
        return self.stats.snapshot()
