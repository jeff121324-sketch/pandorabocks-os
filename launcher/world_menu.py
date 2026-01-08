from pathlib import Path

def list_worlds(world_dir="worlds"):
    paths = sorted(Path(world_dir).glob("*.yaml"))
    return paths

def choose_world():
    worlds = list_worlds()
    if not worlds:
        print("❌ No worlds found")
        return None

    print("\n=== Available Worlds ===")
    for i, w in enumerate(worlds):
        print(f"[{i}] {w.name}")

    idx = input("Select world: ")
    try:
        return worlds[int(idx)]
    except:
        print("❌ Invalid selection")
        return None
