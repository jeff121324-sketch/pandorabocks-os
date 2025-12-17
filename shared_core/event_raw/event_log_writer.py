# shared_core/log_utils/event_log_writer.py

import json
import threading
import time
from pathlib import Path
from typing import Any
from .weak_labeler import WeakLabeler
import time

class EventLogWriter:
    def __init__(
        self,
        filepath: str,
        buffer_size: int = 1000,
        flush_interval: float = 0.2,
        enable_weak_label: bool = True,
    ):
        self.filepath = Path(filepath)
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.enable_weak_label = enable_weak_label

        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        self.buffer = []
        self.lock = threading.Lock()

        self.labeler = WeakLabeler() if enable_weak_label else None

        self._last_busy_log_ts = 0.0
        self._busy_log_interval = 5.0

        self._stop = False
        self.thread = threading.Thread(
            target=self._background_flush_loop, daemon=True
        )
        self.thread.start()

        print(f"[EventLogWriter] 📘 初始化完成 → {self.filepath}")

    # -------------------------------------------------
    def write(self, event: Any):
        try:
            with self.lock:
                data = event.to_dict() if hasattr(event, "to_dict") else event

                if self.enable_weak_label and self.labeler:
                    data["_weak_label"] = self.labeler.label_event(data)

                self.buffer.append(json.dumps(data, ensure_ascii=False))

                if len(self.buffer) >= self.buffer_size:
                    self._flush_locked()

        except Exception as e:
            print("[EventLogWriter] ❌ write error:", e)

    # -------------------------------------------------
    def _background_flush_loop(self):
        last = time.time()
        while not self._stop:
            time.sleep(0.05)
            if time.time() - last >= self.flush_interval:
                with self.lock:
                    self._flush_locked()
                last = time.time()

    # -------------------------------------------------
    def _flush_locked(self):
        if not self.buffer:
            return

        try:
            # ⚠️ 每次 flush 才 open，避免長時間持有 handle
            with open(self.filepath, "a", encoding="utf-8") as f:
                for line in self.buffer:
                    f.write(line + "\n")

            self.buffer.clear()

        except PermissionError:
            # ✔ Windows rotate 同步安全處理（加上 log 節流）
            now = time.time()
            if now - self._last_busy_log_ts >= self._busy_log_interval:
                print("[EventLogWriter] ⚠ flush skipped (file busy)")
                self._last_busy_log_ts = now

        except Exception as e:
            print("[EventLogWriter] ❌ flush error:", e)

    # -------------------------------------------------
    def truncate(self):
        """給 LogRotator 呼叫：清空檔案但不 rename"""
        with self.lock:
            try:
                with open(self.filepath, "w", encoding="utf-8"):
                    pass
            except Exception as e:
                print("[EventLogWriter] ❌ truncate error:", e)

    # -------------------------------------------------
    def close(self):
        self._stop = True
        self.thread.join()
        with self.lock:
            self._flush_locked()
        print("[EventLogWriter] 📕 closed")
