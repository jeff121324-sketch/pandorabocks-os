import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import threading
import time
from pandora_core.pandora_runtime import PandoraRuntime

# ====== 設定 replay 檔案路徑 ======
WARM_FILE_A = r"D:\pandora_data\warm\warm_A.jsonl"
WARM_FILE_B = r"D:\pandora_data\warm\warm_B.jsonl"

def run_replay(runtime, path, name):
    print(f"[Replay-{name}] ▶ start")
    count = runtime.replay.replay_file(path=path, speed=0)
    print(f"[Replay-{name}] ◀ done, events={count}")

def main():
    rt = PandoraRuntime(base_dir=".")
    print("[Stress] PandoraRuntime ready")

    # ====== 啟動雙 Replay（平行）======
    t1 = threading.Thread(
        target=run_replay,
        args=(rt, WARM_FILE_A, "A"),
        daemon=True,
    )
    t2 = threading.Thread(
        target=run_replay,
        args=(rt, WARM_FILE_B, "B"),
        daemon=True,
    )

    start_ts = time.time()
    t1.start()
    t2.start()

    # 等待兩個 replay 結束
    t1.join()
    t2.join()

    elapsed = time.time() - start_ts
    print(f"[Stress] Dual Replay finished in {elapsed:.2f}s")

    # 給 Auditor / Rotator 一點收尾時間
    time.sleep(5)
    print("[Stress] DONE")

if __name__ == "__main__":
    main()
