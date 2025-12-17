class PerceptionCore:

    def run_pipeline(self, adapter, raw, soft=False):
        raw = adapter.filter(raw) if hasattr(adapter, "filter") else raw
        if raw is None:
            return None

        raw = adapter.auto_fix(raw) if hasattr(adapter, "auto_fix") else raw
        if raw is None:
            return None

        raw = adapter.anti_poison(raw) if hasattr(adapter, "anti_poison") else raw
        if raw is None:
            return None

        raw = adapter.enrich(raw) if hasattr(adapter, "enrich") else raw
        if raw is None:
            return None

        event = adapter.make_event(raw)
        return event
