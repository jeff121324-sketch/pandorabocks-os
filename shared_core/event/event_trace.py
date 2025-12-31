# shared_core/event/event_trace.py
from dataclasses import dataclass, field
import time

@dataclass
class EventTrace:
    event_type: str
    source: str
    delivered_to: list[str] = field(default_factory=list)
    ts: float = field(default_factory=time.time)

class EventTracer:
    def __init__(self):
        self.traces = []

    def record(self, trace: EventTrace):
        self.traces.append(trace)
