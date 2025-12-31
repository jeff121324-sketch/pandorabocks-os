import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from locales.zh_TW.formatter import ZhTWFormatter
from locales.ja.formatter import JaFormatter
from locales.en.formatter import EnFormatter
from outputs.debug.console_output import ConsoleOutput
from outputs.warm.file_output import FileOutput
from outputs.output_orchestrator import DecisionOutputOrchestrator

decision = {
    "title": "Market Signal Evaluation",
    "summary": "Momentum indicators show neutral bias.",
    "decision": "HOLD",
    "confidence": 0.62,
    "reasons": ["RSI neutral", "Volume stable"],
}

outputs = [
    ConsoleOutput(),
    FileOutput(base_dir="outputs/warm"),
]

formatters = {
    "zh_TW": ZhTWFormatter(),
    "ja_JP": JaFormatter(),
    "en_US": EnFormatter(),
}

for locale, formatter in formatters.items():
    print(f"\n=== OUTPUT TEST [{locale}] ===")

    orchestrator = DecisionOutputOrchestrator(
        formatter=formatter,
        outputs=outputs,
        metadata={
            "system": "AISOP",
            "version": "0.5",
            "env": "dev",
            "locale": locale,
        },
    )

    orchestrator.dispatch(decision)

