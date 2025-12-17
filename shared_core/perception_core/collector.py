"""
collector.py
資料收集器（Perception Layer 1）
不同的子文明會實作自己的 Collector 子類別。
"""

class BaseCollector:
    """所有 Collector 的共同介面"""

    def __init__(self, source_name="unknown"):
        self.source_name = source_name

    def collect(self):
        """
        收集資料並回傳
        - 交易：K 線、Ticker、Orderbook...
        - 飯店：客人事件、櫃檯輸入、房務狀態...
        """
        raise NotImplementedError
