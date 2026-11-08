# Concept map: demo.py

**Author:** Prithvi Sunilkumar
**Team:** 404NotFound
**Milestone:** M1 Domain Model
**File:** `demo.py` (185 lines; interactive mode on lines 126-159 and the mode menu on lines 162-182 by Ayush Jain)
**AI assistance:** Claude helped draft `demo.py` and this concept map. I reviewed and ran all of it and can explain every line.

`demo.py` runs the whole M1 story with one command, `python demo.py`. It builds two different boards from the same `Board` class, uses them normally, shows two operations being rejected with our own exceptions, then saves both boards to JSON and loads them back.

Line numbers match the version of `demo.py` submitted with M1.

---

## Summary table

| Concept | Where (file: lines) | Why it is needed here |
|---|---|---|
| R1 · Data classes as configuration | demo.py: 34-41, 56-62 | Members and columns are created as frozen `User` and `WorkflowStage` dataclasses and handed to the board, so each board is configured with plain facts. |
| R3 · One owner class, many board types | demo.py: 30-49, 52-73 | The chores board and the referral board are both plain `Board` objects with different members, columns and items. This shows Giraffe is configurable instead of hard-coding one workflow. |
| R4 · Every change goes through Board | demo.py: 81-85, 99-103 | Every claim, move and comment calls a Board method that checks the rules first. The demo never touches an item's owner or column directly. |
| R6 · Rejected operation 1: double claim | demo.py: 88-93 | Claiming an item that already has an owner raises `AlreadyClaimedError`. The demo catches it by name, prints why, and prints the owner to show nothing changed. |
| R6 · Rejected operation 2: full column | demo.py: 106-111 | "Accepted" has a limit of 2 (line 60) because the company gives two referral slots. Moving a third request in raises `StageFullError`, and the demo prints the item's column to show it stayed put. |
| R5 · Save and load round trip | demo.py: 114-119 | Each board is saved with `board.save()` and rebuilt with `load_board()`. `loaded == original` uses `Board.__eq__` to prove nothing was lost, including column order and item history. |
| R2 · Polymorphism, no type checks | demo.py: 121-123 | The same `item.describe()` call prints every loaded item. The loop never checks whether it has a `Chore` or a `ReferralRequest`. |
| R6 · Interactive mode (Ayush) | demo.py: 126-159 | Lets the user claim, move and comment on either sample board. `except GiraffeError` (line 158) catches every custom error through the shared base class, so any broken rule is printed as "Rejected" and the user can keep trying. |
| R6 · Runnable from the README | demo.py: 162-185 | `python demo.py` opens a mode menu: 1 for interactive, 2 for the prepared story. `EOFError` and Ctrl+C exit cleanly, and the main guard means it only runs when started directly, not when imported. |

---

## Each concept in detail

### 1. Two boards from one class (lines 30-73)

```python
board = Board("Amazon SDE Intern Referrals")
for stage in [WorkflowStage("Requested"), WorkflowStage("Accepted", limit=2),
              WorkflowStage("Submitted")]:
    board.add_stage(stage)
```

Giraffe is meant to work for sprints, chores and referrals. Column order is the order they are added, which is the workflow left to right.

### 2. Rejected operation 1: double claim (lines 88-93)

```python
try:
    chores.claim("c1", "ayush")  # c1 already belongs to prithvi
except AlreadyClaimedError as e:
    print("Rejected:", e)
print("c1 owner is still:", chores.get_item("c1").owner)
```

Output:

```
Rejected: Item 'c1' already belongs to 'prithvi'
c1 owner is still: prithvi
```

We catch the specific error, not a bare `Exception`, so a real bug wouldn't be hidden. The second line shows the rule from lecture: raise before changing anything.

### 3. Rejected operation 2: full column (lines 106-111)

```
Rejected: Stage 'Accepted' has reached its limit
r3 is still in: Requested
```

Ana and Ben fill both slots. Eli's request is claimed by a referrer, but it can't move into "Accepted" until a slot opens.

### 4. Save and load (lines 114-123)

```
chores_board.json: loaded == original -> True
   [Chore] Take out trash (due 2026-11-09) | In Progress | prithvi
   ...
referral_board.json: loaded == original -> True
   [Referral] Ana -> Amazon | Accepted | referrer: ayush
   ...
```

Loaded items print as the right class because each item's `"kind"` was saved, and `load_board()` rebuilt the board through the same rule-checking methods.

---

## Which files demo.py uses

| File | What demo.py uses |
|---|---|
| `board.py` (Ayush, Prithvi) | `Board`, `add_user`, `add_stage`, `add_item`, `claim`, `move`, `add_comment`, `describe`, `get_item`, `items`, `save`, `load_board`, `==` |
| `items.py` (Bhuvana) | `User`, `WorkflowStage`, `Chore`, `ReferralRequest`, `describe()` |
| `errors.py` (Ayush) | `AlreadyClaimedError`, `StageFullError`, `GiraffeError` (interactive mode) |

Nothing imports `demo.py`. It is the entry point.

---

## Check-in talking points

1. **Why two boards?** To show one `Board` class handles different workflows just by changing members, columns and limits.
2. **Why catch the specific exception?** Its name says why the operation failed. Catching a bare `Exception` could hide a real bug.
3. **How do we know nothing changed after a rejection?** The demo prints the owner and column right after each rejection.
4. **Why print `loaded == original`?** It proves save and load lose nothing. `Board.__eq__` compares members, column order and every item, including history.
5. **Where is the polymorphism?** The final loop calls `describe()` on every item without checking its type.
