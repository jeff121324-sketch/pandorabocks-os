from dataclasses import dataclass

@dataclass(frozen=True)
class DataEpoch:
    """
    Describe the semantic generation of market data.
    """
    name: str                 # e.g. live_15m_v2, legacy_csv_v1
    source: str               # live / csv / history
    timeframe_policy: str     # strict / derived / mixed
    trust_level: str          # full / degraded