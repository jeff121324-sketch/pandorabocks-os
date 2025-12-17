# trading_core/trading_bridge.py

from shared_core.pb_lang.pb_market import PBmarket
from pandora_core.event_bus import EventBus


class TradingBridge:
    """
    TradingBridge v1
    負責：
    ✔ 接收 data_bridge 合併後的 15m DataFrame
    ✔ 逐筆轉成 PBmarket.kline
    ✔ 丟到 EventBus
    ❌ 不做策略
    ❌ 不做下單
    ❌ 不做 AI 分析
    """

    def __init__(self, bus, gateway, *, symbol="BTC/USDT", interval="1m"):
        self.bus = bus
        self.gateway = gateway
        self.symbol = symbol
        self.interval = interval

class TradingBridge:
    """
    TradingBridge v2
    Ultra Zero-Copy Gateway Path
    -----------------------------
    ✔ data_bridge → DataFrame → PBEvent（全經由 PerceptionGateway）
    ✔ Zero-Copy Publish（fast_bus）
    ❌ 不做策略
    ❌ 不做 AI
    """

    def __init__(self, runtime, gateway, symbol="BTC/USDT", interval="1m"):
        self.rt = runtime
        self.gateway = gateway
        self.bus = runtime.bus
        self.fast_bus = runtime.fast_bus
        self.symbol = symbol
        self.interval = interval

    def emit_kline_df(self, df):
        """
        批次事件化（高速）
        df 必備欄位：
            - open, high, low, close, volume
        可選：
            - ts（float timestamp）
        """

        # 1) 從 bus 找 Runtime（取 fast_bus）
        rt = getattr(self.bus, "rt", None)
        if rt is None:
           print("[TradingBridge] ⚠ bus.rt 未注入，無法進入 Zero-Copy 模式")
           return

        # 🔥 修正：永遠使用 rt.fast_bus，不再 fallback self.bus
        fast_bus = getattr(rt, "fast_bus", None)
        if fast_bus is None:
            print("[TradingBridge] ⚠ runtime.fast_bus 缺失，改用 bus（RAW 層不會啟動）")
            fast_bus = self.bus  # 這行只當最終 fallback，用於緊急模式

        publish = fast_bus.publish
        gateway_process = self.gateway.process

        # 2) 預抓欄位 index
        cols = df.columns
        c_open   = cols.get_loc("open")
        c_high   = cols.get_loc("high")
        c_low    = cols.get_loc("low")
        c_close  = cols.get_loc("close")
        c_volume = cols.get_loc("volume")
        c_ts     = cols.get_loc("ts") if "ts" in cols else None

        symbol = self.symbol
        interval = self.interval

        count = 0

        # ============================================================
        # ⛓ Ultra Zero-Copy Gateway Pipeline
        # ============================================================
        for row in df.itertuples(index=False):

            raw = {
                "symbol": symbol,
                "open":   row[c_open],
                "high":   row[c_high],
                "low":    row[c_low],
                "close":  row[c_close],
                "volume": row[c_volume],
                "interval": interval,
            }

            if c_ts is not None:
                raw["ts"] = float(row[c_ts])
    
            # Gateway（adapter + filter + auto_fix + anti_poison + enrich + validate）
            event = self.gateway.process("market.kline", raw, soft=True)

            if event is None:
                continue

            # 🔥 經過 fast_bus → RAW EVENT LAYER 才會啟動
            publish(event)
            count += 1

        print(f"[TradingBridge] 📡 已發布 {count:,} 筆 K 線事件（Gateway Zero-Copy Path）")