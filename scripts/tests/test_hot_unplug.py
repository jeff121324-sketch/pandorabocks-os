import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import time
from pathlib import Path

from pandora_core.pandora_runtime import PandoraRuntime
from pandora_core.plugins.safe_plugin import SafePlugin

def main():
    base = Path(__file__).resolve().parent.parent
    rt = PandoraRuntime(base)

    print("[TEST] loading SafePlugin")
    rt.load_plugin_instance(
        "safe",
        SafePlugin("safe")
    )

    time.sleep(10)

    print("[TEST] uninstalling SafePlugin")
    rt.uninstall_plugin("safe")

    # 再跑一段，確認系統沒事
    time.sleep(5)

    print("[TEST] done")

if __name__ == "__main__":
    main()
