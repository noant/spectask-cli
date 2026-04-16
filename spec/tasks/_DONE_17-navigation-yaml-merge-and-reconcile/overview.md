# 17: Navigation YAML merge on `--extend` and post-bootstrap reconcile

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
When using `--extend`, merge the remote `spec/navigation.yaml` **extend** section into the project’s registry; warn when the extend source lists **design** entries (they are ignored). After template bootstrap—including `apply_template_migration` from `.metadata/migration.json`—and again after `run_extend`, reconcile `spec/navigation.yaml` with files on disk under `spec/extend/` and `spec/design/`, auto-adding missing entries, removing stale ones, and emitting English CLI warnings.

## Design overview
- Affected modules: `spectask_init/bootstrap.py` (new helpers, hooks from `run_template_bootstrap` after `apply_template_migration`, and from `run_extend`), `spectask_init/cli.py` only if wiring needs a `stderr` sink passed through; `tests/test_bootstrap_unit.py` and/or `tests/test_integration_cli.py`.
- Data flow: template bootstrap completes migrations → reconcile navigation vs `spec/extend` + `spec/design` → optional `--extend` acquire → merge extend navigation (if present) → overlay `spec/extend` files → reconcile again.
- Integration points: existing `NAVIGATION_FILE_RELPATH`, `copy_extend_overlay`, `apply_template_migration`; YAML structure fixed by `spec/main.md` / `spec/navigation.yaml`.

## Before → After
### Before
- `--extend` only copies `spec/extend/*`; any `spec/navigation.yaml` in the extend source is ignored, so new extend docs are not registered.
- Moves/deletes from template migration can leave `spec/navigation.yaml` out of sync with the filesystem; ad-hoc files under `spec/extend/` or `spec/design/` may be missing from the registry or point at deleted paths.

### After
- If the extend root contains `spec/navigation.yaml`, its **`extend:`** list is merged into the cwd registry (by path); **`design:`** entries in that file are warned and not merged or copied.
- After migration and after extend overlay, the CLI syncs the **`extend:`** and **`design:`** sections with actual `.md` files under `spec/extend/` and `spec/design/`, with stderr warnings for auto-fixes.

## Details

### Scope and filenames
- Hook ordering uses the existing migration step: **immediately after** `apply_template_migration(...)` returns inside `run_template_bootstrap` (whether `.metadata/migration.json` was absent or applied operations). The user-facing wording may say “after migrations”; the implementation anchor is that function.
- **Note:** The repo uses `.metadata/migration.json` (singular), not `migrations.json`.

### 1) Extend source `spec/navigation.yaml` merge (`--extend`)
- **When:** Inside `run_extend`, after resolving `extend_root`, **before** `copy_extend_overlay` (so merge sees current cwd state; overlay then adds files).
- **Condition:** `(Path.cwd() / NAVIGATION_FILE_RELPATH).is_file()` and `(extend_root / "spec" / "navigation.yaml").is_file()`. If cwd has no navigation file, skip merge (no error); optionally one stderr warning is acceptable but not required.
- **Parse:** Load both YAML documents. Invalid YAML or wrong shape → **`RuntimeError`** with a clear message (same spirit as other bootstrap validation).
- **Expected shape:** Follow `spec/navigation.yaml`: top-level `extend` is a list of mappings with at least `path` (string); `description` optional. Ignore unknown keys on items unless they break parsing.
- **Merge rule:** For each item in the **source** `extend` list, if `path` is not already present in the **cwd** `extend` list (compare normalized repo-relative POSIX paths), **append** that item to cwd’s `extend` list. If `path` already exists, **keep** the cwd entry unchanged (do not overwrite description).
- **Source `design` section:** If the extend source’s navigation has a non-empty `design` list (or any `design` entries—define “non-empty” as: key present and list length > 0), print an **English warning** to stderr that **design** entries from the extend bundle are **not** merged, **design** files are **not** copied from the extend source, and `--extend` only adds **`spec/extend/**` files plus **`extend:`** registry entries. Do not copy `spec/design/*` from the extend root.
- **Persistence:** Write the updated navigation file to cwd atomically (write temp + replace) if any merge changed content.

### 2) & 3) Reconcile registry with filesystem (extend and design)
- **When:** (a) At end of `run_template_bootstrap`, after `apply_template_migration`. (b) At end of `run_extend`, after `copy_extend_overlay`. Skip entirely if `spec/navigation.yaml` is missing in cwd.
- **Extend directory:** Consider every **file** under `spec/extend/` (recursive or flat—match how overlay copies; today overlay uses `rglob` for files). Only **`*.md`** (or follow `spec/main.md`: concrete `spec/extend/*.md`—if only top-level is allowed by methodology, restrict to non-recursive `*.md`; if repo allows nested, match overlay). **Clarification for implementer:** Use the same inclusion rule as `copy_extend_overlay` (all files under `spec/extend/` with `.md` suffix only, or all files—prefer **`.md` only** to match “concrete spec/extend/*.md” wording in `spec/main.md`).
- **Design directory:** Every **`spec/design/*.md`** file (at minimum `hla.md` and any optional docs). Include `hla.md` in the set of expected files if it exists on disk.
- **Missing from YAML:** For each on-disk path (as registry `path` like `spec/extend/foo.md`), if not listed under the matching section (`extend` vs `design`), **append** an entry: **`extend:`** use `description: additional conventions`; **`design:`** use `description: additional design document` (same English strings everywhere; user may refine descriptions later).
- **Warning (added rows):** For each auto-appended entry, stderr **warning** (English): file was not listed in navigation; it was added with the placeholder description; user should edit `description` in `spec/navigation.yaml`.
- **Stale YAML rows:** For each `extend` / `design` item, if `path` points to a **non-existent** file relative to cwd, **remove** that list element and warn (English) that the file was missing and the entry was removed from the registry.
- **Ordering:** After removals/additions, preserve a stable order: e.g. keep existing order for retained rows; append new rows at the end in deterministic sort order of path.
- **Special cases:**
  - **Stale entries:** No exception for `hla.md`—if the path is listed but the file is absent, remove the row and warn (consistent with other paths).
  - Empty `extend` or `design` lists: valid. If the navigation file has no `design` key but `spec/design/*.md` files exist on disk, **add** a `design` section and register those files (align with `spec/main.md`: every optional design doc must be listed; `hla.md` must exist and be listed when present).

### YAML I/O
- **Dependencies:** `pyproject.toml` currently has no runtime deps. Prefer a **stdlib-only** parser/emitter for this narrow schema if maintainable; otherwise add a single small dependency (e.g. `PyYAML`) and document the choice in the implementation subtask. If comments in `navigation.yaml` are lost on rewrite, note it in tests/docs briefly.

### Warnings
- All new user-facing messages: **English**, actionable, consistent with existing migration warnings.

### Testing
- **Step 2:** reconcile behavior, post-migration hook order (e.g. migration moves a file → reconcile updates yaml), stale/missing rows, placeholder descriptions.
- **Step 3:** dedicated **`--extend` navigation merge** test matrix (append, dedup, path normalization, source `design:` warnings, missing source/cwd navigation, invalid YAML)—see `_DONE_3-merge-test-cases.md`.
- Integration (lightweight): temp template + extend tree with navigation in extend source (may live in step 2 or 3 depending on where it fits best).

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`). 
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): step `_DONE_1-extend-navigation-merge` → step `_DONE_2-navigation-reconcile-and-tests` → step `_DONE_3-merge-test-cases`
