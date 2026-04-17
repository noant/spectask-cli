# Step 2: Tests and documentation

## Goal
Align automated tests and user-facing docs with template navigation merge; ensure `--update` with existing navigation does not error on navigation overwrite.

## Approach
1. Update `tests/test_bootstrap_unit.py`: navigation preflight tests → merge/success expectations; combined preflight test → HLA-only refusal; valid YAML fixtures where merge must succeed.
2. Update `tests/test_integration_cli.py`: `test_init_refuses_overwrite_existing_navigation` → success + assertions on navigation; add or adjust coverage for update + existing navigation if missing.
3. Update `README.md` and `spec/design/hla.md` sections that claim navigation is always refused when present; document merge behavior and when `--skip-navigation-file` still applies.

## Affected files
- `tests/test_bootstrap_unit.py`
- `tests/test_integration_cli.py`
- `README.md`
- `spec/design/hla.md`

## Verification
- Full test suite passes locally (`pytest` or project-standard command).
