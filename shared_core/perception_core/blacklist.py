"""
blacklist.py
Perception Layer 4
負責管理「不可信來源」「被封鎖的 API」「惡意事件」等
"""

class BlacklistLibrary:
    def __init__(self):
        self.blocked_sources = set()

    def block(self, source: str):
        self.blocked_sources.add(source)

    def allow(self, source: str):
        return source not in self.blocked_sources
