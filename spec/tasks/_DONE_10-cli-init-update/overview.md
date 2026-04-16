# 10: `spectask-init --update` (skip example + skip navigation + IDE auto by default)

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
Add a `--update` flag that applies the same outcome as `--skip-example`, `--skip-navigation-file`, and `--ide auto` together, while still accepting every other existing CLI option and using an explicit `--ide` value when the user provides one.

## Design overview
- Affected modules: `spectask_init/cli.py` (`argparse`, validation order, `CliOptions` resolution), tests in `tests/test_cli_parse.py` and `tests/test_integration_cli.py` as needed; optional short mention in `README.md` if user-facing examples are maintained there.
- Data flow changes: after parsing, resolved options passed to `run_template_bootstrap` / `run_extend` match today’s fields (`skip_example`, `skip_navigation_file`, `ide` tuple). No new bootstrap parameters unless a reason appears during implementation.
- Integration points: existing `--ide auto` resolution and `all` / `auto` combination rules in `parse_args` remain authoritative once `ide` is resolved; `--update` only influences defaults and the two skip flags as specified below.

## Before → After
### Before
- Users who want a minimal refresh (no example paths, no `spec/navigation.md` copy, IDE from detection) must pass three separate flags plus remember `--ide auto`.

### After
- `spectask-init --update` (with no `--ide`) behaves like `--skip-example --skip-navigation-file --ide auto`.
- `spectask-init --update --ide cursor` (or any explicit IDE list) behaves like `--skip-example --skip-navigation-file` with the given `--ide` values (not forced to `auto`).
- All other options (`--template-url`, `--template-branch`, `--extend`, `--extend-branch`, etc.) combine unchanged.

## Details
- **Semantics of `--update`:**
  - Sets `skip_example=True` and `skip_navigation_file=True` for the resolved `CliOptions`.
  - If `--ide` is **absent** from the argv for this invocation, treat IDE as `auto` (single token), i.e. resolved `ide` tuple is `("auto",)` and all existing `auto` rules apply (including template `ide-detection.json`, errors, and “`auto` cannot be combined with other `--ide` values” after resolution).
  - If `--ide` is **present**, use the parsed `--ide` list exactly as today; do not inject `auto`.
- **Compatibility with explicit flags:**
  - `--update` together with `--skip-example` and/or `--skip-navigation-file` is valid; skip flags stay `True` (idempotent).
  - **Precedence:** `--update` always turns both skip flags on. There is no `--no-skip-example` / `--no-skip-navigation-file` in the CLI today, so users cannot request “`--update` but still copy example paths” without a future negating option (out of scope unless explicitly added later).
- **`--ide` requiredness:**
  - Today `--ide` is required. After the change: require `--ide` **unless** `--update` is set; when `--update` is set and `--ide` is omitted, default IDE to `auto` as above. Invocations with neither `--ide` nor `--update` must fail with a clear error (same class of message as today’s missing required argument).
- **Help text:** Document `--update` in English per `spec/extend/conventions.md`: one line describing the combined defaults and that explicit `--ide` overrides the `auto` default.
- **Tests:** Cover at least: (1) `--update` alone → skips on, `ide==("auto",)`; (2) `--update --ide cursor` → skips on, `ide==("cursor",)`; (3) neither `--ide` nor `--update` → error; (4) `--update` with `all` / multiple IDEs / `auto` explicitly — behavior matches current validation for those tokens; (5) optional integration smoke: `--update` against existing test template ZIP if the suite already has a suitable fixture pattern.

### Example (after implementation)
```text
spectask-init --update
spectask-init --update --ide cursor
spectask-init --update --template-url https://example.com/template.zip --ide all
```

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`). 
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): step `1-cli-parse-and-help` → step `2-tests`
