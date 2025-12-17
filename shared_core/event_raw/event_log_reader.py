import json
from datetime import datetime
from pathlib import Path

class EventLogReader:
    """
    EventLogReader — RAW EVENT 只讀讀取器
    ✔ 僅供 Audit / Replay 使用
    ✔ 不修改任何資料
    ✔ 不影響 EventLogWriter
    """

    def __init__(self, path):
        self.path = Path(path)

    def load(self, start, end):
        """
        讀取指定時間區間內的事件
        """
        events = []

        if not self.path.exists():
            return events

        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    ts_str = obj.get("timestamp")
                    if not ts_str:
                        continue

                    ts = datetime.fromisoformat(ts_str)
                    if start <= ts <= end:
                        events.append(obj)

                except Exception:
                    # audit 只讀，任何壞資料直接略過
                    continue

        return events
