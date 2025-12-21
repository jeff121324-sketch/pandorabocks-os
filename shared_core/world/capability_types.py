# shared_core/world/capability_types.py
from enum import Enum


class WorldCapability(str, Enum):
    """
    Canonical list of world-level capabilities.
    This defines WHAT can be requested, not HOW it is implemented.
    """
    HOTPLUG = "supports_hotplug"
    MULTI_RUNTIME = "supports_multi_runtime"
    EXTERNAL_TICK = "supports_external_tick"
