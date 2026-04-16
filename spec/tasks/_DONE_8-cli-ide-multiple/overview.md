# 8: Multiple `--ide` values (argparse)

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
Allow passing more than one IDE key in a single run using the standard argparse multi-value form (`nargs='+'`), and copy the union of the corresponding template paths with stable de-duplication.

## Design overview
- Affected modules: `spectask_init/cli.py` (`CliOptions`, `build_parser`, `parse_args`, `main`), `spectask_init/bootstrap.py` (`ide_files_for`, `run_template_bootstrap`), tests under `tests/` that assert `CliOptions.ide` shape and bootstrap behavior.
- Data flow changes: parsed `--ide` becomes an ordered sequence of keys; bootstrap resolves each key against `.metadata/skills-map.json` and copies the ordered union of relative paths (same de-duplication semantics as the existing `all` branch: first occurrence wins, no duplicates).
- Integration points: official template still restricts keys to `OFFICIAL_TEMPLATE_IDE_KEYS` plus `all`; custom `--template-url` still allows any key present in that template’s `skills-map.json`.

## Before → After
### Before
- `--ide` accepts exactly one token; selecting several IDEs requires re-running the tool or using `all`.

### After
- `--ide` accepts one or more tokens: `spectask-init --ide cursor windsurf` (space-separated after the flag, argparse `nargs='+'`).
- Semantics for multiple named keys: union of path lists with de-duplication (order: process keys left to right; within each key, keep template order; skip paths already seen).
- `all` remains valid only as a **single** `--ide` value: if `all` appears, it must be the only token (reject e.g. `--ide all cursor` with a clear error). That preserves today’s meaning of `all` without defining ambiguous mixing with explicit keys.

## Details
- **CLI surface:** `p.add_argument("--ide", ..., nargs="+", ...)` with `required=True` (argparse still requires at least one value). With `choices`, argparse validates each token.
- **`CliOptions`:** replace `ide: str` with a sequence type suitable for a frozen dataclass, e.g. `ide: tuple[str, ...]`, built from `ns.ide` (already a list when using `nargs='+'`).
- **Help text:** update `_ide_argument_help` and any epilog if needed so English prose states that multiple IDE keys may be passed after `--ide` and that files are merged without duplicates. Follow `spec/extend/conventions.md` (English only).
- **`ide_files_for`:** either accept `str | Sequence[str]` or add a small helper that maps a non-empty sequence of keys to the merged path list; keep the existing `all` and single-key behavior internally consistent. Reject an empty sequence at the CLI layer (nargs `+` prevents zero values).
- **Validation (custom template):** for each key in the sequence, the key must exist in `skills-map.json` (same rule as today for a single key); fail on the first unknown key with the existing error style.
- **Tests:** extend `tests/test_cli_parse.py` for `nargs='+'` (multiple official keys, duplicate keys on the command line — de-duplicated path union), `all` alone still works, mixed `all` + key fails; extend `tests/test_bootstrap_unit.py` / integration tests if needed so merged IDE lists match expectations.

### Example (after implementation)
```text
spectask-init --template-url https://example.com/t.zip --ide cursor windsurf
```

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`). 
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): `_DONE_1-bootstrap-merge-paths` → `_DONE_2-cli-and-tests`
