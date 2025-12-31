# aisop/outputs/warm/file_output.py

import json
import os
from datetime import datetime
from outputs.base import BaseOutput


class FileOutput(BaseOutput):
    """
    Warm storage output.

    Rules:
    - No decision logic
    - No retry / fallback
    - No formatting
    - Write-only
    """

    def __init__(self, base_dir: str = "outputs/warm"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def emit(self, payload: dict):
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"decision_{ts}.json"

        path = os.path.join(self.base_dir, filename)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)