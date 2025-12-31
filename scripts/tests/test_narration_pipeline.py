import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# scripts/tests/test_narration_pipeline.py

from datetime import datetime, timezone
from shared_core.event_schema import PBEvent
from shared_core.event.zero_copy_event_bus import ZeroCopyEventBus

from outputs.narrators.narration_handler import NarrationHandler
from outputs.narrators.narrator_registry import NarratorRegistry
from outputs.narrators.stub_narrator import StubNarrator

import time
def test_narration_pipeline():
    print("\n=== NARRATION PIPELINE TEST ===")

    # --------------------------------------------------
    # 1️⃣ 建立 EventBus（單獨測，不用整個 Runtime）
    # --------------------------------------------------
    bus = ZeroCopyEventBus()

    # --------------------------------------------------
    # 2️⃣ 建立 Narrator Registry（先全 stub）
    # --------------------------------------------------
    registry = NarratorRegistry()
    registry.register("stub", StubNarrator())
    registry.register("gpt_low", StubNarrator())
    registry.register("gpt_high", StubNarrator())

    # --------------------------------------------------
    # 3️⃣ NarrationHandler（吃 PBEvent）
    # --------------------------------------------------
    narration_handler = NarrationHandler(
        registry=registry,
        env="test",
    )

    bus.subscribe(
        "system.governance.decision.created",
        narration_handler.handle,
    )

    # --------------------------------------------------
    # 4️⃣ 模擬一個 Governance Decision Event
    # --------------------------------------------------
    decision_payload = {
        "agenda_id": "agenda-test-001",
        "decision": "HOLD",
        "confidence": 0.62,
        "reasons": ["RSI neutral", "Volume stable"],

        # ⭐ 關鍵欄位（你剛剛加的）
        "report_type": "daily",
        "narration_cost": "low",
    }

    event = PBEvent(
        type="system.governance.decision.created",
        source="test.governance",
        payload=decision_payload,
        ts=datetime.now(timezone.utc).timestamp(),
    )

    # --------------------------------------------------
    # 5️⃣ 發送事件（觸發 Narration）
    # --------------------------------------------------
    bus.publish(event)

    print("[OK] Narration pipeline executed")


if __name__ == "__main__":
    test_narration_pipeline()
