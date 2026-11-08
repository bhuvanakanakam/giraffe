# Concept map: board.py

**Author:** Ayush Jain  
**Team:** 404NotFound  
**Milestone:** M1 Domain Model  
**File:** board.py  
**AI assistance:** ChatGPT helped prepare this concept map from the current source.

## Summary table

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
