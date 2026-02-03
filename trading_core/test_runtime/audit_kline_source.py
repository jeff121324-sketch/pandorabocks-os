from typing import Optional
import time


class AuditKlineSource:
    """
    Audit / Test only.
    Provides a single kline snapshot for full pipeline testing.
    """

    def get_latest(self) -> Optional[dict]:
        """
        Return ONE kline-like dict.
        This simulates a 'latest known fact'.
        """

        now = time.time()

        return {
            "source": "audit",
            "market": "crypto",
            "symbol": "BTCUSDT",
            "interval": "1m",
            "kline_open_ts": now - 60,
            "kline_close_ts": now,
            "open": 42000.0,
            "high": 42120.0,
            "low": 41980.0,
            "close": 42080.0,
            "volume": 123.45,
            "mode": "TRAINING",   # 👈 新增
            "episode_id": int(now),  # 👈 每一筆訓練 episode
        }
