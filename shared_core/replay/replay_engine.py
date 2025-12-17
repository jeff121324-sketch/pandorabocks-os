import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional
from datetime import datetime
from typing import Optional, Callable, Any, Literal
from shared_core.event_schema import PBEvent

ReplayTarget = Literal["bus", "library", "both"]

class ReplayEngine:
    """
    ReplayEngine v2

    功能：
    - 從檔案讀 raw dict / PBEvent dict
    - 經由 PerceptionGateway → PBEvent
    - 可選擇：
        * replay()      → 真正 publish 到 bus
        * iter_events() → 只產生 PBEvent，不 publish（給訓練 / 分析）
        * build_sequences() → 將事件組成滑動視窗序列（AI Dataset）

    支援檔案格式：
    - .jsonl  每行一筆 dict
    - .json   list[dict] 或單一 dict
    - .parquet / .feather  (若有 pandas)
    """

    def __init__(
        self,
        bus,
        gateway,
        default_key: str = "market.kline",
        ingestor: Optional[Any] = None,
    ):
        """
        gateway : PerceptionGateway
        bus     : EventBus / ZeroCopyEventBus
        default_key : 給 gateway.process() 用的預設 key
        """
        self.gateway = gateway
        self.bus = bus
        self.default_key = default_key

        # ✅ 新增：LibraryIngestor（可不傳，不影響原本）
        self.ingestor = ingestor
    # ============================================================
    # 內部工具：讀檔 & 解析 raw records
    # ============================================================
    def _iter_jsonl(self, path: Path) -> Iterator[Dict[str, Any]]:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception as e:
                    print(f"[ReplayEngine] ❌ JSONL decode error @ {path}: {e}")
                    continue

    def _iter_json(self, path: Path) -> Iterator[Dict[str, Any]]:
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[ReplayEngine] ❌ JSON decode error @ {path}: {e}")
            return

        if isinstance(data, dict):
            # 單一 dict
            yield data
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    yield item
        else:
            print(f"[ReplayEngine] ⚠ 不支援的 JSON 結構: {type(data)}")

    def _iter_parquet_or_feather(self, path: Path) -> Iterator[Dict[str, Any]]:
        try:
            import pandas as pd  # type: ignore
        except ImportError:
            print(f"[ReplayEngine] ⚠ 需要 pandas 才能讀取 {path.suffix} 檔案")
            return

        try:
            if path.suffix.lower() == ".parquet":
                df = pd.read_parquet(path)
            else:
                # feather / ftr
                df = pd.read_feather(path)
        except Exception as e:
            print(f"[ReplayEngine] ❌ pandas 讀取錯誤 @ {path}: {e}")
            return

        for rec in df.to_dict(orient="records"):
            if isinstance(rec, dict):
                yield rec

    def _iter_raw_records(self, path: str) -> Iterator[Dict[str, Any]]:
        p = Path(path)
        suffix = p.suffix.lower()

        if suffix in (".jsonl", ".log"):
            yield from self._iter_jsonl(p)
        elif suffix == ".json":
            yield from self._iter_json(p)
        elif suffix in (".parquet", ".feather", ".ftr"):
            yield from self._iter_parquet_or_feather(p)
        else:
            # 預設當 JSONL 試試看
            print(f"[ReplayEngine] ⚠ 不認識的副檔名 {suffix}，以 JSONL 模式嘗試")
            yield from self._iter_jsonl(p)

    # ============================================================
    # 內部工具：取得事件型別 & 時間
    # ============================================================
    @staticmethod
    def _get_event_type(ev: PBEvent) -> Optional[str]:
        """
        嘗試從 PBEvent / meta 裡推測事件型別。
        會試：
        - ev.event_type
        - ev.type
        - ev.topic
        - ev.meta['type'] / ev.meta['event_type'] / ev.meta['topic']
        """
        for attr in ("event_type", "type", "topic"):
            v = getattr(ev, attr, None)
            if v:
                return v

        meta = getattr(ev, "meta", None)
        if isinstance(meta, dict):
            for k in ("type", "event_type", "topic"):
                if k in meta and meta[k]:
                    return meta[k]
        return None

    @staticmethod
    def _in_time_range(ts: Optional[datetime],
                       start_time: Optional[datetime],
                       end_time: Optional[datetime]) -> bool:
        if ts is None:
            return True  # 沒時間資訊就不過濾
        if start_time and ts < start_time:
            return False
        if end_time and ts > end_time:
            return False
        return True

    # ============================================================
    # 核心：轉 raw → PBEvent（不 publish）
    # ============================================================
    def _raw_to_event(
        self,
        raw: dict,
        *,
        key: str,
        soft: bool = True,
    ):
        """
        Replay raw record → PBEvent（對齊 PB-Lang v2）
        """

        # === Case 1: raw 已是 PBEvent JSON（event_raw.jsonl）===
        if isinstance(raw, dict):
            if "type" in raw:
                try:
                    return PBEvent(
                        type=raw["type"],
                        payload=raw.get("payload") or raw.get("content") or {},
                        source=raw.get("source", "replay"),
                        priority=raw.get("priority", 1),
                        tags=raw.get("tags"),
                        event_id=raw.get("event_id"),
                        timestamp=raw.get("timestamp"),
                        ts=raw.get("ts"),
                    )
                except Exception as e:
                    print(f"[ReplayEngine] ❌ PBEvent 重建失敗: {e}")
                    return None

        # === Case 2: 非 PBEvent raw → 重新走 Perception Gateway ===
        try:
            return self.gateway.process(key, raw, soft=soft)
        except Exception as e:
            if soft:
                print(f"[ReplayEngine] ⚠ Gateway 處理失敗（soft drop）: {e}")
                return None
            raise
    # ============================================================
    # 對外 API：只產生 PBEvent，不 publish
    # ============================================================
    def iter_events(
        self,
        path: str,
        *,
        key: Optional[str] = None,
        soft: bool = True,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        type_filter: Optional[Iterable[str]] = None,
        limit: Optional[int] = None,
    ) -> Iterator[PBEvent]:
        """
        讀檔 → raw → PBEvent → 依時間 / 型別 / 數量 做過濾。

        type_filter:
            - None     : 不過濾
            - Iterable : 只保留 event_type 在此集合中的事件
        limit:
            - None  : 不限制
            - int   : 只產生前 N 筆
        """

        key = key or self.default_key
        type_set = set(type_filter) if type_filter is not None else None

        count = 0
        for raw in self._iter_raw_records(path):
            ev = self._raw_to_event(raw, key=key, soft=soft)
            if ev is None:
                continue

            ts = getattr(ev, "timestamp", None)
            if not self._in_time_range(ts, start_time, end_time):
                continue

            if type_set is not None:
                etype = self._get_event_type(ev)
                if etype not in type_set:
                    continue

            yield ev
            count += 1

            if limit is not None and count >= limit:
                break

    # ============================================================
    # 對外 API：真正 replay（publish 到 bus）
    # ============================================================
    def replay(
        self,
        path: str,
        *,
        key: Optional[str] = None,
        speed: float = 1.0,
        ignore_timestamp: bool = False,
        soft: bool = True,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        type_filter: Optional[Iterable[str]] = None,
        limit: Optional[int] = None,
        progress_cb: Optional[Any] = None,
        target: ReplayTarget = "bus",
    ) -> int:
        """
        真正將事件重播到 bus。

        speed:
            - 1.0 = 原速
            - 2.0 = 兩倍速
            - 0   = 無限快（完全忽略事件間隔）
        ignore_timestamp:
            - True  → 完全忽略事件間隔，僅使用 speed / limit 控制
            - False → 依事件 timestamp 模擬間隔

        progress_cb:
            - 可選 callback(count: int)，用來打印 / 更新進度列

        回傳：成功 publish 的事件數
        """
        key = key or self.default_key
        count = 0

        prev_ts: Optional[datetime] = None
        type_set = set(type_filter) if type_filter is not None else None

        # ✅ 若要灌庫，必須有 ingestor
        if target in ("library", "both") and self.ingestor is None:
            raise RuntimeError("ReplayEngine target=library/both but ingestor is None")

        for raw in self._iter_raw_records(path):
            ev = self._raw_to_event(raw, key=key, soft=soft)
            if ev is None:
                continue

            ts = getattr(ev, "timestamp", None)
            if not self._in_time_range(ts, start_time, end_time):
                continue

            if type_set is not None:
                etype = self._get_event_type(ev)
                if etype not in type_set:
                    continue

            # ---- 模擬時間間隔 ----
            if not ignore_timestamp and speed != 0 and ts is not None:
                if prev_ts is not None:
                    dt = (ts - prev_ts).total_seconds()
                    if dt > 0:
                        time.sleep(dt / speed)
                prev_ts = ts

            # =====================================================
            # 🔁 Replay 輸出控制（不砍原本邏輯，只加選項）
            # =====================================================

            # 1️⃣ Replay → Library（不走 EventBus）
            if target in ("library", "both"):
                if self.ingestor is None:
                    raise RuntimeError(
                        "ReplayEngine target=library/both but ingestor is None"
                    )
                try:
                    self.ingestor.ingest_event(ev)
                except Exception:
                    pass

            # 2️⃣ Replay → EventBus（原本行為，完全保留）
            if target in ("bus", "both"):
                self.bus.publish(ev)

            count += 1

            # ---- 進度回報（保留）----
            if progress_cb is not None:
                try:
                    progress_cb(count)
                except Exception:
                    pass

            # ---- 數量限制（保留）----
            if limit is not None and count >= limit:
                break

        print(f"[ReplayEngine] 🔁 完成重播，共 {count} 筆事件")
        return count

    # ============================================================
    # 對外 API：為 AI 建 Dataset（滑動視窗序列）
    # ============================================================
    def build_sequences(
        self,
        path: str,
        *,
        key: Optional[str] = None,
        soft: bool = True,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        type_filter: Optional[Iterable[str]] = None,
        window_size: int = 32,
        step: int = 1,
        limit_events: Optional[int] = None,
    ) -> List[List[PBEvent]]:
        """
        從檔案讀事件 → 轉成「滑動視窗」序列，給模型用。

        window_size : 每個序列的長度（例如 32 根 K 線）
        step        : 滑動步伐（1 = 每一筆往後滑；window_size = 不重疊視窗）
        limit_events: 上限事件數（避免吃太多記憶體）

        回傳：
            List[ List[PBEvent] ]
            每個內部 list 就是一個序列（時間順序已維持）
        """
        key = key or self.default_key
        events: List[PBEvent] = list(
            self.iter_events(
                path,
                key=key,
                soft=soft,
                start_time=start_time,
                end_time=end_time,
                type_filter=type_filter,
                limit=limit_events,
            )
        )

        seqs: List[List[PBEvent]] = []
        n = len(events)
        if n < window_size:
            return seqs

        i = 0
        while i + window_size <= n:
            seq = events[i : i + window_size]
            seqs.append(seq)
            i += step

        print(
            f"[ReplayEngine] 📦 Dataset 構建完成：{len(events)} 筆事件 → {len(seqs)} 個序列 "
            f"(window={window_size}, step={step})"
        )
        return seqs
