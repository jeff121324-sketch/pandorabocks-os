# trading_core/state/world_trust_aggregator.py

from typing import Optional, Set, Tuple

from trading_core.state.world_health_state import (
    WorldHealthState,
    WorldHealthLevel,
)


class WorldTrustAggregator:
    """
    Aggregate probe signals into a single world health state.

    - No mutation of data
    - No side effects
    - No governance decision
    """

    def __init__(self):
        # 記住已知的裂痕（避免重複觸發）
        self._known_issues: Set[Tuple] = set()
        self._current_level: WorldHealthLevel = WorldHealthLevel.HEALTHY

    def ingest_probe_report(self, report) -> Optional[WorldHealthState]:
        """
        Ingest a ProbeReport and return a new WorldHealthState
        ONLY if it implies a meaningful health condition.

        Return None if no health signal should be emitted.
        """

        if (
            report.probe_name == "kline_alignment_probe"
            and report.status == "WARNING"
            and report.data_epoch
            and report.data_epoch.trust_level == "degraded"
        ):
            issue_key = (
                report.probe_name,
                report.symbol,
                report.interval,
                report.data_epoch.name,
                tuple(a.code for a in report.anomalies),
            )

            if issue_key in self._known_issues:
                return None

            self._known_issues.add(issue_key)

            # ⭐ 關鍵：只有從 HEALTHY → DEGRADED 才通知
            if self._current_level == WorldHealthLevel.HEALTHY:
                self._current_level = WorldHealthLevel.DEGRADED

                return WorldHealthState(
                    level=WorldHealthLevel.DEGRADED,
                    reasons=[
                        f"Alignment mismatch on {report.interval} "
                        f"(epoch={report.data_epoch.name})"
                    ],
                )

            # 已經是 DEGRADED，不再通知
            return None

