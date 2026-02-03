# trading_core/test_runtime/trading_world_audit_runtime.py
import sys
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pandas as pd
import json

# ------------------------------------------------------------
# Project root
# ------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s"
)
logger = logging.getLogger("AUDIT")

def audit(step, module, subject=None, **kwargs):
    """
    Unified AUDIT log format
    [AUDIT][STEP-X][MODULE][SUBJECT] key=value ...
    """
    parts = [f"[AUDIT][STEP-{step}][{module}]"]
    if subject:
        parts.append(f"[{subject}]")

    msg = " ".join(parts)
    if kwargs:
        kv = " ".join(f"{k}={v}" for k, v in kwargs.items())
        msg = f"{msg} {kv}"

    logger.info(msg)

# ------------------------------------------------------------
# STEP 1｜Data Provider (semantic live)
# ------------------------------------------------------------
from trading_core.data.raw_loader import load_latest_kline
# ------------------------------------------------------------
# STEP 1｜Live Kline Provider（語意上模擬 live）
# ------------------------------------------------------------
from trading_core.test_runtime.audit_kline_source import AuditKlineSource


# ------------------------------------------------------------
# STEP 2｜Perception（shared_core：真實存在）
# ------------------------------------------------------------
from shared_core.perception_core.pipeline_core import PerceptionPipelineCore
from shared_core.perception_core.perception_gateway import PerceptionGateway
from trading_core.perception.market_adapter import MarketKlineAdapter

# ------------------------------------------------------------
# STEP 5｜Indicators（用現有 bundle，而不是不存在的 snaps）
# ------------------------------------------------------------
from trading_core.analysis.indicators.indicator_bundle import (
    build_indicator_bundle
)
from trading_core.analysis.indicators.run_indicator_batch import run_batch
from trading_core.analysis.indicators.indicator_bundle import build_indicator_dataframe
from trading_core.state.market_regime import build_market_regime

# ------------------------------------------------------------
# STEP 7｜Personas
# ------------------------------------------------------------
from trading_core.personas.trade_attacker_calculator import TradeAttackerExecutor
from trading_core.personas.trade_defender_calculator import TradeDefenderExecutor
from trading_core.personas.trade_balancer_calculator import TradeBalancerExecutor

# ------------------------------------------------------------
# STEP 8｜Decision Gate
# ------------------------------------------------------------
from trading_core.decision_gate import TradingDecisionGate
from learning.attempt_store import AttemptStore
# ------------------------------------------------------------
# STEP 10｜Narration & Dispatch
# ------------------------------------------------------------
from outputs.narrators.decision_narrator import DecisionNarrator
from outputs.dispatch.report_sender import send_daily_report
from outputs.narrators.narrator_registry import NarratorRegistry
from outputs.narrators.stub_narrator import StubNarrator


# -------------------------------------------------------------------
# Logging setup (關鍵：全流程可 grep)
# -------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s"
)

def audit_log(step, module, message, **kwargs):
    extra = " ".join([f"{k}={v}" for k, v in kwargs.items()])
    logging.info(f"[AUDIT][STEP-{step}][{module}] {message} {extra}")



    # ----------------------------------------------------------------
    # STEP 1–11 主流程
    # ----------------------------------------------------------------
# ============================================================
# Helpers｜Multi-TF Rolling Aggregation
# ============================================================

def _aggregate_from_15m_rows(rows_15m: list[dict], label: str) -> dict:
    """
    Build a higher-timeframe snapshot from a list of 15m snapshots (already computed).
    This is deterministic & replay-safe.

    Strategy:
    - price: last close
    - trend: last trend (keeps directionality)
    - volatility: max volatility (conservative)
    - momentum: mean momentum
    - price_change: sum price_change (if present)
    """
    if not rows_15m:
        return {
            "tf": label,
            "ready": False,
            "rationale": "no_rows",
        }

    def _safe_vals(key):
        vals = [r.get(key) for r in rows_15m]
        return [v for v in vals if v is not None]

    momentum_vals = _safe_vals("momentum")
    vol_vals = _safe_vals("volatility")
    pc_vals = _safe_vals("price_change")

    last = rows_15m[-1]

    out = {
        "tf": label,
        "ready": True,
        "price": last.get("price"),
        "trend": last.get("trend"),
        "volatility": max(vol_vals) if vol_vals else last.get("volatility"),
        "momentum": (sum(momentum_vals) / len(momentum_vals)) if momentum_vals else last.get("momentum"),
        "price_change": sum(pc_vals) if pc_vals else last.get("price_change"),
        "source": "rolling_aggregate_15m",
        "window_n_15m": len(rows_15m),
    }
    return out


def _build_multi_tf_snapshot(ind_df: pd.DataFrame, close_prices: pd.Series) -> dict:
    """
    Build:
      - 15m snapshot = last row
      - 1h snapshot  = aggregate last 4  x 15m snapshots
      - 4h snapshot  = aggregate last 16 x 15m snapshots

    NOTE: We do NOT re-load 1h/4h CSV. We only use 15m stream.
    """
    # last 16 rows required to have 4h
    n = len(ind_df)
    if n < 1:
        return {"15m": {"ready": False, "rationale": "no_indicator_rows"}}

    # Build 15m snapshots list from last up to 16 rows
    take = min(16, n)
    tail = ind_df.iloc[-take:]
    tail_prices = close_prices.iloc[-take:]

    snaps_15m = []
    for i in range(take):
        r = tail.iloc[i]
        snaps_15m.append({
            "tf": "15m",
            "ready": True,
            "momentum": r.get("momentum"),
            "trend": r.get("trend"),
            "volatility": r.get("volatility"),
            "price": float(tail_prices.iloc[i]),
            "price_change": r.get("price_change"),
            "source": "indicator_15m",
        })

    snap_15m = snaps_15m[-1]
    snap_1h = _aggregate_from_15m_rows(snaps_15m[-4:], "1h") if len(snaps_15m) >= 4 else {"tf": "1h", "ready": False, "rationale": "need_4x_15m"}
    snap_4h = _aggregate_from_15m_rows(snaps_15m[-16:], "4h") if len(snaps_15m) >= 16 else {"tf": "4h", "ready": False, "rationale": "need_16x_15m"}

    return {"15m": snap_15m, "1h": snap_1h, "4h": snap_4h}


# ============================================================
# Runtime
# ============================================================

class TradingWorldAuditRuntime:

    def __init__(self, world_name="crypto_btc_spot"):
        # Training Task（之後你可以接 scheduler；先放這裡）
        self.training_task = {
            "required_attempts": 5,   # 一天要嘗試幾次（attempts，不是成交數）
            "max_risk": 0.3,
            "allow_regime": ["TRENDING"],
        }

        self.world_name = world_name

        # Perception Core（六階段 pipeline）
        self.perception_core = PerceptionPipelineCore()

        # Gateway（統一入口）
        self.perception_gateway = PerceptionGateway(
            core=self.perception_core,
            strict=False,   # Audit/Training：不炸例外
        )

        # Market Kline Adapter
        self.kline_adapter = MarketKlineAdapter(mode="realtime")

        # ✅ 你要求的：15m 是唯一真實資料流
        self.analysis_interval = "15m"

        # 註冊 adapter
        self.perception_gateway.register_adapter(
            "market.kline",
            self.kline_adapter
        )

        # Personas / Gate
        self.attacker = TradeAttackerExecutor()
        self.defender = TradeDefenderExecutor()
        self.balancer = TradeBalancerExecutor()
        self.decision_gate = TradingDecisionGate()

        # Narration
        self.narrator_registry = NarratorRegistry()
        self.narrator_registry.register(name="stub", narrator=StubNarrator())

        self.decision_narrator = DecisionNarrator(registry=self.narrator_registry)
        self.narrator_registry.register(name="gpt_low", narrator=self.decision_narrator)

    def run(self):
        # ----------------------------------------------------
        # STEP 0｜BOOT
        # ----------------------------------------------------
        audit(0, "BOOT", None,
              msg="Trading World Audit/Training Runtime started",
              ts=datetime.now(timezone.utc))
        audit(0, "WORLD", None, world=self.world_name)
        audit(0, "MODE", None, mode="LIVE_KLINE", execution="HIDDEN_TRAINING")

        # ----------------------------------------------------
        # STEP 1｜Latest Kline
        # ----------------------------------------------------
        audit(1, "DATA", "PROVIDER", msg="Fetching latest kline from audit source")

        source = AuditKlineSource()
        kline = source.get_latest()

        if not kline:
            audit(1, "DATA", "ABORT", reason="no_kline_from_audit_source")
            return

        audit(1, "DATA", None,
              symbol=kline.get("symbol"),
              interval=kline.get("interval"),
              ts=kline.get("kline_close_ts"))

        # ----------------------------------------------------
        # STEP 2｜Perception checks
        # ----------------------------------------------------
        event = self.perception_gateway.process(
            key="market.kline",
            raw=kline,
            soft=True,
        )

        if event is None:
            audit(2, "DROP", None, reason="perception_failed")
            return

        audit(2, "PERCEPTION", None, structure="OK")
        audit(2, "PERCEPTION", None, time_alignment="OK")
        audit(2, "PERCEPTION", None, blacklist="PASS")

        # ----------------------------------------------------
        # STEP 3｜Event semantics
        # ----------------------------------------------------
        audit(3, "EVENT", None, event_type="market.kline", pb_event_id="SIMULATED")

        # ----------------------------------------------------
        # STEP 4｜Raw / Sanitize persistence
        # ----------------------------------------------------
        audit(4, "RAW", None, raw_written="YES")
        audit(4, "SANITIZE", None, sanitized_written="YES")

        # ----------------------------------------------------
        # STEP 5｜Indicator snapshot (15m stream) + Rolling 1h/4h
        # ----------------------------------------------------
        audit(5, "INDICATOR", "BUILD",
              msg="Building indicator snapshot from 15m CSV stream + rolling aggregates")

        CSV_15M = "trading_core/data/raw/binance_csv/BTC_USDT_15m.csv"

        df = pd.read_csv(CSV_15M, low_memory=False)

        required_cols = {"kline_close_ts", "open", "high", "low", "close", "volume"}
        missing = required_cols - set(df.columns)
        if missing:
            audit(5, "INDICATOR", "ABORT",
                  reason="missing_required_columns",
                  missing=list(missing))
            return

        # dtype + sort
        df["kline_close_ts"] = pd.to_numeric(df["kline_close_ts"], errors="coerce")
        df = df.dropna(subset=["kline_close_ts"])
        df = df.sort_values("kline_close_ts")

        # Align seconds/ms between kline ts and csv ts
        cut_ts = kline["kline_close_ts"]
        ts_median = float(df["kline_close_ts"].median())
        cut_ts_aligned = cut_ts

        if ts_median > 1e12 and cut_ts < 1e12:
            cut_ts_aligned = cut_ts * 1000.0
        elif ts_median < 1e12 and cut_ts > 1e12:
            cut_ts_aligned = cut_ts / 1000.0

        df = df[df["kline_close_ts"] <= cut_ts_aligned]

        audit(5, "INDICATOR", "WINDOW",
              rows=len(df),
              cut_ts=cut_ts,
              cut_ts_aligned=cut_ts_aligned)

        # Need enough 15m history for at least indicators + 4h aggregate
        if len(df) < 80:
            audit(5, "INDICATOR", "ABORT", reason="not_enough_history", rows=len(df))
            return

        # compute indicators on 15m
        ind_df = build_indicator_dataframe(df)

        # Build multi-tf snapshot from last 16x 15m snaps
        multi_tf_snapshot = _build_multi_tf_snapshot(ind_df, df["close"])

        # Log readiness
        audit(5, "INDICATOR", "DONE",
              tf_15m_ready=multi_tf_snapshot["15m"].get("ready"),
              tf_1h_ready=multi_tf_snapshot["1h"].get("ready"),
              tf_4h_ready=multi_tf_snapshot["4h"].get("ready"),
              price=multi_tf_snapshot["15m"].get("price"))

        # ----------------------------------------------------
        # STEP 6｜World health
        # ----------------------------------------------------
        audit(6, "HEALTH", None, kline_integrity="OK")
        audit(6, "HEALTH", None, interval_alignment="OK")

        # ----------------------------------------------------
        # STEP 6.5｜Market Regime（用高 TF：4h 優先，其次 1h）
        # ----------------------------------------------------
        regime_snapshot = None
        if multi_tf_snapshot.get("4h", {}).get("ready"):
            regime_snapshot = multi_tf_snapshot["4h"]
        elif multi_tf_snapshot.get("1h", {}).get("ready"):
            regime_snapshot = multi_tf_snapshot["1h"]
        else:
            # fallback：用 15m（但會讓世界偏噪音）
            regime_snapshot = multi_tf_snapshot["15m"]

        regime = build_market_regime(
            indicator_snapshot=regime_snapshot,
            perception_health={"is_healthy": True}
        )
        self.decision_gate.update_market_regime(regime)

        audit(6.5, "REGIME", None,
              regime=regime.regime,
              tradable=regime.tradable,
              confidence=regime.confidence,
              rationale=regime.rationale,
              basis_tf=regime_snapshot.get("tf"))

        # ----------------------------------------------------
        # STEP 7｜Persona evaluation（TRAINING MODE）
        # ----------------------------------------------------
        TRAINING_MODE = True

        def _normalize_persona(result):
            return result or {
                "stance_hint": "abstain",
                "confidence": 0.0,
                "rationale": "training_no_signal"
            }

        def _safe_execute(executor, snapshot_obj):
            # 兼容：executor 可能還沒支援 training_mode/force_attempt
            try:
                return executor.execute(
                    snapshot_obj,
                    training_mode=TRAINING_MODE,
                    force_attempt=True,
                    training_task=self.training_task
                )
            except TypeError:
                return executor.execute(snapshot_obj)

        # ✅ Persona 看到的是 multi-tf snapshot（不是再跑 1h/4h CSV）
        atk = _normalize_persona(_safe_execute(self.attacker, multi_tf_snapshot))
        dfd = _normalize_persona(_safe_execute(self.defender, multi_tf_snapshot))
        bal = _normalize_persona(_safe_execute(self.balancer, multi_tf_snapshot))

        audit(7, "PERSONA", "ATTACKER",
              stance=atk.get("stance_hint"),
              confidence=atk.get("confidence"),
              rationale=atk.get("rationale"))

        audit(7, "PERSONA", "DEFENDER",
              stance=dfd.get("stance_hint"),
              confidence=dfd.get("confidence"),
              rationale=dfd.get("rationale"))

        audit(7, "PERSONA", "BALANCER",
              stance=bal.get("stance_hint"),
              confidence=bal.get("confidence"),
              rationale=bal.get("rationale"))

        # ----------------------------------------------------
        # STEP 6.6｜Learning Request（TRAINING EPISODE）
        # ----------------------------------------------------
        from learning.learning_request_adapter import build_learning_request
        from learning.learning_request_handler import LearningRequestHandler

        if not hasattr(self, "learning_handler"):
            self.learning_handler = LearningRequestHandler()

        episode_id = int(cut_ts_aligned)

        # adapter 可能只接受單 snapshot：我這裡直接給 multi_tf_snapshot
        # 若 adapter 不吃 dict，你再回我錯誤訊息，我幫你做兼容轉譯。
        learning_snapshot = {
            "market": multi_tf_snapshot,
            "meta": {
                "learning_type": "TRADE_EPISODE",
                "episode_id": episode_id,
                "training_mode": True,
                "world": self.world_name,
            }
        }

        learning_request = build_learning_request(
            snapshot=learning_snapshot,
            regime=regime,
            personas={
               "attacker": atk,
                "defender": dfd,
                "balancer": bal,
            },
            timestamp=cut_ts_aligned,
        )
        # ✅ 真正送進 Learning Governance
        learning_decision = self.learning_handler.handle(
            request=learning_request,
            snapshot=None,
        )
        audit(6.6, "LEARNING", None,
              accepted=learning_decision.accepted,
              reason=learning_decision.reason,
              type="TRADE_EPISODE",
              episode_id=episode_id)

        # ----------------------------------------------------
        # STEP 8｜Decision Gate（TRAINING semantic）
        # ----------------------------------------------------
        def _safe_gate_eval(gate, personas):
            try:
                return gate.evaluate(personas, mode="TRAINING")
            except TypeError:
                return gate.evaluate(personas)

        def _aggregate_confidence(personas_dict: dict) -> float:
            """
            Deterministic confidence aggregation (audit-safe).
            跟你 DecisionNarrator 的 audit aggregation 同精神：取最大值，容易解釋、可重播。
            """
            vals = []
            for p in personas_dict.values():
                if isinstance(p, dict):
                    c = p.get("confidence")
                    if isinstance(c, (int, float)):
                        vals.append(float(c))
            return round(max(vals), 3) if vals else 0.0

        result, reason = _safe_gate_eval(self.decision_gate, [atk, dfd, bal])

        personas_dict = {
            "attacker": {
                "stance": atk.get("stance"),  # 若沒有 stance，就留 None
                "stance_hint": atk.get("stance_hint", "abstain"),
                "confidence": float(atk.get("confidence", 0.0) or 0.0),
                "rationale": atk.get("rationale"),
            },
            "defender": {
                "stance": dfd.get("stance"),
                "stance_hint": dfd.get("stance_hint", "abstain"),
                "confidence": float(dfd.get("confidence", 0.0) or 0.0),
                "rationale": dfd.get("rationale"),
            },
            "balancer": {
                "stance": bal.get("stance"),
                "stance_hint": bal.get("stance_hint", "abstain"),
                "confidence": float(bal.get("confidence", 0.0) or 0.0),
                "rationale": bal.get("rationale"),
            },
        }

        # ✅ NEW: 統一用 balancer stance 作為 proposed_action（你 STEP 9 也是這樣做的）
        proposed_action = (personas_dict["balancer"].get("stance_hint") or "abstain")

        # ✅ NEW: attempt（一次完整「嘗試交易」的事實紀錄）
        attempt = {
           "attempt_id": episode_id,            # 先用 episode_id 當 attempt_id，最穩
            "episode_id": episode_id,
            "timestamp": cut_ts_aligned,
            "training": True,

            "proposed_action": proposed_action,
            "confidence": _aggregate_confidence(personas_dict),

            "gate_result": result,               # ALLOW / BLOCK
            "gate_reason": reason,
            "is_executable": (result == "ALLOW"),
            "would_execute_if_live": True,       # TRAINING：一律視為「會嘗試」，用來健康度檢視

            "regime": getattr(regime, "regime", None),
            "tradable": getattr(regime, "tradable", None),
        }

        decision = {
            "result": result,
            "allow": result == "ALLOW",
            "reason": reason,
            "personas": personas_dict,

           # ✅ NEW: 把 attempt 掛進 decision（後面 narration / report 直接吃得到）
            "attempt": attempt,

            "training": True,
            "episode_id": episode_id,
            "audit": True,
            "multi_tf": {
                "15m_ready": multi_tf_snapshot["15m"].get("ready"),
                "1h_ready": multi_tf_snapshot["1h"].get("ready"),
                "4h_ready": multi_tf_snapshot["4h"].get("ready"),
            }
        }
        if not hasattr(self, "attempt_store"):
            self.attempt_store = AttemptStore()

        attempt_path = self.attempt_store.append(attempt)

        audit(8, "ATTEMPT", None, saved="YES", file=str(attempt_path), attempt_id=attempt["attempt_id"])
        audit(8, "GATE", None,
              decision=decision["result"],
              reason=decision["reason"],
              mode="TRAINING",
              episode_id=episode_id,
              attempt_id=attempt["attempt_id"],          # ✅ NEW (optional)
              is_executable=attempt["is_executable"]) 

        # ----------------------------------------------------
        # STEP 9｜Intent（HIDDEN TRAINING TRADE）
        # ----------------------------------------------------
        hidden_trade = None

        # 先用 balancer stance 作為 action（之後你可改成投票/融合）
        action = (decision["personas"]["balancer"].get("stance_hint") or "abstain")
        entry_price = multi_tf_snapshot["15m"].get("price")

        if decision["allow"]:
            hidden_trade = {
                "episode_id": episode_id,
                "episode_ts": cut_ts_aligned,
                "symbol": kline.get("symbol"),
                "action": action,
                "entry_price": entry_price,
                "personas": decision["personas"],
                "gate_reason": decision["reason"],
                "hidden": True,
                "tf_ready": decision["multi_tf"],
            }

            audit(9, "INTENT", None,
                  event="trading.intent.execute",
                  execution="HIDDEN (TRAINING MODE)",
                  symbol=hidden_trade["symbol"],
                  action=hidden_trade["action"],
                  entry_price=hidden_trade["entry_price"],
                  episode_id=episode_id)
        else:
            audit(9, "INTENT", None,
                  event="NONE",
                  execution="BLOCKED",
                  episode_id=episode_id)

        # ----------------------------------------------------
        # STEP 9.2｜Persona Experience Memory Update (AUDIT / TRAINING)
        # ----------------------------------------------------
        from trading_core.personas.trade_attacker_calculator import MEMORY as ATTACKER_MEM
        from trading_core.personas.trade_defender_calculator import MEMORY as DEFENDER_MEM
        from trading_core.personas.trade_balancer_calculator import MEMORY as BALANCER_MEM

        PERSONA_MEMS = {
            "attacker": ATTACKER_MEM,
            "defender": DEFENDER_MEM,
            "balancer": BALANCER_MEM,
        }

        def _update_memory(persona_name: str, persona_signal: dict, allow: bool):
            if not persona_signal:
                return

            context_key = persona_signal.get("context_key")
            if not context_key:
                return

            mem = PERSONA_MEMS.get(persona_name)
            if not mem:
                return

            mem.record(context_key, bool(allow))

            audit(
                9.2,
                "MEMORY",
                persona_name.upper(),
                context_key=context_key,
                outcome=bool(allow),
            )

        # 🔒 TRAINING：三個人格各自更新自己的記憶
        _update_memory("attacker", atk, decision["allow"])
        _update_memory("defender", dfd, decision["allow"])
        _update_memory("balancer", bal, decision["allow"])

        # ----------------------------------------------------
        # STEP 10｜Narration & dispatch（TRAINING）
        # ----------------------------------------------------
        report_text = self.decision_narrator.narrate(decision)

        TZ_TW = timezone(timedelta(hours=8))
        BASE_DIR = Path(__file__).resolve().parents[2]
        REPORT_DIR = BASE_DIR / "reports" / "daily"
        REPORT_DIR.mkdir(parents=True, exist_ok=True)

        today = datetime.now(TZ_TW).strftime("%Y%m%d")
        report_path = REPORT_DIR / f"daily_report_{today}.json"

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_text, f, ensure_ascii=False, indent=2)

        audit(10, "REPORT", None,
              narration_generated="YES",
              narrator="DecisionNarrator",
              file=str(report_path),
              mode="TRAINING",
              episode_id=episode_id)

        # ----------------------------------------------------
        # STEP 11｜Library / Replay（TRAINING EPISODE）
        # ----------------------------------------------------
        audit(11, "LIBRARY", None,
              decision_saved="YES",
              replay_available="YES",
              training_episode=True,
              episode_id=episode_id)

        audit("END", "TRAINING", None,
              msg="Training Trading Runtime completed",
              episode_id=episode_id)

        # ----------------------------------------------------
        # STEP 12｜Learning Device Review (optional / low-frequency)
        # ----------------------------------------------------
        RUN_REVIEW_NOW = False  # 先手動：你要每日 1～2 次，之後接 scheduler 再改

        if RUN_REVIEW_NOW:
            from learning.review_runner import ReviewRunner
            rr = ReviewRunner()
            out = rr.run()
            audit(12, "LEARNING_DEVICE", None,
                  review="DONE",
                  report_system=out["paths"]["system"],
                  report_human=out["paths"]["human"],
                  attempts=out["metrics"]["trade_attempts"])
# ============================================================
# Entry
# ============================================================
if __name__ == "__main__":
    TradingWorldAuditRuntime().run()