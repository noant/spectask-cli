# 15: Refuse `init` when `spec/navigation.md` or `spec/design/hla.md` already exists

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
When template bootstrap would copy `spec/navigation.md` or `spec/design/hla.md` from `required-list.json`, abort with a clear error if that destination already exists in the working directory (unless the matching skip flag is set), and tell the user to use `--update` or `--skip-navigation-file` / `--skip-hla-file`.

## Design overview
- Affected modules: `spectask_init/bootstrap.py` (`run_template_bootstrap`, optionally a small helper); `tests/test_bootstrap_unit.py`; `tests/test_integration_cli.py` (if an end-to-end scenario fits existing patterns); `README.md` only if user-facing behavior is documented there and needs a one-line note.
- Data flow changes: after the template root is acquired and before any `copy_into_cwd` from `required-list.json`, for each required `rel` that is exactly `spec/navigation.md` or `spec/design/hla.md`, if that entry is not skipped by the corresponding flag and `(Path.cwd() / rel).exists()`, raise `RuntimeError` with an actionable message. This stays aligned with `required-list.json` if its contents change upstream. Existing `main()` error handling continues to print `spectask-init: …` and exit with code 1.
- Integration points: `--update` already sets both skip flags, so it remains the documented merge path and must not hit this error for those two files. `--extend` runs after template bootstrap; this guard applies only to the two required spec files from the template step.

## Before → After
### Before
- `spectask-init` overwrites `spec/navigation.md` and `spec/design/hla.md` via `shutil.copy2` when they are present, with no warning.

### After
- If the bootstrap would copy `spec/navigation.md` and that path already exists in the CWD, fail before copying.
- If the bootstrap would copy `spec/design/hla.md` and that path already exists in the CWD, fail before copying.
- Error text (English, stderr via existing wrapper) must mention `--update` and, per conflict, `--skip-navigation-file` and/or `--skip-hla-file` so users know how to proceed.

## Details

**Existence rule**

- Only for required-list entries `rel == "spec/navigation.md"` (and not `skip_navigation_file`) or `rel == "spec/design/hla.md"` (and not `skip_hla_file`): if `(Path.cwd() / rel).exists()`, abort. Use `Path.exists()` (same as “would collide with copy” for normal template layouts where these are files).

**Preflight timing**

- Run the check immediately after loading `required-list.json` (or before the first `copy_into_cwd` in the required loop) so no partial required-list copies occur when the run is going to fail.

**Error message**

- Single file conflict: name the path and list `--update` plus the one relevant `--skip-*` flag.
- Both paths conflict in one run: one error listing both paths and mentioning `--update` plus both skip flags (avoid two separate failures when both apply).
- Wording should align with help text: `--update` implies skipping example list and skipping both spec files (per current `parse_args`); keep that implication explicit in the message so users understand why `--update` avoids the overwrite.

**Tests**

- **Unit** (`test_bootstrap_unit.py`): temporary CWD with a pre-created `spec/navigation.md` (and/or `spec/design/hla.md`), call `run_template_bootstrap` with `skip_*` false → expect `RuntimeError` whose message includes `spec/navigation.md` or `spec/design/hla.md` and mentions `--update` and the right `--skip-*`. With `skip_navigation_file=True` and an existing navigation file, required bootstrap for that path must not raise for navigation; same for HLA with `skip_hla_file=True`. Case where both files exist and both would be copied: assert one exception listing both paths (or two paths in message).
- **Integration** (optional but preferred if the suite already spins up subprocess / tmp CWD): mirror one scenario end-to-end with non-zero exit and stderr substring.

**Out of scope**

- Changing behavior for other required-list paths or IDE file copies.
- Russian CLI messages; the tool’s CLI and errors stay English unless a separate task standardizes localization.

**Open questions (resolved defaults)**

- None; defaults above are sufficient for implementation.
