# Concept map: errors.py

**Author:** Ayush Jain (ayushjain_01)
**Team:** 404NotFound
**Milestone:** M1 Domain Model
**File:** `errors.py` (40 lines)
**AI assistance:** No AI in the code. ChatGPT helped prepare this concept map; Claude helped align its format with the other maps.

`errors.py` defines every reason Giraffe can refuse an operation. Each rejection has its own exception class, and all of them belong to one family under `GiraffeError`.

Line numbers match the version of `errors.py` submitted with M1.

---

## Summary table

| Concept | Where (file: lines) | Why it is needed here |
|---|---|---|
| R4 · Custom exception classes | errors.py: 15-40 | Giraffe has several different ways to refuse an operation (item already claimed, column full, unknown user). A separate class for each one means the caller can tell them apart by name instead of reading a `False` or parsing a message. |
| R4 · Exception family through inheritance | errors.py: 15-40 | Every error inherits from `GiraffeError`, so a caller can catch any Giraffe rule violation with one `except GiraffeError`. Interactive mode in `demo.py` (line 158) does exactly this to print any rejection and keep going, and the M2 server will do the same to send error responses. The scripted story catches the specific errors by name (lines 91, 109). |
| R4 · Grouped board setup errors | errors.py: 21-28 | `InvalidUserError` and `InvalidStageError` are children of `InvalidBoardError` because both mean the board was configured wrongly, so they can be handled together. |
| R4 · One error per invariant | errors.py: 36-40 | `AlreadyClaimedError` protects our one-owner rule and `StageFullError` protects our column limits (like the 2 referral slots in the demo). They are the two rules M3 has to keep true under concurrency. |

---

## Each concept in detail

### 1. One class per reason (lines 15-40)

| Class | Lines | Raised when | Raised in |
|---|---|---|---|
| `GiraffeError` | 15-16 | Never directly; the family's parent | |
| `InvalidItemError` | 18-19 | An item's own data is wrong (empty title, 0 points, bad date) | items.py: 149, 151, 206, 234, 262, 265, 294 |
| `InvalidBoardError` | 21-22 | Bad board data or a bad save file | board.py: 32, 99, 192, 244, 250, 309, 331, 333, 336, 340, 344, 360 |
| `InvalidUserError` | 24-25 | A user with no ID or name | board.py: 63, 66, 69 |
| `InvalidStageError` | 27-28 | A column with no name or a negative limit | board.py: 79, 81, 85 |
| `DuplicateIDError` | 30-31 | A second user, column or item with an existing ID | board.py: 71, 90, 104 |
| `NotFoundError` | 33-34 | An unknown item, column or user | board.py: 58, 109, 114, 135, 140, 156, 161, 187, 223, 238 |
| `AlreadyClaimedError` | 36-37 | Claiming an item that already has an owner | board.py: 147 |
| `StageFullError` | 39-40 | Adding or moving an item into a full column | board.py: 125, 178 |

### 2. Why a family instead of returning False

```python
class GiraffeError(Exception): ...
class AlreadyClaimedError(GiraffeError): ...
class StageFullError(GiraffeError): ...
```

A `False` can be ignored by accident and never says why. An exception can't be silently skipped, and its name explains the failure. Because they share a parent, `except GiraffeError` catches all of them, and `except StageFullError` catches just one. Python checks `except` blocks in order, so specific errors are caught before the parent.

---

## Which files use errors.py

| Used by | What they use |
|---|---|
| `items.py` (Bhuvana) | raises `InvalidItemError` |
| `board.py` (Ayush, Prithvi) | raises every other error |
| `demo.py` (Prithvi, Ayush) | the story catches `AlreadyClaimedError` (line 91) and `StageFullError` (line 109); interactive mode catches the whole family with `except GiraffeError` (line 158) |

---

## Check-in talking points

1. **Why custom exceptions?** Each one names the rule that was broken, so callers can react differently to "full" and "already claimed".
2. **Why a common parent?** One `except GiraffeError` catches every rule violation. Interactive mode uses it on demo.py line 158, and the M2 server will use it to send back an error response.
3. **Why are user and stage errors under `InvalidBoardError`?** Both mean the board was set up wrongly.
4. **Which errors guard our invariants?** `AlreadyClaimedError` (one owner) and `StageFullError` (column limits).
