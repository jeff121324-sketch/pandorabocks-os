import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collections import OrderedDict

from outputs.output_schema import CANONICAL_ORDER
from outputs.output_orchestrator import DecisionOutputOrchestrator
from locales.zh_TW.formatter import ZhTWFormatter
from locales.ja.formatter import JaFormatter
from locales.en.formatter import EnFormatter


def _dummy_decision():
    return {
        "title": "Market Signal Evaluation",
        "summary": "Momentum indicators show neutral bias.",
        "decision": "HOLD",
        "confidence": 0.62,
        "reasons": ["RSI neutral", "Volume stable"],
    }


def _assert_contract(payload):
    assert "data" in payload
    data = payload["data"]

    # 1️⃣ 必須是 OrderedDict
    assert isinstance(data, OrderedDict)

    # 2️⃣ key 必須完全一致
    assert list(data.keys()) == CANONICAL_ORDER

    # 3️⃣ 不允許 None
    for k, v in data.items():
        assert v is not None, f"{k} is None"


def test_output_contract_all_locales():
    decision = _dummy_decision()

    for formatter in [
        ZhTWFormatter(),
        JaFormatter(),
        EnFormatter(),
    ]:
        orchestrator = DecisionOutputOrchestrator(
            formatter=formatter,
            outputs=[],   # 不實際輸出
            metadata={"env": "test"},
        )

        payload = orchestrator._build_payload(decision)
        _assert_contract(payload)

if __name__ == "__main__":
    test_output_contract_all_locales()
    print("✔ Output contract test passed")