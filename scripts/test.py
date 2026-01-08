import time
import traceback

# === 測 TradingRuntime ===
from trading_core.trading_runtime import TradingRuntime

# === 測 Event Schema ===
from shared_core.event_schema import PBEvent  
from shared_core.pb_lang.pb_market import PBmarket


# === 測 Bridge ===
from trading_core.trading_bridge import TradingBridge

# === 測 Pandora Runtime ===
from pandora_core.pandora_runtime import PandoraRuntime
from pandora_core.event_bus import EventBus
# === 測 AISOP ===
from aisop_core.aisop_runtime import AISOPRuntime


# --------------------------------
# 📌 共同輔助函數
# --------------------------------
def ok(label):
    print(f"[OK] {label}")

def fail(label, err):
    print(f"\n[FAIL] {label}")
    print(err)
    print("\n==== 測試停止 ====\n")
    exit(1)


# -------------------------------
# 🔧 Test 1 — Event Schema Test
# -------------------------------
def test_event_schema():
    print("\n=== Test 1: Event Schema ===")
    try:
        payload = {
            "symbol": "BTC/USDT",
            "open": 1.0,
            "high": 2.0,
            "low": 0.5,
            "close": 1.8,
            "volume": 100.0,
            "interval": "1m",
        }

        event = PBEvent(
            type="market.kline",
            payload=payload,
            source="unittest",
            ts=1234567890.0,
        )

        ok("Event Schema 建立成功")

    except Exception as e:
        fail("Event Schema 建立失敗", e)
        raise e

# ---------------------------------------------
# Test 2 — TradingRuntime Stress Test
# ---------------------------------------------
def test_trading_runtime():
    try:
        bus = EventBus()
        runtime = TradingRuntime(bus, symbol="BTC/USDT")

        for _ in range(5):
            runtime.tick()

        ok("TradingRuntime 壓力測試成功")

    except Exception as e:
        fail("TradingRuntime 壓力測試失敗", e)
        raise e

# -------------------------------
# 🔌 Test 3 — TradingBridge 測試
# -------------------------------
def test_bridge():
    print("\n=== Test 3: TradingBridge ===")

    try:
        bus = EventBus()               # ⭐ 必須建立 bus
        bridge = TradingBridge(bus=bus)  # ⭐ 必須傳入 bus

        # 假資料
        import pandas as pd
        df = pd.DataFrame([
            {"open": 1.0, "high": 2.0, "low": 0.5, "close": 1.8, "volume": 100},
            {"open": 1.1, "high": 2.1, "low": 0.6, "close": 1.9, "volume": 110},
        ])

        bridge.emit_kline_df(df)

        ok("TradingBridge emit_kline_df 成功")

    except Exception as e:
        fail("TradingBridge 測試失敗", e)
        raise e


# --------------------------------
# 📌 Test 4 — Pandora Plugin Framework
# --------------------------------
def test_pandora_plugin():
    print("\n=== Test 4: Pandora Plugin Framework ===")

    try:
        pandora = PandoraRuntime(base_dir=".")
        aisop = AISOPRuntime(bus=pandora.bus)

        pandora.install_plugin(aisop)
        ok("Pandora Plugin 安裝成功")

    except Exception as e:
        fail("Pandora Plugin 測試失敗", e)


# --------------------------------
# 📌 Test 5 — AISOP 整合測試
# --------------------------------
def test_aisop_integration():
    print("\n=== Test 5: AISOP Integration ===")

    try:
        pandora = PandoraRuntime()
        aisop = AISOPRuntime(bus=pandora.bus)
        pandora.install_plugin(aisop)

        # 正確掛法（TradingRuntime 是 external tick）
        tr = TradingRuntime(bus=pandora.bus, symbol="BTC/USDT")
        pandora.add_external_tick(tr.tick)

        ok("AISOP 整合測試成功")

    except Exception as e:
        fail("AISOP 整合測試失敗", e)
        raise e

# --------------------------------
# 📌 Test 6 — Full System Integration（含 Full Runtime AISOP）
# --------------------------------
def test_full_system():
    print("\n=== Test 6: Full System Integration ===")

    try:
        # 建立 Pandora OS
        pandora = PandoraRuntime(base_dir=".")
        aisop = AISOPRuntime(bus=pandora.bus)

        # 安裝 AISOP plugin（會註冊到 AIManager）
        pandora.install_plugin(aisop)

        # 建立 TradingRuntime（事件來源）
        tr = TradingRuntime(bus=pandora.bus, symbol="BTC/USDT")
        pandora.add_external_tick(tr)

        print("[TEST] Running 5 ticks...")

        for _ in range(5):
            pandora.tick()   # Pandora 主系統 tick
            time.sleep(1)    # 模擬每秒 heartbeat/tick

        ok("Full System 整合運作成功")

    except Exception as e:
        fail("Full System 整合測試失敗", e)
        

# --------------------------------
# 📌 Main
# --------------------------------
if __name__ == "__main__":
    print("=== 🚀 AISOP / Pandora Total Stress Test v1 ===")

    test_event_schema()
    test_trading_runtime()
    test_bridge()
    test_pandora_plugin()
    test_aisop_integration()
    test_full_system()   # ⭐ 新增的測試

    print("\n=== 🎉 全部測試皆通過！System OK ===")

