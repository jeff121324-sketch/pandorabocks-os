# trading_core/perception/market_adapter.py

from shared_core.pb_lang.perception_adapter import PerceptionAdapter
from shared_core.event_schema import PBEvent
from shared_core.security.blacklist import is_symbol_blocked
import math
import time

# ==========================
# 黑名單（你未來可以做成 config）
# ==========================
BLACKLIST = set([
    "BTC3S/USDT",
    "SCAM/USDT",
])

def is_symbol_blocked(sym: str) -> bool:
    return sym in BLACKLIST

class MarketKlineAdapter(PerceptionAdapter):
    """
    市場 K 線感知器（Firewall v3）
    - 毒物過濾器（filter）
    - 資料修復器（auto_fix）
    - Anti-Poison Shield（高頻攻擊緩衝層）
    """
    def __init__(self, mode="realtime", validator=None):
        super().__init__(source="trading.kline")

        self.mode = mode     # ⭐ 新增：批次 / 即時模式切換
        self.validator = validator
        # 用來做 Anti-Poison 高頻保護
        self.last_ts = 0
        self.last_price = None
        self.last_vol = None

        # 黑名單可加在這
        self.blacklist = {"SCAM/USDT", "XX/USDT"}

    # ---------- 【1】毒物過濾器（黑名單・欄位缺失・非法值） ----------
    def filter(self, raw: dict):
        symbol = raw.get("symbol") or raw.get("pair")

        if not symbol:
            print("[MarketKlineAdapter] ⚠️ 無 symbol，丟棄資料")
            return None

        if is_symbol_blocked(symbol):
            print(f"[MarketKlineAdapter] ⛔ 黑名單 symbol：{symbol}，丟棄資料")
            return None

        # 基本欄位檢查
        if self.mode == "realtime":
            required = ("open", "high", "low", "close")
        else:  # batch / replay
            required = ("open", "close")

        for key in required:
            v = raw.get(key)
            if v is None or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0:
                print(
                    f"[MarketKlineAdapter] ⛔ ({self.mode}) {key}={v} 非法，丟棄資料"
                )
                return None

        vol = raw.get("volume", 0)
        if vol is None or not isinstance(vol, (int, float)) or vol < 0:
            print(f"[MarketKlineAdapter] ⛔ volume={vol} 非法，丟棄資料")
            return None

        return raw

    # -------------------------------------------------------
    # 【2】Auto-Fix：自動修復異常資料
    # -------------------------------------------------------
    def auto_fix(self, raw: dict):
        h = raw["high"]
        l = raw["low"]
        c = raw["close"]
        v = raw["volume"]

        # 修復 high < low
        if h < l:
            raw["high"], raw["low"] = l, h
            print(f"[Adapter] 🔧 修復 high/low → high={raw['high']}, low={raw['low']}")

        # 修復 close 暴力跳動（超過 25%）
        if self.last_price is not None:
            if abs(c - self.last_price) / max(self.last_price, 1) > 0.25:
                print(f"[Adapter] 🔧 修復 close 跳動 → 使用上一筆 close={self.last_price}")
                raw["close"] = self.last_price

        # 修復 volume = 0
        if v == 0:
            raw["volume"] = self.last_vol if self.last_vol else 1
            print(f"[Adapter] 🔧 修復 volume=0 → volume={raw['volume']}")

        return raw

    # -------------------------------------------------------
    # ⭐ 中控：auto_fix → anti_poison → enrich
    # -------------------------------------------------------
    def post_filter(self, raw: dict):
        """把三層濾網串成一個統一流程"""

        # 1) 自動修復
        raw = self.auto_fix(raw)
        if raw is None:
            return None

        # 2) Anti-Poison 防護（批次模式直接通過）
        raw = self.anti_poison(raw)
        if raw is None:
            return None

        # 3) 補齊欄位
        raw = self.enrich(raw)
        if raw is None:
            return None

        return raw
    # -------------------------------------------------------
    # 【3】Anti-Poison：高頻垃圾事件防護
    # -------------------------------------------------------
    def anti_poison(self, raw: dict):
        # 系統到達時間（Anti-Poison 專用）
        arrival_ts = time.time()

        # --------------------------------------------------------
        # ⭐ Batch / Bootstrap：允許合法批量湧入
        # --------------------------------------------------------
        if self.mode in ("bootstrap", "batch"):
            # 只做「重複事件」防護，避免交易所 API 問題
            if self.last_price is not None and self.last_vol is not None:
                if raw["close"] == self.last_price and raw["volume"] == self.last_vol:
                    print("[Adapter] 🛡️ Anti-Poison：重複事件 → 拒收")
                    return None

            # 更新狀態（但不做 arrival rate 檢查）
            self.last_price = raw["close"]
            self.last_vol = raw["volume"]
            return raw

        # --------------------------------------------------------
        # ⭐ Real-Time 模式：嚴格防護
        # --------------------------------------------------------
        min_interval = 0.10  # 100ms

        if self.last_ts == 0:
            self.last_ts = arrival_ts
            self.last_price = raw["close"]
            self.last_vol = raw["volume"]
            return raw

        # 1) 到達密度防護（Anti-Flood）
        if arrival_ts - self.last_ts < min_interval:
            print(f"[Adapter] 🛡️ Anti-Poison：到達過密 → 拒收 ({arrival_ts - self.last_ts:.6f}s)")
            return None

        # 2) 重複事件防護
        if raw["close"] == self.last_price and raw["volume"] == self.last_vol:
            print("[Adapter] 🛡️ Anti-Poison：重複事件 → 拒收")
            return None

        # 更新狀態
        self.last_ts = arrival_ts
        self.last_price = raw["close"]
        self.last_vol = raw["volume"]

        return raw


    # -------------------------------------------------------
    # 【4】Enrich：補齊 interval / ts
    # -------------------------------------------------------
    def enrich(self, raw):
        """補齊必備欄位（PBEvent Validator 會要求）"""
    
        # interval：adapter 自己定義，或從 mode 推
        if "interval" not in raw or raw["interval"] is None:
            raw["interval"] = "1m"   # ⭐ 壓力測試版統一用 1m，可自行調
        
        # ts：若沒有，就補現在時間（不影響 batch）
        if "ts" not in raw or raw["ts"] is None:
            raw["ts"] = time.time()


        return raw

    # -------------------------------------------------------
    # 【5】轉換成 PBEvent
    # -------------------------------------------------------
    def make_event(self, raw: dict) -> PBEvent:
        return PBEvent(
            type="market.kline",
            payload={
                "symbol": raw["symbol"],
                "open": float(raw["open"]),
                "high": float(raw["high"]),
                "low": float(raw["low"]),
                "close": float(raw["close"]),
                "volume": float(raw["volume"]),
                "interval": raw["interval"],
            },
            source=self.source,
            ts=raw["ts"],
        )


    # -------------------------------------------------------
    # 【5】總控：raw → PBEvent
    # -------------------------------------------------------
    def to_event(self, raw: dict):
        """
        完整流程：
        1) filter        → 黑名單 / 基本欄位 / 數值合法性
        2) auto_fix      → 修復 high/low / close 跳動 / volume=0
        3) anti_poison   → 高頻垃圾 / 重複事件防護
        4) enrich        → interval / ts 補齊
        5) make_event    → 轉成 PBEvent + Validator
        """

        # 1) 前段毒物過濾
        raw = self.filter(raw)
        if raw is None:
            return None

        # 2) 修復 + 防護 + 補欄位
        raw = self.post_filter(raw)
        if raw is None:
            return None

        # 3) 建立事件
        event = self.make_event(raw)

        # 4) Validator（使用外部注入的 PBEventValidator）
        if self.validator is not None:
            # batch 模式使用 soft-drop，不丟 exception
            soft = (self.mode == "batch")
            event = self.validator.validate(event, soft=soft)

            # soft 模式下，如果驗證失敗會回傳 None → 直接丟棄
            if event is None:
                return None

        # 沒有 validator，當純轉換使用
        return event