import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
    
import time
from pathlib import Path

import pandas as pd

# Adapter + Validator
from trading_core.perception.market_adapter import MarketKlineAdapter
from shared_core.pb_lang.pb_event_validator import PBEventValidator


# ------------------------------------------------------------
# 工具：載入三份測試資料
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
# Adapter → PBEvent → Validator 壓力測試（單純感知層）
# ------------------------------------------------------------
def run_perception_stress():

    print("\n=== 🧪 Perception Layer Stress Test (Adapter + Validator) ===\n")

    # ⭐ 1) 初始化 validator（批次模式 soft-drop）
    validator = PBEventValidator(strict=False)

    # ⭐ 2) 建立 adapter（batch 模式 + validator）
    adapter = MarketKlineAdapter(mode="batch", validator=validator)

    # ⭐ 3) 載入資料
    df_15m, df_1h, df_4h = load_test_dfs()
    total_rows = len(df_15m) + len(df_1h) + len(df_4h)

    print(f"[Load] 15m rows = {len(df_15m)}, 1h rows = {len(df_1h)}, 4h rows = {len(df_4h)}")
    print(f"[Total] Raw rows = {total_rows}\n")

    stats = {
        "total_raw": 0,
        "event_ok": 0,
        "dropped": 0,
        "validator_fail": 0,
    }

    def process(df):
        for row in df.itertuples(index=False):
            raw = row._asdict()
            raw["symbol"] = "BTC/USDT"

            stats["total_raw"] += 1

            # ⭐ 4) Adapter 真實管線：filter → post_filter → make_event → validator
            try:
                event = adapter.to_event(raw)
            except Exception:
                stats["validator_fail"] += 1
                continue

            if event is None:
                stats["dropped"] += 1
                continue

            stats["event_ok"] += 1

    start = time.perf_counter()

    process(df_15m)
    process(df_1h)
    process(df_4h)

    elapsed = time.perf_counter() - start
    eps = stats["event_ok"] / elapsed if elapsed else 0

    # --------------------------------------------------------
    # 結果輸出
    # --------------------------------------------------------
    print("=== 📊 Perception Layer 結果 ===")
    print(f"原始資料總筆數 (raw rows)   ：{stats['total_raw']}")
    print(f"成功產生 PBEvent 筆數      ：{stats['event_ok']}")
    print(f"被 Filter / Anti-Poison 丟棄：{stats['dropped']}")
    print(f"Validator 直接報錯筆數     ：{stats['validator_fail']}")
    print("----------------------------------------")
    print(f"總耗時：{elapsed:.4f} 秒")
    print(f"吞吐量：{eps:,.0f} events/sec")
    print("========================================\n")


if __name__ == "__main__":
    run_perception_stress()
