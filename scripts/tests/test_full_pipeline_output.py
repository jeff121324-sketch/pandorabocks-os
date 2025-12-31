# scripts/tests/test_full_pipeline_output.py

import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/）===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# === Event Bus ===
from shared_core.event.zero_copy_event_bus import ZeroCopyEventBus
from shared_core.event_schema import PBEvent
# === Output System ===
from outputs.output_orchestrator import DecisionOutputOrchestrator
from outputs.output_dispatch_handler import OutputDispatchHandler
from outputs.debug.console_output import ConsoleOutput
from outputs.warm.file_output import FileOutput

# === Formatter ===
from locales.zh_TW.formatter import ZhTWFormatter
from locales.ja.formatter import JaFormatter
from locales.en.formatter import EnFormatter


def _dummy_decision():
    """
    模擬 Governance 最終決策輸出
    （等同 system.governance.decision.created payload）
    """
    return {
        "title": "Market Signal Evaluation",
        "summary": "Momentum indicators show neutral bias.",
        "decision": "HOLD",
        "confidence": 0.62,
        "reasons": ["RSI neutral", "Volume stable"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def run_locale_test(locale_name, formatter):
    print(f"\n=== FULL PIPELINE TEST [{locale_name}] ===")

    bus = ZeroCopyEventBus()

    orchestrator = DecisionOutputOrchestrator(
        formatter=formatter,
        outputs=[
            ConsoleOutput(),
            FileOutput(base_dir="outputs/reports/daily"),
        ],
        metadata={
            "system": "AISOP",
            "version": "0.5",
            "env": "test",
            "locale": locale_name,
        },
    )

    output_handler = OutputDispatchHandler(orchestrator)
    # === 接線（模擬 Runtime 啟動時做的事）===
    bus.subscribe(
        "system.governance.decision.created",
        output_handler.handle,
    )

    # === 發送治理事件（PBEvent 物件）===
    bus.publish(
        PBEvent(
            type="system.governance.decision.created",
            payload=_dummy_decision(),
            source="test.full_pipeline",
            priority=1,
            tags=["test", "full_pipeline"],
        )
    )

    print(f"[OK] {locale_name} pipeline output dispatched")


def test_full_pipeline():
    run_locale_test("zh_TW", ZhTWFormatter())
    run_locale_test("ja_JP", JaFormatter())
    run_locale_test("en_US", EnFormatter())

    print("\n🎉 FULL PIPELINE OUTPUT TEST PASSED")


if __name__ == "__main__":
    test_full_pipeline()
