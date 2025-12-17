import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from pandora_core.pandora_runtime import PandoraRuntime

def main():
    rt = PandoraRuntime(base_dir=".")

    warm_file = r"D:\pandora_data\warm\logs_20251214_213933.jsonl"
    n, stats = rt.replay.ingest_to_library(warm_file)

    print("[TEST] ingest count =", n)
    print("[TEST] stats =", stats)

if __name__ == "__main__":
    main()