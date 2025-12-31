# aisop/outputs/narrators/narration_handler.py

from typing import Dict, Any
from outputs.narrators.narrator_registry import NarratorRegistry
from outputs.reports.writers.daily_report_writer import DailyReportWriter
from outputs.reports.writers.weekly_report_writer import WeeklyReportWriter
from outputs.reports.writers.monthly_report_writer import MonthlyReportWriter
from shared_core.event_schema import PBEvent

class NarrationHandler:
    """
    EventBus subscriber:
    system.governance.decision.created
    """

    def __init__(
        self,
        *,
        registry: NarratorRegistry,
        env: str = "prod",
    ):
        self.registry = registry
        self.env = env

        # writers are deterministic, no AI here
        self.writers = {
            "daily": DailyReportWriter(),
            "weekly": WeeklyReportWriter(),
            "monthly": MonthlyReportWriter(),
        }

    def handle(self, event: PBEvent):
        # 1️⃣ Narration 一定吃 PBEvent（防禦式）
        if not isinstance(event, PBEvent):
            return

        # 2️⃣ ⚠️ payload 本身就是 decision（這是關鍵修正）
        decision = event.payload
        if not isinstance(decision, dict):
            return

        # 3️⃣ 決定報表型態（daily / weekly / monthly）
        report_type = decision.get("report_type", "daily")

        # 4️⃣ 動態選 narrator（依 cost / env / report_type）
        narrator = self.registry.select(
            report_type=report_type,
            env=self.env,
            max_cost=decision.get("narration_cost", "low"),
        )

        # 5️⃣ AI 寫敘事（或 stub）
        narrative_text = narrator.narrate(decision)

        # 6️⃣ 對應 writer（人類可讀）
        writer = self.writers.get(report_type)
        if not writer:
            return  # 防止未註冊 writer 直接炸掉

        # ✅ 統一送 payload
        writer.send({
            "decision": decision,
            "narrative": narrative_text,
            "meta": {
                "source": "narration",
                "report_type": report_type,
            },
        })