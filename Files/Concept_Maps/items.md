# Concept map: items.py

**Author:** Bhuvana Kanakam (bkanakam)
**Team:** 404NotFound
**Milestone:** M1 Domain Model
**File:** `items.py` (324 lines)
**AI assistance:** Claude helped structure this file and write this concept map. I reviewed and tested all of it and can explain every part.

`items.py` defines what can sit on a Giraffe board: two dataclasses for plain facts (`WorkflowStage`, `User`), one abstract base class (`BoardItem`), three kinds of item (`Task`, `Chore`, `ReferralRequest`), and a loader that turns saved JSON back into the right kind of item.

Line numbers match the version of `items.py` submitted with M1.

---

## Summary table

| Concept | Where (file: lines) | Why it is needed here |
|---|---|---|
| R1 · Data classes | items.py: 35-50, 53-64 | A column (`WorkflowStage`) is just a name and an optional limit, and a `User` is just an ID and a name. They hold facts with no rules, so `@dataclass` writes `__init__`, `__repr__` and `__eq__` for us. `frozen=True` stops anyone from quietly raising a column's limit after the board checked it. |
| R1 · Classes for things with rules | items.py: 74-273 | Items do have rules (each kind validates itself and controls how its owner and column change), so they are regular classes. |
| R2 · Abstract base class | items.py: 74-184 | Every item on a board must be able to validate itself, describe itself and list its own fields for saving. `BoardItem` inherits from `ABC`, so Python refuses to create a plain `BoardItem`. |
| R2 · Abstract methods | items.py: 132-142 | `validate()`, `describe()` and `details()` differ for every kind, so the base class only declares them with `@abstractmethod`. A subclass that forgets one can't be created at all. |
| R2 · Concrete subclasses with `super()` | items.py: 193-214, 217-242, 245-273 | A task, a chore and a referral request each *is a* board item, and every parent method (owner, column, history) makes sense for all three. `super().__init__` (lines 199, 223, 255) reuses the shared setup instead of copying it three times. |
| R2 · Polymorphism, no type checks | items.py: 311-313; board.py: 101, 216, 298 | The same calls, `validate()`, `describe()` and `to_dict()`, work on any kind of item. Neither this file's self-check nor `Board` ever checks which kind it has. |
| R4 · Item state changes only through methods | items.py: 98-127 | `owner`, `stage` and `history` are read-only properties. The only way to change an owner or column is `set_owner()` / `set_stage()`, which `Board` calls after its checks pass, and each change is logged to the item's history. |
| R4 · Defensive copy of history | items.py: 93, 106-109 | History is copied on the way in and on the way out, so a list from outside can never change an item's real history. |
| R4 · Custom exception for bad item data | items.py: 146-151, 202-207, 227-235, 259-266 | Bad data raises `InvalidItemError` with a message that says exactly what is wrong. Wrong types (for example a number as a title, or `True` as points) are rejected the same way instead of crashing. |
| R5 · Save: each object writes its own dict | items.py: 45-46, 59-60, 156-168 | Each item writes its shared fields plus its own `details()`, and always includes `"kind"`, because JSON has no idea which class an object came from. |
| R5 · Load: rebuild the right class, no if/elif | items.py: 170-175, 282-295 | `ITEM_KINDS` maps each saved kind to its class, and `item_from_dict()` looks it up. Adding a fourth kind is one new line, and an unknown kind raises `InvalidItemError` instead of a confusing `KeyError`. |

## Optional depth

| Concept | Where (file: lines) | Why it is needed here |
|---|---|---|
| Properties | items.py: 98-113 | Read-only access is what stops `item.owner = "x"` from skipping the one-owner rule. `is_claimed` lets `Board` write `if item.is_claimed:`. |
| Dunder methods | items.py: 177-184 | `__repr__` prints `Chore('c1', 'Take out trash')` instead of a memory address. `__eq__` compares everything we save, which is how we prove a save and load round trip loses nothing. |
| Type hints | items.py: throughout | Every method states what it takes and returns, which makes the contract with `board.py` clear. |
| Self-check | items.py: 302-324 | `python items.py` shows polymorphism, a save and load round trip, and a rejected item without the rest of the project. |

---

## Each concept in detail

### 1. Dataclasses (lines 35-64)

```python
@dataclass(frozen=True)
class WorkflowStage:
    name: str
    limit: int | None = None
```

`limit=None` means "no limit", so the same class works for every board: a sprint's "In Progress" column might hold 3, a referral board's "Accepted" column holds as many as there are referral slots, and a chores board's "Done" column has no limit.

### 2. Abstract base class and abstract methods (lines 74-184, 132-142)

Trying `BoardItem("x", "y")` fails with `TypeError: Can't instantiate abstract class BoardItem...`. A board should only hold real kinds of items, never a vague "item".

| Method | Task | Chore | ReferralRequest |
|---|---|---|---|
| `validate()` | points must be a positive whole number | due date must be a real date | company and applicant can't be empty |
| `describe()` | shows points | shows due date | shows applicant, company and referrer |
| `details()` | `{"points"}` | `{"due_date"}` | `{"company", "applicant"}` |

### 3. Polymorphism (lines 311-313, and board.py)

```python
for item in items:
    item.validate()
    print(item.describe())
```

The lecture showed what goes wrong otherwise: an `if kind == "pedal" / elif kind == "electric"` chain silently returned `None` for a new kind. Here a new kind brings its own `validate()` and `describe()`, and `Board` needs no change.

### 4. Controlled state changes (lines 98-127)

These setters don't check rules themselves, because the rules depend on the whole board (is the column full? is this user a member?), and only `Board` can see that. The flow is: Board checks every rule, raises if anything is wrong, and only then calls `set_owner()` or `set_stage()`.

### 5. Save and load (lines 156-175, 282-295)

A saved chore looks like:

```json
{"kind": "chore", "item_id": "c1", "title": "Take out trash", "description": "",
 "stage": "Unclaimed", "owner": "bhuvana", "history": ["owner set to bhuvana"],
 "due_date": "2026-11-08"}
```

`from_dict()` drops `"kind"` and passes the rest to the constructor. Because `cls` is already the right subclass, `Chore.from_dict(...)` builds a `Chore`. `load_board()` then adds it through `Board.add_item()`, so loaded items are validated like new ones.

---

## Which files use items.py

| Used by | What they call |
|---|---|
| `board.py` (Ayush) | `validate()` in `add_item`, `is_claimed` and `set_owner()` in `claim`, `stage` and `set_stage()` in `move`, `add_note()` in comments and edits, `describe()` in `describe` |
| `board.py` (Prithvi) | `to_dict()`, `item_from_dict()`, `User` and `WorkflowStage` `to_dict` / `from_dict` |
| `demo.py` (Prithvi) | `User`, `WorkflowStage`, `Chore`, `ReferralRequest`, `describe()` |
| `errors.py` (Ayush) | provides `InvalidItemError` |

---

## Check-in talking points

1. **Why an ABC?** Every item must validate and describe itself, and the ABC makes forgetting one impossible.
2. **Why no if/elif on type?** Board calls the same methods on any item, and loading uses a dictionary lookup. New kinds need no change to Board.
3. **Why are owner and column read-only?** So the one-owner rule can only be changed by going through Board, which checks it.
4. **Why save `"kind"`?** JSON doesn't know our classes, so `kind` tells us which one to rebuild.
5. **Why frozen dataclasses?** Columns and users are facts. Freezing them stops anyone from quietly changing a column's limit.
