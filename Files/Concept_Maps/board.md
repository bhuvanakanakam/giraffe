# Concept map: board.py

**Author:** Ayush Jain  
**Team:** 404NotFound  
**Milestone:** M1 Domain Model  
**File:** board.py  
**AI assistance:** ChatGPT helped prepare this concept map from the current source.

## Summary table

| Concept | File: lines | Why it is needed here |
|---|---|---|
| Composition | board.py: 23-29 | Board owns dictionaries of members, stages, and items, making it the future home of shared server state. |
| Properties and collection snapshots | board.py: 31-41 | Callers can read the board name and receive tuples of frozen users and stages without modifying the board collections. |
| Validated admission | board.py: 43-106 | Users, stages, and items are checked before insertion; duplicate identifiers and invalid relationships are rejected. |
| Polymorphism | board.py: 78, 192 | Board calls validate() and describe() through the BoardItem interface without branching on concrete item type. |
| Custom exceptions | board.py: 43-170, 196-240 | Domain failures explain invalid membership, duplicate IDs, ownership conflicts, and capacity violations. |
| Controlled ownership changes | board.py: 108-127 | claim() checks membership and existing ownership before recording a new owner. |
| Capacity invariant | board.py: 95-104, 129-158 | Admission and movement count destination items before allowing a change; same-stage moves are harmless. |
| Validate before mutation | board.py: 160-170, 205-240 | Invalid comments and edits are rejected before history or item fields change. |
| Read-only presentation | board.py: 172-194 | describe() groups items by stage and returns text without changing state. |
| Collection removal | board.py: 196-203 | Deleting an existing item frees capacity; missing items raise a domain exception. |
| Type hints | Throughout | Annotations describe the expected domain objects, identifiers, and return values. |
