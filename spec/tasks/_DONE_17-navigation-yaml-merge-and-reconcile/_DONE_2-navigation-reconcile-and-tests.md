# Step 2: Post-migration / post-extend navigation reconcile + targeted tests

## Goal
After `apply_template_migration` inside `run_template_bootstrap`, and again after `run_extend` completes overlay, reconcile `spec/navigation.yaml` **`extend:`** and **`design:`** sections with files under `spec/extend/` and `spec/design/`: append missing paths with placeholder descriptions and warnings; remove entries whose files are gone and warn.

## Approach
- Add a single internal function e.g. `reconcile_navigation_with_spec_tree(cwd: Path, stderr: TextIO | None = None) -> None` (or pass stderr from CLI/bootstrap consistently with `apply_template_migration`).
- Call it from `run_template_bootstrap` immediately after `apply_template_migration`.
- Call it from `run_extend` after `copy_extend_overlay`.
- If `spec/navigation.yaml` missing, return immediately.
- Implement path collection, YAML read/write, and English warnings per `overview.md`.
- Add **smoke / regression** tests for reconcile + migration ordering here; leave **extend navigation merge** matrix to step `_DONE_3-merge-test-cases`.

## Affected files
- `spectask_init/bootstrap.py`
- `spectask_init/cli.py` (only if stderr plumbing is required)
- `tests/test_bootstrap_unit.py`, optionally `tests/test_integration_cli.py`

## Code examples
(None — mirror `apply_template_migration` stderr style.)
