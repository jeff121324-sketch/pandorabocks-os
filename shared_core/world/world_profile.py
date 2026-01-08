# shared_core/world/world_profile.py

from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class WorldProfile:
    """
    World Profile v1
    世界憲法（Declarative Only）

    ⚠ 原則：
    - 不包含任何邏輯
    - 不檢查 capability
    - 不接觸 runtime
    """

    def __init__(self, raw: Dict[str, Any]):
        self.raw = raw

        # === Identity ===
        self.world_id: str = raw["world_id"]
        self.domain: str = raw.get("domain", "unknown")

        # === Mode ===
        self.mode: Dict[str, Any] = raw.get("mode", {})

        # === Market / Data（World Runtime 可能會用到）===
        self.market: Dict[str, Any] = raw.get("market", {})
        self.data: Dict[str, Any] = raw.get("data", {})

        # === Pipeline Control ===
        self.pipeline: Dict[str, Any] = raw.get("pipeline", {})

        # === Personality Declaration ===
        self.personality: Dict[str, Any] = raw.get("personality", {})

        # === Permission Declaration（會映射到 capability）===
        self.permission: Dict[str, Any] = raw.get("permission", {})

        # === Meta ===
        self.meta: Optional[Dict[str, Any]] = raw.get("meta")

    # -------------------------------------------------
    # Loader
    # -------------------------------------------------
    @classmethod
    def load(cls, path: Path) -> "WorldProfile":
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        return cls(raw)

    def __repr__(self) -> str:
        return f"<WorldProfile world_id={self.world_id}>"
