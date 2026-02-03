from library.library_writer import LibraryWriter
from library.decision_writer import DecisionLibraryWriter
from shared_core.event_schema import PBEvent

class DecisionPersistenceHandler:
    """
    Handle system.governance.decision.created
    → persist decision into Library
    """

    def __init__(self, library_root):
        library_writer = LibraryWriter(library_root)
        self.decision_writer = DecisionLibraryWriter(library_writer)

    def handle(self, event):
        if not isinstance(event, PBEvent):
            return  # 🔒 防禦，直接丟掉
    
        decision_dict = event.payload
        if not isinstance(decision_dict, dict):
            return
    
        # DecisionLibraryWriter 吃的是 Decision 物件 or dict
        self.decision_writer.write_from_dict(decision_dict)
