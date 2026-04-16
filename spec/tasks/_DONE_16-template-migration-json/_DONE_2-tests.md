# 2: Tests for migration.json behavior

## Goal
Cover migration validation, ordering (moves before deletes), quarantine behavior, missing-path no-ops, and unsafe path rejection.

## Approach
1. Extend `tests/test_bootstrap_unit.py` with tests that build a temporary cwd and template_root layout, calling the new migration entrypoint or `run_template_bootstrap` with a local template URL if the harness allows; otherwise test internal helpers if they must be exposed for testing (prefer testing through public `run_template_bootstrap` with a `file://` ZIP or temp git-less template per existing `acquire` tests).
2. Capture stderr where warnings are required (subprocess or `capsys`/`capfd` as fits the suite).
3. Keep tests hermetic: no network unless an existing integration pattern already uses it.

## Affected files
- `tests/test_bootstrap_unit.py`
- `tests/test_integration_cli.py` (only if a small integration adds real value)
- `tests/conftest.py` (only if shared fixtures are genuinely reused)

## Constraints
- Follow existing pytest style and temp directory fixtures in the repo.
- User-facing assertions only on stable English substrings agreed in the implementation (avoid overfitting full multiline messages—check key phrases).
