import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pandora_core.pandora_runtime import PandoraRuntime


class StressPlugin:
    plugin_name = "StressPlugin"
    required_capabilities = []


class StressBadPlugin:
    plugin_name = "StressBadPlugin"
    required_capabilities = ["EXTERNAL_TICK"]


def run():
    print("\n=== Stress Test: Plugin Capability Guard ===")

    rt = PandoraRuntime(base_dir=".")

    success = 0
    blocked = 0

    # ----------------------------
    # 高頻 attach 測試
    # ----------------------------
    for i in range(100):
        try:
            rt.load_plugin_instance(f"StressPlugin-{i}", StressPlugin())
            success += 1
        except Exception:
            pass

    # ----------------------------
    # 高頻非法 attach 測試
    # ----------------------------
    for i in range(100):
        try:
            rt.load_plugin_instance(f"StressBadPlugin-{i}", StressBadPlugin())
        except Exception:
            blocked += 1

    print(f"[RESULT] Attached OK: {success}")
    print(f"[RESULT] Blocked illegal: {blocked}")

    # ----------------------------
    # 判斷條件
    # ----------------------------
    assert success == 100, "Not all safe plugins attached"
    assert blocked == 100, "Not all illegal plugins were blocked"

    print("\n🔥 Stress Test PASSED — Guard is stable")


if __name__ == "__main__":
    run()
