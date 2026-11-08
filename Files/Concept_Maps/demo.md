# Concept map: demo.py

**Author:** Prithvi Sunilkumar
**Team:** 404NotFound
**Milestone:** M1 Domain Model
**File:** `demo.py` (127 lines)
**AI assistance:** I used Claude to help draft `demo.py` and this concept map. I reviewed and ran all of it and can explain every line.

`demo.py` runs the whole M1 story with one command, `python demo.py`. It builds two different boards from the same `Board` class, uses them normally, shows two actions being rejected with our own exceptions, then saves both boards to JSON and loads them back.

Line numbers match the version of `demo.py` submitted with M1.

---

## Summary table

| Concept | File: lines | Why it is needed here |
|---|---|---|
| One class, many board types | demo.py: 30-49, 52-73 | The chores board and the referral board are both plain `Board` objects with different users, stages and items. This shows Giraffe is configurable instead of hard-coding one workflow. |
| Dataclasses as configuration | demo.py: 34-41, 56-62 | Users and stages are created as frozen `User` and `WorkflowStage` dataclasses and handed to the board. |
| Stage limit as a rule | demo.py: 60 | "Accepted" has `limit=2` because the company gives two referral slots. Board enforces this, not the demo. |
| Changes go through Board's methods | demo.py: 81-85, 99-103 | Every claim, move and comment goes through a Board method that checks the rules first. The demo never touches an item's owner or stage directly. |
| Custom exception caught and printed: double claim | demo.py: 88-93 | Claiming an item that already has an owner raises `AlreadyClaimedError`. The demo catches it by name, prints why, and shows the owner didn't change. |
| Custom exception caught and printed: full stage | demo.py: 106-111 | Moving a third request into a 2-slot "Accepted" stage raises `StageFullError`. The demo shows the item stayed where it was, proving Board raises before it changes anything. |
| JSON save and load | demo.py: 114-120 | Each board is saved with `board.save()` and rebuilt with `load_board()`. `loaded == original` uses `Board.__eq__` to prove nothing was lost, including stage order and item history. |
| Polymorphism | demo.py: 122-123 | The same `item.describe()` call prints every loaded item. The loop never checks whether an item is a `Chore` or a `ReferralRequest`. |
| Read-only snapshots | demo.py: 93, 111, 122 | `get_item()` and `items` return copies, so the demo can read state without being able to change the board. |
| Main guard | demo.py: 126-127 | The story only runs when the file is run directly, not when it is imported. |

---

## Each concept in detail

### 1. Two boards from one class (lines 30-73)

```python
board = Board("Amazon SDE Intern Referrals")
for stage in [WorkflowStage("Requested"), WorkflowStage("Accepted", limit=2),
              WorkflowStage("Submitted")]:
    board.add_stage(stage)
```

Giraffe is meant to work for sprints, chores and referrals. The demo proves that with two boards that share no code except `Board` itself. Stage order is the order we add them in, which is the workflow left to right.

### 2. Rejected action 1: double claim (lines 88-93)

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

We catch the specific `AlreadyClaimedError`, not a bare `Exception`, so a real bug wouldn't be hidden. The second line shows the rule from lecture: raise before changing anything.

### 3. Rejected action 2: full "Accepted" stage (lines 106-111)

```python
try:
    referrals.move("r3", "Accepted")  # both slots are taken
except StageFullError as e:
    print("Rejected:", e)
```

Output:

```
Rejected: Stage 'Accepted' has reached its limit
r3 is still in: Requested
```

Ana and Ben fill both slots. Eli's request is claimed by a referrer, but it can't move into "Accepted" until a slot opens.

### 4. Save and load (lines 114-123)

```python
original.save(path)
loaded = load_board(path)
print(f"{path}: loaded == original -> {loaded == original}")
for item in loaded.items:
    print("  ", item.describe())
```

Output:

```
chores_board.json: loaded == original -> True
   [Chore] Take out trash (due 2026-11-09) | In Progress | prithvi
   ...
referral_board.json: loaded == original -> True
   [Referral] Ana -> Amazon | Accepted | referrer: ayush
   ...
```

Each board gets its own file. `load_board()` rebuilds the board through `add_user`, `add_stage` and `add_item`, so loaded data is checked by the same rules. The printed items come back as the right class (chores print as chores, referrals as referrals) because each item's `"kind"` was saved.

---

## Which files demo.py uses

| File | What demo.py uses |
|---|---|
| `board.py` (Ayush, Prithvi) | `Board`, `add_user`, `add_stage`, `add_item`, `claim`, `move`, `add_comment`, `describe`, `get_item`, `items`, `save`, `load_board`, `__eq__` |
| `items.py` (Bhuvana) | `User`, `WorkflowStage`, `Chore`, `ReferralRequest`, `item.describe()` |
| `errors.py` (Ayush) | `AlreadyClaimedError`, `StageFullError` |

Nothing imports `demo.py`. It is the entry point.

---

## Check-in talking points

1. **Why two boards?** To show one `Board` class handles different workflows just by changing users, stages and limits.
2. **Why catch the specific exception?** Its name says why the action failed. Catching a bare `Exception` could hide a real bug.
3. **How do we know nothing changed after a rejection?** The demo prints the owner and stage right after each rejection.
4. **Why print `loaded == original`?** It is the proof that save and load lose nothing. `Board.__eq__` compares users, stage order and every item, including history.
5. **Where is the polymorphism?** The final loop calls `describe()` on every item without checking its type.
