class JaFormatter:
    """
    Japanese formatter.

    Target:
    - Internal review
    - Audit / compliance
    - Conservative organizational usage

    Principles:
    - Non-assertive tone
    - Avoid absolute claims
    - Responsibility-diffusing language
    """

    def format(self, decision: dict) -> dict:
        confidence = decision.get("confidence")

        confidence_text = (
            f"{confidence:.1%} 程度"
            if confidence is not None
            else "算出されていません"
        )

        return {
            "title": decision.get("title", ""),
            "summary": decision.get("summary", ""),
            "decision": decision.get("decision", ""),
            "confidence": confidence_text,
            "reasons": decision.get("reasons", []),
            "notes": decision.get(
                "notes",
                "本判断は現時点で利用可能な情報に基づくものであり、"
                "将来の結果を保証するものではありません。"
            ),
        }