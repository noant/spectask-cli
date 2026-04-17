# 19: Merge template `spec/navigation.yaml` instead of preflight refusal

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
When `spec/navigation.yaml` already exists in the working directory, `spectask-init` must not fail preflight with “Refusing to overwrite”; it must merge registry rows from the template’s `spec/navigation.yaml` into the existing file (same path-dedup semantics as `--extend`), then continue bootstrap so `--update` and other flows work without `--skip-navigation-file`.

## Design overview
- Affected modules: `spectask_init/bootstrap.py` (`_preflight_required_navigation_and_hla`, `run_template_bootstrap`, new or shared merge helper), optionally `spectask_init/cli.py` only if error messages reference navigation overwrite; `tests/test_bootstrap_unit.py`, `tests/test_integration_cli.py`; user-facing text in `README.md` and `spec/design/hla.md` where they still say navigation is always refused when present.
- Data flow: preflight continues to block only **HLA** overwrite when `skip_hla_file` is false. For `spec/navigation.yaml`, if the path is in `required` and not skipped: when the file **does not** exist, copy from template as today; when it **does** exist, merge template navigation into cwd (no full-file replace from `copy_into_cwd`), then `apply_template_migration` → `reconcile_navigation_with_spec_tree` unchanged.
- Integration points: reuse `_load_yaml_document`, `_navigation_root_mapping`, `_parse_registry_section`, `_normalize_extend_registry_path`, `_write_navigation_yaml_atomic`; mirror list-merge logic from `merge_extend_source_navigation` for both `extend` and `design` keys. If cwd omits `extend` or `design`, treat that section as an empty list before appending template-only rows. Missing section in the template means nothing to merge for that section.

## Before → After
### Before
- `_preflight_required_navigation_and_hla` treats existing `spec/navigation.yaml` as a conflict and raises `RuntimeError` with “Refusing to overwrite…”, including when the user runs `--update` with a valid tree (navigation merge + reconcile already exist for `--extend`, but template install still refuses).

### After
- Existing `spec/navigation.yaml` is never a preflight conflict. Template bootstrap merges template `extend:` and `design:` entries into the cwd document by **appending** rows whose normalized `path` is not yet listed; if `path` already exists in cwd, **keep** the cwd row (description and extra keys unchanged). Top-level keys other than merged lists stay cwd-first: start from cwd’s parsed mapping, update only `extend` / `design` lists when merge appends rows. If merge adds nothing, avoid rewriting the file. `--skip-navigation-file` still skips both copy and merge (behavior unchanged). `reconcile_navigation_with_spec_tree` still runs at the end of `run_template_bootstrap`.

## Details

### Merge semantics (template source)
- **Sections:** Merge **`extend:`** and **`design:`** using the same rules as task 17’s **`extend:`** merge from an extend bundle (append new paths only; preserve cwd row on duplicate path after POSIX normalization). Unlike `--extend`, there is **no** “source lists design → warn and skip design” rule: the template may contribute **`design:`** rows because template bootstrap is allowed to install design files from `required`.
- **Source:** `template_root / spec / navigation.yaml`. If the template file is missing while `required` still lists it, keep current behavior (copy path would fail—no change expected).
- **Invalid cwd YAML:** Loading or validating cwd navigation fails with **`RuntimeError`** and a clear message (same class of failure as today for bad registry files).
- **Empty lists:** Valid; merging from a template with empty `extend` is a no-op for that section.

### Preflight and combined conflicts
- **`_preflight_required_navigation_and_hla`:** Remove navigation from the conflict set. **Only** `spec/design/hla.md` when `not skip_hla_file` and file exists. When both old navigation and HLA existed, the user previously saw one error listing both paths; **after:** only HLA triggers refusal (message must not imply navigation must be skipped for that scenario). Adjust the multi-path error string so it only mentions HLA/`--skip-hla-file`/`--update` as appropriate.

### Tests
- Replace or repurpose `test_preflight_existing_navigation_refuses`: bootstrap **succeeds**; assert merged content (e.g. cwd-only row kept + template-only row appended). Use **valid** minimal YAML for cwd navigation (a line like `# existing` alone is not a mapping and is unsuitable).
- Update `test_preflight_both_existing_refuses_once`: expect failure **only** from HLA; navigation merge proceeds if HLA conflict is resolved—or split into separate cases per implementer preference.
- Update `test_init_refuses_overwrite_existing_navigation`: expect **success** (exit 0) and merged or preserved+augmented `spec/navigation.yaml` with valid starting YAML.
- Keep `test_preflight_skip_navigation_allows_existing_navigation` behavior: skip flag still leaves navigation bytes unchanged.
- Add or extend a focused test that simulates **`--update`** with pre-existing valid `spec/navigation.yaml` and asserts no “Refusing… navigation” error (integration or unit, whichever stays fastest and clearest).

### Documentation
- **`README.md` / `spec/design/hla.md`:** Replace statements that say a normal run **always** refuses when `spec/navigation.yaml` exists; describe **merge** + when `--skip-navigation-file` is still needed (user wants zero edits from template).

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`). 
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): step `_DONE_1-bootstrap-template-navigation-merge` → step `_DONE_2-tests-and-docs`
