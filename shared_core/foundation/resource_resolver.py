# shared_core/foundation/resource_resolver.py

import os
import platform
from pathlib import Path


class ResourceResolver:
    """
    🌐 Pandora Resource Resolver v1.0
    全文明的「資源定位系統」：
    - 統一文件路徑
    - 跨作業系統
    - 跨磁碟
    - 自動建立資料夾
    """

    # ---- OS 層資訊 -------------------------------------------------

    OS_NAME = platform.system().lower()   # windows / linux / darwin

    @staticmethod
    def is_windows():
        return ResourceResolver.OS_NAME == "windows"

    @staticmethod
    def is_mac():
        return ResourceResolver.OS_NAME == "darwin"

    @staticmethod
    def is_linux():
        return ResourceResolver.OS_NAME == "linux"

    # ---- 核心方法 --------------------------------------------------

    @staticmethod
    def resolve(path: str | Path) -> Path:
        """
        將任意路徑（相對 / 絕對）轉為「絕對、標準化、安全」的 Path
        """
        p = Path(path).expanduser().resolve()
        return p

    @staticmethod
    def resolve_under(base: str | Path, *parts) -> Path:
        """
        用於：resolve(root, "logs", "daily", "2025-12-06.json")
        不管 base 是 C:\ 或 /Users/... 都可以運作
        """
        base_path = ResourceResolver.resolve(base)
        final = base_path.joinpath(*parts)
        return final

    @staticmethod
    def ensure_dir(path: str | Path) -> Path:
        """
        自動建立資料夾，避免 FileNotFoundError。
        """
        p = ResourceResolver.resolve(path)
        p.mkdir(parents=True, exist_ok=True)
        return p

    # ---- 常用資源定位 API -------------------------------------------

    ROOT = Path(__file__).resolve().parents[3]   # 指向 aisop/ 頂層專案根目錄

    @staticmethod
    def logs(*parts) -> Path:
        """
        取得 logs/ 下的任意路徑
        """
        path = ResourceResolver.resolve_under(ResourceResolver.ROOT, "logs", *parts)
        ResourceResolver.ensure_dir(path.parent)
        return path

    @staticmethod
    def cache(*parts) -> Path:
        """
        取得 cache/ 下的任意路徑
        """
        path = ResourceResolver.resolve_under(ResourceResolver.ROOT, "cache", *parts)
        ResourceResolver.ensure_dir(path.parent)
        return path

    @staticmethod
    def datasets(*parts) -> Path:
        """
        取得 datasets/ 下的檔案
        """
        path = ResourceResolver.resolve_under(ResourceResolver.ROOT, "datasets", *parts)
        ResourceResolver.ensure_dir(path.parent)
        return path

    @staticmethod
    def configs(*parts) -> Path:
        """
        configs/ 下的設定檔（例如 settings.json）
        """
        path = ResourceResolver.resolve_under(ResourceResolver.ROOT, "configs", *parts)
        ResourceResolver.ensure_dir(path.parent)
        return path

    @staticmethod
    def modules(*parts) -> Path:
        """
        mod/ 下的任何模組資料，例如 cache、模型檔、模板
        """
        path = ResourceResolver.resolve_under(ResourceResolver.ROOT, "mod", *parts)
        ResourceResolver.ensure_dir(path.parent)
        return path
