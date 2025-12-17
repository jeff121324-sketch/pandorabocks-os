import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from pathlib import Path
from library.index.library_index import LibraryIndex

def main():
    idx = LibraryIndex(Path("library"))
    idx.build()
    idx.flush()
    print("[TEST] LibraryIndex v1 OK")

if __name__ == "__main__":
    main()
