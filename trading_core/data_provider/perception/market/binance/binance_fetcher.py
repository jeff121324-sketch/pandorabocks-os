import time
import os
import ccxt
import random
from dotenv import load_dotenv
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from .interval_map import BINANCE_INTERVAL_MAP
from ..base.fetcher_base import RawMarketFetcherBase

load_dotenv()

def safe_fetch_ohlcv(
    exchange,
    *,
    symbol: str,
    timeframe: str,
    since: int | None = None,
    limit: int = 1000,
    max_retry: int = 5,
):
    for attempt in range(max_retry):
        try:
            return exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                since=since,
                limit=limit,
            )
        except ccxt.NetworkError as e:
            wait = min(2 ** attempt + random.random(), 30)
            print(f"[Binance] ⚠ NetworkError retry {attempt+1}/{max_retry} in {wait:.1f}s")
            time.sleep(wait)
        except ccxt.ExchangeError:
            # 交易所回錯（例如封 IP / maintenance）
            raise
    raise RuntimeError("❌ Binance fetch failed after retries")

class BinanceRawFetcher(RawMarketFetcherBase):
    def __init__(self):
        self.exchange = ccxt.binance({
            "apiKey": os.getenv("BINANCE_API_KEY"),
            "secret": os.getenv("BINANCE_API_SECRET"),
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        })
        self._last_fetch_ts: dict[str, float] = {}
        self._history_fetching = False
    def fetch(self, symbol: str, interval: str) -> list[dict]:

        if not hasattr(self, "_last_fetch_ts"):
            self._last_fetch_ts = {}

        fetch_ts = time.time()
        interval_sec = BINANCE_INTERVAL_MAP[interval]["seconds"]

        # ==================================================
        # ⭐ Throttle：一個 interval 內只 fetch 一次
        # ==================================================
        last = self._last_fetch_ts.get(interval, 0)
        if fetch_ts - last < interval_sec:
            # 還沒到下一根 K 線，安全地什麼都不做
            return []

        # 更新 fetch 時間
        self._last_fetch_ts[interval] = fetch_ts

        candles = self._fetch_from_binance(symbol, interval)

        records = []
        
        for c in candles:
            open_ts = c["open_ts"]
            records.append({
                "source": "binance",
                "market": "crypto",
                "symbol": symbol,
                "interval": interval,

                # === 市場時間 ===
                "kline_open_ts": c["open_ts"],
                "kline_close_ts": c["open_ts"] + interval_sec,

                # === 系統時間 ===
                "fetch_ts": fetch_ts,
                # ✅ 新增這一行
                # === 人類時間（衍生）===
                "human_open_time": datetime.fromtimestamp(
                    open_ts, tz=timezone.utc
                ).isoformat(),
                # ✅ 新增這一個（就在這裡）
                "human_open_time_local": datetime.fromtimestamp(
                    open_ts, tz=ZoneInfo("Asia/Taipei")
                ).isoformat(),
                # === OHLCV ===
                "open": c["open"],
                "high": c["high"],
                "low": c["low"],
                "close": c["close"],
                "volume": c["volume"],
            })

        return records

    def _fetch_from_binance(self, symbol: str, interval: str):
        timeframe = BINANCE_INTERVAL_MAP[interval]["ccxt"]

        ohlcv = safe_fetch_ohlcv(
            self.exchange,
            symbol=symbol,
            timeframe=timeframe,
            limit=3,
        )

        candles = []

        # ⭐ 只取「倒數第二根」＝ 已 close
        ts_ms, o, h, l, c, v = ohlcv[-2]

        candles.append({
            "open_ts": ts_ms / 1000,  # 秒
            "open": float(o),
            "high": float(h),
            "low": float(l),
            "close": float(c),
            "volume": float(v),
        })


        return candles
    def fetch_history(
        self,
        symbol: str,
        interval: str,
        since_ts: int,
        until_ts: int | None = None,
        limit: int = 1000,
    ) -> list[dict]:
        """
        Historical backfill fetcher.
        This method is ONLY for history bootstrap.
        """

        if self._history_fetching:
            print("[Binance] ⏸ history fetch already running, skip")
            return []

        self._history_fetching = True
        interval_sec = BINANCE_INTERVAL_MAP[interval]["seconds"]
        timeframe = BINANCE_INTERVAL_MAP[interval]["ccxt"]

        since_ms = since_ts * 1000
        end_ms = until_ts * 1000 if until_ts else None

        records = []

        while True:
            ohlcv = safe_fetch_ohlcv(
                self.exchange,
                symbol=symbol,
                timeframe=timeframe,
                since=since_ms,
                limit=limit,
            )

            if not ohlcv:
                break

            for ts_ms, o, h, l, c, v in ohlcv:
                open_ts = ts_ms / 1000

                if end_ms and ts_ms >= end_ms:
                    return records

                records.append({
                    "source": "binance",
                    "market": "crypto",
                    "symbol": symbol,
                    "interval": interval,

                    # === 市場時間 ===
                    "kline_open_ts": open_ts,
                    "kline_close_ts": open_ts + interval_sec,

                    # === 系統時間 ===
                    "fetch_ts": time.time(),

                    # === 人類時間（衍生）===
                    "human_open_time": datetime.fromtimestamp(
                        open_ts, tz=timezone.utc
                    ).isoformat(),
                    "human_open_time_local": datetime.fromtimestamp(
                        open_ts, tz=ZoneInfo("Asia/Taipei")
                    ).isoformat(),

                    # === OHLCV ===
                    "open": float(o),
                    "high": float(h),
                    "low": float(l),
                    "close": float(c),
                    "volume": float(v),
                })

            # 下一批從最後一根之後開始
            since_ms = ohlcv[-1][0] + interval_sec * 1000

            # 尊重交易所 rate limit
            time.sleep(self.exchange.rateLimit / 1000)
            
        self._history_fetching = False
        return records
    
    def fetch_history_max(
        self,
        symbol: str,
        interval: str,
        max_bars: int = 20000,
        limit: int = 1000,
    ) -> list[dict]:
        """
        Cold start history fetcher.
        Fetch as many bars as possible up to max_bars, backward from now.
        """
        interval_sec = BINANCE_INTERVAL_MAP[interval]["seconds"]
        timeframe = BINANCE_INTERVAL_MAP[interval]["ccxt"]

        records = []
        since_ms = None  # 從「最新」往回抓

        while len(records) < max_bars:
            ohlcv = self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                since=since_ms,
                limit=limit,
            )

            if not ohlcv:
                break

            batch = []
            for ts_ms, o, h, l, c, v in ohlcv:
                open_ts = ts_ms / 1000
                batch.append({
                    "source": "binance",
                    "market": "crypto",
                    "symbol": symbol,
                    "interval": interval,

                    "kline_open_ts": open_ts,
                    "kline_close_ts": open_ts + interval_sec,
                    "fetch_ts": time.time(),

                    "human_open_time": datetime.fromtimestamp(
                        open_ts, tz=timezone.utc
                    ).isoformat(),
                    "human_open_time_local": datetime.fromtimestamp(
                        open_ts, tz=ZoneInfo("Asia/Taipei")
                    ).isoformat(),

                    "open": float(o),
                    "high": float(h),
                    "low": float(l),
                    "close": float(c),
                    "volume": float(v),
                })

            # 往「更早」疊
            records = batch + records

            # 下一輪往更早抓
            since_ms = ohlcv[0][0] - interval_sec * 1000

            if len(ohlcv) < limit:
                break

            time.sleep(self.exchange.rateLimit / 1000)

        # 裁切最多 max_bars
        return records[-max_bars:]

