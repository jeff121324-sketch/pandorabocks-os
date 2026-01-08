# pandora_core/replay_runtime.py

from pathlib import Path
from shared_core.replay.replay_engine import ReplayEngine
from library.replay.library_replay_source import LibraryReplaySource
import time

class ReplayRuntime:
    """
    Runtime-level Replay 接線器（強化版）

    職責：
    - 接 Gateway / EventBus
    - 選擇 Replay 來源（file / hot / warm）
    - 控制 replay 模式（正常 / 灌庫 / 壓力測試）
    - 不包含 replay 邏輯本身
    """
    plugin_name = "ReplayRuntime"
    required_capabilities = []
    
    def __init__(self, runtime, raw_root: Path, world_context):
        self.runtime = runtime
        self.raw_root = raw_root
        self.world_context = world_context

        self.engine = ReplayEngine(
            bus=runtime.fast_bus,
            gateway=runtime.gateway,
        )
        self._replay_files = self._collect_replay_files()
        self._done = False

        if hasattr(runtime, "library_ingestor") and runtime.library_ingestor:
            self.engine.ingestor = runtime.library_ingestor
            print("[ReplayRuntime] 📚 LibraryIngestor attached")
    # ============================================================
    # 基礎 replay
    # ============================================================

    def replay_file(
        self,
        path: Path,
        speed: float = 0,
        *,
        limit: int | None = None,
        progress_cb=None,
        ignore_timestamp: bool = False,
        type_filter: set[str] | None = None,
    ) -> int:
        """
        從任意 jsonl 檔 replay

        Args:
            path: jsonl 檔案路徑
            speed: replay 倍速（0 = 不 sleep）
            limit: 最多 replay 幾筆
            progress_cb: 每 N 筆回呼
            ignore_timestamp: True = 不依時間 sleep
            type_filter: 只 replay 特定 event type
        """
        return self.engine.replay(
            path=path,
            speed=speed,
            limit=limit,
            progress_cb=progress_cb,
            ignore_timestamp=ignore_timestamp,
            type_filter=type_filter,
        )

    # ============================================================
    # Storage-aware replay
    # ============================================================

    def replay_hot(
        self,
        speed: float = 0,
        **kwargs,
    ) -> int:
        """
        Replay HOT layer（目前運行中的事件）
        """
        hot_file = self.runtime.storage.hot_file
        return self.replay_file(hot_file, speed=speed, **kwargs)

    def replay_warm(
        self,
        warm_file: Path,
        speed: float = 0,
        **kwargs,
    ) -> int:
        """
        Replay 指定 warm 檔案
        """
        return self.replay_file(warm_file, speed=speed, **kwargs)

    # --------------------------------------------------
    # ⭐ 新增：Replay → Library 灌庫專用 API
    # --------------------------------------------------

    def ingest_to_library(
        self,
        path,
        target="library",
        speed=0,
        limit=None,
    ):
        """
        Replay 檔案並灌入 Library（不走 EventBus）

        Returns:
            (count, stats)
        """
        if not getattr(self.runtime, "library_ingestor", None):
            raise RuntimeError("LibraryIngestor not attached to runtime")

        print(f"[ReplayRuntime] 📚 ingest_to_library: {path}")

        count = self.engine.replay(
            path=path,
            target=target,        # library / both
            speed=speed,
            limit=limit,
        )

        stats = {
            "path": str(path),
            "events": count,
            "target": target,
        }

        return count, stats
    # ============================================================
    # 🔁 Replay ← Library ← Replay（閉環驗證）
    # ============================================================

    def replay_from_library(
        self,
        day: str,
        *,
        speed: float = 0,
        limit: int | None = None,
    ) -> int:
        """
        Replay events directly from Library (jsonl) back into Gateway
        """
        src = LibraryReplaySource(Path("library"))
        count = 0

        for record in src.iter_day(day):
            # 🚨 重點：永遠用 library.event
            self.runtime.gateway.process(
                "library.event",
                record
            )
            count += 1

            if limit is not None and count >= limit:
                break

            if speed > 0:
                time.sleep(1 / speed)
    
        print(f"[ReplayRuntime] 🔁 replay_from_library done, events={count}")
        return count

    # ============================================================
    # 專用模式（文明級）
    # ============================================================

    def replay_ingest_only(
        self,
        path: Path,
        *,
        limit: int | None = None,
        progress_cb=None,
        type_filter: set[str] | None = None,
    ) -> int:
        """
        🔒 Library 灌庫專用模式
        - 不 sleep
        - 忽略 timestamp
        - 不依賴真實時間
        """
        return self.replay_file(
            path=path,
            speed=0,
            limit=limit,
            progress_cb=progress_cb,
            ignore_timestamp=True,
            type_filter=type_filter,
        )

    def replay_stress(
        self,
        path: Path,
        rounds: int = 1,
        **kwargs,
    ) -> int:
        """
        💣 壓力測試模式
        - 同一檔案重播多次
        - 回傳總事件數
        """
        total = 0
        for i in range(rounds):
            print(f"[ReplayRuntime] 🔄 stress round {i + 1}/{rounds}")
            total += self.replay_file(path, **kwargs)
        return total
    
    def _collect_replay_files(self):
        """
        從 raw_root 底下收集所有可 replay 的檔案
        支援 csv / jsonl
        """
        raw_root = Path(self.raw_root)

        if not raw_root.exists():
            return []

        files = []
        for ext in ("*.jsonl", "*.csv"):
            files.extend(raw_root.rglob(ext))

        files.sort()
        return files

    def replay_csv_as_events(self, path: Path):
        """
        將 CSV Kline 資料轉成 Event，再送進 ReplayEngine
        v1：最小轉譯，只支援 Binance OHLCV
        """
        import csv
        from shared_core.event_schema import PBEvent

        count = 0

        try:
            interval = path.stem.split("_")[-1]
    
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    raw_ts = (
                        row.get("kline_open_ts")
                        or row.get("open_time")
                        or row.get("timestamp")
                    )

                    event = PBEvent(
                        source="replay.csv",
                        type="market.kline",
                        payload={
                            "world_id": self.world_context.world_id,
                            "symbol": self.world_context.world_id,
                            "interval": interval,
                            "timestamp": int(float(raw_ts)), 
                            "open": float(row["open"]),
                            "high": float(row["high"]),
                            "low": float(row["low"]),
                            "close": float(row["close"]),
                            "volume": float(row["volume"]),
                        },
                    )

                    self.engine.bus.publish(event)
                    count += 1

        except Exception as e:
            print(f"[ReplayRuntime] ❌ CSV replay error @ {path}: {e}")
            return 0   # ⬅️ 關鍵：**這裡一定要 return**

        return count

    def tick(self):
        """
        Pandora OS external tick entrypoint (World Runtime v1)
        """
        if self._done:
            return

        count = 0

        if not self._replay_files:
            print(f"[ReplayRuntime] ⚠ no replay files under: {self.raw_root}")
            self._done = True
            return

        path = self._replay_files.pop(0)
        print(f"[ReplayRuntime] ▶ replay_file: {path}")

        try:
            if path.suffix.lower() == ".csv":
                print(f"[ReplayRuntime] ⚠ CSV detected, convert before replay: {path}")
                count = self.replay_csv_as_events(path)
            else:
                count = self.replay_file(
                    path=path,
                    speed=0,
                    ignore_timestamp=True,
                )

            print(f"[ReplayRuntime] ✅ replay completed, events={count}")

        except Exception as e:
            print(f"[ReplayRuntime] ❌ replay failed: {e}")
            count = 0   # ⬅️ 保證 count 一定存在

        self._done = True
        print("[ReplayRuntime] 🧪 replay done, waiting for downstream listeners")



