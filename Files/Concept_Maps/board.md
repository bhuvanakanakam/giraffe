# Concept map: board.py

**Author:** Ayush Jain  
**Team:** 404NotFound  
**Milestone:** M1 Domain Model  
**File:** board.py  
**AI assistance:** ChatGPT helped prepare this concept map from the current source.

## Summary table

| Concept | File: lines | Why it is needed here |
|---|---|---|
| Composition | board.py: 30-36 | Board owns members, stages, and items as the future shared state. |
| Read-only properties | board.py: 39-40; board.py: 43-44; board.py: 47-48 | The name is read-only; user and stage collections are tuples containing frozen dataclasses. |
| Defensive copies and ownership | board.py: 96-130; board.py: 51-53; board.py: 55-59 | Copy on admission and copy on retrieval prevent external references from changing board-owned items, including nested history. |
| Validated admission | board.py: 61-75; board.py: 77-94; board.py: 96-130 | Validate data, uniqueness, membership, and capacity before inserting. |
| Polymorphism | board.py: 96-130; board.py: 196-218 | Call validate() and describe() through BoardItem without branching on concrete subclass. |
| Ownership invariant | board.py: 132-151 | Reject a second claim before updating owner or history. |
| Capacity invariant | board.py: 153-182 | Count destination items before moving; same-stage moves change nothing. |
| Validate before mutation | board.py: 184-194; board.py: 229-264 | Check all supplied fields before changing text or history. |
| Collection removal | board.py: 220-227 | Reject missing IDs; removal frees stage capacity. |
| Read-only presentation | board.py: 196-218 | Return a grouped text summary without changing state. |
| Custom exceptions and type hints | Throughout | Explain domain rejections and document operation contracts. |
| JSON save (Prithvi) | board.py: 287-309 | `save()` writes the name, users, stages and items to JSON. Stages go in a list so the workflow order survives, and each item's `to_dict()` includes its `"kind"` so the right class can be rebuilt. |
| Load through public methods (Prithvi) | board.py: 319-362 (rebuild on 348-356) | `load_board()` rebuilds the board with `add_user`, `add_stage` and `add_item`, so every rule runs again on loaded data and nothing outside Board touches `_items`. Stages load before items because `add_item` checks the stage exists. |
| No if/elif on kind when loading (Prithvi) | board.py: 356 | Each item goes through `item_from_dict()`, which uses the `ITEM_KINDS` lookup, so load works for any kind without type checks. |
| Custom exceptions for bad files (Prithvi) | board.py: 305-309, 327-346, 357-360 | A missing file, broken JSON or the wrong shape raises `InvalidBoardError` instead of a raw `OSError`/`KeyError`/`TypeError`, so callers only need to catch Giraffe errors. `raise ... from e` keeps the original cause for debugging. |
| Fail before writing (Prithvi) | board.py: 303 | The JSON text is built in full before the file is opened, so a serialization error can't leave a half-written file. |

---

## Save and load in detail (Prithvi Sunilkumar)

**AI assistance:** I used Claude to help draft `save()`, `load_board()` and this section. I reviewed and tested all of it and can explain every line.

### Saving (board.py: 287-309)

```python
data = {
    "name": self._name,
    "users": [user.to_dict() for user in self._users.values()],
    "stages": [stage.to_dict() for stage in self._stages.values()],
    "items": [item.to_dict() for item in self._items.values()],
}
text = json.dumps(data, indent=2)
```

`save()` is a method on Board because only Board can see its private dictionaries. It asks each object for its own dict (`to_dict()`), so Board doesn't need to know what fields a `Chore` or a `ReferralRequest` has. That is polymorphism again: the same call on every item, and each kind adds its own fields.

### Loading (board.py: 319-362)

```python
board = Board(data["name"])
for user_data in data["users"]:
    board.add_user(User.from_dict(user_data))
for stage_data in data["stages"]:
    board.add_stage(WorkflowStage.from_dict(stage_data))
for item_data in data["items"]:
    board.add_item(item_from_dict(item_data))
```

`load_board()` is a plain function, not a method, because there is no board yet when you start loading. It never writes to `_items` directly. Every user, stage and item goes back in through the same public methods a person would use, so a hand-edited JSON file can't create a board that breaks our rules (for example, three items in a stage with a limit of 2 raises `StageFullError`).

The order matters: `add_item` checks that the item's stage exists and that its owner is a member, so users and stages have to be loaded first.

### Errors (board.py: 305-309, 327-360)

| Problem | What the caller sees |
|---|---|
| File missing or unreadable | `InvalidBoardError` |
| Not valid JSON | `InvalidBoardError` |
| Not an object, missing keys, or a section isn't a list | `InvalidBoardError` |
| An entry with wrong fields or not a dict | `InvalidBoardError` (from `TypeError` / `AttributeError`) |
| Unknown item kind | `InvalidItemError` (from `item_from_dict`) |
| Data breaks a board rule | The same error the Board method raises, e.g. `StageFullError` |

### Who uses save and load

| Used by | What they call |
|---|---|
| `demo.py` | `board.save(path)`, `load_board(path)`, then `loaded == original` |
| `items.py` (relied on) | `to_dict()`, `from_dict()`, `item_from_dict()` |

### Check-in talking points

1. **Why load through the public methods?** So loaded data is checked by the same rules as new data, and nothing outside Board touches `_items`.
2. **Why save `"kind"`?** JSON doesn't know our classes. `kind` tells `item_from_dict()` which class to rebuild, using a dict lookup instead of if/elif.
3. **Why stages as a list?** Stage order is the workflow order, and a list keeps it. `Board.__eq__` compares stage order, so the round trip proves it survived.
4. **Why wrap errors?** Callers only need to catch Giraffe errors; `from e` keeps the original cause.
5. **How do we know it works?** `demo.py` prints `loaded == original -> True` for both boards.
