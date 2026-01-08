# trading_core/perception/kline_listener.py


def register_kline_listener(bus, world_rt=None):
    """
    Perception Kline Listener
    - bus: EventBus / ZeroCopyEventBus
    - world_rt: WorldRuntime（可選，用於世界記憶）
    """

    def on_kline(event):
        payload = event.payload

        print(
            f"[Perception] 📈 KLINE "
            f"{payload.get('symbol')} "
            f"{payload.get('interval')} "
            f"close={payload.get('close')}"
        )

        # 🧠 世界正式承認：我看到這件事
        if world_rt is not None:
            world_rt.state.append(event)

    bus.subscribe("market.kline", on_kline)
    print("[Perception] ✅ Kline listener registered")
