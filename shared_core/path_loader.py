import sys
from pathlib import Path

def load_paths():
    ROOT = Path(__file__).resolve().parent.parent  # 回到 aisop/
    sys.path.append(str(ROOT))
    sys.path.append(str(ROOT / "shared_core"))
    sys.path.append(str(ROOT / "shared_core" / "pb_lang"))
    sys.path.append(str(ROOT / "shared_core" / "foundation"))
    sys.path.append(str(ROOT / "trading_core"))
