# shared_core/pb_lang/pb_ai.py

from __future__ import annotations
from typing import Any, Dict, Optional

from shared_core.event_schema import PBEvent


class PBai:
    """
    PB-Lang: AI Decision Language v2
    用於：
    - 交易決策人格（Attacker / Defender / Balancer…）
    - 議會系統（Proposal / Vote / Decision）
    - RewardHub 學習
    - Self-Reflection 反思
    - XAI 解釋
    - AI 健康 / 錯誤回報
    """

    DEFAULT_SOURCE = "ai_core"

    # ============================================================
    # 1) 基本訊號 / 提案 / 投票 / 決策
    # ============================================================

    @staticmethod
    def signal(
        symbol: str,
        action: str,
        confidence: float,
        reason: str = "",
        factors: Optional[Dict[str, Any]] = None,
        source: str = DEFAULT_SOURCE,
    ) -> PBEvent:
        """
        粗略 AI 訊號：ai.signal
        action: "long" / "short" / "close" / "hold"
        """
        payload = {
            "symbol": symbol,
            "action": action,
            "confidence": float(confidence),
            "reason": reason,
            "factors": factors or {},  # e.g. {"rsi": 68, "trend": "up"}
        }

        return PBEvent(
            type="ai.signal",
            payload=payload,
            source=source,
        )

    @staticmethod
    def proposal(
        agent: str,
        symbol: str,
        proposal: str,
        confidence: float,
        reason: str = "",
        details: Optional[Dict[str, Any]] = None,
        source: str = "ai_agent",
    ) -> PBEvent:
        """
        人格提案：ai.proposal
        agent: "attacker" / "defender" / "balancer" / ...
        proposal: 例如 "open_long" / "reduce_position" / "do_nothing"
        """
        payload = {
            "agent": agent,
            "symbol": symbol,
            "proposal": proposal,
            "confidence": float(confidence),
            "reason": reason,
            "details": details or {},
        }

        return PBEvent(
            type="ai.proposal",
            payload=payload,
            source=source,
        )

    @staticmethod
    def vote(
        agent: str,
        vote: str,
        weight: float = 1.0,
        reason: str = "",
        source: str = "ai_agent",
        meta: Optional[Dict[str, Any]] = None,
    ) -> PBEvent:
        """
        人格投票：ai.vote
        vote: "agree" / "reject" / "abstain"
        """
        payload = {
            "agent": agent,
            "vote": vote,
            "weight": float(weight),
            "reason": reason,
        }
        if meta:
            payload["meta"] = meta

        return PBEvent(
            type="ai.vote",
            payload=payload,
            source=source,
        )

    @staticmethod
    def decision(
        final_action: str,
        final_confidence: float,
        reason: str = "",
        source: str = "ai_chairman",
        details: Optional[Dict[str, Any]] = None,
    ) -> PBEvent:
        """
        主席層最終決策：ai.decision
        final_action: "open_long" / "open_short" / "close" / "hold"...
        """
        payload = {
            "final_action": final_action,
            "final_confidence": float(final_confidence),
            "reason": reason,
        }
        if details:
            payload["details"] = details

        return PBEvent(
            type="ai.decision",
            payload=payload,
            source=source,
            priority=8,  # 比一般事件重要
        )

    # ============================================================
    # 2) RewardHub / 學習相關事件
    # ============================================================

    @staticmethod
    def reward(
        agent: str,
        score: float,
        reason: str = "",
        meta: Optional[Dict[str, Any]] = None,
        source: str = "reward_hub",
    ) -> PBEvent:
        """
        RewardHub 用的獎懲事件：ai.reward
        score: 正值 = 獎勵、負值 = 懲罰
        """
        payload = {
            "agent": agent,
            "score": float(score),
            "reason": reason,
            "meta": meta or {},
        }

        # 給學習用的事件，優先度高一點
        return PBEvent(
            type="ai.reward",
            payload=payload,
            source=source,
            priority=7,
        )

    # ============================================================
    # 3) 自我反思 / 日誌 / 解釋
    # ============================================================

    @staticmethod
    def explain(
        target: str,
        content: str,
        level: str = "short",
        lang: str = "zh-TW",
        source: str = "ai_explainer",
        meta: Optional[Dict[str, Any]] = None,
    ) -> PBEvent:
        """
        XAI 解釋事件：ai.explain
        target: "trade_decision" / "risk_change" / "system" ...
        level: "short" / "detailed"
        """
        payload = {
            "target": target,
            "content": content,
            "level": level,
            "lang": lang,
            "meta": meta or {},
        }

        return PBEvent(
            type="ai.explain",
            payload=payload,
            source=source,
        )

    @staticmethod
    def reflect(
        topic: str,
        content: str,
        quality: Optional[Dict[str, Any]] = None,
        source: str = "self_reflection",
        meta: Optional[Dict[str, Any]] = None,
    ) -> PBEvent:
        """
        自我反思事件：ai.reflect
        topic: "trade_review" / "risk_policy" / "strategy_update"...
        """
        payload = {
            "topic": topic,
            "content": content,
            "quality": quality or {},   # e.g. {"depth": 0.8, "consistency": 0.9}
            "meta": meta or {},
        }

        return PBEvent(
            type="ai.reflect",
            payload=payload,
            source=source,
        )

    # ============================================================
    # 4) 健康狀態 / 錯誤事件
    # ============================================================

    @staticmethod
    def health(
        component: str,
        status: str,
        detail: Optional[Dict[str, Any]] = None,
        source: str = "ai_monitor",
    ) -> PBEvent:
        """
        AI 健康狀態：ai.health
        component: "attacker" / "defender" / "chairman" / "reward_hub" / ...
        status: "ok" / "degraded" / "error"
        """
        payload = {
            "component": component,
            "status": status,
            "detail": detail or {},
        }

        return PBEvent(
            type="ai.health",
            payload=payload,
            source=source,
        )

    @staticmethod
    def error(
        component: str,
        message: str,
        detail: Optional[Dict[str, Any]] = None,
        source: str = "ai_core",
    ) -> PBEvent:
        """
        AI 模組錯誤：ai.error
        專門給人格 / RewardHub / SelfReflection 報錯用
        """
        payload = {
            "component": component,
            "message": message,
            "detail": detail or {},
        }

        return PBEvent(
            type="ai.error",
            payload=payload,
            source=source,
            priority=9,
        )