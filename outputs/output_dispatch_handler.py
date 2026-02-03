# aisop/outputs/output_dispatch_handler.py
from shared_core.event_schema import PBEvent
class OutputDispatchHandler:
    """
    Handle system.governance.decision.created
    → forward decision to DecisionOutputOrchestrator
    """

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def handle(self, event):
        """
        event: PBEvent
        """
        if isinstance(event, PBEvent):
            decision = event.payload

        self.orchestrator.dispatch(decision)