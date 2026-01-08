from plugin_base import PluginBase
from learning.learning_request_handler import LearningRequestHandler

class LearningPlugin(PluginBase):
    plugin_name = "learning"

    def __init__(self, name="learning"):
        super().__init__(name)
        self.handler = None

    def on_load(self, bus):
        self._active = True
        self.handler = LearningRequestHandler()
        print("[LearningPlugin] loaded")

    def on_unload(self):
        self._active = False
        self.handler = None
        print("[LearningPlugin] unloaded")
