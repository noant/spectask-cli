# 11: Integration tests for `--ide auto` and `--update` without `--ide`

IMPORTANT: always use `spec/main.md` and `spec/navigation.md` for rules.

## Status
- [x] Spec created
- [x] Self spec review passed
- [x] Spec review passed
- [x] Code implemented
- [x] Self code review passed
- [ ] Code review passed
- [x] HLA updated

## Goal
Add **integration** pytest coverage so `main()` exercises **`--ide auto`** end-to-end and **`--update`** with **no `--ide`** (default `auto`), closing gaps left after tasks 9 and 10.

## Design overview
- Affected modules: **`tests/test_integration_cli.py`** (primary); optionally tiny shared helpers or constants only if the file already uses a pattern that benefits from extraction — **prefer minimal diff**.
- Data flow changes: none for production code; tests call `main()` with the same **`TEMPLATE_ZIP`** URL and isolation pattern as existing integration cases (`chdir` to `tmp_path`, `@pytest.mark.integration`).
- Integration points: **network** fetch of the official template ZIP (same canonical URL as task 4 / existing tests); **no** new runtime dependencies.

## Before → After
### Before
- **`--ide auto`** and **`resolve_auto_ide_key`** are covered by **unit** tests only; **`main()`** is never run with `auto`.
- **`--update`** without **`--ide`** is covered in **`parse_args`** unit tests only; integration suite only runs **`--update` with explicit `--ide`**.

### After
- At least one integration test runs **`spectask-init --template-url <ZIP> --ide auto`** after preparing the temp CWD so **exactly one** IDE matches the template’s shipped **`.metadata/ide-detection.json`** (success path).
- At least one integration test asserts a **detection failure** when using **`--ide auto`** with the same ZIP and a CWD that matches **no** markers: process exits with **non-zero**, **stderr** mentions **`--ide all`** and lists **explicit IDE keys** (or the same phrasing as `spectask_init.bootstrap` today).
- At least one integration test runs **`--template-url <ZIP> --update` only**, with the same CWD marker setup as the success **`auto`** case, and asserts **`--skip-example` / `--skip-navigation-file`** outcomes (no example-only paths, no `spec/navigation.md`) **and** that IDE-specific files for the resolved IDE are present (same class of assertions as **`test_update_with_explicit_ide_skips_example_and_navigation`**).

## Details
- **Hermetic policy:** Keep using the existing **GitHub archive ZIP** constant in `tests/test_integration_cli.py` (do not change the canonical URL unless a separate maintenance task updates it everywhere). These tests stay **`@pytest.mark.integration`** and may hit the network, consistent with the rest of the file.
- **CWD markers:** Do **not** hardcode detection rules in production code; tests may create **directories or files under `tmp_path`** that satisfy the **current** upstream `ide-detection.json` in that ZIP. If upstream changes markers, **update the test fixture** (document this in a one-line comment near the test if helpful). A **`.cursor`** directory is the expected fixture for matching **Cursor** today; confirm against the fetched template’s detection file when implementing.
- **Failure assertions:** `main()` catches `RuntimeError` and prints `spectask-init: …` to **stderr** then **`sys.exit(1)`**. Use **`pytest.raises(SystemExit)`** with **`excinfo.value.code == 1`** (or project-consistent pattern) and **`capsys`** (or equivalent) to assert stderr contains the required user-facing fragments (**`--ide all`**, explicit key list / comma-separated names as implemented in **`spectask_init/bootstrap.py`**).
- **Scope limit:** Do **not** add new markdown docs, new CI workflows, or change **`README.md`** unless the user later asks; this task is **tests only**.
- **Language:** Test docstrings and any new comments in **English** per `spec/extend/conventions.md`.

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`). 
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if the step seems trivial or small.
- Phase 1 (sequential): step `1-integration-ide-auto-cli` → step `2-integration-update-default-ide`
