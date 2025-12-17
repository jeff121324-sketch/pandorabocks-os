import time
from pathlib import Path
from threading import Thread

import pandas as pd

# Pandora OS Runtime & TradingBridge / Adapter
from pandora_core.pandora_runtime import PandoraRuntime
from trading_core.trading_bridge import TradingBridge
from trading_core.perception.market_adapter import MarketKlineAdapter


# ------------------------------------------------------------
# 載入測試資料（三份一起上）
# ------------------------------------------------------------
def load_test_dfs():
    base = Path(__file__).resolve().parent / "test_data"

    df_15m = pd.read_csv(base / "BTC_USDT_15m.csv")
    df_1h = pd.read_csv(base / "BTC_USDT_1h.csv")
    df_4h = pd.read_csv(base / "BTC_USDT_4h.csv")

    df_15m["interval"] = "15m"
    df_1h["interval"] = "1h"
    df_4h["interval"] = "4h"

    return df_15m, df_1h, df_4h


# ------------------------------------------------------------
# 建立一個簡單的 Listener，模擬 Runtime 在吃事件
# ------------------------------------------------------------
def make_dummy_listener():
    count = {"n": 0}

    def on_kline(event):
        # 這邊不要做太重的事，只增加計數就好
        count["n"] += 1

    return on_kline, count


# ------------------------------------------------------------
# Runtime 壓力測試：Adapter → PBEvent → EventBus → Listener
# ------------------------------------------------------------
def run_runtime_stress():
    # 1) 啟動 PandoraRuntime（含 EventBus / Zero-Copy Bus）
    base = Path(__file__).resolve().parent
    print("\n[RuntimeStress] 🚀 Initializing PandoraRuntime ...")
    rt = PandoraRuntime(base)

    # 2) 註冊 market 感知層 Adapter
    adapter = MarketKlineAdapter(mode="batch")
    rt.register_adapter("market", adapter)
    print("[RuntimeStress] 🧩 MarketKlineAdapter 已註冊")

    # 3) 在 EventBus 上掛一個簡單 Listener（模擬真正策略 / Runtime）
    listener, counter = make_dummy_listener()
    rt.fast_bus.subscribe("market.kline", listener)
    print("[RuntimeStress] 👂 已掛載 market.kline Listener")

    # 4) 建立 TradingBridge（使用主 bus，內部會自動走 fast_bus）
    bridge = TradingBridge(rt.bus, "BTC/USDT")

    # 5) 載入三份測試資料
    df_15m, df_1h, df_4h = load_test_dfs()
    total_rows = len(df_15m) + len(df_1h) + len(df_4h)
    print(f"[RuntimeStress] 📘 15m={len(df_15m)}, 1h={len(df_1h)}, 4h={len(df_4h)} (Total={total_rows})")

    # 6) 定義三個 worker，模擬三來源同時灌進來
    def worker(df, label):
        print(f"[RuntimeStress] ▶ {label} start emit_kline_df(...)")
        bridge.emit_kline_df(df)
        print(f"[RuntimeStress] ◀ {label} done")

    print("\n=== 🚀 Runtime Stress Test（三來源並行）啟動 ===")
    start = time.perf_counter()

    t1 = Thread(target=worker, args=(df_15m, "15m"))
    t2 = Thread(target=worker, args=(df_1h, "1h"))
    t3 = Thread(target=worker, args=(df_4h, "4h"))

    t1.start()
    t2.start()
    t3.start()

    t1.join()
    t2.join()
    t3.join()

    end = time.perf_counter()
    elapsed = end - start

    total_events = counter["n"]
    eps = total_events / elapsed if elapsed > 0 else 0.0

    print("\n=== 📊 Runtime Stress Test 結果 ===")
    print(f"原始資料總筆數        ：{total_rows}")
    print(f"Listener 實際收到事件數：{total_events}")
    print("----------------------------------------")
    print(f"總耗時：{elapsed:.4f} 秒")
    print(f"吞吐量：{eps:,.0f} events/sec")
    print("========================================\n")


if __name__ == "__main__":
    run_runtime_stress()
