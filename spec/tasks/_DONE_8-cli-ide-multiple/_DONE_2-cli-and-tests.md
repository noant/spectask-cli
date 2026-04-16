# 2: CLI `nargs='+'` and tests

## Goal
Expose multiple IDE tokens on the command line via argparse `nargs='+'`, wire `CliOptions` and `main()` to bootstrap, and lock behavior in tests.

## Approach
- In `build_parser`, set `--ide` to `nargs="+"`, keep `choices` when the official template URL is used.
- Build `CliOptions.ide` as `tuple(ns.ide)` (or equivalent immutable sequence).
- Reject `all` combined with other keys at parse time with `argparse.ArgumentTypeError` or a post-parse check in `parse_args` for a clearer message (prefer user-facing consistency with bootstrap).
- Update `_ide_argument_help` to describe multiple keys (English only).
- Update `tests/test_cli_parse.py`, `tests/test_bootstrap_unit.py`, and integration tests as needed.

## Affected files
- `spectask_init/cli.py`
- `tests/test_cli_parse.py`
- `tests/test_integration_cli.py`
- `tests/test_bootstrap_unit.py` (if `ide_files_for` tests need new cases)

## Code examples (illustrative)
```python
p.add_argument("--ide", required=True, nargs="+", choices=ide_choices, help=ide_help)
# ...
return CliOptions(..., ide=tuple(ns.ide), ...)
```
