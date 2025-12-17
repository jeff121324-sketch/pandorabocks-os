import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
    
from pathlib import Path
from library.library_reader import LibraryReader

# 1️⃣ 初始化
r = LibraryReader(Path("D:/aisop/library"))

# 2️⃣ 讀 stats（不掃 events）
stats = r.get_stats()
print("[STATS]", stats["summary"])

# 3️⃣ 迭代 5 筆事件（串流）
print("\n[ITER EVENTS]")
for ev in r.iter_events(type="market.kline", limit=5):
    print(
        ev.get("event_type"),
        ev.get("timestamp") or ev.get("ts") or ev.get("time")
    )

# 4️⃣ 抽樣 20 筆（按 day）
print("\n[SAMPLE]")
s = r.sample(n=20, by="day", seed=42)
print("sample size =", len(s))
print("sample keys =", list(s[0].keys()) if s else "EMPTY")
