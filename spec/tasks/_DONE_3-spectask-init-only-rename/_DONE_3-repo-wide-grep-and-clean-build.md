# Step 3: repo-wide grep and clean build

## Goal
Ensure no stale **`spectask-bootstrap`** / **`spectask_bootstrap`** references remain where users or tooling read them, and verify the package builds.

## Approach
1. Search the repo (excluding **`spec/tasks/_DONE_*`** and **`.git`**) for **`spectask-bootstrap`** and **`spectask_bootstrap`**; fix any stragglers in active project files (e.g. **`.cursor/`** skills only if they reference this repo’s package name — optional, minimal).
2. Remove obsolete **`spectask_bootstrap.egg-info/`** if present; run **`uv build`** (or **`python -m build`**) from repo root and confirm success.
3. Smoke-check: **`spectask-init --help`** or **`python -m spectask_init --help`** from an editable install / fresh venv.

## Affected files
- Any remaining matches outside archived task specs
- **`spectask_bootstrap.egg-info/`** (delete) — regenerated on build

## Constraints
- Do not broaden scope to unrelated refactors.
- If **`AGENTS.md`** or other root docs mention the old name, update only when they refer to this project’s CLI/package (not generic English “bootstrap”).

## Code examples

```bash
rg "spectask-bootstrap|spectask_bootstrap" --glob '!spec/tasks/_DONE_*'
uv build
spectask-init --help
```
