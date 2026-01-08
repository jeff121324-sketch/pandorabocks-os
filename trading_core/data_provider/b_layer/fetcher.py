# trading_core/data_provider/fetcher.py
"""
PERCEPTION DATA ONLY

This module produces raw market facts.
- No indicators
- No aggregation
- No strategy logic
- Must never be used for training or optimization
"""
import pandas as pd

class MarketDataFetcher:
    """
    統一的市場資料提供者（可替換）
    v1: 假資料 / CSV
    v2: 可改成 Binance, CCXT, DB, 雲端資料庫
    """

    def __init__(self, source="mock"):
        self.source = source

    def load(self):
        """
        回傳 DataFrame
        必須包含 open, high, low, close, volume
        """

        # v1: Mock 資料
        data = [
            {"open": 1.0, "high": 2.0, "low": 0.5, "close": 1.8, "volume": 100},
            {"open": 1.8, "high": 2.1, "low": 1.7, "close": 2.0, "volume": 120},
        ]

        return pd.DataFrame(data)
