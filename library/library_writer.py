# aisop/library/library_writer.py
from pathlib import Path
import json
from datetime import datetime, timezone
import threading
from library.library_event import LibraryEvent

class LibraryWriter:
    """
    Library Writer v1
    =================
    - Append-only
    - Input: PBEvent (validated)
    - Output: daily jsonl
    """

    def __init__(self, library_root: Path):
        self.library_root = library_root
        self.events_dir = library_root / "events"

        self.events_dir.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()

        print(f"[LibraryWriter] 📚 Library ready at {self.events_dir}")


    def write_event(self, event: LibraryEvent):
        if not isinstance(event, LibraryEvent):
            raise TypeError("LibraryWriter only accepts LibraryEvent")

        # ✅ 使用事件本身時間（不是 now）
        ts = datetime.fromisoformat(event.ts)

        year = ts.strftime("%Y")
        month = ts.strftime("%m")
        day = ts.strftime("%Y-%m-%d")

        # ✅ 年 / 月 目錄
        dir_path = self.events_dir / year / month
        dir_path.mkdir(parents=True, exist_ok=True)

        path = dir_path / f"{day}.jsonl"

        # ✅ thread-safe append
        with self._lock:
            with open(path, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")

    # === 預留擴充（現在不啟用） ===

    def flush(self):
        """
        v1 不需要 flush（每次 write 即落盤）
        v2 可升級為 buffer / batch
        """
        pass
