class BaseOutput:
    """
    Base class for all output channels.

    Rules:
    - No decision logic
    - No formatting
    - No routing
    """

    def emit(self, payload: dict):
        raise NotImplementedError("Output must implement emit()")