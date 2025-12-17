"""
error_manager.py
集中管理錯誤處理邏輯，之後可以：
- 寫入 logs
- 發 LINE / Discord 通知
- 觸發健康檢查
"""

import traceback


class ErrorManager:
    def __init__(self):
        self.handlers = []

    def register_handler(self, handler):
        """
        handler 必須是一個函式，簽名為 handler(exc: Exception)
        你可以在外面註冊：
        - 寫檔 log
        - 發通知
        """
        self.handlers.append(handler)

    def handle(self, exc: Exception):
        """被呼叫時，統一處理一個 Exception"""
        print("[ErrorManager] ❌ Exception caught:", exc)
        traceback.print_exc()

        for h in self.handlers:
            try:
                h(exc)
            except Exception as e:
                print("[ErrorManager] handler error:", e)

    #
