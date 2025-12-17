"""
health_check.py
提供簡單的健康檢查框架，之後可以掛：
- 交易資料來源是否正常
- 事件匯流排是否有活動
- RewardHub / Redis / DB 是否在線
"""

from typing import Callable, Dict, Any


class HealthCheckRegistry:
    """
    註冊多個健康檢查項目，並一次跑完。
    """

    def __init__(self):
        self.checks: Dict[str, Callable[[], Any]] = {}

    def register(self, name: str, func: Callable[[], Any]):
        """
        func 不接受參數，回傳：
        - True / False
        - 或 dict（包含更多資訊）
        """
        self.checks[name] = func

    def run_all(self):
        """
        回傳一個 dict：
        {
          "check_name": {"ok": True/False, "detail": ...}
        }
        """
        results = {}
        for name, func in self.checks.items():
            try:
                res = func()
                if isinstance(res, bool):
                    results[name] = {"ok": res, "detail": None}
                else:
                    results[name] = {"ok": True, "detail": res}
            except Exception as e:
                results[name] = {"ok": False, "detail": str(e)}
        return results
