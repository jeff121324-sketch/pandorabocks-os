# =========================================
# Daily Report Runner
# =========================================

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter

# =========================================
# Bootstrap project root (stable)
# =========================================

def find_project_root(start: Path) -> Path:
    """
    Walk up directories until 'shared_core' is found.
    This allows runners to be executed from any location.
    """
    for parent in [start] + list(start.parents):
        if (parent / "shared_core").exists():
            return parent
    raise RuntimeError("Project root not found (shared_core missing)")

ROOT_DIR = find_project_root(Path(__file__).resolve())
sys.path.insert(0, str(ROOT_DIR))

# =========================================
# Shared Core Imports (AFTER sys.path)
# =========================================

from shared_core.event_time import extract_event_time

# =========================================
# Path Configuration
# =========================================

REPORTS_DIR = ROOT_DIR / "outputs" / "reports"
DAILY_DIR = REPORTS_DIR / "daily"
DECISION_ARCHIVE_DIR = REPORTS_DIR / "decision_archived"

DECISION_PATTERN = "decision_*.json"

# =========================================
# Timezone / Business Day Config
# =========================================

TZ_TAIPEI = timezone(timedelta(hours=8))

# ===== 載入 decision（依日期） =====
def load_decisions_by_date(target_date: str):
    """
    Load decision events that belong to the given local business date (YYYY-MM-DD).
    """
    decisions = []
    files = []

    for file in DAILY_DIR.glob(DECISION_PATTERN):

        try:
            with file.open("r", encoding="utf-8") as f:
                data = json.load(f)

            # === 統一時間來源（shared_core）===
            dt_utc = extract_event_time(data, filename=file.name)
            if not dt_utc:
                continue

            # UTC → Taipei local date
            dt_local = dt_utc.astimezone(TZ_TAIPEI)
            decision_date = dt_local.strftime("%Y-%m-%d")

            if decision_date != target_date:
                continue

            decisions.append(data)
            files.append(file)

        except json.JSONDecodeError:
            continue

    return decisions, files


# ===== 建立 daily report =====
def build_daily_report(date: str, decisions: list[dict]) -> dict:
    actions = [
        d.get("decision", {}).get("action")
        for d in decisions
        if isinstance(d.get("decision"), dict)
    ]

    action_dist = Counter(a for a in actions if a is not None)

    return {
        "date": date,
        "total_decisions": len(decisions),
        "decisions": decisions,
        "summary": {
            "action_distribution": dict(action_dist),
            "dominant_action": (
                action_dist.most_common(1)[0][0]
                if action_dist else None
            ),
        },
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "daily_runner",
        },
    }


# ===== 歸檔 decision =====
def archive_decision_files(files: list[Path], date: str):
    subdir = DECISION_ARCHIVE_DIR / date
    subdir.mkdir(parents=True, exist_ok=True)

    for file in files:
        shutil.move(str(file), str(subdir / file.name))


# ===== 主流程 =====
def main():
    target_date = (datetime.now(TZ_TAIPEI) - timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"[INFO] Building daily report for {target_date}")

    decisions, decision_files = load_decisions_by_date(target_date)

    print(f"[DEBUG] Found decisions: {len(decisions)}")

    if not decisions:
        print("[WARN] No decisions found for today. Daily runner skipped.")
        return

    daily_report = build_daily_report(target_date, decisions)

    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    report_path = DAILY_DIR / f"daily_report_{target_date}.json"

    with report_path.open("w", encoding="utf-8") as f:
        json.dump(daily_report, f, ensure_ascii=False, indent=2)

    archive_decision_files(decision_files, target_date)

    print("[OK] Daily report generated.")
    print(f"     Path: {report_path}")
    print("[OK] Decisions archived.")


if __name__ == "__main__":
    main()
