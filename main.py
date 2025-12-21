
import sys
from pathlib import Path

from shared_core.path_loader import load_paths
load_paths()

from dotenv import load_dotenv
load_dotenv()
# === 自動載入整個 Pandora 生態系 ===
ROOT = Path(__file__).resolve().parent

def add_path(path: Path):
    """避免重複加入 sys.path，也更乾淨"""
    p = str(path)
    if p not in sys.path:
        sys.path.append(p)

# --- 加入母平台核心 ---
add_path(ROOT)  # 根目錄
add_path(ROOT / "pandora_core")

# --- 加入共享核心（工具、EventBus、時間、df工具等） ---
add_path(ROOT / "shared_core")

# --- 加入 PB-Lang（所有標準事件語言） ---
add_path(ROOT / "pb_lang")

# --- 加入 TradingCore（可拔插）---
add_path(ROOT / "trading_core")

# --- 加入 AISOP Core（可拔插）---
add_path(ROOT / "aisop_core")

print("[PathLoader] 🔧 系統模組路徑載入完成")

from pandora_core.pandora_runtime import PandoraRuntime
from trading_core.trading_runtime import TradingRuntime


def main():
    base = Path(__file__).resolve().parent

    print("[Main] 🚀 Initializing Pandora OS...")
    rt = PandoraRuntime(base)

    # ---------------------------------------------------
    # 註冊感知層 Adapter（市場 K 線 → PBEvent）
    # ---------------------------------------------------
    from trading_core.perception.market_adapter import MarketKlineAdapter
    rt.register_adapter("market", MarketKlineAdapter())
    print("[Main] 🧩 MarketKlineAdapter 已註冊")


    # ---------------------------------------------------
    # 載入 AI Plugin：AISOPRuntime（人格模組）
    # ---------------------------------------------------
    try:
        rt.load_plugin("aisop_core.aisop_runtime", "AISOPRuntime")
    except Exception as e:
        print("[Main] ⚠ AISOPRuntime load failed:", e)

    # ---------------------------------------------------
    # 建立 TradingRuntime（世界心跳）
    # ---------------------------------------------------
    try:
        trade_rt = TradingRuntime(rt, symbol="BTC/USDT")

        # ➤ 只註冊為「外部心跳源」
        rt.register_external_tick_source(trade_rt)

        print("[Main] ✔ TradingRuntime 已啟動並掛載 Plugin")
    except Exception as e:
        print("[Main] ⚠ TradingRuntime init failed:", e)

    # ---------------------------------------------------
    # 啟動 OS
    # ---------------------------------------------------
    rt.run_forever()


if __name__ == "__main__":
    main()