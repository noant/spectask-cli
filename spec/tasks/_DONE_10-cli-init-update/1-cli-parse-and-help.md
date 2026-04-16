# Step 1: CLI parse and help

## Goal
Implement `--update` in `spectask_init/cli.py` with the semantics in `overview.md`: set both skip flags, default `--ide` to `auto` when `--update` is used and `--ide` is omitted, keep explicit `--ide` when provided; adjust `--ide` requiredness accordingly.

## Approach
- Add `--update` (`store_true`) to the parser with English help matching the overview.
- Make `--ide` optional at argparse level (e.g. `nargs='+'`, `required=False`, `default=None`) and run post-parse validation: if `ide` is missing and `--update` is false, call `parser.error` with a clear message; if `ide` is missing and `--update` is true, set `ide` to `["auto"]`.
- Apply skip flags: `skip_example = ns.skip_example or ns.update`, `skip_navigation_file = ns.skip_navigation_file or ns.update` (or equivalent so explicit skips and `--update` both yield `True`).
- Preserve existing checks for `auto` / `all` combination after `ide` is resolved.
- Optionally align `README.md` only if it documents `spectask-init` flags and the project convention is to keep it in sync.

## Affected files
- `spectask_init/cli.py`
- `README.md` (optional, if it lists flags)

## Code examples

```python
# After parse_args(ns):
# if not ns.update and ns.ide is None:
#     p.error("--ide is required unless --update is set")
# if ns.update and ns.ide is None:
#     ns.ide = ["auto"]
```
