import sys
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storage_core.storage_manager import StorageManager
from storage_core.log_rotator import LogRotator, RotatePolicy, ArchivePolicy


def rotate_named(hot_file: Path, warm_dir: Path, name: str):
    """
    壓力測試專用：
    直接從 HOT 複製出一份固定命名的 WARM 檔
    """
    warm_dir.mkdir(parents=True, exist_ok=True)
    target = warm_dir / f"{name}.jsonl"
    shutil.copy(hot_file, target)
    print(f"[Rotate] WARM file created: {target}")


def main():
    sm = StorageManager("config/storage.yaml")
    cfg = sm.config()

    hot_file = sm.event_raw_path(cfg["event_raw"]["filename"])
    rotate_cfg = cfg["event_raw"]["rotate"]
    archive_cfg = cfg["event_raw"]["archive"]

    rotator = LogRotator(
        hot_file=hot_file,
        warm_dir=sm.warm(),
        cold_dir=sm.cold(),
        rotate_policy=RotatePolicy(
            max_mb=int(rotate_cfg.get("max_mb", 256)),
            max_age_minutes=int(rotate_cfg.get("max_age_minutes", 0)),
        ),
        archive_policy=ArchivePolicy(
            keep_warm_days=int(archive_cfg.get("keep_warm_days", 7)),
        ),
    )

    print("[Rotate] HOT file :", hot_file)
    print("[Rotate] WARM dir :", sm.warm())
    print("[Rotate] COLD dir :", sm.cold())

    # === 正式輪轉（原本行為，完全保留）===
    rotator.tick()

    # === 壓力測試模式（只在指定時啟用）===
    if "--stress-dual" in sys.argv:
        rotate_named(hot_file, sm.warm(), "warm_A")
        rotate_named(hot_file, sm.warm(), "warm_B")

    print("[Rotate] done")


if __name__ == "__main__":
    main()
