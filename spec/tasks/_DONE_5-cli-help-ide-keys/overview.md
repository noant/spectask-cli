# 5: CLI help lists official IDE keys (hardcoded)

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
Ensure `spectask-init --help` always shows the concrete `--ide` values that match the official default template repository (`https://github.com/noant/spectask.git`), using a hardcoded list derived from that template’s `.metadata/skills-map.json` (no runtime fetch).

## Design overview
- Affected modules: `spectask_init/cli.py` (argparse `--ide` help, choice list source); optionally a small constant module or `bootstrap.py` if we centralize the list; `tests/test_cli_parse.py` if help/choices behavior is asserted.
- Data flow changes: none beyond build-time string constants; parsing still validates `--ide` against template `skills-map.json` at bootstrap time.
- Integration points: official Spectask repo `main` branch `skills-map.json` is the **source of truth** for the hardcoded list; when upstream adds/renames IDE keys, this repo must be updated in lockstep (documented in Details).

## Before → After
### Before
- `--ide` help may reference a dynamic or missing helper (`default_template_ide_names` is imported in `cli.py` but not defined in `bootstrap.py`, so the package may fail to import).
- For non-default `--template-url`, help text can be vague about which keys are “usual”.

### After
- A single authoritative tuple/list in code documents IDE keys: `cursor`, `claude-code`, `qwen-code`, `qoder`, `windsurf`, plus the literal `all` for argparse choices when `--template-url` is the default (unchanged choice behavior).
- Help text explicitly lists these keys (and mentions `all`) so users see valid values without opening the template.
- Import/runtime error from the missing `default_template_ide_names` is removed.

## Details
**Hardcoded keys (from `noant/spectask` `main` as of spec authoring):** `cursor`, `claude-code`, `qwen-code`, `qoder`, `windsurf`. Append `all` for CLI choices only (not a `name` in JSON).

**Scope boundaries:**
- Do **not** fetch the template at CLI import or `--help` time; hardcode only.
- Custom `--template-url`: keep current behavior — `--ide` is free-form (metavar) and validated when the template is acquired; help should still **show** the same official key list as documentation, with a short note that custom templates may define different `ides[].name` values in their `skills-map.json`.

**Implementation notes:**
- Prefer one module-level constant (e.g. `OFFICIAL_TEMPLATE_IDE_KEYS` or `DEFAULT_TEMPLATE_IDE_KEYS`) next to `DEFAULT_TEMPLATE_URL` in `cli.py`, or in `bootstrap.py` if we want reuse — minimal surface.
- Replace `default_template_ide_names()` usage with that constant; delete the broken import.
- Optional: add a unit test that default-template `parse_args` accepts each hardcoded key (or that choices match the constant) to prevent drift without network.

**Maintenance:** If `https://github.com/noant/spectask` changes `skills-map.json`, update the constant and any tests in the same change.
