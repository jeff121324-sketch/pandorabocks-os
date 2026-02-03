# shared_core/world/external_tick_executor.py

from pathlib import Path

from trading_core.data_ingestion_runtime import DataIngestionRuntime
from pandora_core.replay_runtime import ReplayRuntime


class ExternalTickExecutor:
    """
    External Tick Executor (World Runtime v1)

    職責：
    - 在 ExternalTickGate = ENABLED 時
    - 根據 WorldProfile.mode
      - attach 即時資料
      - 或 attach Replay
    """

    def __init__(self, runtime, profile, world_context):
        self.runtime = runtime
        self.profile = profile
        self.world_context = world_context

    def attach(self):
        # =========================================
        # 🛑 WORLD-AWARE GUARD（關鍵修正）
        # =========================================
        world_type = getattr(self.world_context, "domain", None)

        if world_type == "trading":
            print(
                "[ExternalTickExecutor] 🚫 Trading world detected → "
                "REPLAY external tick is forbidden"
            )
            # trading world 只允許 realtime
            self._attach_realtime()
            return

        # =========================================
        # 原本邏輯（保留）
        # =========================================
        mode = self.profile.mode or {}

        if mode.get("replay"):
            self._attach_replay()
        else:
            self._attach_realtime()

    # -------------------------------------------------
    # Internal
    # -------------------------------------------------
    def _attach_realtime(self):
        print("[ExternalTickExecutor] ▶ Attaching REALTIME data ingestion")
        ingest_rt = DataIngestionRuntime(self.runtime)
        self.runtime.register_external_tick_source(ingest_rt)

    def _attach_replay(self):
        raw_root = Path(
            self.profile.data.get("storage", {}).get(
                "csv_root", "trading_core/data/raw"
            )
        )

        if not raw_root.exists():
            print(
                f"[ExternalTickExecutor] ⚠ Replay root not found, skip replay attach: {raw_root}"
            )
            return

        print(f"[ExternalTickExecutor] ▶ Attaching REPLAY runtime at {raw_root}")
        replay_rt = ReplayRuntime(self.runtime, raw_root, self.world_context)
        self.runtime.register_external_tick_source(replay_rt)
