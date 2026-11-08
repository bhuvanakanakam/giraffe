# Concept map: errors.py

**Author:** Ayush Jain  
**Team:** 404NotFound  
**Milestone:** M1 Domain Model  
**File:** errors.py  
**AI assistance:** ChatGPT helped prepare this concept map from the current source.

## Summary table

| Concept | File: lines | Why it is needed here |
|---|---|---|
| Custom exceptions | errors.py: 15–40| Gives callers specific reasons why Giraffe rejects invalid data or board operations. |
| Inheritance | errors.py: 15–40 | All domain errors inherit from GiraffeError, allowing the demo to catch expected Giraffe failures together. |
| Docstrings | Throughout | Explains which rule or failure each exception represents. |