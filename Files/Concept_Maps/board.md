# Concept map: board.py

**Authors:** Ayush Jain (ayushjain_01): board rules, lines 1-281. Prithvi Sunilkumar: persistence, lines 283-362.
**Team:** 404NotFound
**Milestone:** M1 Domain Model
**File:** `board.py` (362 lines)
**AI assistance:** Board rules: no AI in the code; ChatGPT helped prepare this map. Persistence: Claude helped draft `save()`, `load_board()` and their map rows. Claude helped align the format with the other maps. Both authors reviewed and can explain every line.

`Board` is the class that owns everything on one board: its members, its columns (stages) and its items. Every change goes through a Board method that checks the rules first. In M2 this object becomes the server's shared state.

Line numbers match the version of `board.py` submitted with M1.

---

## Summary table

| Concept | Where (file: lines) | Why it is needed here |
|---|---|---|
| R1 · Class for the domain's owner | board.py: 25-281 | A board has rules that involve many objects at once (is this column full? is this user a member?), so it is a regular class with methods, not a dataclass. |
| R2 · Polymorphism, no type checks | board.py: 101, 216, 298 | Board calls `item.validate()`, `item.describe()` and `item.to_dict()` on any item. It never asks whether it holds a Task, Chore or ReferralRequest, so a new kind of item needs no change here. |
| R3 · Composition | board.py: 30-36 | Board owns three collections: members (`_users`), columns (`_stages`) and items (`_items`). It is the single owner of the state that M2 moves onto the server and M3 protects with a lock. |
| R4 · Invariant: one owner per item | board.py: 132-151 | `claim()` checks the item exists, the user is a member, and the item is unclaimed (line 146) before it calls `set_owner()` (line 151). A second claim raises `AlreadyClaimedError` and changes nothing. |
| R4 · Invariant: column limits | board.py: 118-127, 153-182 | `add_item()` and `move()` count the items already in the target column and raise `StageFullError` before anything changes. This is what keeps the 2-slot "Accepted" column at 2. |
| R4 · Validated setup | board.py: 61-94 | `add_user()` and `add_stage()` reject empty IDs, negative limits and duplicates, so a board can't start in a broken state. |
| R4 · Other changes go through methods | board.py: 184-194, 220-227, 229-264 | Comments, deletes and edits each have one method that validates every input first and only then changes the item. |
| R4 · Defensive copies | board.py: 51-53, 55-59, 100 | Items are copied on the way in and on the way out, so code outside Board can never hold a reference to a board-owned item and change it behind Board's back. |
| R5 · Save to JSON | board.py: 287-309 | `save()` asks each object for its own dict, keeps columns as a list so the workflow order survives, and builds the full JSON text (line 303) before opening the file so a failure can't leave a half-written file. |
| R5 · Load through public methods | board.py: 319-362 | `load_board()` rebuilds the board with `add_user`, `add_stage` and `add_item` (lines 348-356), so loaded data passes the same rule checks as new data. Users and columns load first because `add_item` checks they exist. |
| R5 · Bad files raise custom errors | board.py: 305-309, 327-344, 357-360 | A missing file, broken JSON or a wrong shape raises `InvalidBoardError` instead of a raw `OSError` or `KeyError`, and `from e` keeps the original cause for debugging. |

## Optional depth

| Concept | Where (file: lines) | Why it is needed here |
|---|---|---|
| Read-only properties | board.py: 38-53 | Callers can read `name`, `users`, `stages` and `items`, but can't assign to them. Users and stages come back as tuples of frozen dataclasses; items come back as copies. |
| Dunder methods | board.py: 265-281 | `__repr__` gives a one-line summary for debugging. `__eq__` compares name, members, column order and every item including history, which is how `demo.py` proves a save and load loses nothing. |
| Type hints | board.py: throughout | Every method states what it takes and returns, which makes the contract with `items.py` and `demo.py` clear. |

---

## Each concept in detail

### 1. Board owns the state (lines 30-36)

```python
self._users: dict[str, User] = {}
self._stages: dict[str, WorkflowStage] = {}
self._items: dict[str, BoardItem] = {}
```

Dictionaries keyed by ID make lookups and duplicate checks one step. The underscore marks them as Board's own; nothing outside Board touches them.

### 2. Check everything, then change (lines 132-182)

```python
if item.is_claimed:
    raise AlreadyClaimedError(...)
item.set_owner(user_id)
```

Every rule is checked before the single line that changes state. If any check fails, the exception leaves the board exactly as it was. `demo.py` prints the owner and column right after each rejection to show this.

### 3. Copies in and out (lines 51-59, 100)

`add_item()` stores a deep copy of the item it is given, and `items` / `get_item()` hand back deep copies. Without this, a caller could keep the original item and call `set_owner()` on it directly, skipping the one-owner check.

### 4. Save and load (lines 287-362, Prithvi)

```python
for user_data in data["users"]:
    board.add_user(User.from_dict(user_data))
for stage_data in data["stages"]:
    board.add_stage(WorkflowStage.from_dict(stage_data))
for item_data in data["items"]:
    board.add_item(item_from_dict(item_data))
```

`load_board()` is a function, not a method, because there is no board yet when loading starts. It never writes to `_items` directly, so a hand-edited JSON file with three items in a 2-slot column raises `StageFullError` instead of loading.

| Problem in the file | What the caller sees |
|---|---|
| Missing or unreadable | `InvalidBoardError` |
| Not valid JSON | `InvalidBoardError` |
| Wrong shape or a malformed entry | `InvalidBoardError` |
| Unknown item kind | `InvalidItemError` (from `item_from_dict`) |
| Data breaks a board rule | The same error the Board method raises, e.g. `StageFullError` |

---

## Which files use board.py

| Used by | What they call |
|---|---|
| `demo.py` (Prithvi) | `Board`, `add_user`, `add_stage`, `add_item`, `claim`, `move`, `add_comment`, `describe`, `get_item`, `items`, `save`, `load_board`, `==` |
| `items.py` (relied on) | `validate()`, `describe()`, `to_dict()`, `set_owner()`, `set_stage()`, `add_note()`, `item_from_dict()` |

---

## Check-in talking points

1. **What is the shared state?** Board's three dictionaries. In M2 one Board lives on the server.
2. **What are the invariants?** One owner per item, and no column over its limit. `claim()` and `move()` check them before changing anything.
3. **Why copy items in and out?** So no outside code can change a board-owned item without going through Board.
4. **Why load through the public methods?** So loaded data is checked by the same rules as new data.
5. **How do we know save and load lose nothing?** `demo.py` prints `loaded == original -> True`, using `Board.__eq__`.
