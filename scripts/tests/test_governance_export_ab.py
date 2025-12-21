import sys
from pathlib import Path

# -------------------------------------------------
# Path bootstrap
# -------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared_core.governance.parliament.parliament_engine import ParliamentEngine
from shared_core.governance.parliament.parliament_schema import Proposal, Vote
from library.library_writer import LibraryWriter
from library.decision_writer import DecisionLibraryWriter
from shared_core.reports.decision_reporter import DecisionReporter


# -------------------------------------------------
# helpers
# -------------------------------------------------
def make_proposal(aid, pid):
    return Proposal(
        agenda_id=aid,
        proposal_id=pid,
        proposer_role="tester",
        action={"type": "noop"},
    )


def make_vote(aid, pid, role, stance):
    return Vote(
        agenda_id=aid,
        proposal_id=pid,
        role=role,
        stance=stance,
        confidence=1.0,
        rationale=f"{role} says {stance}",
    )


def run():
    # ==================================================
    # Init Governance
    # ==================================================
    engine = ParliamentEngine(
        rules_path="shared_core/governance/parliament/rules.yaml"
    )

    # ==================================================
    # Init A + B exporters
    # ==================================================
    library_root = Path("aisop/library")
    library_writer = LibraryWriter(library_root)
    decision_writer = DecisionLibraryWriter(library_writer)
    reporter = DecisionReporter()

    # ==================================================
    # Make a decision
    # ==================================================
    proposal = make_proposal("agenda-Z", "proposal-Z1")
    decision = engine.evaluate(
        proposal,
        [
            make_vote("agenda-Z", "proposal-Z1", "r1", "approve"),
            make_vote("agenda-Z", "proposal-Z1", "r2", "approve"),
        ],
    )

    print("\n[Test A+B - Governance Decision]")
    print(
        f"agenda={decision.agenda_id} "
        f"outcome={decision.outcome} "
        f"notes={decision.notes}"
    )

    # ==================================================
    # A: Decision → Library
    # ==================================================
    decision_writer.write(decision)
    print("\n[Test A - Decision written to Library]")

    # ==================================================
    # B: Decision → Report
    # ==================================================
    report_text = reporter.render(decision.to_dict())

    print("\n[Test B - Decision Report]")
    print(report_text)

    assert "Agenda: agenda-Z" in report_text
    assert "Outcome: APPROVED" in report_text

    print("\n✅ A+B EXPORT TEST PASSED")


if __name__ == "__main__":
    run()
