"""
sanitizer.py
資料清洗器（Perception Layer 2）
負責：
- 過濾 None / NaN / 空資料
- 移除明顯異常
- 防止毒資料進入 PB-Lang
"""

class DataSanitizer:
    def sanitize(self, data):
        """最基本版本：確保資料不是 None 或空"""
        if data is None:
            return None

        # 空字串或空 dict 也要當錯誤處理
        if data == "" or data == {}:
            return None

        # 如果是 list 或 dict，看是否有內容
        if isinstance(data, (list, dict)) and len(data) == 0:
            return None

        return data
