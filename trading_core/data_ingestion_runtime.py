# trading_core/data_ingestion_runtime.py
from data_provider.raw_fetcher import RawMarketFetcher
from trading_core.data.raw_writer import RawMarketWriter

class DataIngestionRuntime:
    """
    Data Ingestion Runtime v1
    - 抓 raw 資料
    - 落地到 data/raw
    - 可選：送進 Gateway
    """
    plugin_name = "DataIngestionRuntime"
    required_capabilities = []

    def __init__(self, rt):
        self.fetcher = RawMarketFetcher()
        self.writer = RawMarketWriter(base_dir="trading_core/data")

        self.gateway = getattr(rt, "gateway", None)
        self.bus = rt.fast_bus
        self._done = False   # ⭐ 新增這一行
        print("[DataIngestionRuntime] Initialized")

    def tick(self):
        if self._done:
            return   # ⛔ 已完成就什麼都不做

        records = self.fetcher.fetch(
            symbol="BTC/USDT",
            interval="1m",
            limit=2
        )

        for r in records:
            self.writer.write(r)

            # 可選：直接 event 化（你現在可以開）
            if self.gateway:
                self.gateway.process_and_publish(
                    "market.kline",
                    r,
                    bus=self.bus,
                    soft=True
                )

        print("[DataIngestionRuntime] ✅ ingestion completed")
        self._done = True    # ⭐ 關鍵：標記完成
