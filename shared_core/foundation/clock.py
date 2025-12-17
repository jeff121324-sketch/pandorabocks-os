# shared_core/foundation/clock.py
from datetime import datetime, timezone, timedelta
import time


class Clock:
    """
    🌐 Pandora Universal Clock
    全文明統一時間標準：
    - UTC 為基準
    - Local TZ 可設定（預設 Asia/Taipei）
    - 支援 Unix timestamp
    - 支援標準化格式
    """

    # 你之後可以讓這個設定接 AI / CLI / config
    LOCAL_TZ_OFFSET = timedelta(hours=8)   # Asia/Taipei (+08)

    @staticmethod
    def utc_now():
        """取得 UTC 標準時間（ISO 格式）"""
        return datetime.now(timezone.utc)

    @staticmethod
    def utc_iso():
        """UTC ISO 字串版本"""
        return Clock.utc_now().isoformat()

    @staticmethod
    def unix():
        """Unix timestamp，用於交易 K 線對齊"""
        return int(time.time())

    @staticmethod
    def local_now():
        """在本地時區取得現在時間（不依賴系統時區）"""
        return datetime.now(timezone.utc) + Clock.LOCAL_TZ_OFFSET

    @staticmethod
    def local_iso():
        """本地時區 ISO 格式（台灣系統、AISOP 系統會用到）"""
        return Clock.local_now().isoformat()

    @staticmethod
    def format(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S"):
        """格式化 datetime 為字串"""
        return dt.strftime(fmt)

    @staticmethod
    def from_unix(ts: int):
        """將 unix timestamp 轉為 datetime"""
        return datetime.fromtimestamp(ts, timezone.utc)
