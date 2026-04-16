# Step 1: CLI, bootstrap preflight copy, tests

## Goal
Change `--update` so it does not imply `--skip-navigation-file`; refresh preflight error text and automated tests.

## Approach
- In `spectask_init/cli.py`: stop OR-ing `ns.update` into `skip_navigation_file`; update `--update` help to keep `--skip-example` and `--skip-hla-file`, and remove any claim about navigation.
- In `spectask_init/bootstrap.py`: rewrite `_preflight_required_navigation_and_hla` messages so they never say `--update` avoids copying `spec/navigation.yaml` by itself. For navigation conflicts, the primary fix is `--skip-navigation-file` (optionally with `--update` if the user also wants `--skip-example` and `--skip-hla-file` from `--update`). For HLA, keep valid `--skip-hla-file` and/or `--update`. When both paths conflict, use a consistent flag combination (see overview **Details**).
- In `tests/test_cli_parse.py`: for all `--update` tests, expect `skip_navigation_file is False` unless `--skip-navigation-file` is passed; rename tests if names still imply navigation is always skipped.
- In `tests/test_integration_cli.py`: wherever `--update` previously implied no `spec/navigation.yaml`, assert the template file is present; in `test_update_quarantines_existing_navigation`, assert `spec/navigation.yaml` exists after success; rename `*_skips_*_navigation*` tests if the name is misleading.

## Affected files
- `spectask_init/cli.py`
- `spectask_init/bootstrap.py`
- `tests/test_cli_parse.py`
- `tests/test_integration_cli.py`

## Code examples
```python
# cli.py — before:
skip_navigation_file = ns.skip_navigation_file or ns.update
# after:
skip_navigation_file = ns.skip_navigation_file
```

```text
# bootstrap.py — replace a single update_hint with correct guidance per conflicting path
# (navigation vs HLA vs both), without claiming --update alone skips navigation.
```
