from collections import OrderedDict

CANONICAL_ORDER = [
    "title",
    "summary",
    "decision",
    "confidence",
    "reasons",
    "notes",
]

def build_canonical(localized: dict) -> OrderedDict:
    output = OrderedDict()
    for key in CANONICAL_ORDER:
        output[key] = localized.get(key)
    return output
