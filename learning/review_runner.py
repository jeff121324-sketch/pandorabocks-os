# learning/review_runner.py
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import json
from typing import Dict, Any, List


class ReviewRunner:
    def __init__(
        self,
        attempts_dir: str | Path = "library/learning/attempts",
        reports_dir: str | Path = "reports/learning",
    ):
        self.attempts_dir = Path(attempts_dir)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def _today_attempts_path(self) -> Path:
        day = datetime.now(timezone.utc).strftime("%Y%m%d")
        return self.attempts_dir / f"attempts_{day}.jsonl"

    def load_today_attempts(self) -> List[Dict[str, Any]]:
        path = self._today_attempts_path()
        if not path.exists():
            return []
        rows = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows

    def build_metrics(self, attempts: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(attempts)
        allow = sum(1 for a in attempts if a.get("gate_result") == "ALLOW")
        block = total - allow
        executable = sum(1 for a in attempts if a.get("is_executable") is True)

        # persona counts + confidence tracking
        persona_stats = {}
        for a in attempts:
            personas = a.get("personas", {}) or {}
            for name, p in personas.items():
                if not isinstance(p, dict):
                    continue
                persona_stats.setdefault(name, {"count": 0, "conf_max": 0.0, "conf_avg": 0.0, "conf_list": []})
                c = p.get("confidence", 0.0) or 0.0
                persona_stats[name]["count"] += 1
                persona_stats[name]["conf_list"].append(float(c))

        for name, s in persona_stats.items():
            cl = s["conf_list"]
            s["conf_max"] = round(max(cl), 3) if cl else 0.0
            s["conf_avg"] = round(sum(cl) / len(cl), 3) if cl else 0.0
            del s["conf_list"]

        blocked_reasons = {}
        for a in attempts:
            if a.get("gate_result") != "ALLOW":
                r = a.get("gate_reason") or "unknown"
                blocked_reasons[r] = blocked_reasons.get(r, 0) + 1

        # list executable attempts (你要「哪幾次可執行＋信心」)
        executable_list = []
        for a in attempts:
            if a.get("is_executable") is True:
                executable_list.append({
                    "attempt_id": a.get("attempt_id"),
                    "proposed_action": a.get("proposed_action"),
                    "confidence": a.get("confidence"),
                    "regime": a.get("regime"),
                })

        return {
            "date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "trade_attempts": total,
            "gate_allowed": allow,
            "gate_blocked": block,
            "executable_trades": executable,
            "blocked_reasons": blocked_reasons,
            "persona_stats": persona_stats,
            "executable_attempts": executable_list,
        }

    def write_reports(self, metrics: Dict[str, Any]) -> Dict[str, str]:
        day = datetime.now(timezone.utc).strftime("%Y%m%d")
        # system report (JSON)
        sys_path = self.reports_dir / f"learning_report_system_{day}.json"
        with open(sys_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)

        # human report (simple markdown)
        md_path = self.reports_dir / f"learning_report_human_{day}.md"
        lines = []
        lines.append(f"# Learning Report ({metrics['date_utc']})")
        lines.append("")
        lines.append(f"- Attempts: **{metrics['trade_attempts']}**")
        lines.append(f"- Gate Allowed: **{metrics['gate_allowed']}**")
        lines.append(f"- Gate Blocked: **{metrics['gate_blocked']}**")
        lines.append(f"- Executable (would trade if live): **{metrics['executable_trades']}**")
        lines.append("")
        lines.append("## Block Reasons")
        for k, v in sorted(metrics["blocked_reasons"].items(), key=lambda x: -x[1]):
            lines.append(f"- {k}: {v}")
        lines.append("")
        lines.append("## Persona Stats")
        for name, s in metrics["persona_stats"].items():
            lines.append(f"- {name}: count={s['count']} conf_avg={s['conf_avg']} conf_max={s['conf_max']}")
        lines.append("")
        lines.append("## Executable Attempts")
        for a in metrics["executable_attempts"]:
            lines.append(f"- attempt_id={a['attempt_id']} action={a['proposed_action']} conf={a['confidence']} regime={a['regime']}")
        md_path.write_text("\n".join(lines), encoding="utf-8")

        return {"system": str(sys_path), "human": str(md_path)}

    def run(self) -> Dict[str, Any]:
        attempts = self.load_today_attempts()
        metrics = self.build_metrics(attempts)
        paths = self.write_reports(metrics)

        # ------------------------------------------------
        # Persona Trust Snapshot (Learning → Bias, read-only)
        # ------------------------------------------------
        from learning.trust_builder import PersonaTrustBuilder

        day = datetime.now(timezone.utc).strftime("%Y%m%d")

        builder = PersonaTrustBuilder()
        trust_snapshot = builder.build(metrics)

        snapshot_path = self.reports_dir / f"persona_trust_snapshot_{day}.json"
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    name: {
                        "trust": p.trust,
                        "evidence": p.evidence
                    }
                    for name, p in trust_snapshot.personas.items()
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        # ------------------------------------------------
        # return everything
        # ------------------------------------------------
        return {
            "metrics": metrics,
            "paths": paths,
            "trust_snapshot": str(snapshot_path),
        }
