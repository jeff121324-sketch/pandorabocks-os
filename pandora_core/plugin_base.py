class PluginBase:
    """
    所有插件（人格、子模組、子文明）的共同介面。
    Pandora 不知道他是交易、飯店還是別的——全部一視同仁。
    """

    def __init__(self, name):
        self.name = name

    def on_event(self, event_type, data):
        """事件回應"""
        pass

    def tick(self):
        """每一輪 loop 呼叫一次"""
        pass
