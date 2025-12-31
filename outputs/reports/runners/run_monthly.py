# outputs/reports/runners/run_monthly.py

import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from outputs.reports.aggregators.monthly_aggregator import MonthlyAggregator
from outputs.reports.writers.monthly_report_writer import MonthlyReportWriter

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
        print("[WARN] No daily reports found. Monthly runner skipped.")
        return

    summary = MonthlyAggregator(daily_reports).aggregate()
    MonthlyReportWriter(base_dir="outputs/reports/monthly").send(summary)

    print("[OK] Monthly runner completed.")
    print(f"     Total decisions: {summary['total_decisions']}")


if __name__ == "__main__":
    main()

