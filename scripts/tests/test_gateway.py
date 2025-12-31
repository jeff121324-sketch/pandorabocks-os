# test_gateway.py
import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/）===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared_core.perception_core.perception_gateway import PerceptionGateway
from shared_core.pb_lang.pb_event_validator import PBEventValidator
from trading_core.perception.market_adapter import MarketKlineAdapter
from shared_core.perception_core.simple_text_adapter import SimpleTextInputAdapter
from shared_core.perception_core.core import PerceptionCore
# ------------------------------------------------------
# 1) 建立核心 PerceptionCore
# ------------------------------------------------------
core = PerceptionCore()

# ------------------------------------------------------
# 2) 建立 Validator
# ------------------------------------------------------
validator = PBEventValidator(strict=True)

# ------------------------------------------------------
# 3) 建立 Gateway（新版必須同時給 core + validator）
# ------------------------------------------------------
gateway = PerceptionGateway(core, validator)
print("[Gateway] 🌐 Initialized")

# ------------------------------------------------------
# 4) 建立各種 Adapter
# ------------------------------------------------------
market_adapter = MarketKlineAdapter(mode="realtime", validator=validator)
gateway.register_adapter("market.kline", market_adapter)
print("[Gateway] 🟢 MarketKlineAdapter registered")

text_adapter = SimpleTextInputAdapter(validator=validator)
gateway.register_adapter("text.input", text_adapter)
print("[Gateway] 🟢 SimpleTextInputAdapter registered")

# ------------------------------------------------------
# 5) 測試一筆 K 線資料
# ------------------------------------------------------
raw = {
    "symbol": "BTC/USDT",
    "open": 100,
    "high": 110,
    "low": 95,
    "close": 105,
    "volume": 123,
    "interval": "1m",
    "ts": 1765283457.9,
}

event = gateway.process("market.kline", raw, soft=False)

print("\n=== 最終事件（market.kline） ===")
print(event)
print(event.to_dict())

# ------------------------------------------------------
# 6) 測試文字感知來源
# ------------------------------------------------------
ev2 = gateway.process("text.input", {"text": "Hello AI!"})
print("\n=== 最終事件（text.input） ===")
print(ev2)
print(ev2.to_dict())
