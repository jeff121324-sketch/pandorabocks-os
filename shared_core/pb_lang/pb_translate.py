# shared_core/pb_lang/pb_translate.py

from shared_core.event_schema import PBEvent


class PBtranslate:
    """
    PB-Lang: Translation / Output Language
    用於：日報、英文版輸出、X 帳號貼文、LINE 帳號訊息
    """

    @staticmethod
    def text(content: str, lang: str = "zh-TW", target: str = None, source="translator"):
        payload = {
            "content": content,
            "lang": lang,
            "target": target,   # e.g. "daily_report" / "x_post"
        }
        return PBEvent(
            type="translate.text",
            payload=payload,
            source=source
        )

    @staticmethod
    def summary(content: str, lang: str = "zh-TW", target: str = None, source="translator"):
        payload = {
            "content": content,
            "lang": lang,
            "target": target
        }
        return PBEvent(
            type="translate.summary",
            payload=payload,
            source=source
        )
