import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from library.library_writer import LibraryWriter
from library.library_event import LibraryEvent


# --------------------------------------------------
# 模擬一顆 PBEvent（最小可用）
# --------------------------------------------------
# 模擬 PBEvent
class DummyPBEvent:
    event_id = "test-001"
    type = "market.kline"
    source = "replay"
    payload = {"price": 12345}
    timestamp = datetime.now(timezone.utc).isoformat()


def main():
    library_root = Path("library")
    writer = LibraryWriter(library_root)

    lib_event = LibraryEvent.from_pbevent(
        DummyPBEvent,
        weak_label={"confidence": 0.9},
        meta={"note": "unit test"},
    )

    writer.write_event(lib_event)
    print("[TEST] Library write OK")


if __name__ == "__main__":
    main()
