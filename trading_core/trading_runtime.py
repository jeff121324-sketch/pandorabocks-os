# trading_core/trading_runtime.py

from pandora_core.event_bus import EventBus
from trading_core.trading_bridge import TradingBridge
from trading_core.data_provider.fetcher import MarketDataFetcher
from trading_core.perception.market_adapter import MarketKlineAdapter
from shared_core.perception_core.perception_gateway import PerceptionGateway
from shared_core.world.capability_types import WorldCapability

class TradingRuntime:
    """
    TradingRuntime v2（完全 plugin 化）
    ✔ 由 Pandora OS 自動 tick
    ✔ 可獨立取代 / 插拔
    ✔ 資料來源 → PB-Lang → EventBus（Gateway）
    """
    plugin_name = "TradingRuntime"
    # === Plugin Capability Declaration v1.1 ===
    required_capabilities = [
        WorldCapability.EXTERNAL_TICK,
        WorldCapability.MULTI_RUNTIME,
    ]
    def __init__(self, rt, symbol="BTC/USDT"):
        self.bus = rt.bus
        self.fast_bus = rt.fast_bus            # ★ 統一從 Runtime 取得 fast_bus
        self.symbol = symbol

        # ★ 交易市場資料 fetcher（你原本的功能不動）
        self.fetcher = MarketDataFetcher()

        # ★ 取得 PerceptionGateway（必須事先由 PandoraRuntime 設定）
        gateway = getattr(rt, "gateway", None)
        if gateway is None:
            raise RuntimeError("[TradingRuntime] ❌ PandoraRuntime 未設定 gateway")

        # ★ 建立 TradingBridge v3（吃 runtime + gateway）
        self.bridge = TradingBridge(rt, gateway, symbol=self.symbol)

        self._started = True
        print("[TradingRuntime] Initialized")


    # =========================================================
    # Plugin 載入後由 Pandora 呼叫
    # =========================================================
    def on_load(self, bus):
        bus.subscribe("market.kline", self.on_kline)
        print("[TradingRuntime] 🔔 已訂閱事件：market.kline")

    # =========================================================
    # TradingRuntime 的事件入口
    # =========================================================
    def on_kline(self, event):
        payload = event.payload

        symbol = payload.get("symbol")
        close = payload.get("close")
        interval = payload.get("interval")

        print(f"[TradingRuntime] 📥 收到 K 線事件：{symbol} {interval} close={close}")

    # =========================================================
    # 手動呼叫（Debug 用）
    # =========================================================
    def run_once(self):
        """手動觸發一次資料讀取（Debug 用）"""
        print("[DEBUG] TradingRuntime.run_once 被呼叫")
        self._process_once()

    # =========================================================
    # Pandora 自動呼叫
    # =========================================================
    def tick(self):
        """Pandora Runtime 每秒呼叫此函式"""
        if not self._started:
            return
        self._process_once()

    # =========================================================
    # 📌 核心處理流程
    # =========================================================
    def _process_once(self):
        print("[TradingRuntime] 📈 讀取市場資料中…")

        df = self.fetcher.load()

        if df is None or len(df) == 0:
            print("[TradingRuntime] ⚠ 無資料，略過。")
            return

        print(f"[TradingRuntime] 📘 已取得 {len(df)} 筆資料，開始事件化…")

        # === df → PBmarket.kline → bus.publish ===
        self.bridge.emit_kline_df(df)

        print("[TradingRuntime] 🧩 事件化完成！")