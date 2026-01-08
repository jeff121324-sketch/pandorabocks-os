# launcher/aisop_launcher.py

import sys
from pathlib import Path
# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from pandora_core.pandora_runtime import PandoraRuntime

from shared_core.world.registry import WorldRegistry
from shared_core.world.world_profile import WorldProfile
from shared_core.world.world_runtime_bridge import WorldRuntimeBridge
from shared_core.world.perception_attach_gate import PerceptionAttachGate
from shared_core.world.external_tick_attach_gate import ExternalTickAttachGate
from shared_core.world.external_tick_executor import ExternalTickExecutor
from shared_core.world.world_runtime import WorldRuntime
from trading_core.data_provider.perception.market.runner.live_market_tick_provider import (
    LiveMarketTickProvider
)


def run_world(profile_path: str):
    # -------------------------------------------------
    # Resolve base path
    # -------------------------------------------------
    base = Path(__file__).resolve().parents[1]

    # -------------------------------------------------
    # Load World Profile (憲法)
    # -------------------------------------------------
    profile = WorldProfile.load(Path(profile_path))
    print(f"[Launcher] 📜 Loaded WorldProfile: {profile.world_id}")
    rt = PandoraRuntime(base)

    # -------------------------------------------------
    #  Init Pandora Runtime (但先不 run)
    # -------------------------------------------------
    from shared_core.event_schema import PBEvent

    test_event = PBEvent(
        type="world.health.warning",
        payload={
            "reason": "manual_test",
            "interval": "15m",
        },
        source="launcher",
        priority=2,
        tags=["health", "test"],
    )

    print("🧪 Injecting manual health warning test")
    rt.fast_bus.publish(test_event)


    # -------------------------------------------------
    # Init World Registry
    # -------------------------------------------------
    registry = WorldRegistry()

    # -------------------------------------------------
    # Register World via Bridge
    # -------------------------------------------------
    bridge = WorldRuntimeBridge(registry)
    ctx = bridge.register_world(profile)
    # 👉 建立「活著的世界 Runtime」
    world_rt = WorldRuntime(
        context=ctx,
        event_writer=rt.event_log_writer,  # 用你現有的唯一 writer
    )
    # 🟢 新增：建立 Live Market Tick Provider
    live_provider = LiveMarketTickProvider(
        world_id=ctx.world_id
    )

    # 🟢 修改：把 provider 一起交給 Pandora
    rt.attach_world_runtime(
        world_rt=world_rt,
        live_provider=live_provider,
    )

    print(f"[Launcher] 🌍 World registered: {ctx.world_id}")
    print("🔥 DEBUG ctx.domain =", ctx.domain, type(ctx.domain))

    # === World → Domain Runtime attach（唯一正確位置）===
    if ctx.domain == "trading":
        print("[Launcher] 🎮 Trading world detected, preparing trading runtime...")

        from trading_core.trading_runtime import TradingRuntime

        trading_rt = TradingRuntime(
            rt,  
            symbol=profile.market.get("symbol", "BTC/USDT") if profile.market else "BTC/USDT",

        )

        print("[Launcher] ✅ TradingRuntime attached (init-time)")
    # -------------------------------------------------
    #  Apply Perception Attach Gate
    # -------------------------------------------------
    gate = PerceptionAttachGate(rt, profile)
    gate.apply()
    # -------------------------------------------------
    # 6Apply External Tick Attach Gate
    # -------------------------------------------------
    tick_gate = ExternalTickAttachGate(rt, registry, profile)
    tick_gate.apply()
    # -------------------------------------------------
    # Attach External Tick Execution (NEW)
    # -------------------------------------------------
    if profile.permission.get("allow_external_tick", False):
        executor = ExternalTickExecutor(rt, profile, ctx)
        executor.attach()
    # -------------------------------------------------
    # (暫停在這裡)
    # -------------------------------------------------
    print("[Launcher] ✅ World birth complete (runtime not started yet)")
    print("[Launcher] ℹ Registry snapshot:")
    print(registry.export_capability_map())
    # -------------------------------------------------
    # Start Runtime (世界開始跑)
    # -------------------------------------------------
    print("[Launcher] ▶ World runtime starting...")
    from trading_core.data_provider.perception.market.runner.start_market_system import main as start_market_system

    print("[Launcher] 🚀 Starting market system bootstrap")
    start_market_system()
    
    rt.run_forever()

def main():
    # -------------------------------------------------
    # 1️⃣ 工程模式：直接指定 world
    # -------------------------------------------------
    if len(sys.argv) >= 2:
        run_world(sys.argv[1])
        return

    # -------------------------------------------------
    # 2️⃣ Launcher 模式：選擇 world
    # -------------------------------------------------
    from launcher.world_menu import choose_world

    world = choose_world()
    if not world:
        print("[Launcher] ❌ No world selected, exit.")
        return

    run_world(str(world))



if __name__ == "__main__":
    main()
