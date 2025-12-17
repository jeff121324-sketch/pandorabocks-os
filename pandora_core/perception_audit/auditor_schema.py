AUDIT_SCHEMA = {
    "audit_window": {
        "start": "ISO8601",
        "end": "ISO8601"
    },
    "schema_check": {
        "status": ["PASS", "FAIL"],
        "violations": []
    },
    "poison_filter": {
        "expected_hits": "int",
        "actual_hits": "int",
        "anomalies": []
    },
    "leak_check": {
        "suspected_poison_events": "int",
        "event_ids": []
    },
    "overall_status": ["PASS", "WARN"],
    "confidence": "float"
}
