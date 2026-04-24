# 20: `navigation.yaml` merge respects `read` (upstream)

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
When merging `spec/navigation.yaml` from the template or from `--extend`, merge the per-row `read` key so **`read: required` remains in the result if either the project or the source has it**, and **explicit `read: optional` is preserved when at least one side has it and neither is `required`**, per [noant/spectask](https://github.com/noant/spectask) `spec/main.md` and `spec/navigation.yaml` comments; new rows still append as a full copy from the source.

## Design overview
- Affected modules: `spectask_init/bootstrap.py` — `_merge_navigation_registry_sections_from_src` (and any small helper for row-level merge); `tests/test_navigation_merge.py`, `tests/test_bootstrap_unit.py` for template/extend merge cases; `spec/design/hla.md` (and any user-facing help text that describes merge semantics) in the docs step.
- Data flow: unchanged entry points (`merge_template_source_navigation`, `merge_extend_source_navigation`); only the in-memory merge of `extend:` / `design:` list rows changes for duplicate `path` values. `reconcile_navigation_with_spec_tree` already retains full row dicts for existing files; auto-appended placeholder rows stay `{ path, description }` without a `read` key unless a future spec adds defaults.
- Integration points: PyYAML load/dump and atomic write are unchanged; validation continues to require non-empty `path` per row; optional keys beyond `path` / `description` / `read` stay untouched by merge (still deep-copied on append from source).

## Before → After
### Before
- On normalized duplicate `path`, the cwd row is kept verbatim and the source row is ignored, so a cwd row that predates `read` never gains `read: required` from a newer template or extend bundle, and a cwd row that already has `read: required` is never downgraded if the source only has `read: optional`.
### After
- Duplicates: **base row** = deep copy of the cwd row for `path`, `description`, and any other keys except `read`. Then **merge only the `read` key** by the rules below. **New paths:** unchanged — append a deep copy of the source row (full row including `read`).

## Details

### Upstream field (source of truth: [noant/spectask `spec/main.md`](https://github.com/noant/spectask/blob/main/spec/main.md))
- `spec/navigation.yaml` list entries may set `read` to `required` or `optional` (omitting `read` means default **optional**). Upstream **Embedded rules** 4–5 define agent reading order; this task only defines **how `read` is merged** when the template or `--extend` is applied.
- **Validation:** If `read` is present, it must be the string `required` or the string `optional` (no other values). **RuntimeError** with `nav_file` / row index context on parse/merge, consistent with other registry validation.

### Merge algorithm for `read` (normative)
Apply **only** on duplicate normalized `path` (same section `extend` or `design`); do not change `description` or other non-`read` fields from the cwd row; update only the `read` key (set `read`, or remove it when the coalesced result is default-optional / omit-key).

1. **Required wins (symmetric, source-agnostic).** If **either** the cwd row or the source row has `read: required`, the merged row **must** have `read: required` — it does not matter whether `required` came from the project, the template, or the extend bundle.
2. **Otherwise (neither side is `required`).** If **either** side has `read: optional` (explicit), the merged row **must** have `read: optional` — an explicit `optional` on one side must not be lost when the other side omits `read` (default optional).
3. **Otherwise** (both sides omit `read` or an equivalent “default optional”), the merged row **omits** the `read` key (default optional, minimal YAML).
4. All non-`read` fields on the merged row for that path still come from the **cwd** row (description, extra keys) except the above updates to the `read` key.

- Invoke this merge when `nk in seen` instead of discarding the source row with no `read` update. If the merged row differs from the previous `merged_list[i]`, mark `any_change` and replace at that index.
- **Version key:** `version` and other top-level keys remain cwd-first; do not overwrite top-level `version` from the source during navigation merge (unchanged from current “cwd document is base” model).

### Out of scope
- Changing `reconcile` placeholder text or auto-adding `read` for new files on disk.
- Resolving non-merge conflicts (e.g. HLA) or `design:` behavior for `--extend` warnings.

### Documentation surface
- **`spec/main.md`:** Align the `spec/navigation.yaml` Folder Structure bullet and any **Embedded rules** about `read` with upstream **noant/spectask** (see [upstream `spec/main.md`](https://github.com/noant/spectask/blob/main/spec/main.md)) so this repo’s methodology file matches the canonical wording for `read: required` / `read: optional` and session read order.

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`). 
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): step `1-bootstrap-read-merge` → step `2-tests-and-docs`
