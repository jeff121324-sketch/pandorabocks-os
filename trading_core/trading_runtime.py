# trading_core/trading_runtime.py

from pandora_core.event_bus import EventBus
from trading_core.trading_bridge import TradingBridge
from trading_core.data_provider.b_layer.fetcher import MarketDataFetcher
from trading_core.perception.market_adapter import MarketKlineAdapter
from shared_core.perception_core.perception_gateway import PerceptionGateway
from shared_core.world.capability_types import WorldCapability
from trading_core.decision_pipeline.listener import make_on_market_kline
from trading_core.probes.kline_integrity_probe import KlineIntegrityProbe
from trading_core.probes.kline_alignment_probe import KlineAlignmentProbe
from trading_core.state.world_trust_aggregator import WorldTrustAggregator
from trading_core.state.world_health_state import WorldHealthState
from shared_core.event_schema import PBEvent
from trading_core.decision_gate import TradingDecisionGate
from trading_core.state.market_regime import build_market_regime
def _probe_icon(status: str) -> str:
    return {
        "OK": "✅",
        "INFO": "ℹ️",      # ← 加這行
        "WARNING": "⚠️",
        "ERROR": "❌",
    }.get(status, "❓")

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

    def __init__(        self, rt, symbol="BTC/USDT"):
        self.bus = rt.bus
        self.fast_bus = rt.fast_bus
        self.symbol = symbol
        self._seen_probe_warnings = set()
        self.decision_gate = TradingDecisionGate()
        # =====================================================
        # 🌍 Phase B v2: World Health State
        # =====================================================
        self.world_trust = WorldTrustAggregator()
        self._last_world_health: WorldHealthState | None = None

        # === Market Data ===
        self.fetcher = MarketDataFetcher()

        # === Perception Gateway ===
        gateway = getattr(rt, "gateway", None)
        if gateway is None:
            raise RuntimeError("[TradingRuntime] ❌ PandoraRuntime 未設定 gateway")

        # === Trading Bridge（只負責事件化）===
        self.bridge = TradingBridge(rt, gateway, symbol=self.symbol)
        # =====================================================
        # 🧪 Strategy Probe（Phase 1）
        # =====================================================
        self.kline_probe = KlineIntegrityProbe()
        self.kline_alignment_probe = KlineAlignmentProbe()
        # =====================================================
        # 🔥 A MODE: 明確掛載 Decision Listener（關鍵）
        # =====================================================
        self.fast_bus.subscribe("market.kline", make_on_market_kline)

        print("[TradingRuntime] 🔔 DecisionListener attached (A-MODE)")

        self.bus.subscribe(
            "system.governance.decision.created",
            lambda event: self.decision_gate.update_governance(event.payload)
        )
        # =====================================================
        # 🧪 Phase 1: Kline Integrity Probe（只讀）
        # =====================================================
        def _on_kline_probe(event):
            report = self.kline_probe.on_kline(event)
            if report and report.status != "OK":
                print(f"[Probe:{report.probe_name}] {report}")

        self.fast_bus.subscribe("market.kline", _on_kline_probe)
        print("[TradingRuntime] 🧪 KlineIntegrityProbe attached")

        # =====================================================
        # 🧪 Phase 2: Kline Alignment Probe（只讀）
        # =====================================================
        def _on_kline_alignment_probe(event):
            report = self.kline_alignment_probe.on_kline(event)
            if not report:
                return

            icon = _probe_icon(report.status)

            # ===============================
            # 🛑 Step 1.5-B: WARNING 去重
            # ===============================
            if report.status == "WARNING" and report.data_epoch:
                key = (
                    report.probe_name,
                    report.symbol,
                    report.interval,
                    report.data_epoch.name,
                    tuple(a.code for a in report.anomalies),
                )

                if key in self._seen_probe_warnings:
                    return  # ⛔ 同一裂痕，不再洗畫面
                else:
                    self._seen_probe_warnings.add(key)

            # ===============================
            # 正常輸出（表現層）
            # ===============================
            if report.status == "INFO" and report.data_epoch:
                key = (
                    report.probe_name,
                    report.symbol,
                    report.interval,
                    report.data_epoch.name,
                )

                if key in self._seen_probe_warnings:
                    return   # ⛔ 同一資料世代，安靜
                else:
                    self._seen_probe_warnings.add(key)

            # =====================================================
            # 🌍 Phase B v2: World Trust Aggregation（一定要在這裡）
            # =====================================================
            health = self.world_trust.ingest_probe_report(report)
        
            if health and health != self._last_world_health:
                self._last_world_health = health
        
                print(
                    f"[WorldHealth] {health.level.upper()} | "
                    + " ; ".join(health.reasons)
                )

                event = PBEvent(
                    type=f"world.health.{health.level}",  # warning / error / ok
                    payload={
                        "world_id": "crypto.btc.spot",
                        "reason": ",".join(health.reasons),
                        "interval": "multi",  # 或之後由 aggregator 算
                        "level": health.level,
                    },
                    source="trading_runtime",
                    priority=0,
                    tags=["health", "world", "trading"],                
                )
                self.bus.publish(event)

        self.fast_bus.subscribe("market.kline", _on_kline_alignment_probe)
        print("[TradingRuntime] 🧪 KlineAlignmentProbe attached")

        self._started = True
        print("[TradingRuntime] Initialized")

        # =====================================================
        # 🎭 Trade Persona Sentinels (v1-strict)
        # =====================================================
        from trading_core.personas.trade_attacker_calculator import TradeAttackerSentinel
        from trading_core.personas.trade_defender_calculator import TradeDefenderSentinel
        from trading_core.personas.trade_balancer_calculator import TradeBalancerSentinel

        self.trade_personas = [
            TradeAttackerSentinel(self.fast_bus),
            TradeDefenderSentinel(self.fast_bus),
            TradeBalancerSentinel(self.fast_bus),
        ]

        for persona in self.trade_personas:
            # 市場主幹（最高頻）
            self.fast_bus.subscribe("market.kline", persona.on_market_kline)

            # 風險快照（較低頻，但關鍵）
            self.bus.subscribe("risk.snapshot", persona.on_risk_snapshot)

        print("[TradingRuntime] 🎭 Trade Persona Sentinels attached (v1-strict)")
        # =====================================================
        # 👂 Trade Persona Signal Listener (observe only)
        # =====================================================
        def _on_trade_persona_signal(event):
            payload = event.payload
            signal = payload.get("signal", {})

            decision, info = self.decision_gate.evaluate(signal)

            if decision != "ALLOW":
                print(
                    f"[DecisionGate] ⛔ BLOCKED | "
                    f"{payload.get('source')} | "
                    f"reason={info}"
                )
                return

            # ✅ ALLOW → emit trading intent
            intent = PBEvent(
                type="trading.intent.execute",
                payload={
                    "symbol": self.symbol,
                    "action": signal.get("stance_hint"),
                    "confidence": info,
                    "source": payload.get("source"),
                },
                source="trading_runtime",
                tags=["trading", "intent"],
            )

            print(
                f"[DecisionGate] ✅ ALLOW | "
                f"{signal.get('stance_hint')} (conf={info})"
            )

            self.bus.publish(intent)
        self.bus.subscribe("persona.signal.trade", _on_trade_persona_signal)


        print("[TradingRuntime] 👂 TradePersonaSignal listener attached")

        def debug_event_probe(event):
            print(f"[EVENT-PROBE] got event type = {event.type}")

        self.bus.subscribe("*", debug_event_probe)
        print("[TradingRuntime] 🧪 Event probe attached")
        # =====================================================
        # 🧪 POST-ATTACH PROBE（Phase 1 最終驗收）
        # =====================================================
        try:
            live_provider = getattr(rt, "live_market_tick_provider", None)

            if live_provider is not None:
                import time

                now_ms = int(time.time() * 1000)

                live_provider.emit_kline(
                    symbol=self.symbol,
                    interval="1m",
                    open_time_ms=now_ms,
                    close_time_ms=now_ms,
                    open_price=0,
                    high_price=0,
                    low_price=0,
                    close_price=0,
                    volume=0,
                    source="post_attach_probe",
                )

                print("[TradingRuntime] 🧪 post_attach_probe emitted")

            else:
                print(
                    "[TradingRuntime] ⚠ LiveMarketTickProvider not found, "
                    "post_attach_probe skipped"
                )

        except Exception as e:
            # 🔒 post_attach_probe 不得影響世界啟動
            print(
                f"[TradingRuntime] ❌ post_attach_probe failed: {e!r}"
            )
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
    # 🚨 Trading → Health Error 上報出口（唯一）
    # =========================================================
    def report_health_error(self, reason: str, detail: str):
        from shared_core.event_schema import PBEvent

        event = PBEvent(
            type="world.health.error",
            payload={
                "world_id": "crypto.btc.spot",
                "reason": reason,
                "detail": detail,
            },
            source="trading_runtime",
            priority=0,
            tags=["health", "error", "trading"],
        )

        self.bus.publish(event)
    # =========================================================
    # Pandora 每秒呼叫
    # =========================================================
    def tick(self):
        if not self._started:
            return

        try:
            self._process_once()

        except Exception as e:
            # 🚨 任何 TradingRuntime 無法自行處理的錯誤
            self.report_health_error(
                reason="trading_runtime_exception",
                detail=repr(e),
            )
            raise  # ⛔ 讓 Pandora OS 決定是否 Freeze

    # =========================================================
    # 📌 核心處理流程
    # =========================================================
    def _process_once(self):
        
        print("[TradingRuntime] 📈 讀取市場資料中…")

        df = self.fetcher.load()

        if df is None or len(df) == 0:
            self.report_health_error(
            reason="market_data_empty",
            detail="MarketDataFetcher returned empty dataframe",
        )
            return
        

        print(f"[TradingRuntime] 📘 已取得 {len(df)} 筆資料，開始事件化…")

        # === df → PBmarket.kline → bus.publish ===
        self.bridge.emit_kline_df(df)

        print("[TradingRuntime] 🧩 事件化完成！")