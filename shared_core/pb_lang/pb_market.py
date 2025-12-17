# shared_core/pb_lang/pb_market.py

from __future__ import annotations

from typing import Any, Dict, Optional
  # 👈 新增這行
from shared_core.event_schema import PBEvent

DEFAULT_SOURCE = "market"

class PBmarket:
    """
    PB-Lang: Market Language v2
    給「交易文明」用的市場事件語言。

    命名範圍統一使用：
      - market.kline
      - market.trade
      - market.risk_alert
      - market.indicator.update
      - market.signal.proposed / filtered / final
      - market.order.new / filled / canceled
      - market.position.update
      - market.latency.warning
      - market.status
    """

    # 之後如果要從 config 或環境注入，可以再改
    DEFAULT_SOURCE = "trading_runtime"

    # ------------------------------------------------------------------
    # 1) 價格 / 成交基礎事件
    # ------------------------------------------------------------------
    @staticmethod
    def kline(
        symbol: str,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        interval: str,
        source: str = DEFAULT_SOURCE,
        extra: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
        ts: Optional[float] = None,
    ) -> PBEvent:
        """
        K 線事件：market.kline（PB-Lang v2 標準格式）
        """

        payload = {
            "symbol": symbol,
            "open": float(open),
            "high": float(high),
            "low": float(low),
            "close": float(close),
            "volume": float(volume),
            "interval": interval,
        }

        # v2 新增欄位
        if extra:
            payload["extra"] = extra

        if meta:
            payload["meta"] = meta

        return PBEvent(
            type="market.kline",
            payload=payload,
            source=source,
            ts=ts,
        )

    @staticmethod
    def trade(
        symbol: str,
        price: float,
        qty: float,
        side: str,
        trade_id: str,
        source: str = DEFAULT_SOURCE,
        extra: Optional[Dict[str, Any]] = None,
    ) -> PBEvent:
        """
        即時成交事件：market.trade
        """
        payload = {
            "symbol": symbol,
            "price": float(price),
            "qty": float(qty),
            "side": side,          # "buy" / "sell"
            "trade_id": trade_id,
        }
        if extra:
            payload["extra"] = extra

        return PBEvent(
            type="market.trade",
            payload=payload,
            source=source,
        )

    @staticmethod
    def risk_alert(
        symbol: str,
        level: str,
        reason: str,
        source: str = DEFAULT_SOURCE,
        extra: Optional[Dict[str, Any]] = None,
    ) -> PBEvent:
        """
        風險警報：market.risk_alert
        level: "info" / "warning" / "danger" / "critical"
        """
        payload = {
            "symbol": symbol,
            "level": level,
            "reason": reason,
        }
        if extra:
            payload["extra"] = extra

        return PBEvent(
            type="market.risk_alert",
            payload=payload,
            source=source,
            priority=5 if level in ("danger", "critical") else 3,
        )

    # ------------------------------------------------------------------
    # 2) 指標 / 訊號流水線事件
    # ------------------------------------------------------------------
    @staticmethod
    def indicator_update(
        symbol: str,
        name: str,
        value: float,
        timeframe: str,
        source: str = "indicator_engine",
        extra: Optional[Dict[str, Any]] = None,
    ) -> PBEvent:
        """
        指標更新事件：market.indicator.update
        e.g. name="rsi_14", timeframe="15m"
        """
        payload = {
            "symbol": symbol,
            "name": name,
            "value": float(value),
            "timeframe": timeframe,
        }
        if extra:
            payload["extra"] = extra

        return PBEvent(
            type="market.indicator.update",
            payload=payload,
            source=source,
        )

    @staticmethod
    def signal_proposed(
        symbol: str,
        action: str,
        confidence: float,
        reason: str = "",
        factors: Optional[Dict[str, Any]] = None,
        source: str = "signal_engine",
    ) -> PBEvent:
        """
        初始訊號提案：market.signal.proposed
        action: "long" / "short" / "close" / "hold"
        """
        payload = {
            "symbol": symbol,
            "action": action,
            "confidence": float(confidence),
            "reason": reason,
            "factors": factors or {},   # 指標/情緒/結構等細節
        }

        return PBEvent(
            type="market.signal.proposed",
            payload=payload,
            source=source,
        )

    @staticmethod
    def signal_filtered(
        symbol: str,
        action: str,
        passed: bool,
        filters: Optional[Dict[str, bool]] = None,
        reason: str = "",
        source: str = "signal_filter",
    ) -> PBEvent:
        """
        訊號經過濾器後的結果：market.signal.filtered
        passed: True 代表通過所有 filter
        """
        payload = {
            "symbol": symbol,
            "action": action,
            "passed": bool(passed),
            "filters": filters or {},   # e.g. {"risk_guard": True, "cooldown": False}
            "reason": reason,
        }

        return PBEvent(
            type="market.signal.filtered",
            payload=payload,
            source=source,
        )

    @staticmethod
    def signal_final(
        symbol: str,
        action: str,
        confidence: float,
        reason: str = "",
        source: str = "decision_engine",
        meta: Optional[Dict[str, Any]] = None,
    ) -> PBEvent:
        """
        最終可執行訊號：market.signal.final
        這通常是已經通過風控、冷卻時間、攻擊者/防禦者討論後。
        """
        payload = {
            "symbol": symbol,
            "action": action,
            "confidence": float(confidence),
            "reason": reason,
        }
        if meta:
            payload["meta"] = meta

        return PBEvent(
            type="market.signal.final",
            payload=payload,
            source=source,
            priority=7,   # 比一般事件高一點
        )

    # ------------------------------------------------------------------
    # 3) 下單 / 成交 / 取消 / 倉位 相關事件
    # ------------------------------------------------------------------
    @staticmethod
    def order_new(
        symbol: str,
        side: str,
        qty: float,
        order_type: str,
        price: Optional[float] = None,
        client_order_id: Optional[str] = None,
        source: str = "order_manager",
        extra: Optional[Dict[str, Any]] = None,
    ) -> PBEvent:
        """
        新建訂單事件：market.order.new
        side: "buy" / "sell"
        order_type: "market" / "limit" / ...
        """
        payload = {
            "symbol": symbol,
            "side": side,
            "qty": float(qty),
            "order_type": order_type,
            "price": float(price) if price is not None else None,
            "client_order_id": client_order_id,
        }
        if extra:
            payload["extra"] = extra

        return PBEvent(
            type="market.order.new",
            payload=payload,
            source=source,
            priority=8,
        )

    @staticmethod
    def order_filled(
        symbol: str,
        side: str,
        qty: float,
        avg_price: float,
        order_id: str,
        client_order_id: Optional[str] = None,
        source: str = "trade_executor",
        extra: Optional[Dict[str, Any]] = None,
    ) -> PBEvent:
        """
        訂單完全成交：market.order.filled
        """
        payload = {
            "symbol": symbol,
            "side": side,
            "qty": float(qty),
            "avg_price": float(avg_price),
            "order_id": order_id,
            "client_order_id": client_order_id,
        }
        if extra:
            payload["extra"] = extra

        return PBEvent(
            type="market.order.filled",
            payload=payload,
            source=source,
            priority=9,
        )

    @staticmethod
    def order_canceled(
        symbol: str,
        side: str,
        order_id: str,
        reason: str,
        client_order_id: Optional[str] = None,
        source: str = "trade_executor",
        extra: Optional[Dict[str, Any]] = None,
    ) -> PBEvent:
        """
        訂單取消事件：market.order.canceled
        """
        payload = {
            "symbol": symbol,
            "side": side,
            "order_id": order_id,
            "client_order_id": client_order_id,
            "reason": reason,
        }
        if extra:
            payload["extra"] = extra

        return PBEvent(
            type="market.order.canceled",
            payload=payload,
            source=source,
        )

    @staticmethod
    def position_update(
        symbol: str,
        position: str,
        size: float,
        entry_price: float,
        pnl: Optional[float] = None,
        leverage: Optional[float] = None,
        source: str = "position_manager",
        extra: Optional[Dict[str, Any]] = None,
    ) -> PBEvent:
        """
        倉位更新：market.position.update
        position: "LONG" / "SHORT" / "FLAT"
        """
        payload = {
            "symbol": symbol,
            "position": position,
            "size": float(size),
            "entry_price": float(entry_price),
            "pnl": float(pnl) if pnl is not None else None,
            "leverage": float(leverage) if leverage is not None else None,
        }
        if extra:
            payload["extra"] = extra

        return PBEvent(
            type="market.position.update",
            payload=payload,
            source=source,
        )

    # ------------------------------------------------------------------
    # 4) 延遲 / 市場狀態 事件
    # ------------------------------------------------------------------
    @staticmethod
    def latency_warning(
        component: str,
        latency_ms: float,
        threshold_ms: float,
        source: str = "latency_monitor",
        extra: Optional[Dict[str, Any]] = None,
    ) -> PBEvent:
        """
        延遲警告事件：market.latency.warning
        用來監控：API、資料源、指標計算等。
        """
        payload = {
            "component": component,      # e.g. "binance_api", "indicator_engine"
            "latency_ms": float(latency_ms),
            "threshold_ms": float(threshold_ms),
        }
        if extra:
            payload["extra"] = extra

        return PBEvent(
            type="market.latency.warning",
            payload=payload,
            source=source,
        )

    @staticmethod
    def market_status(
        symbol: str,
        status: str,
        reason: str = "",
        source: str = "market_watcher",
        extra: Optional[Dict[str, Any]] = None,
    ) -> PBEvent:
        """
        市場狀態事件：market.status
        status: "normal" / "halted" / "high_volatility" / ...
        """
        payload = {
            "symbol": symbol,
            "status": status,
            "reason": reason,
        }
        if extra:
            payload["extra"] = extra

        return PBEvent(
            type="market.status",
            payload=payload,
            source=source,
        )

