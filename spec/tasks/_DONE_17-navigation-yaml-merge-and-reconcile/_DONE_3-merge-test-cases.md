# Step 3: Test cases for navigation merge (`--extend`)

## Goal
Add focused automated tests that cover **important merge scenarios** for merging the extend source’s `spec/navigation.yaml` **`extend:`** section into the cwd registry (step 1 behavior), including edge cases and stderr expectations.

## Approach
- Implement as `pytest` tests (prefer `tests/test_bootstrap_unit.py` or a dedicated module if the file grows).
- **Minimum scenarios to cover:**
  - **Append new paths:** cwd has `extend: [A]`, source has `extend: [B, C]` → result lists A then B, C (or stable order per spec); B/C get descriptions from source.
  - **Dedup by path:** same `path` in cwd and source → cwd **description preserved**, no duplicate row; no unnecessary file rewrite if nothing would change.
  - **Path normalization:** logically same path with different slash or trivial normalization (if implementation normalizes) does not create duplicates.
  - **Source has `design:`:** non-empty `design` list in extend navigation → stderr **warning** appears; cwd **`design:`** unchanged after merge; no `spec/design/*` copied from extend (assert filesystem + yaml).
  - **No source navigation:** extend root lacks `spec/navigation.yaml` → merge no-op, overlay still works.
  - **No cwd navigation:** cwd missing `spec/navigation.yaml` → merge skipped (no crash); overlay still works.
  - **Invalid YAML in source or cwd:** `RuntimeError` with clear message (if step 1 validates strictly per overview).
- Use `tmp_path`, capture stderr (`io.StringIO` or `capsys`), and small inline YAML strings or fixtures—no network unless an existing integration pattern is reused.
- Do not duplicate exhaustive reconcile coverage from step 2 unless a scenario is merge-specific (e.g. merge then overlay then reconcile).

## Affected files
- `tests/test_bootstrap_unit.py` and/or new `tests/test_navigation_merge.py` (only if justified by size)

## Code examples
(None — follow existing bootstrap test style.)
