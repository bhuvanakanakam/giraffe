# Concept map: errors.py
> AI Use note: This .md file was created using ChatGPT 

**Author:** Ayush Jain
**Team:** 404NotFound
**Milestone:** M1 Domain Model
**File:** errors.py

## Summary table

| Concept | File: lines | Why it is needed here |
|---|---|---|
| Custom exceptions | errors.py: 15–34 | Gives callers specific reasons why Giraffe rejects invalid data or board operations. |
| Inheritance | errors.py: 15–34 | All domain errors inherit from GiraffeError, allowing the demo to catch expected Giraffe failures together. |
| Docstrings | Throughout | Explains which rule or failure each exception represents. |
