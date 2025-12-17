"""
[LEGACY / DEBUG TOOL]
Manual replay script.
Core replay logic lives in shared_core.replay.replay_engine.
"""
import sys
from pathlib import Path
import json
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storage_core.storage_manager import StorageManager
from pandora_core.pandora_runtime import PandoraRuntime


def replay_from_file(runtime: PandoraRuntime, path: Path, delay: float = 0.0):
    print(f"[Replay] ▶ start replay: {path.name}")

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            try:
                ev = json.loads(line)
                runtime.fast_bus.publish(ev["type"], ev["payload"])
            except Exception as e:
                print(f"[Replay] ❌ error: {e}")

            if delay > 0:
                time.sleep(delay)

    print(f"[Replay] ◀ done: {path.name}")


def main():
    sm = StorageManager("config/storage.yaml")

    runtime = PandoraRuntime(base_dir=".")
    runtime.bus.rt = runtime
    runtime.fast_bus.rt = runtime

    warm_dir = sm.warm()
    files = sorted(warm_dir.glob("logs_*.jsonl"))

    if not files:
        print("[Replay] ⚠ no warm logs found")
        return

    for p in files:
        replay_from_file(runtime, p, delay=0.0)


if __name__ == "__main__":
    main()
