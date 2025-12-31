from datetime import datetime
from .base import load_report

def format_daily_report_zh(report_path):
    data = load_report(report_path)

    title = "📊【每日交易日報】"
    date = data.get("date", "")
    summary = data.get("summary", {})
    metrics = data.get("metrics", {})

    lines = [
        title,
        f"📅 日期：{date}",
        "",
        "📈 今日概覽",
        f"- 交易筆數：{metrics.get('trades', 0)}",
        f"- 勝率：{metrics.get('win_rate', '0%')}",
        f"- 平均 Reward：{metrics.get('avg_reward', '0')}",
        "",
        "🧠 系統狀態",
        f"- 模式：{summary.get('mode', 'N/A')}",
        f"- 信心指數：{summary.get('confidence', 'N/A')}",
        "",
        "（本報告為系統自動產出，僅供參考）"
    ]

    return "\n".join(lines)
