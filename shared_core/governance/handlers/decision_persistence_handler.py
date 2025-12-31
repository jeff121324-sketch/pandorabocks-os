from library.library_writer import LibraryWriter
from library.decision_writer import DecisionLibraryWriter


class DecisionPersistenceHandler:
    """
    Handle system.governance.decision.created
    → persist decision into Library
    """

    def __init__(self, library_root):
        library_writer = LibraryWriter(library_root)
        self.decision_writer = DecisionLibraryWriter(library_writer)

    def handle(self, event):
        decision_dict = event.payload["decision"]

        # DecisionLibraryWriter 吃的是 Decision 物件 or dict
        self.decision_writer.write_from_dict(decision_dict)
