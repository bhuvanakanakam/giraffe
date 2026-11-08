# Giraffe

Giraffe is a customizable board system for organizing software sprints, shared household chores, and referral requests. Members can define workflow stages, add and edit items, claim ownership, move items between stages, and add comments to an item's activity history. The board checks ownership and stage-capacity rules before applying changes.

For M1, Giraffe runs locally as plain Python objects with no networking. Tasks, chores, and referral requests share a common interface, alongside users and configurable workflow stages. JSON file persistence and an integrated command-line demo are planned parts of this milestone; a shared server comes in M2.

**Team:** 404NotFound (Ayush Jain, Bhuvana Kanakam, Prithvi Sunilkumar)
**Course:** 95-895 Python Systems Fundamentals, Fall 2026
**Folder started by:** Bhuvana Kanakam (bkanakam)

Each code file has its own concept map here, written by the person who built that file. Each map lists every course concept in the file, the exact lines, and why we used it there. The combined table in the main README is built from these.

| File | Concept map | Owner | Status |
|---|---|---|---|
| items.py | [items.md](Files/Concept_Maps/items.md) | Bhuvana Kanakam | Done |
| errors.py | [errors.md](Files/Concept_Maps/errors.md) | Ayush Jain |  Done |
| board.py (rules) | [board.md](Files/Concept_Maps/board.md) | Ayush Jain | Done |
| board.py (save and load) | [board.md](Files/Concept_Maps/board.md) | Prithvi Sunilkumar | To do |
| demo.py | demo.md | Prithvi Sunilkumar | To do |

## Format for each file

1. Header: author, milestone, file
2. Summary table: Concept | File: lines | Why it is needed here
3. Each concept in detail, with a short code snippet
4. Which other files use this one
5. Check-in talking points

## Before submitting

- Line numbers change whenever a file is edited. Recheck every row after the final merge.
- Copy the summary rows into the concept map in the main README, since graders score against that one.
- Every "why" should say why the concept fits *our* project, not just what the concept is. That is the difference between scoring Correct (2) and Justified (3).

## Board encapsulation

Board stores a deep copy of each admitted item. Use `board.get_item(item_id)` or `board.items` to inspect detached snapshots; input objects and old snapshots do not track later board changes. Apply changes through Board methods. Internal underscore attributes are not part of the public API.

### Board concept summary

| Concept | File: lines | Why it is needed here |
|---|---|---|
| Composition | board.py: 25-31 | Board owns members, stages, and items as the future shared state. |
| Read-only properties | board.py: 34-35; board.py: 38-39; board.py: 42-43 | The name is read-only; user and stage collections are tuples containing frozen dataclasses. |
| Defensive copies and ownership | board.py: 91-125; board.py: 46-48; board.py: 50-54 | Copy on admission and copy on retrieval prevent external references from changing board-owned items, including nested history. |
| Validated admission | board.py: 56-70; board.py: 72-89; board.py: 91-125 | Validate data, uniqueness, membership, and capacity before inserting. |
| Polymorphism | board.py: 91-125; board.py: 191-213 | Call validate() and describe() through BoardItem without branching on concrete subclass. |
| Ownership invariant | board.py: 127-146 | Reject a second claim before updating owner or history. |
| Capacity invariant | board.py: 148-177 | Count destination items before moving; same-stage moves change nothing. |
| Validate before mutation | board.py: 179-189; board.py: 224-259 | Check all supplied fields before changing text or history. |
| Collection removal | board.py: 215-222 | Reject missing IDs; removal frees stage capacity. |
| Read-only presentation | board.py: 191-213 | Return a grouped text summary without changing state. |
| Custom exceptions and type hints | Throughout | Explain domain rejections and document operation contracts. |
