import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pandora_core.pandora_runtime import PandoraRuntime


def main():
    rt = PandoraRuntime(base_dir=".")
    # 你現在 hot 在 C:\pandora_data\hot\logs.jsonl，但測試你也可以指定任意 jsonl
    hot = r"C:\pandora_data\hot\logs.jsonl"

    n, stats = rt.replay.ingest_to_library(hot)
    print("[TEST] ingest count =", n)
    print("[TEST] stats =", stats)


if __name__ == "__main__":
    main()
