import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pandora_core.pandora_runtime import PandoraRuntime


# ----------------------------
# 測試用 Plugin
# ----------------------------

class SafePlugin:
    plugin_name = "SafePlugin"
    required_capabilities = []


class DangerousPlugin:
    plugin_name = "DangerousPlugin"
    required_capabilities = ["EXTERNAL_TICK"]


class BadDeclaredPlugin:
    plugin_name = "BadDeclaredPlugin"
    required_capabilities = "EXTERNAL_TICK"  # ❌ 錯誤宣告（應該被擋）


def run():
    print("\n=== Governance Test: Plugin Capability Enforcement ===")

    rt = PandoraRuntime(base_dir=".")

    # ---- Test 1: Safe plugin should pass ----
    try:
        rt.load_plugin_instance("SafePlugin", SafePlugin())
        print("[PASS] SafePlugin attached successfully")
    except Exception as e:
        print("[FAIL] SafePlugin should not be blocked:", e)

    # ---- Test 2: Dangerous plugin should be blocked ----
    try:
        rt.load_plugin_instance("DangerousPlugin", DangerousPlugin())
        print("[FAIL] DangerousPlugin should have been blocked")
    except Exception as e:
        print("[PASS] DangerousPlugin blocked as expected:", e)

    # ---- Test 3: Bad declared plugin should be blocked early ----
    try:
        rt.load_plugin_instance("BadDeclaredPlugin", BadDeclaredPlugin())
        print("[FAIL] BadDeclaredPlugin should have been blocked")
    except Exception as e:
        print("[PASS] BadDeclaredPlugin blocked due to bad declaration:", e)

    print("\n✅ Governance Capability Enforcement Test Completed")


if __name__ == "__main__":
    run()
