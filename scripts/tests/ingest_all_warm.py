import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pathlib import Path
from pandora_core.pandora_runtime import PandoraRuntime

def main():
    rt = PandoraRuntime(base_dir=".")

    warm_dir = Path(r"D:\pandora_data\warm")
    total = 0

    for f in sorted(warm_dir.glob("logs_*.jsonl")):
        print(f"[INGEST] {f.name}")
        n, _ = rt.replay.ingest_to_library(f)
        total += n

    print("================================")
    print("TOTAL INGESTED EVENTS:", total)

if __name__ == "__main__":
    main()