# trading_core/data_provider/perception/market/live/base.py

from abc import ABC, abstractmethod


class LiveFeedBase(ABC):
    """
    Live feed base:
    - NO storage
    - NO history
    - NO world mutation
    """

    def __init__(self, symbol: str, interval: str, provider):
        self.symbol = symbol
        self.interval = interval
        self.provider = provider

    @abstractmethod
    def start(self):
        ...

    @abstractmethod
    def stop(self):
        ...
