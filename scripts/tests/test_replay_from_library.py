import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pandora_core.pandora_runtime import PandoraRuntime
import time


def main():
    rt = PandoraRuntime(base_dir=".")

    print("\n==============================")
    print("🧪 Test 1: basic replay_from_library")
    print("==============================")

    count = rt.replay.replay_from_library(
        day="2025-12-14",
        limit=100,
        speed=0,
    )
    print(f"[TEST1] replayed={count}")

    # --------------------------------------------------

    print("\n==============================")
    print("⚡ Test 2: speed test (no sleep)")
    print("==============================")

    t0 = time.time()
    count = rt.replay.replay_from_library(
        day="2025-12-14",
        limit=10_000,
        speed=0,        # 關鍵：0 = 不 sleep
    )
    dt = time.time() - t0

    print(f"[TEST2] replayed={count}, elapsed={dt:.3f}s")

    # 你要的文明級驗證條件
    assert dt < 3, "Replay too slow, sleep might be active"
    print("✅ Test 2 PASS: no timestamp / no sleep")

    # --------------------------------------------------

    print("\n==============================")
    print("🐢 Test 3: slow replay (human speed)")
    print("==============================")

    count = rt.replay.replay_from_library(
        day="2025-12-14",
        limit=50,
        speed=10,   # 每秒 10 筆
    )
    print(f"[TEST3] replayed={count}")
    print("✅ Test 3 DONE (observe timing manually)")


if __name__ == "__main__":
    main()
