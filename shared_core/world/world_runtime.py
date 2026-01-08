# shared_core/world/world_runtime.py

from shared_core.world.world_context import WorldContext
from shared_core.world.world_state import WorldState


class WorldRuntime:
    """
    WorldRuntime v1
    世界在執行期的實體
    """

    def __init__(self, context: WorldContext, event_writer):
        self.context = context

        # 世界的「記憶器官」
        self.state = WorldState(
            world_id=context.world_id,
            writer=event_writer,
        )
