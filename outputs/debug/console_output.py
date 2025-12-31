from outputs.base import BaseOutput
import pprint


class ConsoleOutput(BaseOutput):
    """
    Debug output: print payload to console.
    """

    def emit(self, payload: dict):
        pprint.pprint(payload)
