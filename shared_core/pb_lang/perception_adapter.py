# shared_core/pb_lang/perception_adapter.py

from shared_core.event_schema import PBEvent
from shared_core.pb_lang.pb_event_validator import PBEventValidator


class PerceptionAdapter:
    """
    Perception Layer base class:
    raw external data -> PBEvent (with optional filtering / enrichment).
    """

    def __init__(self, source="unknown", validator: PBEventValidator = None):
        self.source = source
        self.validator = validator or PBEventValidator()

    # ---------- Hook 1: filter (can drop bad data) ----------
    def filter(self, raw: dict):
        """
        Return:
          - dict: keep and continue
          - None: drop this record (blacklist / poison / invalid)
        """
        return raw

    # ---------- Hook 2: enrich (add / normalize fields) ----------
    def enrich(self, raw: dict) -> dict:
        """
        Add / normalize fields before building PBEvent.
        e.g. fill default interval / ts / tags...
        """
        return raw

    # ---------- Hook 3: build PBEvent ----------
    def make_event(self, raw: dict) -> PBEvent:
        """
        Child classes MUST implement:
        raw -> PBEvent
        """
        raise NotImplementedError("Child class must implement make_event()")

    # ---------- Main entry: raw -> PBEvent ----------
    def to_event(self, raw_data) -> PBEvent | None:
        """
        Standard pipeline:
        raw -> filter -> enrich -> PBEvent -> validate
        """
        raw = self.filter(raw_data)
        if raw is None:
            # dropped by filter (e.g., blacklist / poison)
            return None

        raw = self.enrich(raw)
        event = self.make_event(raw)
        
        try:
            return self.validate(event)
        except Exception as e:
            if self.mode == "batch":
                return None
            raise

    # ---------- Final validation ----------
    def validate(self, event: PBEvent):
        """Run PBEventValidator on the event"""
        self.validator.validate(event)
        return event