# Step 1: Merge `extend:` from extend source `spec/navigation.yaml`

## Goal
When `--extend` is used and both cwd and extend root have `spec/navigation.yaml`, merge **only** the **`extend:`** list into cwd’s registry by appending new paths; if the source file has **`design:`** entries, warn on stderr and do not merge or copy design files from the extend bundle.

## Approach
- In `run_extend`, after `acquire_source` yields `extend_root`, if cwd navigation exists and `extend_root / spec / navigation.yaml` exists, load both, apply merge rules from task `overview.md`, write cwd navigation if changed.
- Emit one or more clear stderr warnings listing that design entries from the extend navigation are ignored (wording per overview).
- Keep `copy_extend_overlay` behavior unchanged: still only `spec/extend/` files from extend root.

## Affected files
- `spectask_init/bootstrap.py` (`run_extend`, new helpers)
- Tests as needed in `tests/test_bootstrap_unit.py`

## Code examples
(None — follow existing `bootstrap.py` patterns for paths and errors.)
