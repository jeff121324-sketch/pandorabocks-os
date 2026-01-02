"""
pandora_runtime.py
Pandora OS 的啟動器，負責：
- 初始化 AIManager、ModuleLoader、ErrorManager、HealthCheck
- 掛載不同的子文明（TradingCore / AISOP / others）
- 提供 run() 介面給 main.py 啟動
"""

import inspect
import asyncio
import threading
import time
from pathlib import Path
from shared_core.event.zero_copy_event_bus import ZeroCopyEventBus
from pandora_core.event_bus import EventBus
from shared_core.pb_lang.pb_event_validator import PBEventValidator
from shared_core.event_raw.event_log_writer import EventLogWriter
from shared_core.perception_core.core import PerceptionCore
from shared_core.perception_core.perception_gateway import PerceptionGateway
from pandora_core.perception_audit.auditor_runtime import PerceptionSafetyAuditor
from pandora_core.perception_audit.scheduler import run_audit_loop
from shared_core.event_raw.event_log_reader import EventLogReader
from .ai_manager import AIManager
from .module_loader import ModuleLoader
from storage_core.storage_manager import StorageManager
from storage_core.log_rotator import LogRotator, RotatePolicy, ArchivePolicy
from pandora_core.replay_runtime import ReplayRuntime
from shared_core.event_schema import PBEvent

from dotenv import load_dotenv
load_dotenv()

class PandoraRuntime:
    def __init__(self, base_dir="."):
        self.base_dir = base_dir
        self.world_id = "pandora"
        self.plugins = {}

        # =========================================================
        # PBEvent Validator（全系統唯一）
        # =========================================================
        self.validator = PBEventValidator(strict=False, soft=True)

        # =========================================================
        # EventBus（安全）＋ ZeroCopyBus（高速）
        # =========================================================
        self.bus = EventBus(validator=self.validator)
        self.bus.rt = self

        self.fast_bus = ZeroCopyEventBus()
        self.fast_bus.rt = self

        print("[PandoraRuntime] ⚡ Zero-Copy EventBus 已啟用")

        # =========================================================
        # Core / Gateway / Manager
        # =========================================================
        self.core = PerceptionCore()
        self.gateway = PerceptionGateway(self.core, self.validator)
        self.manager = AIManager(self.bus)
        self.loader = ModuleLoader()

        self.external_ticks = []
        self.adapters = {}

        print("[PandoraRuntime] 🌍 Initialized")

        # =========================================================
        # Runtime Attach Guard（World Capability）
        # =========================================================
        from shared_core.world.registry import WorldRegistry
        from shared_core.world.capability_gate import WorldCapabilityGate
        from pandora_core.runtime_attach_guard import RuntimeAttachGuard
        from shared_core.world.world_context import WorldContext

        # 1️⃣ 建立 World Registry（單一實例）
        self.world_registry = WorldRegistry()

        # 建立 WorldContext（這才是真正的「世界」）
        pandora_world = WorldContext(
            world_id="pandora",
            world_type="core",          
            owner="pandora-os",         # ← 新增（或用你的組織 / 系統名）
            description="Pandora OS Core Runtime"
        )        
        # （暫時）先註冊 pandora 世界本身
        self.world_registry.register(pandora_world)
        # =========================================================
        # Governance World（制度世界）
        # =========================================================
        from shared_core.world.capabilities import WorldCapabilities

        governance_world = WorldContext(
            world_id="governance",
            world_type="system",
            owner="pandora-os",
            description="Governance Runtime World"
        )

        self.world_registry.register(governance_world)

        # Governance world 的能力（極小化）
        self.world_registry.register_capabilities(
            WorldCapabilities(
                world_id="governance",
                supports_hotplug=False,
                supports_multi_runtime=False,
                supports_external_tick=False,
            )
        )
        # 你之後會在這裡註冊能力（之後再做）
        # self.world_registry.register_capabilities(...)

        # 2️⃣ 用 registry 建立 Gate
        self.world_capability_gate = WorldCapabilityGate(
            registry=self.world_registry
        )

        # 3️⃣ 注入 Runtime Attach Guard
        self._runtime_attach_guard = RuntimeAttachGuard(
            capability_gate=self.world_capability_gate
        )


        # =========================================================
        # Governance Runtime（議會 + 決策落盤）
        # =========================================================
        from shared_core.governance.runtime.governance_runtime import GovernanceRuntime
        from shared_core.governance.handlers.governance_snapshot_handler import GovernanceSnapshotHandler
        from shared_core.governance.handlers.decision_persistence_handler import DecisionPersistenceHandler
        from shared_core.governance.parliament.parliament_engine import ParliamentEngine

        # 議會引擎
        parliament_engine = ParliamentEngine(
            rules_path="shared_core/governance/parliament/rules.yaml"
        )

        # Snapshot → Parliament
        snapshot_handler = GovernanceSnapshotHandler(
            engine=parliament_engine,
            event_bus=self.bus,   # 用正常 EventBus（治理不走 fast_bus）        
        )

        # Decision → Library
        decision_persistence_handler = DecisionPersistenceHandler(
            library_root=Path(base_dir) / "library"
        )

        # Governance Runtime 本體
        self.governance_runtime = GovernanceRuntime(
            engine=parliament_engine,
            snapshot_handler=snapshot_handler,
            decision_persistence_handler=decision_persistence_handler,
        )
        # 1️⃣ 先做 capability 檢查（制度）
        self._runtime_attach_guard.ensure_can_attach(
            world_id="governance",
            plugin_instance=self.governance_runtime,
            plugin_name="governance-runtime",
        )

        # 2️⃣ 再真正 attach（生命週期）
        if hasattr(self.governance_runtime, "on_load"):
            self.governance_runtime.on_load(self.bus)
            print("[PandoraRuntime] 🏛️ GovernanceRuntime attached")
        # =========================================================
        # Output System（結構化輸出，給系統 / 人）
        # =========================================================
        from outputs.output_orchestrator import DecisionOutputOrchestrator
        from outputs.output_dispatch_handler import OutputDispatchHandler
        from locales.zh_TW.formatter import ZhTWFormatter
        from outputs.debug.console_output import ConsoleOutput
        from outputs.warm.file_output import FileOutput

        output_orchestrator = DecisionOutputOrchestrator(
            formatter=ZhTWFormatter(),   # 之後再做動態 locale
            outputs=[
                ConsoleOutput(),
                FileOutput(base_dir="outputs/reports/daily"),
            ],
            metadata={
                "system": "AISOP",
                "version": "0.5",
                "env": "prod",
            }
        )

        output_handler = OutputDispatchHandler(output_orchestrator)

        self.bus.subscribe(
            "system.governance.decision.created",
            output_handler.handle,
        )

        # =========================================================
        # Narration System（給人看的「AI 自述」，完全平行）
        # =========================================================
        from outputs.narrators.narration_handler import NarrationHandler
        from outputs.narrators.narrator_registry import NarratorRegistry
        from outputs.narrators.stub_narrator import StubNarrator

        # 1️⃣ 建立並初始化 Registry（一定要做）
        narrator_registry = NarratorRegistry()
        narrator_registry.register("stub", StubNarrator())
        narrator_registry.register("gpt_low", StubNarrator())
        narrator_registry.register("gpt_high", StubNarrator())


        # 2️⃣ 建立 Handler（⚠️ 不要先 select narrator）
        narration_handler = NarrationHandler(
            registry=narrator_registry,
            env="prod",
        )

        # 4️⃣ 接線（平行，不影響 Output）
        self.bus.subscribe(
            "system.governance.decision.created",
            narration_handler.handle,
        )

        # =========================================================
        # Adapters
        # =========================================================
        from trading_core.perception.market_adapter import MarketKlineAdapter
        adapter = MarketKlineAdapter(self.validator)
        adapter.mode = "batch"          # ⭐ A-MODE：完全跳過 Anti-Poison
        self.gateway.register_adapter(
            "market.kline",
            adapter
        )
        print("[PandoraRuntime] 🧩 Adapter registered: market.kline")

        from shared_core.perception_core.simple_text_adapter import SimpleTextInputAdapter
        self.gateway.register_adapter(
            "text.input",
            SimpleTextInputAdapter(self.validator)
        )
        print("[PandoraRuntime] 🧩 Adapter registered: text.input")

        from shared_core.adapters.library_event_adapter import LibraryEventAdapter

        self.gateway.register_adapter(
            "library.event",
            LibraryEventAdapter(validator=None)
        )
        print("[PandoraRuntime] 🧩 Adapter registered: library.event")
        # =========================================================
        # Storage / RAW Event Layer（唯一 Writer）
        # =========================================================
        sm = StorageManager("config/storage.yaml")
        cfg = sm.config()
        hot_path = sm.event_raw_path(cfg["event_raw"]["filename"])

        print(f"[PandoraRuntime] 🧊 Storage(HOT) = {hot_path}")

        # ★ 全系統唯一 EventLogWriter
        self.event_log_writer = EventLogWriter(str(hot_path))
        from shared_core.event.event_trace import EventTracer

        self.event_tracer = EventTracer()
        self.fast_bus.tracer = self.event_tracer
        self.bus.tracer = self.event_tracer
        # ★ 所有事件（Live + Replay）都走這條
        def _raw_event_sink(ev):
            if isinstance(ev, PBEvent):
                self.event_log_writer.write(ev)

        self.bus.subscribe("market.kline", self.event_log_writer.write)

        print("[PandoraRuntime] 📝 RAW EVENT LAYER 已啟動（唯一 Writer）")

        # =========================================================
        # Background tasks
        # =========================================================
        self._start_perception_auditor()
        self._start_background_rotator(interval_sec=60)

        # =========================================================
        # Replay Runtime（正式接線）
        # =========================================================
        #self.replay = ReplayRuntime(self)
        #print("[PandoraRuntime] 🔁 ReplayRuntime attached")


        # === Library Writer（被動記憶層）===
        from library.library_writer import LibraryWriter
        from library.ingest.replay_ingestor import LibraryIngestor

        self.library = LibraryWriter(Path(base_dir) / "library")

        def _library_sink(ev):
            try:
                self.library.write_event(ev)
            except Exception as e:
                print("[Library] ❌ write failed:", e)

        # 只接 fast_bus（代表事件已經乾淨）
        self.fast_bus.subscribe("*", _library_sink)
        self.library_ingestor = LibraryIngestor(self.library)
# ReplayRuntime 內把 ingestor 傳下去

        print("[PandoraRuntime] 📚 Library v1 attached (passive)")

    # --------------------------------------------------------------------------------------           
    # 外部 Tick 來源注入（TradingRuntime / AISOPRuntime / Functions）
    # --------------------------------------------------------------------------------------
    def add_external_tick(self, src):
        """
        外部 tick 來源可以是：
        1. 含 tick() 的 runtime 物件（TradingRuntime / AISOPRuntime）
        2. 普通 function（callable）
        3. async function（未來用於雲端並聯）
        """
        if src is None:
            print("[PandoraRuntime] ⚠️ 無法加入 external tick：來源為 None")
            return

        self.external_ticks.append(src)
        print(f"[PandoraRuntime] 🔗 External tick source added: {type(src).__name__}")


    # -------------------------------------------------------
    # Plugin Loader（AI plugin 用，會自動注入 bus）
    # -------------------------------------------------------
    def load_plugin(self, module_path: str, class_name: str):
        cls, plugin_meta = self.loader.load_class(module_path, class_name)
        if not cls:
            print(f"[PandoraRuntime] ❌ Class {class_name} not found in module")
            return None

        # ⚠️ Step 4-2：只「保存」 metadata，不做判斷
        plugin_name = plugin_meta["plugin_name"]
        required_capabilities = plugin_meta["required_capabilities"]

        try:
            instance = cls(self.bus)
        except TypeError:
            instance = cls()

            # 🔹 把 metadata 掛在 instance 上（供 Step 4-3 使用）
        instance._plugin_name = plugin_name
        instance._required_capabilities = required_capabilities

        self.manager.register(instance)
        print(
            f"[PandoraRuntime] 🔌 Plugin loaded: {plugin_name} "
            f"(caps={list(required_capabilities)})"
        )
        return instance

    
    def load_plugin_instance(self, name, instance):
        """
        將已建立的物件註冊為 Plugin（受 World / Capability Gate 保護）
        """

        # === Runtime Attach Guard ===
        if hasattr(self, "_runtime_attach_guard") and self.world_id:
            self._runtime_attach_guard.ensure_can_attach(
                world_id=self.world_id,
                plugin_name=name,
                plugin_instance=instance,
            )

        # 如果 plugin 有 on_load()，則呼叫它（讓它訂閱事件）
        if hasattr(instance, "on_load"):
            instance.on_load(self.bus)

        # 加入 plugin 列表
        self.plugins[name] = instance

        print(f"[PandoraRuntime] 🔌 Plugin instance installed: {name}")
    # -------------------------------------------------------
    # Plugin installer（直接安裝物件版 plugin）
    # -------------------------------------------------------
    def install_plugin(self, plugin):
        """直接安裝 PluginBase 物件（不透過動態載入）"""

        if not plugin:
            print("[PandoraRuntime] ❌ plugin is None，無法安裝")
            return None

        # 插件若沒有 bus，才注入（避免覆蓋）
        if getattr(plugin, "bus", None) is None:
           plugin.bus = self.bus

        # 呼叫插件初始化生命週期（如果有）
        if hasattr(plugin, "on_install"):
            try:
                plugin.on_install(self)
            except Exception as e:
                print(f"[PandoraRuntime] ⚠ Plugin on_install() 執行錯誤: {e}")

        # 註冊 plugin
        self.manager.register(plugin)
        print(f"[PandoraRuntime] 🔌 Plugin installed: {plugin.__class__.__name__}")

        return plugin
    # -------------------------------------------------------
    # 外部 Runtime（世界心跳來源）
    # -------------------------------------------------------
    def register_external_tick_source(self, obj):
        """讓 TradingRuntime 等非 AI 模組加入系統 tick"""
        self.external_ticks.append(obj)
        print(f"[PandoraRuntime] 🔗 External tick source added: {obj.__class__.__name__}")

    # -------------------------------------------------------
    # Perception Adapter 註冊
    # -------------------------------------------------------
    def register_adapter(self, name, adapter):
        """
        註冊感知層 Adapter：
        將 raw_input → PBEvent 的轉換器加入系統
        """
        self.adapters[name] = adapter
        print(f"[PandoraRuntime] 🧩 Adapter registered: {name}")

    # -------------------------------------------------------
    # 核心 tick 管線
    # -------------------------------------------------------
    def tick(self):
        """Pandora 主 tick（呼叫 plugin tick + external tick）"""

        # ① 呼叫 plugin runtime tick()
        for plugin in self.manager.plugins:
            if hasattr(plugin, "tick"):
                try:
                    plugin.tick()
                except Exception as e:
                    print(f"[PandoraRuntime] ❌ Plugin tick error: {e}")

        # ② 呼叫 external tick sources
        for src in self.external_ticks:
            try:
                # 情境 A：如果是 async function
                if inspect.iscoroutinefunction(src):
                    asyncio.run(src())
                    continue

                # 情境 B：如果是一般 function（沒有 tick，但是 callable）
                if callable(src) and not hasattr(src, "tick"):
                    src()
                    continue

                # 情境 C：runtime 物件（具有 tick 方法）
                if hasattr(src, "tick"):
                    src.tick()
                    continue

                # 其他未知型態
                print(f"[PandoraRuntime] ⚠️ 未知的 external tick 類型：{src}")

            except Exception as e:
                print(f"[PandoraRuntime] ❌ External tick error: {e}")

    def _start_background_rotator(self, interval_sec: int = 60):
        """
        Background Log Rotator
        - 非阻塞
        - 不影響主事件流
        - 定期 rotate + archive
        """

        try:
            sm = StorageManager("config/storage.yaml")
            cfg = sm.config()

            hot_file = sm.event_raw_path(cfg["event_raw"]["filename"])
            rotate_cfg = cfg["event_raw"]["rotate"]
            archive_cfg = cfg["event_raw"]["archive"]

            rotator = LogRotator(
                hot_file=hot_file,
                warm_dir=sm.warm(),
                cold_dir=sm.cold(),
                rotate_policy=RotatePolicy(
                    max_mb=int(rotate_cfg.get("max_mb", 256)),
                    max_age_minutes=int(rotate_cfg.get("max_age_minutes", 0)),
                ),
                archive_policy=ArchivePolicy(
                    keep_warm_days=int(archive_cfg.get("keep_warm_days", 7)),
                ),
            )

        except Exception as e:
            print(f"[PandoraRuntime] ❌ Failed to init LogRotator: {e}")
            return

        def _loop():
            print("[PandoraRuntime] 🧊 Background LogRotator started")
            print(f"[Storage] HOT  = {sm.hot()}")
            print(f"[Storage] WARM = {sm.warm()}")
            print(f"[Storage] COLD = {sm.cold()}")

            while True:
                try:
                    rotator.tick()
                except Exception as e:
                    print(f"[LogRotator] ❌ error: {e}")

                time.sleep(interval_sec)

        t = threading.Thread(
            target=_loop,
            name="BackgroundLogRotator",
            daemon=True,
        )
        t.start()
    def _start_perception_auditor(self):
        """
        啟動感知層安全稽核員
        - 背景 thread
        - 獨立 asyncio event loop
        - 不影響 Pandora OS 主循環
        """

        import threading
        import asyncio

        def _runner():
            try:
                asyncio.run(self._run_auditor_loop())
            except Exception as e:
                print(f"[PandoraRuntime] ❌ Auditor loop crashed: {e}")

        try:
            t = threading.Thread(
                target=_runner,
                daemon=True,
                name="PerceptionSafetyAuditorThread"
            )
            t.start()

            print("[PandoraRuntime] 🛡️ Perception Safety Auditor started (background thread)")

        except Exception as e:
            print(f"[PandoraRuntime] ⚠️ Failed to start Perception Auditor: {e}")
    async def _run_auditor_loop(self):
        """
        感知層安全稽核 async loop
        每 30 分鐘執行一次（由 scheduler 控制）
        """

        from pathlib import Path
        from pandora_core.perception_audit.auditor_runtime import PerceptionSafetyAuditor
        from pandora_core.perception_audit.scheduler import run_audit_loop
        from shared_core.event_raw.event_log_reader import EventLogReader

        # 只讀 RAW EVENT
        reader = EventLogReader(
            path=Path(self.base_dir) / "event_raw" / "logs.jsonl"
        )

        auditor = PerceptionSafetyAuditor(
            llm_client=self.manager.get_auditor_llm(),  # Claude mini
            raw_event_reader=reader
        )

        # 交給 scheduler（內部 sleep 30 分鐘）
        await run_audit_loop(auditor)

    # -------------------------------------------------------
    # OS 主循環（呼吸節奏）
    # -------------------------------------------------------
    def run_forever(self):
        print("[PandoraRuntime] ♾ Pandora OS running...")
        while True:
            self.tick()
