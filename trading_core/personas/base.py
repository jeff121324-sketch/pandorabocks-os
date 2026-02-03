# trading_core/personas/base.py

from abc import ABC, abstractmethod
from shared_core.event_schema import PBEvent

class BaseTradePersonaSentinel(ABC):
    """
    Persona Sentinel (always resident)
    - Extremely light
    - No heavy state
    - Only decides whether to activate executor
    """

    persona_name: str           # attacker / defender / balancer
    function_tag = "trade"

    def __init__(self, bus):
        self.bus = bus
        self._last_activation_ts = None

    # ---------- Event Entry Points ----------

    def _extract_payload(self, event):
        if hasattr(event, "payload"):
            return event.payload
        return event  # assume dict

    # ---------- Event Entry Points ----------

    def on_market_kline(self, event):
        payload = self._extract_payload(event)
        if self.should_activate(payload):
            self.activate(payload)

    def on_risk_snapshot(self, event):
        payload = self._extract_payload(event)
        if self.should_activate(payload):
            self.activate(payload)

    # ---------- Activation Logic ----------

    @abstractmethod
    def should_activate(self, payload: dict) -> bool:
        """
        VERY cheap check.
        Must be O(1), no loops, no history scan.
        """
        raise NotImplementedError

    def activate(self, payload: dict):
        executor = self.create_executor()
        signal = executor.execute(payload)

        if signal:
            self.emit_signal(signal)

    @abstractmethod
    def create_executor(self):
        raise NotImplementedError

    # ---------- Output ----------

    def emit_signal(self, signal):
        self.bus.publish(
            PBEvent(
                type="persona.signal.trade",
                payload={
                    "source": self.__class__.__name__,
                    "target_persona": self.persona_name,
                    "function": self.function_tag,
                    "signal": signal,
                },
                source="trade_persona",
            )
        )

class BaseTradePersonaExecutor(ABC):
    """
    Persona Executor (activated on demand)
    - Heavy logic allowed
    - No persistence after execution
    """

    @abstractmethod
    def execute(self, payload: dict):
        """
        return TradeSignal or None
        """
        raise NotImplementedError
