import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import time
from pandora_core.pandora_runtime import PandoraRuntime

WARM_FILE = r"D:\pandora_data\warm\warm_A.jsonl"
RUN_MINUTES = 30   # 👉 改成 60 就是 1 小時

def main():
    rt = PandoraRuntime(base_dir=".")
    print("[LongRun] PandoraRuntime started")

    start_ts = time.time()
    end_ts = start_ts + RUN_MINUTES * 60
    round_id = 0

    while time.time() < end_ts:
        round_id += 1
        print(f"[LongRun] ▶ Replay round {round_id}")

        count = rt.replay.replay_file(
            path=WARM_FILE,
            speed=0
        )

        print(f"[LongRun] ◀ Replay round {round_id}, events={count}")

        # 小休息，避免極端 I/O 壓爆
        time.sleep(2)

    elapsed = time.time() - start_ts
    print(f"[LongRun] FINISHED after {elapsed/60:.1f} minutes")

    # 給背景系統時間收尾
    time.sleep(10)
    print("[LongRun] DONE")

if __name__ == "__main__":
    main()
