# Step 2: Tests

## Goal
Extend unit and integration tests so `--update` behavior is locked in and regressions on `--ide` requiredness are caught.

## Approach
- In `tests/test_cli_parse.py`, add cases for `--update` alone, `--update` with explicit `--ide`, and rejection when neither `--ide` nor `--update` is passed.
- In `tests/test_integration_cli.py` (or existing bootstrap integration patterns), add at least one path that exercises `--update` with the project’s template ZIP fixture if available, asserting skip behavior or file presence consistent with `--skip-example` and `--skip-navigation-file`.
- Keep tests hermetic where the suite already avoids network calls.

## Affected files
- `tests/test_cli_parse.py`
- `tests/test_integration_cli.py` (as needed)

## Code examples

```python
# parse_args(["--update"]) -> ide == ("auto",), skip_example and skip_navigation_file True
# parse_args(["--update", "--ide", "cursor"]) -> ide == ("cursor",), both skips True
# parse_args([]) or parse without ide/update -> SystemExit or parser.error
```
