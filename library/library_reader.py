# aisop/library/library_reader.py
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Union


class LibraryReader:
    """
    LibraryReader v1 (Read-only, Immutable)
    ======================================
    ✅ 只讀 events/ + index/
    ✅ 不 import Runtime / Gateway / Replay
    ✅ 回傳 dict（不回 PBEvent、不建立行為物件）
    ✅ generator-based，避免一次載入大量事件

    Directory layout (expected):
      library_root/
        events/YYYY/MM/YYYY-MM-DD.jsonl
        index/
          stats.json
          by_type.json      (optional, v1 legacy)
          by_source.json    (optional, v1 legacy)
          by_day.json       (optional, v1 legacy)
    """

    def __init__(self, library_root: Union[str, Path]):
        self.library_root = Path(library_root)
        self.events_root = self.library_root / "events"
        self.index_root = self.library_root / "index"

    # ------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------
    def get_stats(self) -> Dict[str, Any]:
        """
        只讀 index/stats.json。
        不掃 events、不補資料、不推導。
        """
        stats_path = self.index_root / "stats.json"
        if not stats_path.exists():
            # v1: 明確 fail fast，避免學習腦偷偷掃全庫造成性能事故
            raise FileNotFoundError(
                f"[LibraryReader] stats.json not found: {stats_path}. "
                f"Run LibraryIndex.build()+flush() first."
            )

        with open(stats_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def iter_events(
        self,
        *,
        day: Optional[str] = None,
        type: Optional[Union[str, Sequence[str]]] = None,
        source: Optional[Union[str, Sequence[str]]] = None,
        limit: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        迭代事件（只讀、串流）。
        - day: "YYYY-MM-DD"
        - type: "market.kline" 或 ["a", "b", ...]
        - source: "replay/live/..." 或 ["replay", "live", ...]
        - limit: 最多 yield 幾筆

        回傳：dict（原始 record）
        """
        if limit is not None and limit <= 0:
            return iter(())  # type: ignore[return-value]

        type_set = _to_set(type)
        source_set = _to_set(source)

        count = 0
        for path in self._iter_event_files(day=day):
            for rec in self._iter_jsonl(path):
                if type_set is not None:
                    et = rec.get("event_type") or rec.get("type")
                    if et not in type_set:
                        continue

                if source_set is not None:
                    src = rec.get("source")
                    if src not in source_set:
                        continue

                yield rec
                count += 1
                if limit is not None and count >= limit:
                    return

    def sample(
        self,
        *,
        n: int = 100,
        by: str = "day",
        seed: Optional[int] = None,
        day: Optional[str] = None,
        type: Optional[Union[str, Sequence[str]]] = None,
        source: Optional[Union[str, Sequence[str]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        抽樣（只讀，不建立索引、不回寫）。
        - by="day": 以 stats.json 的 files/day 做「按日抽樣」策略（優先用 index，避免全掃）
        - by="type": 以 by_type.json 的 key 選一組 type，再從 events 串流抽樣（不做重索引）

        你也可以加上 day/type/source 限縮抽樣範圍（仍保持只讀）。

        回傳：List[dict]
        """
        if n <= 0:
            return []

        rng = random.Random(seed)

        # 額外 filter
        type_set = _to_set(type)
        source_set = _to_set(source)

        if by not in ("day", "type"):
            raise ValueError(f"[LibraryReader] sample(by=...) must be 'day' or 'type', got: {by}")

        # ---- by=day (index-first) ----
        if by == "day":
            # 若指定 day，直接從該日檔案做 reservoir sampling（不碰 index）
            if day is not None:
                return self._sample_from_day_file(day, n=n, rng=rng, type_set=type_set, source_set=source_set)

            # 否則：用 stats.json 取得有哪些 day 與各 day 的 event count
            stats = self.get_stats()
            files = (stats or {}).get("files", {})
            if not isinstance(files, dict) or not files:
                return []

            # 以「count」作為權重（常見：大日子被多抽到；符合資料分布）
            # 如果你想要「每天等機率」，把 weights 改成 1 即可。
            days: List[str] = []
            weights: List[float] = []
            for d, info in files.items():
                if not isinstance(info, dict):
                    continue
                c = info.get("count", 0)
                if isinstance(c, int) and c > 0:
                    days.append(d)
                    weights.append(float(c))

            if not days:
                return []

            # 反覆抽 day，再從該 day 檔案抽一些事件（reservoir），直到累積 n
            out: List[Dict[str, Any]] = []
            # 每次從一天最多抽的量，避免單一天壟斷
            per_day_cap = max(5, min(200, n // 3 if n >= 30 else n))

            safety = 0
            while len(out) < n and safety < n * 10:
                pick_day = rng.choices(days, weights=weights, k=1)[0]
                chunk = self._sample_from_day_file(
                    pick_day,
                    n=min(per_day_cap, n - len(out)),
                    rng=rng,
                    type_set=type_set,
                    source_set=source_set,
                )
                out.extend(chunk)
                safety += 1

                # 若 filter 太嚴格導致抽不到，就會自然停滯；這裡用 safety 防止死迴圈
                if safety >= n * 10:
                    break

            return out[:n]

        # ---- by=type (type-key-first, stream sample) ----
        # 選一組候選 type（只用 index 的 keys，不依賴 event_id mapping）
        chosen_types: Optional[set] = None
        if type_set is None:
            by_type_path = self.index_root / "by_type.json"
            if by_type_path.exists():
                try:
                    with open(by_type_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, dict) and data:
                        keys = [k for k in data.keys() if isinstance(k, str) and k]
                        if keys:
                            # 選最多 12 個 type 作為抽樣候選，避免全庫掃描仍偏向「多樣性」
                            k = min(12, len(keys))
                            chosen_types = set(rng.sample(keys, k=k))
                except Exception:
                    chosen_types = None

        # 若 caller 指定了 type，或 by_type.json 不存在，就回到「filter + reservoir」全域抽樣
        if chosen_types is None:
            chosen_types = type_set  # 可能為 None

        # reservoir sampling across stream
        reservoir: List[Dict[str, Any]] = []
        seen = 0

        for rec in self.iter_events(day=day, source=source, limit=None):
            # type filter
            et = rec.get("event_type") or rec.get("type")
            if chosen_types is not None and et not in chosen_types:
                continue
            if type_set is not None and et not in type_set:
                continue
            if source_set is not None:
                src = rec.get("source")
                if src not in source_set:
                    continue

            seen += 1
            if len(reservoir) < n:
                reservoir.append(rec)
            else:
                j = rng.randrange(seen)
                if j < n:
                    reservoir[j] = rec

        return reservoir

    # ------------------------------------------------------------
    # Internal helpers (read-only)
    # ------------------------------------------------------------
    def _iter_event_files(self, *, day: Optional[str] = None) -> Iterator[Path]:
        """
        events/YYYY/MM/YYYY-MM-DD.jsonl
        """
        if day is not None:
            # 精準定位單日檔案
            y, m, _ = day.split("-")
            path = self.events_root / y / m / f"{day}.jsonl"
            if path.exists():
                yield path
            return

        if not self.events_root.exists():
            return

        for year_dir in sorted(self.events_root.iterdir()):
            if not year_dir.is_dir():
                continue
            for month_dir in sorted(year_dir.iterdir()):
                if not month_dir.is_dir():
                    continue
                for file in sorted(month_dir.glob("*.jsonl")):
                    yield file

    def _iter_jsonl(self, path: Path) -> Iterator[Dict[str, Any]]:
        """
        只讀 jsonl 串流。
        """
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if isinstance(rec, dict):
                    yield rec

    def _sample_from_day_file(
        self,
        day: str,
        *,
        n: int,
        rng: random.Random,
        type_set: Optional[set],
        source_set: Optional[set],
    ) -> List[Dict[str, Any]]:
        """
        對單日檔案做 reservoir sampling（只讀）。
        """
        y, m, _ = day.split("-")
        path = self.events_root / y / m / f"{day}.jsonl"
        if not path.exists():
            return []

        reservoir: List[Dict[str, Any]] = []
        seen = 0
        for rec in self._iter_jsonl(path):
            et = rec.get("event_type") or rec.get("type")
            if type_set is not None and et not in type_set:
                continue
            if source_set is not None:
                src = rec.get("source")
                if src not in source_set:
                    continue

            seen += 1
            if len(reservoir) < n:
                reservoir.append(rec)
            else:
                j = rng.randrange(seen)
                if j < n:
                    reservoir[j] = rec

        return reservoir


def _to_set(v: Optional[Union[str, Sequence[str]]]) -> Optional[set]:
    if v is None:
        return None
    if isinstance(v, str):
        return {v}
    return {x for x in v if isinstance(x, str)}
