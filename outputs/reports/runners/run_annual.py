import sys
import json
import shutil
from pathlib import Path
from datetime import datetime   # ← 原本缺這個，會炸

# =========================================
# Bootstrap project root
# =========================================

ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

# =========================================
# Imports
# =========================================

from outputs.reports.aggregators.annual_aggregator import AnnualAggregator
from outputs.reports.writers.weekly_report_writer import WeeklyReportWriter

# =========================================
# Path config
# =========================================

REPORTS_DIR = ROOT_DIR / "outputs" / "reports"
DAILY_DIR = REPORTS_DIR / "daily"
ARCHIVE_DIR = REPORTS_DIR / "daily_archived"

DAILY_PATTERN = "daily_report_*.json"

# =========================================
# Load daily reports
# =========================================

def load_daily_reports():
    """
    Load all daily reports.
    Returns:
        items: list[dict]
        files: list[Path]
    """
    items = []
    files = []

    for file in DAILY_DIR.glob(DAILY_PATTERN):
        try:
            with file.open("r", encoding="utf-8") as f:
                items.append(json.load(f))
            files.append(file)
        except json.JSONDecodeError:
            continue

    return items, files


# =========================================
# Archive daily reports (ONLY after success)
# =========================================

def archive_daily_files(files: list[Path]):
    """
    Move daily reports into archive folders grouped by YYYY-MM.
    """
    for file in files:
        # daily_report_2025-12-29.json → 2025-12
        date_part = file.stem.replace("daily_report_", "")

        try:
            dt = datetime.strptime(date_part, "%Y-%m-%d")
            subdir = ARCHIVE_DIR / dt.strftime("%Y-%m")
        except ValueError:
            subdir = ARCHIVE_DIR / "unknown"

        subdir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(file), str(subdir / file.name))


# =========================================
# Main
# =========================================

def main():
    daily_reports, daily_files = load_daily_reports()

    print(f"[DEBUG] Looking for daily reports in: {DAILY_DIR}")
    print(f"[DEBUG] Found files: {daily_files}")

    if not daily_reports:
        print("[WARN] No daily reports found. Annual runner skipped.")
        return

    # === Aggregate ===
    aggregator = AnnualAggregator(daily_reports)
    summary = aggregator.aggregate()

    # === Write annual report ===
    writer = WeeklyReportWriter(base_dir="outputs/reports/annual")
    writer.send(summary)

    # === Archive ONLY after success ===
    archive_daily_files(daily_files)

    print("[OK] Annual runner completed.")
    print(f"     Total decisions: {summary['total_decisions']}")
    print("[OK] Daily reports archived.")


if __name__ == "__main__":
    main()
