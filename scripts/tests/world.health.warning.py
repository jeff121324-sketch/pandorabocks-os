import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared_core.event_schema import PBEvent
from pandora_core.runtime_singleton import get_runtime


def main():
    # 取得「目前正在跑的」PandoraRuntime（唯一實例）
    rt = get_runtime()

    # 建立一個 world health warning 事件
    event = PBEvent(
        type="world.health.warning",
        payload={
            "reason": "manual_test",
            "interval": "15m",
        },
        source="manual-test",
        priority=2,
        tags=["health", "test"],
    )

    # 🔔 發送到 ZeroCopyEventBus（和 Live Provider 一樣）
    rt.fast_bus.publish(event)

    print("✅ world.health.warning sent")


if __name__ == "__main__":
    main()