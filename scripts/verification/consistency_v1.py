import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from pathlib import Path
from collections import defaultdict

from pandora_core.pandora_runtime import PandoraRuntime
from pandora_core.replay_runtime import ReplayRuntime
from shared_core.decision.fingerprint import fingerprint_core



RAW_FILE = Path("trading_core/data/raw/mock/BTC/USDT/1m/2026-01-01.jsonl")
REPLAY_ROUNDS = 3




class DecisionCollector:
    """
    Consistency v1:
    Side-channel observer to collect decision.core directly
    (NOT an event listener)
    """

    def __init__(self):
        self.cores = []

    def observe(self, decision):
        """
        decision: dict with keys {core, extension}
        """
        if not isinstance(decision, dict):
            return

        core = decision.get("core")
        if core:
            self.cores.append(core)



def run_once():
    """
    跑一次 replay，回傳所有 decision.core fingerprint
    """
    rt = PandoraRuntime(base_dir=".")
    collector = DecisionCollector()

    # =====================================================
    # 1️⃣ Market → Decision（高速事實流）
    # =====================================================
    from trading_core.decision_pipeline.listener import make_on_market_kline
    rt.fast_bus.subscribe(
        "market.kline",
        make_on_market_kline(rt.bus,observer=collector.observe )   # 👈 decision 明確送到 bus
    )

    # =====================================================
    # 2️⃣ Decision → Collector（制度流）
    # =====================================================


    # =====================================================
    # 3️⃣ Replay
    # =====================================================
    replay_rt = ReplayRuntime(
        rt,
        raw_root=Path("trading_core/data/raw")
    )

    replay_rt.replay_file(
        RAW_FILE,
        speed=0,
        ignore_timestamp=True,
    )

    # =====================================================
    # 4️⃣ 防呆檢查
    # =====================================================
    if not collector.cores:
        raise RuntimeError(
            "No decision.core collected — "
            "decision event not observed on rt.bus"
        )

    return [
        fingerprint_core(core)
        for core in collector.cores
    ]




def main():
    print("### USING PER-EVENT CONSISTENCY CHECK ###")

    all_runs = []

    for i in range(REPLAY_ROUNDS):
        fps = run_once()
        all_runs.append(fps)

    lengths = {len(run) for run in all_runs}
    if len(lengths) != 1:
        raise RuntimeError(f"Inconsistent decision counts: {lengths}")

    decision_count = lengths.pop()

    print("\n=== Consistency Verification v1 (per-event) ===")

    inconsistent = False

    for idx in range(decision_count):
        fps_at_idx = [run[idx] for run in all_runs]
        unique = set(fps_at_idx)

        if len(unique) == 1:
            print(f"[OK] event[{idx}] fingerprint = {fps_at_idx[0]}")
        else:
            inconsistent = True
            print(f"[FAIL] event[{idx}] fingerprints = {fps_at_idx}")

    if not inconsistent:
        print("\n✅ PASS: decision.core is deterministic per event")
    else:
        print("\n❌ FAIL: per-event fingerprint mismatch detected")

if __name__ == "__main__":
    main()
