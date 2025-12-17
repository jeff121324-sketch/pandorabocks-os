from pathlib import Path
import json
from collections import defaultdict
from datetime import datetime
from typing import Dict, Any

class LibraryIndex:
    """
    LibraryIndex v2
    - 只讀 Library events（jsonl）
    - 不修改事件
    - 不依賴 PBEvent / EventBus
    - 提供學習 / replay / 分析用索引
    """

    def __init__(self, library_root: Path):
        self.library_root = Path(library_root)
        self.events_root = self.library_root / "events"
        self.index_root = self.library_root / "index"
        self.index_root.mkdir(parents=True, exist_ok=True)

        # v1 indexes（保留）
        self.by_type = defaultdict(list)
        self.by_source = defaultdict(list)
        self.by_day = defaultdict(list)

        # v2 stats（新增）
        self.stats = {
            "files": {},        # per-file stats
            "summary": {        # overall stats
                "total_events": 0,
                "total_files": 0,
            }
        }
    # --------------------------------------------------
    # 主入口
    # --------------------------------------------------
    def build(self):
        """
        全量掃描 events 目錄，重建 index
        """
        for path in self._iter_event_files():
            self._index_file(path)

    # --------------------------------------------------
    # 掃描 events
    # --------------------------------------------------
    def _iter_event_files(self):
        """
        events/YYYY/MM/YYYY-MM-DD.jsonl
        """
        if not self.events_root.exists():
            return

        for year_dir in self.events_root.iterdir():
            if not year_dir.is_dir():
                continue

            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir():
                    continue

                for file in month_dir.glob("*.jsonl"):
                    yield file

    # --------------------------------------------------
    # 索引單一檔案
    # --------------------------------------------------
    def _index_file(self, path: Path):
        day = path.stem  # YYYY-MM-DD

        file_stat = {
            "path": str(path),
            "count": 0,
            "size_bytes": path.stat().st_size,
            "first_ts": None,
            "last_ts": None,
        }

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line)
                except Exception:
                    continue

                eid = record.get("event_id")
                etype = record.get("event_type")
                source = record.get("source")

                # ✅ v2：支援多種時間欄位
                ts = None
                for key in ("timestamp", "ts", "time"):
                    if key in record and record[key]:
                        ts = record[key]
                        break

                # ---- v1 行為（保留）----
                if eid:
                    self.by_day[day].append(eid)
                if etype:
                    self.by_type[etype].append(eid)
                if source:
                    self.by_source[source].append(eid)

                # ---- v2 stats ----
                file_stat["count"] += 1
                self.stats["summary"]["total_events"] += 1

                if ts:
                    if file_stat["first_ts"] is None:
                        file_stat["first_ts"] = ts
                    file_stat["last_ts"] = ts

        self.stats["files"][day] = file_stat
        self.stats["summary"]["total_files"] += 1

    # --------------------------------------------------
    # 寫出 index
    # --------------------------------------------------
    def flush(self):
        self._write("by_type.json", self.by_type)
        self._write("by_source.json", self.by_source)
        self._write("by_day.json", self.by_day)
        self._write("stats.json", self.stats)

    def _write(self, name: str, data: Dict[str, Any]):
        path = self.index_root / name
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[LibraryIndex] 🧭 wrote {path}")
