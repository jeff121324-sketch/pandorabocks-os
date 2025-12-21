"""
module_loader.py
負責載入各種 plugin / runtime 模組。
第一版先做「安全載入」，之後你要再加檔案監控、熱更新都可以接在這裡。
"""

import importlib
import traceback


class ModuleLoader:
    """
    ModuleLoader
    ------------
    負責：
    - 動態載入 module
    - 熱更新 module
    - 取得 plugin class
    - 靜態讀取 plugin 的制度宣告（capabilities）

    不負責：
    - plugin lifecycle
    - runtime attach
    - capability enforcement
    """

    def __init__(self):
        # 已載入的模組快取，避免重複 import
        self.loaded_modules = {}

    # =========================================================
    # Module Loading
    # =========================================================

    def load_module(self, module_path: str):
        """
        載入指定模組，例如：
        - "trading_core.trading_runtime"
        - "aisop_core.aisop_runtime"

        回傳：module 物件 或 None
        """
        try:
            if module_path in self.loaded_modules:
                return self.loaded_modules[module_path]

            module = importlib.import_module(module_path)
            self.loaded_modules[module_path] = module
            print(f"[ModuleLoader] ✅ Loaded module: {module_path}")
            return module

        except Exception:
            print(f"[ModuleLoader] ❌ Failed to load module: {module_path}")
            traceback.print_exc()
            return None

    def reload_module(self, module_path: str):
        """
        重新載入模組（簡單版本熱更新）。
        """
        try:
            if module_path not in self.loaded_modules:
                return self.load_module(module_path)

            module = importlib.reload(self.loaded_modules[module_path])
            self.loaded_modules[module_path] = module
            print(f"[ModuleLoader] ♻ Reloaded module: {module_path}")
            return module

        except Exception:
            print(f"[ModuleLoader] ❌ Failed to reload module: {module_path}")
            traceback.print_exc()
            return None

    # =========================================================
    # Class Loading
    # =========================================================

    def load_class(self, module_path: str, class_name: str):
        """
        只負責載入 class，本身不碰制度、不碰 capability。
        """
        module = self.load_module(module_path)
        if not module:
            return None

        cls = getattr(module, class_name, None)
        if not cls:
            print(
                f"[ModuleLoader] ❌ Class {class_name} not found in {module_path}"
            )
            return None

        return cls

    # =========================================================
    # Plugin Capability Inspection (v1.3)
    # =========================================================

    def inspect_plugin_capabilities(self, plugin_cls):
        """
        靜態讀取 plugin 的制度宣告（不 instantiate）。

        支援：
        - plugin_name
        - required_capabilities
        """

        plugin_name = getattr(
            plugin_cls,
            "plugin_name",
            plugin_cls.__name__,
        )

        caps = getattr(
            plugin_cls,
            "required_capabilities",
            [],
        )

        # === 制度級防呆（避免 set("EXTERNAL_TICK") 這種災難）===
        if isinstance(caps, (str, bytes)):
            raise TypeError(
                f"{plugin_name}.required_capabilities must be iterable, got str"
            )

        try:
            required_caps = list(caps)
        except TypeError as e:
            raise TypeError(
                f"{plugin_name}.required_capabilities must be iterable"
            ) from e

        return {
            "plugin_name": plugin_name,
            "required_capabilities": required_caps,
        }
