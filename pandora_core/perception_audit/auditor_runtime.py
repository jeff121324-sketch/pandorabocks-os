from datetime import datetime, timedelta
from .auditor_prompt import AUDITOR_SYSTEM_PROMPT
from .auditor_schema import AUDIT_SCHEMA

class PerceptionSafetyAuditor:

    def __init__(self, llm_client, raw_event_reader):
        self.llm = llm_client          # Claude mini client
        self.reader = raw_event_reader # 只讀 raw logs

    async def run_audit(self):
        end = datetime.utcnow()
        start = end - timedelta(minutes=30)

        events = self.reader.load(start, end)

        summary = self._build_summary(events)

        result = await self.llm.audit(
            system_prompt=AUDITOR_SYSTEM_PROMPT,
            input_data=summary,
            schema=AUDIT_SCHEMA
        )

        self._store_report(result)

    def _build_summary(self, events):
        return {
            "total_events": len(events),
            "schema_violations": [e.id for e in events if e.schema_invalid],
            "poison_hits": sum(e.poison_hit for e in events),
            "suspected_leaks": [e.id for e in events if e.suspected_poison]
        }

    def _store_report(self, report):
        # 只寫 log / dashboard，不影響系統
        print("[AUDIT REPORT]", report)
