
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timedelta
import shutil
from typing import Optional
import shutil
import time

@dataclass
class RotatePolicy:
    max_mb: int = 256
    max_age_minutes: int = 0


@dataclass
class ArchivePolicy:
    keep_warm_days: int = 7


class LogRotator:
    def __init__(
        self,
        hot_file: Path,
        warm_dir: Path,
        cold_dir: Path,
        rotate_policy,
        archive_policy,
        writer=None,   # ★ 新增：EventLogWriter
        cooldown_sec: int = 10,   # ★ 新增
    ):
        self.hot_file = hot_file
        self.warm_dir = warm_dir
        self.cold_dir = cold_dir
        self.rotate_policy = rotate_policy
        self.archive_policy = archive_policy
        self.writer = writer

        self.cooldown_sec = cooldown_sec      # ★ 新增
        self._last_rotate_ts = 0.0             # ★ 新增

        self.warm_dir.mkdir(parents=True, exist_ok=True)
        self.cold_dir.mkdir(parents=True, exist_ok=True)

    def should_rotate(self) -> bool:
        if not self.hot_file.exists():
            return False

        size_mb = self.hot_file.stat().st_size / (1024 * 1024)
        if self.rotate_policy.max_mb > 0 and size_mb >= self.rotate_policy.max_mb:
            return True

        if self.rotate_policy.max_age_minutes and self.rotate_policy.max_age_minutes > 0:
            mtime = datetime.fromtimestamp(self.hot_file.stat().st_mtime)
            if datetime.now() - mtime >= timedelta(minutes=self.rotate_policy.max_age_minutes):
                return True

        return False

    def rotate_now(self) -> Path | None:
        now = time.time()

        # ★ 冷卻中，直接跳過
        if now - self._last_rotate_ts < self.cooldown_sec:
            return None
    
        if not self.hot_file.exists() or self.hot_file.stat().st_size == 0:
            return None

        # ★ 新增：Writer 正忙，直接跳過
        if self.writer and self.writer.is_busy():
            self._last_rotate_ts = now
            print("[LogRotator] ⏸ writer busy, skip rotate")
            return None

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        rotated = self.warm_dir / f"logs_{ts}.jsonl"

        try:
            shutil.copy2(self.hot_file, rotated)

            if self.writer:
                self.writer.truncate()
            else:
                with open(self.hot_file, "w", encoding="utf-8"):
                    pass

            print(f"[LogRotator] 🔁 rotated → {rotated}")
            return rotated

        except Exception as e:
            print(f"[LogRotator] ❌ error: {e}")
            return None


    def archive_warm_to_cold(self) -> int:
        if self.archive_policy.keep_warm_days <= 0:
            return 0

        cutoff = datetime.now() - timedelta(days=self.archive_policy.keep_warm_days)
        moved = 0

        for p in self.warm_dir.glob("logs_*.jsonl"):
            mtime = datetime.fromtimestamp(p.stat().st_mtime)
            if mtime < cutoff:
                target = self.cold_dir / p.name
                shutil.move(str(p), str(target))
                moved += 1

        return moved

    def tick(self) -> None:
        if self.should_rotate():
            rotated = self.rotate_now()
            if rotated is None:
                return  # ★ writer busy，直接跳過本輪
        self.archive_warm_to_cold()
