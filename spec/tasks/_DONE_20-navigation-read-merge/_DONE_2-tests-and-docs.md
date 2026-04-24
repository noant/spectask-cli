# Step 2: Tests and documentation

## Goal
Lock merge behavior with tests and update architecture docs so the `read` field is part of the described contract.

## Approach
- **Unit / integration tests:**
  - **Template merge, missing → required:** cwd has no `read`; template has `read: required` for the same `path` → result `read: required`.
  - **Template merge, optional → required:** cwd has `read: optional`; template has `read: required` → result `read: required` (required wins from either side).
  - **Extend merge, required preserved from cwd:** cwd has `read: required`; source has `read: optional` or omits `read` → result `read: required` (required from project must not be lost).
  - **Explicit optional OR:** cwd omits `read`, source has `read: optional` (or the reverse) → result `read: optional` (explicit optional is preserved if at least one side has it, and neither side is `required`).
  - **Both omit `read`:** merged row omits `read`.
  - **Append:** new path from source still deep-copies full row (including `read`).
  - **Invalid `read` value** in cwd or source (e.g. wrong string) → `RuntimeError` (if validation is in scope for this step).
- **Docs:** Update `spec/design/hla.md` and **`spec/main.md`** with upstream-aligned `read` semantics and merge: **`read: required` wins if present on either side**; explicit **`optional`** is preserved if either side sets it and neither is `required`; **README** only if it documents merge.

## Affected files
- `tests/test_bootstrap_unit.py`, `tests/test_navigation_merge.py` (or new focused module if cleaner)
- `spec/design/hla.md`
- `spec/main.md` only if a Folder Structure bullet is needed for optional `read` (see task overview)
- `README.md` only if it currently documents merge semantics

## Code examples
Use `yaml.safe_load` assertions on written `spec/navigation.yaml` like existing navigation tests; avoid brittle ordering beyond what the spec guarantees.
