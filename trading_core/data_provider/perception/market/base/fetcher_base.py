from abc import ABC, abstractmethod

class RawMarketFetcherBase(ABC):
    """
    PERCEPTION FETCHER BASE

    - Produce raw market facts only
    - No indicators
    - No aggregation
    - No strategy logic
    """

    @abstractmethod
    def fetch(self, symbol: str, interval: str) -> list[dict]:
        pass
