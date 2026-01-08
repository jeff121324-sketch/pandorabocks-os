class PluginBase:
    """
    Minimal plugin abstraction.

    Optional attributes (NOT enforced):
    - plugin_name: str
    - required_capabilities: Iterable[str]
    - version: str

    Optional lifecycle hooks:
    - on_install(runtime)
    - on_load(bus)
    - on_unload()
    - tick()
    """

    def __init__(self, name):
        self.name = name
        self._active = True 

    def on_unload(self):
        """Hot Unplug hook（可選）"""
        self._active = False
        
    def on_event(self, event_type, data):
        """事件回應"""
        pass

    def tick(self):
        """每一輪 loop 呼叫一次"""
        pass
    def __repr__(self):
        return f"<Plugin {self.__class__.__name__}>"