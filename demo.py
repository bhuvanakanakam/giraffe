"""
demo.py - Runs the Giraffe M1 story end to end.

Author:  Prithvi Sunilkumar
Team:    404NotFound (Ayush Jain, Bhuvana Kanakam, Prithvi Sunilkumar)
Course:  95-895 Python Systems Fundamentals, Fall 2026, Mini 2
Part of: M1 Domain Model

What this shows:
  - A chores board and a referral board built from the same Board class
  - Claiming, moving and commenting on items
  - Two rejected actions, each caught as a custom exception and printed
  - Saving both boards to JSON and loading them back unchanged

Run with: python demo.py   (Python 3.9+)

AI use: I used Claude to help draft this file. I reviewed and ran every
line and can explain all of it. Cited in the README.
"""

from board import Board, load_board
from errors import AlreadyClaimedError, StageFullError
from items import Chore, ReferralRequest, User, WorkflowStage


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def build_chores_board() -> Board:
    """Roommates share household chores. No stage has a limit."""
    board = Board("Apartment 4B Chores")

    for user in [User("ayush", "Ayush"), User("bhuvana", "Bhuvana"),
                 User("prithvi", "Prithvi")]:
        board.add_user(user)

    # Stage order is insertion order, so this is the workflow left to right.
    for stage in [WorkflowStage("Unclaimed"), WorkflowStage("In Progress"),
                  WorkflowStage("Done")]:
        board.add_stage(stage)

    board.add_item(Chore("c1", "Take out trash", due_date="2026-11-09",
                         stage="Unclaimed"))
    board.add_item(Chore("c2", "Clean kitchen", due_date="2026-11-10",
                         stage="Unclaimed"))
    board.add_item(Chore("c3", "Buy groceries", due_date="2026-11-11",
                         stage="Unclaimed"))
    return board


def build_referral_board() -> Board:
    """Referrers pick up applicants' requests. 'Accepted' has 2 slots."""
    board = Board("Amazon SDE Intern Referrals")

    for user in [User("ayush", "Ayush"), User("bhuvana", "Bhuvana")]:
        board.add_user(user)

    # The company gives 2 referral slots, so "Accepted" is limited to 2.
    for stage in [WorkflowStage("Requested"), WorkflowStage("Accepted", limit=2),
                  WorkflowStage("Submitted")]:
        board.add_stage(stage)

    board.add_item(ReferralRequest("r1", "SDE intern referral",
                                   company="Amazon", applicant="Ana",
                                   stage="Requested"))
    board.add_item(ReferralRequest("r2", "SDE intern referral",
                                   company="Amazon", applicant="Ben",
                                   stage="Requested"))
    board.add_item(ReferralRequest("r3", "SDE intern referral",
                                   company="Amazon", applicant="Eli",
                                   stage="Requested"))
    return board


def main() -> None:
    # --- Chores board: normal use, then a double claim ---------------------
    chores = build_chores_board()

    section("Chores board: claim, move, comment")
    chores.claim("c1", "prithvi")
    chores.move("c1", "In Progress")
    chores.claim("c2", "bhuvana")
    chores.move("c2", "Done")
    chores.add_comment("c1", "Bins go out before 8 AM")
    print(chores.describe())

    section("Rejected action 1: double claim")
    try:
        chores.claim("c1", "ayush")  # c1 already belongs to prithvi
    except AlreadyClaimedError as e:
        print("Rejected:", e)
    print("c1 owner is still:", chores.get_item("c1").owner)

    # --- Referral board: fill "Accepted", then try one more ----------------
    referrals = build_referral_board()

    section("Referral board: referrers accept requests")
    referrals.claim("r1", "ayush")
    referrals.move("r1", "Accepted")
    referrals.claim("r2", "bhuvana")
    referrals.move("r2", "Accepted")
    referrals.claim("r3", "ayush")
    print(referrals.describe())

    section("Rejected action 2: move into a full stage")
    try:
        referrals.move("r3", "Accepted")  # both slots are taken
    except StageFullError as e:
        print("Rejected:", e)
    print("r3 is still in:", referrals.get_item("r3").stage)

    # --- Save and load ------------------------------------------------------
    section("Save to JSON and load back")
    for original, path in [(chores, "chores_board.json"),
                           (referrals, "referral_board.json")]:
        original.save(path)
        loaded = load_board(path)
        print(f"{path}: loaded == original -> {loaded == original}")

        # Same describe() call on every item; each kind prints itself.
        for item in loaded.items:
            print("  ", item.describe())


if __name__ == "__main__":
    main()
