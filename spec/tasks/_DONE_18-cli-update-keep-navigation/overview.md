# 18: CLI — `--update` no longer implies `--skip-navigation-file`

IMPORTANT: always use `spec/main.md` and `spec/navigation.yaml` for rules.

## Status
- [x] Spec created
- [x] Self spec review passed
- [x] Spec review passed
- [x] Code implemented
- [x] Self code review passed
- [x] Code review passed
- [x] HLA updated

## Goal
`--update` must still imply `--skip-example` and `--skip-hla-file`, but must **not** imply `--skip-navigation-file`, so the template `spec/navigation.yaml` is copied from the required list like a normal init when the file is absent and preflight allows it.

## Design overview
- Affected modules: `spectask_init/cli.py` (flag wiring and `--update` help text), `spectask_init/bootstrap.py` (preflight `RuntimeError` guidance for navigation/HLA), `tests/test_cli_parse.py`, `tests/test_integration_cli.py`, and short user-facing edits in `README.md` if needed.
- Data flow changes: with `--update` and no explicit `--skip-navigation-file`, `CliOptions.skip_navigation_file` becomes `False`; `run_template_bootstrap` still receives the flag; copying `NAVIGATION_FILE_RELPATH` from the required list for `--update` runs again whenever that path is not skipped and preflight passes.
- Integration points: `_preflight_required_navigation_and_hla` currently claims `--update` implies `--skip-navigation-file`; reword to match reality (e.g. `--update` implies `--skip-example` and `--skip-hla-file`; to keep an existing registry, pass `--skip-navigation-file` explicitly).

## Before → After
### Before
- `parse_args`: `skip_navigation_file = ns.skip_navigation_file or ns.update`.
- `--update` help: “Apply --skip-example, --skip-navigation-file, and --skip-hla-file”.
- Overwrite preflight hint: “Use --update (implies … --skip-navigation-file …)”.
- Integration tests for `--update` expect `spec/navigation.yaml` to be missing after the run.

### After
- `skip_navigation_file` comes only from `ns.skip_navigation_file` (no `or ns.update`); `skip_example` and `skip_hla_file` still combine with `ns.update`.
- Help and preflight copy describe only what `--update` actually implies.
- Tests: all `parse_args` cases with `--update` expect `skip_navigation_file is False` unless `--skip-navigation-file` is passed; integration tests expect a **copied** `spec/navigation.yaml` wherever the scenario previously asserted absence (no pre-existing `spec/navigation.yaml`, no other expected conflict).
- `test_update_quarantines_existing_navigation`: after `--update`, expect `spec/navigation.yaml` to **exist** (template registry); legacy `navigation.md` is still quarantined by migration; keep the rest of the test’s invariants.

## Details
- **Breaking change (intentional):** workflows that used `spectask-init --update` to refresh IDE files **without** touching `spec/navigation.yaml` must add `--skip-navigation-file` explicitly.
- `--update --skip-navigation-file` must keep today’s navigation behavior (registry copy skipped).
- **Preflight messages:** a single `update_hint` saying `--update` implies `--skip-navigation-file` is wrong. For a conflict on `spec/navigation.yaml` only, do not present `--update` alone as a way to avoid overwriting the registry without `--skip-navigation-file`. Reword hints (including both paths at once): HLA still supports `--skip-hla-file` and/or `--update`; navigation needs `--skip-navigation-file` (optionally with `--update` if the user also wants skip-example + skip-hla from `--update`).
- Align `spec/design/hla.md` (paragraph on `--update`) and the flag table in `README.md` during implementation (finalize HLA in process Step 7 after your code review).
- The `README.md` paragraph about refusing overwrites (“hint to use **`--update`** or …”): after the semantics change, ensure it does not imply that `--update` alone avoids overwriting `spec/navigation.yaml`.
- Implementation touchpoints: `spectask_init/cli.py` (`skip_navigation_file` and `--update` help), `spectask_init/bootstrap.py` (`_preflight_required_navigation_and_hla` logic/text), `tests/test_cli_parse.py` (`skip_navigation_file` asserts for `--update` variants), `tests/test_integration_cli.py` (`--update` scenarios and navigation quarantine), and if assertions change, overwrite tests such as `test_init_refuses_overwrite_existing_navigation`; adjust `README.md` if UX text drifts.

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`). 
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): step `_DONE_1-cli-bootstrap-and-tests` → step `_DONE_2-docs-hla`
