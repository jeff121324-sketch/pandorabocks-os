# trading_core/test_runtime/trading_world_audit_runtime.py

import sys
from pathlib import Path
from datetime import datetime, timezone
import logging

# ============================================================
# 專案根目錄
# ============================================================
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ============================================================
# Logging（全流程可 grep / 可審計）
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s"
)

def audit_log(step, layer, message, **data):
    extra = " ".join(f"{k}={v}" for k, v in data.items())
    logging.info(f"[AUDIT][STEP-{step}][{layer}] {message} {extra}")

# ============================================================
# STEP 1｜資料層：最新 K 線（事實）
# ============================================================
from trading_core.data.raw_loader import load_latest_kline

# ============================================================
# STEP 2｜計算層：Indicator Snapshot
# ============================================================
from trading_core.analysis.indicators.indicator_snaps_hot import (
    build_indicator_snapshot
)

# ============================================================
# STEP 3｜Persona
# ============================================================
from trading_core.personas.trade_attacker_calculator import TradeAttackerSentinel
from trading_core.personas.trade_defender_calculator import TradeDefenderSentinel
from trading_core.personas.trade_balancer_calculator import TradeBalancerSentinel

# ============================================================
# STEP 4｜Decision Gate（治理）
# ============================================================
from trading_core.decision_gate import TradingDecisionGate

# ============================================================
# STEP 7｜Report / Dispatch（既有系統）
# ============================================================
from outputs.narrators.decision_narrator import DecisionNarrator
from outputs.dispatch.report_sender import send_daily_report


# ============================================================
# Test Module
# ============================================================
class TradingWorldAuditRuntime:

    def run(self):
        audit_log(0, "TEST", "Trading World Snapshot Test started",
                  ts=datetime.now(timezone.utc))

        # ----------------------------------------------------
        # STEP 1｜最新一根 K 線
        # ----------------------------------------------------
        audit_log(1, "DATA", "Loading latest kline from database")
        kline = load_latest_kline()

        if not kline:
            audit_log(1, "DATA", "No kline found, abort")
