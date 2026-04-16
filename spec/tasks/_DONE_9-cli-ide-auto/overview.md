# 9: `--ide auto` via template `.metadata/ide-detection.json`

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
Support `--ide auto` so the tool picks a single IDE key using the marker rules shipped in the resolved template’s `.metadata/ide-detection.json` (markers combined with logical OR per IDE), and on failure emit a clear English error that points to `--ide all` and explicit IDE keys.

## Design overview
- Affected modules: `spectask_init/bootstrap.py` (load detection file, evaluate markers against the current working directory, resolve `auto` before `ide_files_for`), `spectask_init/cli.py` (accept `auto` in official-template choices, forbid combining `auto` with other tokens, extend help), tests under `tests/test_bootstrap_unit.py`, `tests/test_cli_parse.py`, and integration tests if needed.
- Data flow changes: after the template is acquired and `skills-map.json` is loaded, if `ide` is exactly `("auto",)`, replace it with one concrete name from `skills-map.json` using **`ide-detection.json` read from that same acquired tree** (no baked-in rules in the package). Otherwise pass `ide` through unchanged. Marker checks use paths relative to `Path.cwd()` (same semantics as `copy_into_cwd`).
- Integration points: official default template must ship `.metadata/ide-detection.json` with `name` values that match `ides[].name` in `skills-map.json` (upstream template repo change is out of scope for this repo unless the team also bumps the default URL content—implementation here only consumes the file if present).

## Before → After
### Before
- User must always pass explicit IDE key(s) or `all`; there is no way to derive the IDE from the current project layout.

### After
- User may pass `--ide auto` alone: the tool reads `.metadata/ide-detection.json`, applies OR semantics per IDE’s marker list against the CWD, and selects exactly one IDE when unambiguous.
- If detection fails (missing file, invalid JSON, no match, or ambiguous multiple matches), the process exits with an English `RuntimeError` (or CLI error where appropriate) that explains the situation and mentions `--ide all` plus the list of valid explicit IDE keys from `skills-map.json`.

## Details
- **Reserved token `auto`:** Like `all`, `auto` must be the only value after `--ide` (reject `--ide auto cursor`, `--ide all auto`, etc., with the same clarity as existing `all` combination errors).
- **Official template argparse:** Extend restricted choices to include `auto` (e.g. append after named keys, before `all`, or group in help text—match readability of existing help). Custom `--template-url` without restricted choices still allows `--ide auto`; behavior is defined only when the resolved template contains a valid detection file.
- **File location and schema:** `.metadata/ide-detection.json` at the template root (same layout as `skills-map.json`), read **at runtime** from the acquired template tree only. **Do not hardcode** marker paths, kinds, or IDE names for auto-detection in the CLI package; the upstream template may change, and the tool must follow whatever file ships with the resolved `--template-url`. Root is a JSON object. Required: an `ides` array of objects; each object has:
  - `name` (string): must match an `ides[].name` in the same template’s `skills-map.json` (if not, fail with a clear error referencing both files).
  - `markers` (array of objects): each object has `path` (string, relative to `Path.cwd()`) and `kind` (`"file"` or `"directory"`). **OR semantics:** the IDE matches if **any** marker matches: use `Path.is_file()` for `kind: "file"` and `Path.is_dir()` for `kind: "directory"` (so type must match, not merely `exists()`). Schema and semantics are fully specified in `1-bootstrap-ide-detection.md` (no duplicated JSON snapshot there either).
- **Selection rules:**
  - Collect every `ides[]` entry whose marker OR condition is satisfied.
  - **Zero matches:** error message must state that the IDE could not be detected, and must tell the user they can pass `--ide all` to install files for every IDE or pass a specific key. Include the list of explicit IDE names from `skills-map.json` (same names as today’s valid keys for that template).
  - **More than one match:** error message must state that detection is ambiguous, list the matched IDE names, and instruct the user to pass an explicit `--ide` (not `auto`).
  - **Exactly one match:** replace `auto` with that `name` and proceed with existing `ide_files_for` behavior for a single key.
- **Missing or invalid `ide-detection.json` when `--ide auto`:** Treat as a detection failure (or dedicated message that the template does not define auto-detection). Do not silently fall back; user must use explicit keys or `all`.
- **Order:** Evaluation order of `ides` entries follows array order in JSON only for deterministic error messages (e.g. listing ambiguous matches); it does not change OR semantics within one entry.
- **Conventions:** All new user-facing strings and spec-facing prose in English per `spec/extend/conventions.md`.
- **Integration tests:** The default template on `main` includes `.metadata/ide-detection.json`; integration tests may assert `--ide auto` against the published GitHub ZIP once network/hermetic policy allows. Unit tests with a synthetic `template_root` remain required for edge cases.

### Example (after implementation)
```text
spectask-init --ide auto
```

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`). 
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): step `_DONE_1-bootstrap-ide-detection` → step `_DONE_2-cli-help-and-tests`
