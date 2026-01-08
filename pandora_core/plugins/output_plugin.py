from plugin_base import PluginBase
from outputs.output_orchestrator import DecisionOutputOrchestrator
class OutputPlugin(PluginBase):
    plugin_name = "outputs"

    def __init__(self, name="outputs"):
        super().__init__(name)
        self.orchestrator = None

    def on_load(self, bus):
        self._active = True
        self.orchestrator = DecisionOutputOrchestrator()
        print("[OutputPlugin] loaded")

    def on_unload(self):
        self._active = False
        self.orchestrator = None
        print("[OutputPlugin] unloaded")
