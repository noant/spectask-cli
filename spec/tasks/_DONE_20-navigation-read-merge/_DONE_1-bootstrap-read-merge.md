# Step 1: Bootstrap merge updates for `read`

## Goal
Implement row-level handling of `read` in `_merge_navigation_registry_sections_from_src` so duplicate `path` rows get the **merged** `read` per upstream: **`read: required` if either side is required**; else **`read: optional` if either side is explicitly optional**; else **omit** `read`. Cwd still supplies `path`, `description`, and other keys; only `read` is combined from both sides.

## Approach
- Refactor the inner loop: for each `key` in `keys`, build `merged_list` from cwd items; for each `src` item, compute normalized path; if new, append deep copy; if duplicate, find the index in `merged_list`, compute `out = _merge_read_field_into_row(merged_list[i], src_item)` (see overview), and if `out` differs from `merged_list[i]`, replace and set `any_change`.
- Implement `_merge_read_field_into_row` (or split into `_coalesce_read` + apply) in `bootstrap.py` with the normative lattice in the task overview (required OR; then optional OR; else omit).
- **Validate** `read` on load or when merging: only `required` and `optional` are allowed as string values; reject `read` of wrong type or unknown string with `RuntimeError` and context.
- Preserve ordering: first occurrence order comes from cwd list, then appended new paths from src in src order (unchanged).
- Run existing unit tests locally; new failures only where expectations must change in step 2.

## Affected files
- `spectask_init/bootstrap.py`

## Code examples
```python
def _coalesce_read(cwd_read: str | None, src_read: str | None) -> str | None:
    """``None`` = key absent (default optional). Return ``required`` / ``optional`` / omit (None)."""
    if cwd_read == "required" or src_read == "required":
        return "required"
    if cwd_read == "optional" or src_read == "optional":
        return "optional"
    return None  # omit key in row
```

(Copy `cwd_row` to `out`, set or delete `out["read"]` from the coalesced result; do not take `description` from `src`.)
