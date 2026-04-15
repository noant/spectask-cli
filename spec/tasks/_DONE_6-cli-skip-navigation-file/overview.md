# 6: CLI flag `--skip-navigation-file`

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
Add an optional `--skip-navigation-file` flag so template bootstrap does not copy `spec/navigation.md` from the template.

## Design overview
- Affected modules: `spectask_init/cli.py` (argparse, `CliOptions`, `parse_args`, `main`); `spectask_init/bootstrap.py` (`run_template_bootstrap`); `tests/test_integration_cli.py` (and `tests/test_cli_parse.py` if present and used for new flags).
- Data flow changes: when the flag is set, the iteration over `required-list.json`’s `required` paths skips the entry whose relative path is exactly `spec/navigation.md` (same string form as in the JSON); all other required paths copy unchanged. The flag is not passed to `run_extend` (extend overlay only copies `spec/extend/**`).
- Integration points: official template’s `.metadata/required-list.json` includes `spec/navigation.md`; behavior must stay identical when the flag is omitted.

## Before → After
### Before
- `spectask-init` always copies every path listed in `required-list.json`, including `spec/navigation.md`.
- Users merging into a repo that already defines `spec/navigation.md` must accept an overwrite or avoid bootstrap.

### After
- With `--skip-navigation-file`, template bootstrap omits copying `spec/navigation.md`; default run still copies it.
- Help text documents the flag clearly (mirror tone of `--skip-example`).

## Details
**CLI**
- Add `--skip-navigation-file` with `action="store_true"`.
- Extend `CliOptions` with `skip_navigation_file: bool`.
- Wire `main()` → `run_template_bootstrap(..., skip_navigation_file=opts.skip_navigation_file)`.

**Bootstrap**
- Extend `run_template_bootstrap` signature with `skip_navigation_file: bool = False` (or keyword-only, default `False`).
- In the `required` copy loop, before `copy_into_cwd`, if `skip_navigation_file` and `rel == "spec/navigation.md"`, `continue`.
- Do not skip any other path; do not special-case `example-list.json` or IDE paths.

**Semantics / scope**
- Only affects the template step. `--extend` does not install `navigation.md` today; no change there.
- If the target directory has no `spec/navigation.md` and the user passes the flag, the working tree may not satisfy Spectask’s usual “full spec tree” rules — that is an intentional advanced / merge use case; the flag help can note that the file is normally required by the methodology.

**Tests**
- Add an integration test: same template source as existing ZIP tests, `--ide cursor`, plus `--skip-navigation-file`, then assert `spec/navigation.md` is **not** present while another required artifact still is (e.g. `spec/main.md` or `spec/design/hla.md` — pick one stable path from `required-list` that is not navigation).
- Optionally extend unit coverage if the project already tests `CliOptions` / `parse_args` for boolean flags.

**Implementation sketch**

```python
# In run_template_bootstrap, inside the `for rel in required:` loop
if skip_navigation_file and rel == "spec/navigation.md":
    continue
copy_into_cwd(template_root, rel)
```

**Open questions:** none — path to skip is fixed to `spec/navigation.md` as in the official template’s `required-list.json`.
