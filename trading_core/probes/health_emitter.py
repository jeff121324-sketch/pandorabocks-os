from shared_core.event_schema import PBEvent


def emit_health_warning(rt, world_id, reason, interval):
    event = PBEvent(
        type="world.health.warning",
        payload={
            "world_id": world_id,
            "reason": reason,
            "interval": interval,
        },
        source="trading.probe",
        priority=2,
        tags=["health", "probe"]
    )
    rt.fast_bus.publish(event)


def emit_health_error(rt, world_id, reason, detail):
    event = PBEvent(
        type="world.health.error",
        payload={
            "world_id": world_id,
            "reason": reason,
            "detail": detail,
        },
        source="trading.probe",
        priority=1,
        tags=["health", "probe"]
    )
    rt.fast_bus.publish(event)
    
def emit_runtime_error(rt, world_id, reason, detail):
    event = PBEvent(
        type="world.health.error",
        payload={
            "world_id": world_id,
            "reason": reason,
            "detail": detail,
        },
        source="trading.runtime",
        priority=1,
        tags=["health", "runtime"]
    )
    rt.fast_bus.publish(event)