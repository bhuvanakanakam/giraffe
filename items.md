# Concept map: items.py

**Author:** Bhuvana Kanakam (bkanakam)
**Team:** 404NotFound
**Milestone:** M1 Domain Model
**File:** `items.py` (324 lines)

This file defines what can sit on a Giraffe board. It has two dataclasses for plain facts (`WorkflowStage`, `User`), one abstract base class (`BoardItem`), three concrete item kinds (`Task`, `Chore`, `ReferralRequest`), and a loader that turns saved JSON back into the right kind of item.

Line numbers match the version of `items.py` submitted with M1. If the file changes, update this table before submitting.

---

## Summary table

| Concept | File: lines | Why it is needed here |
|---|---|---|
| Dataclass | items.py: 35-50 (`WorkflowStage`), 53-64 (`User`) | Stages and users are plain facts with no rules, so a dataclass gives us `__init__`, `__repr__` and `__eq__` without writing them. `frozen=True` stops them from being changed after creation. |
| Abstract base class | items.py: 74-184 | Every item on a board must be able to validate itself, describe itself, and list its own fields for saving. `BoardItem` forces that, and Python refuses to create a plain `BoardItem`. |
| Abstract methods | items.py: 132-142 | `validate()`, `describe()` and `details()` are different for every kind, so the base class only declares them and each subclass must write its own. |
| Inheritance and `super()` | items.py: 193-214, 217-242, 245-273 (`super()` on 199, 223, 255) | A task, a chore and a referral request each *is a* board item, so inheritance is the right fit. `super().__init__` reuses the shared setup (id, title, owner, stage, history) instead of copying it three times. |
| Polymorphism | items.py: 311-313; used by Board in `add_item()` | The same two calls, `item.validate()` and `item.describe()`, run on any kind of item. No code checks the type, so Board works with all three kinds and any we add later. |
| Encapsulation with `@property` | items.py: 98-113 | `owner`, `stage` and `history` are read-only from outside. Code can read `item.owner` but can't write `item.owner = "x"`, so nothing can skip Board's one-owner rule. |
| Controlled state changes | items.py: 118-127 | `set_owner()` and `set_stage()` are the only way to change an item's owner or stage. Board calls them after its checks pass, and each change is logged to the item's history. |
| Defensive copy | items.py: 93, 106-109 | `history` is copied on the way in and on the way out, so a list from outside can't change the item's real history. |
| Custom exception | items.py: 146-151, 202-207, 227-235, 259-266 | Bad item data raises `InvalidItemError` (defined in `errors.py`) with a message that says exactly what is wrong, instead of failing silently or printing. |
| JSON save | items.py: 156-168 (`to_dict`), 45-50 and 59-64 (dataclasses) | Each item saves its shared fields plus its own `details()`, and always includes `"kind"` so we know which class to rebuild later. |
| JSON load with no if/elif | items.py: 282-295 | `ITEM_KINDS` maps each saved kind to its class. `item_from_dict()` looks the class up and builds it. Adding a new kind is one new line in the dict. |
| Dunder methods | items.py: 177-184 (`__repr__`, `__eq__`) | `__repr__` gives a readable printout while debugging. `__eq__` lets us check that an item saved and loaded back is the same as the original. |
| Type hints | throughout | Every method says what it takes and returns, which makes the contract with `board.py` clear. |
| Self-check | items.py: 302-324 | Running `python items.py` shows polymorphism, a save/load round trip, and a rejected item without needing the rest of the project. |

---

## Each concept in detail

### 1. Dataclasses: `WorkflowStage` and `User` (lines 35-64)

```python
@dataclass(frozen=True)
class WorkflowStage:
    name: str
    limit: int | None = None
```

A stage is just a name and an optional limit. A user is just an id and a name. Neither has any rules to enforce, so writing a full class with a hand-written `__init__` would be extra code for nothing. The lecture rule was "facts become dataclasses, rules become regular classes," and these are facts.

`frozen=True` makes them read-only. Once a stage is created with `limit=3`, nobody can quietly change it to `limit=10` and break the board's rule. If someone tries, Python raises an error.

`limit=None` means "no limit," which lets the same class work for every board type. A sprint's "In Progress" stage might have a limit of 3, a referral opening's "Accepted" stage has a limit equal to the number of slots, and a chores board's "Done" stage has no limit at all.

Each dataclass also has `to_dict()` and `from_dict()` so Prithvi's save and load code can treat them the same way as items.

### 2. Abstract base class: `BoardItem` (lines 74-184)

`BoardItem` holds everything every item shares: an id, a title, a description, a stage, an owner, and a history of changes. It inherits from `ABC`, which means it is only a template. Trying `BoardItem("x", "y")` fails with:

```
TypeError: Can't instantiate abstract class BoardItem without an implementation
for abstract methods 'describe', 'details', 'validate'
```

That's the point. A board should only ever hold real kinds of items, never a vague "item."

### 3. Abstract methods (lines 132-142)

```python
@abstractmethod
def validate(self) -> None: ...
@abstractmethod
def describe(self) -> str: ...
@abstractmethod
def details(self) -> dict: ...
```

These are the three things every kind of item does differently:

| Method | Task | Chore | ReferralRequest |
|---|---|---|---|
| `validate()` | points must be a positive whole number | due date must be a real date | company and applicant can't be empty |
| `describe()` | shows points | shows due date | shows applicant, company and referrer |
| `details()` | `{"points"}` | `{"due_date"}` | `{"company", "applicant"}` |

If a new subclass forgets one of these, Python won't let us create it, so the mistake shows up immediately instead of during the demo.

### 4. Inheritance and `super()` (lines 193-273)

A task *is a* board item, a chore *is a* board item, and a referral request *is a* board item. The lecture's test for inheritance was "is a" being really true, and every parent method still making sense for the child. Both are true here: every kind needs an owner, a stage and a history.

Each subclass calls `super().__init__(item_id, title, **kwargs)` so the shared setup is written once in the parent. Then it adds only its own field (`points`, `due_date`, or `company` and `applicant`).

### 5. Polymorphism (lines 311-313, and Board's `add_item`)

```python
for item in items:
    item.validate()
    print(item.describe())
```

This loop never asks "is this a Task or a Chore?" It calls the same methods and each object answers in its own way. Board does the same thing in `add_item()`: it calls `item.validate()` and lets the item decide what valid means.

The lecture showed what goes wrong with the other approach: an `if kind == "pedal" / elif kind == "electric"` chain silently returned `None` when a new kind showed up. With subclasses, a new kind brings its own `validate()` and `describe()`, and Board needs no changes at all.

### 6. Encapsulation with `@property` (lines 98-113)

```python
@property
def owner(self) -> str | None:
    return self._owner
```

The real value is stored in `_owner` (the underscore means "private, don't touch from outside"). The property lets other code *read* `item.owner`, but there's no setter, so `item.owner = "bob"` raises an error.

This matters because our invariant is "each item has at most one owner." If any code could just assign an owner directly, it could skip Board's check. Making the attribute read-only means the only way to change an owner is through Board.

`is_claimed` is a small convenience property so Board can write `if item.is_claimed:` instead of `if item.owner is not None:`.

### 7. Controlled state changes (lines 118-127)

`set_owner()` and `set_stage()` are the only way to change an item's owner or stage. These methods don't check rules themselves, because the rules depend on the whole board (is the stage full? is this user a member?), and only Board can see that. So the flow is:

1. Board checks every rule.
2. If anything is wrong, Board raises an exception and nothing changes.
3. If everything passes, Board calls `item.set_owner()` or `item.set_stage()`.

Each setter also writes a line to the item's history, so every change leaves a record.

### 8. Defensive copy of history (lines 93, 106-109)

```python
self._history = list(history) if history else []   # copy on the way in
return list(self._history)                          # copy on the way out
```

Without these copies, someone could do `item.history.append("fake entry")` and change the item's real history. Copying means the outside world only ever gets a snapshot.

### 9. Custom exception: `InvalidItemError` (lines 146-151, 202-266)

Every `validate()` raises `InvalidItemError` with a clear message, for example:

```
task t2 needs a positive whole number of points
chore c3 needs a due date like 2026-11-08
referral r4 needs a company
```

`InvalidItemError` is defined in `errors.py` as a subclass of `GiraffeError`, so `demo.py` can catch it specifically, or catch every Giraffe error at once with `except GiraffeError`.

`_check_common()` (lines 146-151) holds the checks every item shares (non-empty id and title), so each subclass calls it first instead of repeating those lines.

In `Chore.validate()`, `date.fromisoformat()` raises its own `ValueError` for a bad date. We catch that and raise our own `InvalidItemError` instead, so the caller only has to know about Giraffe's exceptions.

### 10. JSON save: `to_dict()` (lines 156-168)

```python
return {
    "kind": self.KIND,
    "item_id": ...,
    ...
    **self.details(),
}
```

The shared fields are written once in the base class. `**self.details()` adds whatever is special to that kind. So a saved chore looks like:

```json
{"kind": "chore", "item_id": "c1", "title": "Take out trash",
 "description": "", "stage": "Unclaimed", "owner": "bhuvana",
 "history": ["owner set to bhuvana"], "due_date": "2026-11-08"}
```

The `"kind"` field is the key part. JSON has no idea what a `Chore` is, so without it we couldn't tell which class to rebuild when loading. This is what the lecture meant by "save each object's kind."

### 11. JSON load with no if/elif: `ITEM_KINDS` and `item_from_dict()` (lines 282-295)

```python
ITEM_KINDS = {"task": Task, "chore": Chore, "referral": ReferralRequest}

def item_from_dict(data):
    item_class = ITEM_KINDS.get(data.get("kind"))
    if item_class is None:
        raise InvalidItemError(...)
    return item_class.from_dict(data)
```

Instead of `if kind == "task": ... elif kind == "chore": ...`, a dictionary maps each kind to its class. Adding a fourth kind later means adding one line to the dict. An unknown kind raises our own exception instead of crashing with a confusing `KeyError`.

`from_dict()` (lines 170-174) removes `"kind"` and passes the rest to the constructor. Because `cls` is already the right subclass, `Chore.from_dict(...)` builds a `Chore`.

Loaded items should then be added to the board through `Board.add_item()`, so loaded data gets validated the same way new data does.

### 12. Dunder methods (lines 177-184)

- `__repr__` prints `Chore('c1', 'Take out trash')` instead of `<items.Chore object at 0x10a...>`, which makes debugging much easier.
- `__eq__` says two items are equal if everything we'd save about them matches. We use it to prove a save and load round trip loses nothing.

### 13. Self-check (lines 302-324)

Running `python items.py` on its own prints:

```
[Task] Build login page (3 pts) | To Do | unassigned
[Chore] Take out trash (due 2026-11-08) | Unclaimed | unassigned
[Referral] Ana -> Amazon | Requested | referrer: unassigned
round trip ok: True | [Chore] Take out trash (due 2026-11-08) | Unclaimed | bhuvana
Rejected: task t2 needs a positive whole number of points
```

This shows polymorphism, a save and load round trip, and a correctly rejected item, all without the rest of the project. The `if __name__ == "__main__":` guard means this code doesn't run when another file imports `items.py`.

---

## How other files use items.py

| Used by | What they call |
|---|---|
| `board.py` (Ayush) | `item.validate()` in `add_item`, `item.is_claimed` and `item.set_owner()` in `claim`, `item.stage` and `item.set_stage()` in `move`, `item.add_note()` in `add_comment` |
| `board.py` save and load (Prithvi) | `item.to_dict()`, `item_from_dict()`, `WorkflowStage.to_dict/from_dict`, `User.to_dict/from_dict` |
| `demo.py` (Prithvi) | `item.describe()` to print the board |
| `errors.py` (Ayush) | must define `InvalidItemError` as a subclass of `GiraffeError` |

---

## Check-in talking points

1. **Why an ABC?** Every item must validate and describe itself, and the ABC makes forgetting one impossible.
2. **Why no if/elif on type?** Board calls `validate()` and `describe()` on anything. New kinds need no changes to Board.
3. **Why are owner and stage read-only?** So the one-owner rule can only be bypassed by going through Board, which checks it.
4. **Why save `"kind"`?** JSON doesn't know our classes, so `kind` tells us which one to rebuild.
5. **Why frozen dataclasses?** Stages and users are facts. Freezing them stops anyone from quietly changing a stage's limit.

---

## AI use

I used Claude to help structure this file and write this concept map. I reviewed and tested all of it and can explain every part. This is also cited in the project README.
