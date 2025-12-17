from shared_core.pb_lang.perception_adapter import PerceptionAdapter
from shared_core.event_schema import PBEvent

import time


class HotelCheckinAdapter(PerceptionAdapter):

    def __init__(self):
        super().__init__(source="aisop.hotel")

    def filter(self, raw: dict):
        # Minimal required fields
        for key in ("guest_id", "room", "time"):
            if key not in raw:
                print(f"[HotelCheckinAdapter] ⚠ missing field: {key}")
                return None
        return raw

    def enrich(self, raw: dict) -> dict:
        # Normalize time -> ts
        ts = raw.get("ts")
        if ts is None:
            # time 可能是 ISO string
            if isinstance(raw.get("time"), str):
                try:
                    ts = float(pd.Timestamp(raw["time"]).timestamp())
                except Exception:
                    ts = time.time()
            else:
                ts = time.time()
        raw["ts"] = ts
        return raw

    def make_event(self, raw: dict) -> PBEvent:
        return PBEvent(
            type="hotel.checkin",
            payload={
                "guest_id": raw["guest_id"],
                "room": raw["room"],
                "time": raw.get("time"),
            },
            source=self.source,
            ts=raw["ts"],
        )
