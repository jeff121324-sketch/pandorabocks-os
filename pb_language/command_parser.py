# pb_language/command_parser.py

from typing import Optional
from pb_language.schema import PBSemanticFeatures


class PBLangCommandParser:
    """
    PB-Lang Command Parser v1
    -------------------------
    將文字 + 語意轉為「結構化指令」
    """

    # === 簡易指令表（v1，可之後改成 rule / model）===
    COMMAND_PATTERNS = [
        # 系統級
        ("shutdown", ["shutdown", "關機", "/shutdown"], "system.shutdown"),
        ("pause", ["pause", "暫停", "stop trading"], "trading.pause"),
        ("resume", ["resume", "繼續", "start trading"], "trading.resume"),

        # AISOP / 飯店
        ("checkout", ["check out", "退房", "關帳"], "hotel.checkout.start"),
        ("frontdesk_close", ["關櫃台", "close frontdesk"], "hotel.frontdesk.close"),
    ]

    @staticmethod
    def parse(text: str, semantics: PBSemanticFeatures) -> Optional[str]:
        """
        回傳 command string，若不是指令則回 None
        """
        low = text.lower()

        # 1️⃣ 明確 intent 為 command 時優先處理
        if semantics.get("intent") == "command":
            for _, keywords, command in PBLangCommandParser.COMMAND_PATTERNS:
                if any(k in low for k in keywords):
                    return command

        # 2️⃣ 非 command intent，但仍可能是隱含指令
        for _, keywords, command in PBLangCommandParser.COMMAND_PATTERNS:
            if any(k in low for k in keywords):
                return command

        return None
