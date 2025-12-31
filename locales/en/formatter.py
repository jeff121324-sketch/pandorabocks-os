class EnFormatter:
    """
    English formatter.

    Target:
    - Logs
    - API responses
    - Data pipelines
    - Engineering / research usage

    Principles:
    - Stable keys
    - Machine-friendly
    - No narrative, no emotion
    """

    def format(self, decision: dict) -> dict:
        confidence = decision.get("confidence")

        confidence_text = (
            f"{confidence:.1%} approximately"
            if confidence is not None
            else "Not available"
        )

        return {
            "title": decision.get("title", ""),
            "summary": decision.get("summary", ""),
            "decision": decision.get("decision", ""),
            "confidence": confidence_text,
            "reasons": decision.get("reasons", []),
            "notes": decision.get(
                "notes",
                "This assessment is based on information available at the time "
                "and does not constitute any guarantee or assurance of future outcomes."
            ),
        }