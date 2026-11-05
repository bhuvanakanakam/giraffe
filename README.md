# Giraffe: One Board for Every Workflow

Giraffe is a shared, customizable board system built in Python for 95-895 Python Systems Fundamentals (Carnegie Mellon University, Fall 2026). Groups create boards with their own workflow stages, add items, claim owners, and track progress together. The same board engine supports many uses, such as software sprints, referral openings, and shared household chores.

The core guarantee: **each item has at most one owner at a time, and no stage ever goes over its limit** (for example, a referral opening never accepts more requests than its slot count), even when many people update the board at once.

## Project status

| Milestone | Focus | Due | Status |
|---|---|---|---|
| M0 | Proposal | Oct 30 | Done |
| M1 | Domain model: classes, ABCs, exceptions, JSON persistence | Nov 8 | In progress |
| M2 | Networked: TCP server and client | Nov 22 | Not started |
| M3 | Concurrent: threaded server, locking, load test | Dec 2 | Not started |

## Example uses

| Board | Stages | Limit example |
|---|---|---|
| Software sprint | To Do, In Progress, Done | In Progress holds at most 3 tasks |
| Referral opening | Requested, Accepted, Referred, Offer | Accepted holds at most the number of referral slots |
| Roommate chores | Unclaimed, Claimed, Done | Each chore has one owner |

## Project structure

```
giraffe/
  errors.py      custom exceptions
  items.py       BoardItem abstract base class, Task, Chore, ReferralRequest, data classes
  board.py       Board class, rule checks, save and load
  demo.py        runs an example story end to end
  README.md
  board.json     created when demo.py runs
```

## How to run

Requires Python 3.10 or later. No external packages.

```bash
cd giraffe
python demo.py
```

No terminal? In Google Colab, upload the files and run `!python demo.py`.

The demo builds a chores board and a referral board, claims and moves items, shows rejected actions (a double claim and a full stage), saves the boards to `board.json`, loads them back, and prints the result.

## Design overview

- **Board** owns its stages, members, and items. Every change goes through a Board method that checks the rules first and raises a custom exception if the action is invalid, before changing anything.
- **BoardItem** is an abstract base class. `Task`, `Chore`, and `ReferralRequest` each implement their own `validate()` and `describe()`, so the board works with any item kind without checking its type.
- **WorkflowStage** and **User** are data classes for plain facts.
- **GiraffeError** is the base exception, with `ItemNotFoundError`, `AlreadyOwnedError`, `StageFullError`, `NotAMemberError`, and `InvalidStageError`.
- Boards are saved to JSON with each item's kind, and loaded back through Board's own methods.

## Concept map

Line numbers are filled in after the final merge.

| Concept | File: lines | Why we used it here |
|---|---|---|
| Classes (3+) | | |
| Data class | | |
| Composition | | |
| Encapsulated state change | | |
| Invariant check: one owner | | |
| Invariant check: stage limit | | |
| Custom exceptions | | |
| Raise before change | | |
| Abstract base class | | |
| Polymorphism | | |
| Inheritance (exceptions) | | |
| JSON save | | |
| JSON load | | |
| Rejected operation in demo | | |

## Team: 404NotFound

| Member | Andrew ID | Built |
|---|---|---|
| Ayush Jain | ayushj3 | errors.py, board.py: Board class and rule-checking methods |
| Bhuvana Kanakam | bkanakam | items.py: BoardItem ABC, Task, Chore, ReferralRequest, data classes, item_from_dict |
| Prithvi Sunilkumar | psunilku | board.py: save and load, demo.py, README |

## AI use

Per the course AI policy, we cite AI assistance here. Brainstorming, project scoping, and the README structure were developed with help from Claude. All code is written by the team members listed above.