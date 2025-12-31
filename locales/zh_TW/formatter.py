class ZhTWFormatter:
    """
    Traditional Chinese (Taiwan) formatter.

    Target:
    - Human decision makers
    - Reports / dashboards
    - Investor-facing summaries

    Principles:
    - Readable
    - Contextual
    - Slightly narrative, but not speculative
    """

    def format(self, decision: dict) -> dict:
        confidence = decision.get("confidence")

        confidence_text = (
            f"{confidence:.1%} 左右"
            if confidence is not None
            else "尚未計算"
        )

        return {
            "title": decision.get("title", ""),
            "summary": decision.get("summary", ""),
            "decision": decision.get("decision", ""),
            "confidence": confidence_text,
            "reasons": decision.get("reasons", []),
            "notes": decision.get(
                "notes",
                "本判斷係依據目前可取得之資訊所整理，"
                "不代表任何承諾、保證或未來結果之推定。"
            ),
        }