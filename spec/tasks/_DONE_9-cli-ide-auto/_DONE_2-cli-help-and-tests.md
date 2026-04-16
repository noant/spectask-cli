# 2: CLI — `auto` token, validation, help, integration tests

## Goal
Expose `--ide auto` on the CLI consistently with `all`, update help text, and cover end-to-end behavior in tests.

## Approach
- **`spectask_init/cli.py`:**
  - Include `auto` in official-template `choices` alongside existing keys and `all` (exact ordering should keep help readable).
  - After parse, reject any combination where `auto` appears with more than one `--ide` token, or with `all`, mirroring the `all` + other keys guard.
  - Extend `_ide_argument_help` to document `auto`: resolves IDE from the **template’s** `.metadata/ide-detection.json` (loaded at runtime) using markers against the current directory; must be used alone; do **not** hardcode upstream marker paths or IDE names in help—describe the mechanism only.
- **Tests:**
  - `tests/test_cli_parse.py`: `auto` alone accepted on default template; `auto` + another key rejected; `auto` + `all` rejected; custom URL still accepts `--ide auto` at parse time (detection may fail later in bootstrap).
  - `tests/test_integration_cli.py` (or new cases): with a fixture template (ZIP or existing test harness), assert successful `auto` when CWD has markers for one IDE; assert failure messages mention `--ide all` and list explicit keys when unresolvable.

## Affected files
- `spectask_init/cli.py`
- `tests/test_cli_parse.py`
- `tests/test_integration_cli.py` (or whichever integration module hosts template ZIP tests)

## Notes
- User-facing errors from `parse_args` vs `run_template_bootstrap` should stay consistent with existing patterns (`parser.error` vs `RuntimeError` caught in `main`).
