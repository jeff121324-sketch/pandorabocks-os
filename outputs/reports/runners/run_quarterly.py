# outputs/reports/runners/run_quarterly.py

import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from outputs.reports.aggregators.quarterly_aggregator import QuarterlyAggregator
from outputs.reports.writers.weekly_report_writer import WeeklyReportWriter

REPORTS_DIR = ROOT_DIR / "outputs" / "reports"
DAILY_DIR = REPORTS_DIR / "daily"
DAILY_PATTERN = "daily_report_*.json"


def load_daily_reports():
    items = []
    for file in DAILY_DIR.glob(DAILY_PATTERN):
        try:
            with file.open("r", encoding="utf-8") as f:
                items.append(json.load(f))
        except json.JSONDecodeError:
            continue
    return items


def main():
    daily_reports = load_daily_reports()
    if not daily_reports:
        print("[WARN] No daily reports found. Quarterly runner skipped.")
        return

    summary = QuarterlyAggregator(daily_reports).aggregate()
    WeeklyReportWriter(base_dir="outputs/reports/quarterly").send(summary)

    print("[OK] Quarterly runner completed.")
    print(f"     Total decisions: {summary['total_decisions']}")


if __name__ == "__main__":
    main()
