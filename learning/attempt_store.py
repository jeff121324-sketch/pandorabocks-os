# learning/attempt_store.py
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import json
from typing import Dict, Any


class AttemptStore:
    def __init__(self, base_dir: str | Path = "library/learning/attempts"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _today_path(self) -> Path:
        day = datetime.now(timezone.utc).strftime("%Y%m%d")
        return self.base_dir / f"attempts_{day}.jsonl"

    def append(self, attempt: Dict[str, Any]) -> Path:
        path = self._today_path()
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(attempt, ensure_ascii=False) + "\n")
        return path
