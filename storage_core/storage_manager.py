from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os

import yaml


@dataclass(frozen=True)
class StoragePaths:
    hot_dir: Path
    warm_dir: Path
    cold_dir: Path


class StorageManager:
    """
    跨平台儲存分層管理：
    HOT  : 即時寫入（event_raw）
    WARM : 近期回放/分析
    COLD : 長期封存
    """

    def __init__(self, config_path: str | Path = "config/storage.yaml"):
        self.config_path = Path(config_path)
        self._cfg = self._load_config(self.config_path)

        root = Path.cwd()

        hot = self._resolve_path(self._cfg["storage"]["hot_dir"], root)
        warm = self._resolve_path(self._cfg["storage"]["warm_dir"], root)
        cold = self._resolve_path(self._cfg["storage"]["cold_dir"], root)

        hot.mkdir(parents=True, exist_ok=True)
        warm.mkdir(parents=True, exist_ok=True)
        cold.mkdir(parents=True, exist_ok=True)

        self.paths = StoragePaths(hot_dir=hot, warm_dir=warm, cold_dir=cold)

    def _load_config(self, p: Path) -> dict:
        if not p.exists():
            raise FileNotFoundError(f"storage config not found: {p.resolve()}")
        with p.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _resolve_path(self, raw: str, root: Path) -> Path:
        raw = os.path.expandvars(raw)
        p = Path(raw)
        return p if p.is_absolute() else (root / p).resolve()

    def hot(self) -> Path:
        return self.paths.hot_dir

    def warm(self) -> Path:
        return self.paths.warm_dir

    def cold(self) -> Path:
        return self.paths.cold_dir

    def event_raw_path(self, filename: str) -> Path:
        return self.hot() / filename

    def config(self) -> dict:
        return self._cfg
