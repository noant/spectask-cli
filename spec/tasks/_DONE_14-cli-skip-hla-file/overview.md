# 14: CLI flag `--skip-hla-file` and `--update` integration

IMPORTANT: always use `spec/main.md` and `spec/navigation.md` for rules.

## Status
- [x] Spec created
- [x] Self spec review passed
- [x] Spec review passed
- [x] Code implemented
- [x] Self code review passed
- [x] Code review passed
- [x] HLA updated

## Goal
Add `--skip-hla-file` so template bootstrap can omit copying `spec/design/hla.md`, and include that behavior in `--update` the same way as `--skip-navigation-file`.

## Design overview
- Affected modules: `spectask_init/cli.py` (`CliOptions`, parser, `parse_args`, `--update` help); `spectask_init/bootstrap.py` (`run_template_bootstrap`); `tests/test_cli_parse.py`; `tests/test_integration_cli.py`; `README.md` (flag table and `--update` line).
- Data flow changes: a new boolean flows from CLI into `run_template_bootstrap`. In the `required-list.json` copy loop, when the flag is set, skip the entry whose relative path is exactly `spec/design/hla.md` (same string form as in JSON). `--update` sets this flag on together with the existing skip flags (OR semantics, idempotent with an explicit `--skip-hla-file`).
- Integration points: official template `required-list` includes `spec/design/hla.md`; default runs stay unchanged when the new flag is omitted and `--update` is not used.

## Before → After
### Before
- There is no way to skip copying `spec/design/hla.md` from the template except not running bootstrap.
- `--update` applies `--skip-example` and `--skip-navigation-file` only.

### After
- `--skip-hla-file` omits copying `spec/design/hla.md` from `required` paths.
- `--update` also implies `--skip-hla-file` (in addition to the two existing skips). Help text for `--update` lists all three implied flags.

## Details
**CLI**
- Add `--skip-hla-file` with `action="store_true"`. Help: mirror `--skip-navigation-file` tone — advanced / merge use case; a normal Spectask tree usually keeps HLA in `spec/design/hla.md`.
- Extend `CliOptions` with `skip_hla_file: bool`.
- Resolution: `skip_hla_file = ns.skip_hla_file or ns.update` (same pattern as `skip_navigation_file`).
- Update `--update` help to say it applies `--skip-example`, `--skip-navigation-file`, and `--skip-hla-file`.

**Bootstrap**
- Extend `run_template_bootstrap` with keyword-only `skip_hla_file: bool`.
- In the `for rel in required:` loop, if `skip_hla_file and rel == "spec/design/hla.md"`, `continue` before `copy_into_cwd`.
- Do not skip other paths; no change to example-list or IDE file merging.

**Semantics**
- Only the template step; `--extend` does not touch `hla.md` today — no change there.
- Skipping HLA can leave a tree that does not match `spec/main.md`’s usual “full spec” expectations — intentional, like `--skip-navigation-file`.

**Tests**
- **Unit (`test_cli_parse.py`):** default `skip_hla_file` is False; `--skip-hla-file` alone sets True; `--update` alone and `--update --ide …` set True; `--update` with `--skip-hla-file` remains True (idempotence); adjust any test that assumes only two skip fields if options are asserted wholesale.
- **Integration (`test_integration_cli.py`):** add a test analogous to `test_skip_navigation_file_omits_navigation`: e.g. `--skip-hla-file`, assert `spec/design/hla.md` is absent and a different required file (e.g. `spec/main.md` or `spec/navigation.md`) is still present. Extend `test_update_with_explicit_ide_skips_example_and_navigation` and `test_update_only_zip_defaults_ide_auto` (and any other `--update` test that asserts baseline layout) to assert `spec/design/hla.md` is **absent** as well, and align shared helpers like `_assert_baseline` if they currently assume `hla.md` always exists after bootstrap.

**Implementation sketch (bootstrap loop)**

```python
if skip_navigation_file and rel == "spec/navigation.md":
    continue
if skip_hla_file and rel == "spec/design/hla.md":
    continue
copy_into_cwd(template_root, rel)
```

**Open questions:** none — skipped path is fixed to `spec/design/hla.md` as in the official template’s `required-list.json`.
