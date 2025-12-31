# shared_core/foundation/file_utils.py
from pathlib import Path
import os
import tempfile

def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path

def read_text(path: Path, *, encoding="utf-8") -> str:
    return path.read_text(encoding=encoding)

def write_text(path: Path, content: str, *, encoding="utf-8") -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding=encoding)

def atomic_write(path: Path, content: str, *, encoding="utf-8") -> None:
    """
    Write file atomically to avoid partial writes.
    """
    ensure_dir(path.parent)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding=encoding,
        delete=False,
        dir=str(path.parent),
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)
