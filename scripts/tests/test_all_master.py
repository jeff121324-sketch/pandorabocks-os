# scripts/tests/test_all_master.py
import sys
import time
import subprocess
from pathlib import Path

# ======================================================
# Bootstrap
# ======================================================
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PYTHON = sys.executable

# ======================================================
# Test Runner Helper
# ======================================================
def run_test(path: str):
    print("\n" + "=" * 80)
    print(f"🧪 RUN TEST: {path}")
    print("=" * 80)

    t0 = time.time()
    result = subprocess.run(
        [PYTHON, path],
        cwd=ROOT,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    dt = time.time() - t0

    if result.returncode != 0:
        print(f"\n❌ FAILED: {path}")
        raise SystemExit(1)

    print(f"\n✅ PASSED: {path} ({dt:.2f}s)")
    return dt


# ======================================================
# Test Plan (22 tests)
# ======================================================
TESTS = [

    # --------------------------------------------------
    # 1️⃣ Perception / Gateway / Event
    # --------------------------------------------------
    "scripts/tests/test_gateway.py",

    # --------------------------------------------------
    # 2️⃣ World / Capability / Runtime Guard
    # --------------------------------------------------
    "scripts/tests/test_world_registry_v0.py",
    "scripts/tests/test_world_registry_capability_map_v1_1.py",
    "scripts/tests/test_world_capability_gate_v1.py",
    "scripts/tests/test_runtime_attach_guard_v1.py",

    # --------------------------------------------------
    # 3️⃣ Governance – Parliament / Snapshot / Flow
    # --------------------------------------------------
    "scripts/tests/test_parliament_v0.py",
    "scripts/tests/test_parliament_conflict_and_parallel.py",
    "scripts/tests/test_snapshot_event_to_parliament_v0.py",
    "scripts/tests/test_governance_full_flow.py",
    "scripts/tests/test_plugin_capability_enforcement_v1_2.py",

    # --------------------------------------------------
    # 4️⃣ Library – Write / Index / Ingest / Replay
    # --------------------------------------------------
    "scripts/tests/test_library_write.py",
    "scripts/tests/test_library_index.py",
    "scripts/tests/test_replay_from_library.py",
    "scripts/tests/test_replay_ingest_library.py",

    # --------------------------------------------------
    # 5️⃣ Output / Formatter / Contract
    # --------------------------------------------------
    "scripts/tests/test_output.py",
    "scripts/tests/test_output_contract.py",

    # --------------------------------------------------
    # 6️⃣ Full Pipeline
    # --------------------------------------------------
    "scripts/tests/test_full_pipeline_output.py",

]

# ======================================================
# MAIN
# ======================================================
def main():
    print("\n🚀 AISOP / Pandora MASTER TEST START")
    print(f"ROOT = {ROOT}")
    print(f"TOTAL TESTS = {len(TESTS)}")

    total_time = 0.0

    for test in TESTS:
        total_time += run_test(test)

    print("\n" + "=" * 80)
    print("🎉 ALL TESTS PASSED")
    print(f"🕒 TOTAL ELAPSED TIME: {total_time:.2f}s")
    print("=" * 80)


if __name__ == "__main__":
    main()