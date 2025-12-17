
# shared_core/security/blacklist.py

from pathlib import Path

# base dir: shared_core/security/
BASE_DIR = Path(__file__).resolve().parent
SYMBOL_FILE = BASE_DIR / "symbols.txt"


def _load_symbols() -> set[str]:
    if not SYMBOL_FILE.exists():
        return set()
    symbols = set()
    with SYMBOL_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            symbols.add(line.upper())
    return symbols


_SYMBOL_BLACKLIST = None


def get_symbol_blacklist() -> set[str]:
    global _SYMBOL_BLACKLIST
    if _SYMBOL_BLACKLIST is None:
        _SYMBOL_BLACKLIST = _load_symbols()
    return _SYMBOL_BLACKLIST


def is_symbol_blocked(symbol: str) -> bool:
    if not symbol:
        return False
    return symbol.upper() in get_symbol_blacklist()
