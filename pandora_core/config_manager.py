"""
config_manager.py
統一管理 config/ 底下的 YAML 設定檔
例如：
- pandora.yaml
- trading.yaml
- aisop.yaml
"""

import os
import yaml
from pathlib import Path


class ConfigManager:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.config_cache = {}

    def load(self, name: str):
        """
        name = "pandora" -> 載入 config/pandora.yaml
        回傳 dict
        """
        if name in self.config_cache:
            return self.config_cache[name]

        config_path = self.base_dir / "config" / f"{name}.yaml"
        if not config_path.exists():
            print(f"[ConfigManager] ⚠ Config not found: {config_path}")
            self.config_cache[name] = {}
            return {}

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                self.config_cache[name] = data
                print(f"[ConfigManager] ✅ Loaded config: {name}")
                return data
        except Exception as e:
            print(f"[ConfigManager] ❌ Failed to load config {name}:", e)
            return {}

    def reload(self, name: str):
        """重新讀取設定"""
        if name in self.config_cache:
            del self.config_cache[name]
        return self.load(name)
