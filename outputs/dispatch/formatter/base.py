import json

def load_report(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
