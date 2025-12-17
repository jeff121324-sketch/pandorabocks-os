# library/replay/library_replay_source.py

import json
from pathlib import Path
from typing import Iterator, Dict, Any

class LibraryReplaySource:
    """
    Library → Replay 專用讀取器（只讀）
    - 不寫 EventBus
    - 不做 ingest
    - 只負責把 LibraryEvent 還原成 dict
    """

    def __init__(self, library_root: Path):
        self.library_root = Path(library_root)

    def iter_day(self, day: str) -> Iterator[Dict[str, Any]]:
        """
        day: YYYY-MM-DD
        """
        year, month, _ = day.split("-")
        path = self.library_root / "events" / year / month / f"{day}.jsonl"

        if not path.exists():
            raise FileNotFoundError(path)

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    yield json.loads(line)
                except Exception:
                    continue

    def iter_range(self, start_day: str, end_day: str):
        """
        簡單版：先只支援單日（之後再擴）
        """
        if start_day != end_day:
            raise NotImplementedError("range replay not implemented yet")
        yield from self.iter_day(start_day)
