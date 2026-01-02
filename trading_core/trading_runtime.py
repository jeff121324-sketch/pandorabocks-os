# trading_core/trading_runtime.py

from pandora_core.event_bus import EventBus
from trading_core.trading_bridge import TradingBridge
from trading_core.data_provider.fetcher import MarketDataFetcher
from trading_core.perception.market_adapter import MarketKlineAdapter
from shared_core.perception_core.perception_gateway import PerceptionGateway
from shared_core.world.capability_types import WorldCapability
from trading_core.decision_pipeline.listener import on_market_kline

class TradingRuntime:
    """
    TradingRuntime v2（External Tick Source）
    ✔ 由 Pandora OS 自動 tick
    ✔ 主動掛載 EventBus listener
    ✔ A 模式安全（不下單）
    """
    plugin_name = "TradingRuntime"

    required_capabilities = [
        WorldCapability.EXTERNAL_TICK,
        WorldCapability.MULTI_RUNTIME,
    ]

    def __init__(self, rt, symbol="BTC/USDT"):
        self.bus = rt.bus
        self.fast_bus = rt.fast_bus
        self.symbol = symbol

        # === Market Data ===
        self.fetcher = MarketDataFetcher()

        # === Perception Gateway ===
        gateway = getattr(rt, "gateway", None)
        if gateway is None:
            raise RuntimeError("[TradingRuntime] ❌ PandoraRuntime 未設定 gateway")

        # === Trading Bridge（只負責事件化）===
        self.bridge = TradingBridge(rt, gateway, symbol=self.symbol)

        # =====================================================
        # 🔥 A MODE: 明確掛載 Decision Listener（關鍵）
        # =====================================================
        self.fast_bus.subscribe("market.kline", on_market_kline)

        print("[TradingRuntime] 🔔 DecisionListener attached (A-MODE)")

        self._started = True
        print("[TradingRuntime] Initialized")

        def debug_event_probe(event):
            print(f"[EVENT-PROBE] got event type = {event.type}")

        self.bus.subscribe("*", debug_event_probe)
        print("[TradingRuntime] 🧪 Event probe attached")
    # =========================================================
    # TradingRuntime 本身的市場事件（可留著 debug）
    # =========================================================
    def on_kline(self, event):
        payload = event.payload
        print(
            f"[TradingRuntime] 📥 kline "
            f"{payload.get('symbol')} "
            f"{payload.get('interval')} "
            f"close={payload.get('close')}"
        )

    # =========================================================
    # Pandora 每秒呼叫
    # =========================================================
    def tick(self):
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