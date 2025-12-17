"""
module_loader.py
負責載入各種 plugin / runtime 模組。
第一版先做「安全載入」，之後你要再加檔案監控、熱更新都可以接在這裡。
"""

import importlib
import traceback


class ModuleLoader:
    def __init__(self):
        # 記錄已載入模組，避免重複
        self.loaded_modules = {}

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
        之後你可以接檔案監控，改檔就 reload。
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
