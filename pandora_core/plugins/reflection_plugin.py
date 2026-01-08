from plugin_base import PluginBase
from reflection.self_review_engine import SelfReviewEngine

class ReflectionPlugin(PluginBase):
    plugin_name = "reflection"

    def __init__(self, name="reflection"):
        super().__init__(name)
        self.engine = None

    def on_load(self, bus):
        self._active = True
        self.engine = SelfReviewEngine()
        print("[ReflectionPlugin] loaded")

    def on_unload(self):
        self._active = False
        self.engine = None
        print("[ReflectionPlugin] unloaded")
