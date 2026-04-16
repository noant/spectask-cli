# 13: `--ide auto` merges all matched IDEs

IMPORTANT: always use `spec/main.md` and `spec/navigation.md` for rules.

## Status
- [x] Spec created
- [x] Self spec review passed
- [ ] Spec review passed
- [x] Code implemented
- [x] Self code review passed
- [ ] Code review passed
- [x] HLA updated

## Goal
When `--ide auto` is used and more than one IDE entry in `.metadata/ide-detection.json` matches the current working directory, resolve `auto` to **all** matching IDE keys and copy the merged path list (same merge semantics as explicit multi-key `--ide`), instead of failing with an ambiguous-detection error.

## Design overview
- Affected modules: `spectask_init/bootstrap.py` (`resolve_auto_ide_key` or successor, `run_template_bootstrap`), `spectask_init/cli.py` (`_ide_argument_help` and any prose that claims `auto` picks exactly one IDE), `tests/test_bootstrap_unit.py` (replace ambiguous expectation with multi-match merge test), any tests or docs that assert the old ambiguous `RuntimeError`.
- Data flow changes: after acquiring the template, when `ide == ("auto",)`, compute the ordered list of IDE `name` values whose marker OR-condition matches `Path.cwd()`, using the same rules as today (`file` / `directory`, paths relative to CWD). If the list is empty, keep the current error. If it has one or more entries, pass that sequence into `ide_files_for` (same as `--ide k1 k2 ...`): merged paths, deduplicated in key order, no duplicate paths.
- Integration points: official template’s `ide-detection.json` and `skills-map.json` unchanged; behavior is fully driven by those files. Task 9’s “ambiguous → error” rule is **superseded** by this task for multi-match cases only.

## Before → After
### Before
- Two or more IDE entries match → `RuntimeError` (“IDE detection is ambiguous… Pass an explicit --ide value…”).

### After
- Two or more IDE entries match → treat as `--ide <name1> <name2> ...` where the order of names follows the **order of matching entries** in `ide-detection.json` `ides[]` (iterate the array in file order; append each matching entry’s `name`). Then reuse existing multi-key merge in `ide_files_for`.
- Exactly one match → unchanged (behavior equivalent to today’s single resolved key).
- Zero matches → unchanged error text and guidance (`--ide all`, explicit keys).

## Details
- **Backward compatibility:** This is a **behavior change** for users who previously hit the ambiguous error when both Cursor and Claude Code markers were present; they now get a merged install without passing explicit `--ide`. No new CLI flag.
- **Duplicate `name` in `ides[]`:** If the detection file contains multiple entries with the same `name` and more than one matches, the resolved key sequence may repeat the same name; `ide_files_for` already supports repeated keys (merge semantics / de-duplication per task 8 tests).
- **Naming:** Prefer renaming `resolve_auto_ide_key` to `resolve_auto_ide_keys` returning `tuple[str, ...]` with length ≥ 1 on success, or an equivalent clear API; update all imports and tests. Avoid returning a single `str` for multi-match to keep call sites obvious.
- **User-facing English:** Update CLI help so `auto` is described as resolving to one or more IDE keys from the template’s detection rules and merging their file lists when several environments match (not “selects one IDE”).
- **Project docs:** Update `README.md` (`--ide` / `auto` description) during implementation. During Step 7, update `spec/design/hla.md` where it states that `auto` resolves to a **single** IDE name; align with multi-key resolution.
- **Conventions:** English only for strings and spec prose per `spec/extend/conventions.md`.

### Example (after implementation)
```text
spectask-init --ide auto
```
When both Cursor and Claude Code markers exist under CWD, copies the union of template paths for those IDEs in detection-file order, without requiring `--ide cursor claude-code`.
