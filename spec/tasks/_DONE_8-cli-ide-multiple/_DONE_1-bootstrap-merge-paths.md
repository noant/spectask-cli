# 1: Bootstrap — merge paths for multiple IDE keys

## Goal
Resolve several IDE keys from `skills-map.json` into one ordered, de-duplicated list of template-relative paths for copying.

## Approach
- Extend or replace the single-key entry point so callers can pass a non-empty sequence of keys.
- For each key in order, reuse the same per-key lookup as today; append paths not yet seen (identical de-dupe policy as the `all` branch).
- Keep `all` as a single-key special case: when the sequence is exactly `("all",)`, behavior stays the same as current `ide == "all"`.
- If the sequence contains `all` and any other key, raise a clear `RuntimeError` before merging (CLI may pre-validate; bootstrap stays defensive).

## Affected files
- `spectask_init/bootstrap.py` — `ide_files_for` (or helper used by it), `run_template_bootstrap` signature `ide: str` → sequence type.

## Code examples (illustrative)
```python
def ide_files_for(skills: dict[str, Any], ide: str | Sequence[str]) -> list[str]:
    keys: tuple[str, ...] = (ide,) if isinstance(ide, str) else tuple(ide)
    if "all" in keys and len(keys) != 1:
        raise RuntimeError("When using 'all', it must be the only --ide value")
    if keys == ("all",):
        ...
 # else merge named keys left-to-right with seen-set
```
