"""
Unified Stress Test v1
完整壓測：
    Adapter → Gateway → TradingBridge → EventBus → Runtime Listener → ReplayEngine
"""

import time
from pathlib import Path
from threading import Thread

import pandas as pd
from dotenv import load_dotenv
load_dotenv()
# === Pandora Core ===
from pandora_core.pandora_runtime import PandoraRuntime

# === Perception Layer ===
from shared_core.perception_core.perception_gateway import PerceptionGateway
from trading_core.perception.market_adapter import MarketKlineAdapter
from shared_core.pb_lang.pb_event_validator import PBEventValidator

# === Trading Bridge ===
from trading_core.trading_bridge import TradingBridge

# === Replay Engine ===
from shared_core.replay.replay_engine import ReplayEngine

from shared_core.perception_core.core import PerceptionCore
from shared_core.perception_core.perception_gateway import PerceptionGateway
# ----------------------------------------------------------------------
# 1. Load test data
# ----------------------------------------------------------------------
def load_test_dfs():
    base = Path(__file__).resolve().parent / "test_data"

    df_15m = pd.read_csv(base / "BTC_USDT_15m.csv")
    df_1h = pd.read_csv(base / "BTC_USDT_1h.csv")
    df_4h = pd.read_csv(base / "BTC_USDT_4h.csv")

    df_15m["interval"] = "15m"
    df_1h["interval"] = "1h"
    df_4h["interval"] = "4h"

    total = len(df_15m) + len(df_1h) + len(df_4h)
    print(f"[Data] Loaded 15m={len(df_15m)}, 1h={len(df_1h)}, 4h={len(df_4h)} (Total={total})")

    return df_15m, df_1h, df_4h, total


# ----------------------------------------------------------------------
# 2. Dummy Listener（模擬策略核心 / Runtime）
# ----------------------------------------------------------------------
def make_dummy_listener():
    counter = {"n": 0}

    def on_event(event):
        counter["n"] += 1

    return on_event, counter


# ----------------------------------------------------------------------
# 3. Stress Test: Adapter → Gateway → EventBus → Listener
# ----------------------------------------------------------------------
def stress_runtime(df_list, total_rows):
    print("\n=== 🚀 Stress Test: Runtime × Gateway × TradingBridge ===")

    # ① Runtime 初始化
    rt = PandoraRuntime(Path("."))
    print("[Init] PandoraRuntime OK")

    # ② 建立 Validator + Adapter + Gateway
    validator = PBEventValidator(strict=False)
    core = PerceptionCore()
    gateway = PerceptionGateway(core, validator)
    adapter = MarketKlineAdapter(mode="batch", validator=validator)

    gateway.register_adapter("market.kline", adapter)
    rt.register_adapter("market", adapter)  # 若有需要 Runtime 查詢 adapter

    print("[Init] Adapter + Gateway OK")

    # ③ Listener（模擬策略核心）
    listener, counter = make_dummy_listener()
    rt.fast_bus.subscribe("market.kline", listener)
    print("[Init] Listener OK")

    # ④ TradingBridge v2（Gateway Path）
    bridge = TradingBridge(rt, gateway, symbol="BTC/USDT")

    # ⑤ 定義 worker
    def worker(df, label):
        print(f"[Worker] ▶ {label} start")
        bridge.emit_kline_df(df)
        print(f"[Worker] ◀ {label} done")

    # ⑥ 並行壓力測試
    start = time.perf_counter()

    threads = [
        Thread(target=worker, args=(df_list[0], "15m")),
        Thread(target=worker, args=(df_list[1], "1h")),
        Thread(target=worker, args=(df_list[2], "4h")),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    elapsed = time.perf_counter() - start
    events = counter["n"]

    print("\n=== 📊 Runtime Stress Result ===")
    print(f"原始資料總筆數    ：{total_rows}")
    print(f"Listener 接收事件 ：{events}")
    print(f"耗時              ：{elapsed:.4f} 秒")
    print(f"吞吐量            ：{events / elapsed:,.0f} events/sec")
    print("================================================\n")


# ----------------------------------------------------------------------
# 4. Stress Test: ReplayEngine v2
# ----------------------------------------------------------------------
def stress_replay(path: str):
    print("\n=== 🔁 Stress Test: ReplayEngine v2 ===")

    # ① Runtime
    rt = PandoraRuntime(Path("."))

    # ② Gateway + Adapter
    validator = PBEventValidator(strict=False)
    gateway = PerceptionGateway(validator=validator)
    adapter = MarketKlineAdapter(mode="batch", validator=validator)
    gateway.register_adapter("market.kline", adapter)

    # ③ Listener
    listener, counter = make_dummy_listener()
    rt.fast_bus.subscribe("market.kline", listener)

    # ④ ReplayEngine
    engine = ReplayEngine(gateway, rt.fast_bus)

    start = time.perf_counter()
    count = engine.replay(
        path,
        key="market.kline",
        speed=0,  # 無限快
        ignore_timestamp=True,
        soft=True,
    )
    elapsed = time.perf_counter() - start

    print("\n=== 📊 Replay Stress Result ===")
    print(f"回放事件數        ：{count}")
    print(f"耗時              ：{elapsed:.4f} 秒")
    print(f"吞吐量            ：{count / elapsed:,.0f} events/sec")
    print("================================================\n")


# ----------------------------------------------------------------------
# 5. Main
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # --- 資料 ---
    df_15m, df_1h, df_4h, total = load_test_dfs()

    # --- Runtime × Gateway × TradingBridge 壓測 ---
    stress_runtime([df_15m, df_1h, df_4h], total)

    # --- ReplayEngine v2 壓測（建議把事件 log 先匯出）---
    # stress_replay("events.jsonl")
