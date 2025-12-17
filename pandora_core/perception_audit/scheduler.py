import asyncio
from datetime import datetime, timedelta

AUDIT_INTERVAL = 1800  # 30 minutes

async def run_audit_loop(auditor):
    while True:
        try:
            await auditor.run_audit()
        except Exception as e:
            print(f"[AUDIT ERROR] {e}")
        await asyncio.sleep(AUDIT_INTERVAL)
