# shared_core/pb_lang/pb_system.py

from shared_core.event_schema import PBEvent


class PBsystem:
    """
    PB-Lang: System Language
    給 Pandora Runtime / Trading Runtime / AISOP Runtime 使用
    """

    @staticmethod
    def error(module: str, message: str, detail: dict = None, source="system"):
        payload = {
            "module": module,
            "message": message,
            "detail": detail or {}
        }
        return PBEvent(
            type="system.error",
            payload=payload,
            source=source,
            priority=10
        )

    @staticmethod
    def tick(runtime: str, tick_id: int, cpu: float = None, mem: float = None, source="system"):
        payload = {
            "runtime": runtime,
            "tick_id": tick_id,
            "cpu": cpu,
            "mem": mem
        }
        return PBEvent(
            type="system.tick",
            payload=payload,
            source=source
        )

    @staticmethod
    def status(module: str, status: str, info: dict = None, source="system"):
        payload = {
            "module": module,
            "status": status,
            "info": info or {}
        }
        return PBEvent(
            type="system.status",
            payload=payload,
            source=source
        )
