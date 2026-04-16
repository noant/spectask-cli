# 16: Template `.metadata/migration.json` (post-bootstrap delete/move)

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
After a successful template bootstrap (`spectask-init` init or `--update`), apply optional `.metadata/migration.json` from the resolved template by running declared **move** and **delete** operations against the current working directory, using a safe `.backup_spectask/` quarantine and English warnings that suggest adding that folder to `.gitignore` when backups occur.

## Design overview
- Affected modules: `spectask_init/bootstrap.py` (load/validate migration, backup helpers, hook at end of `run_template_bootstrap` before leaving the template acquisition context), `tests/test_bootstrap_unit.py` and/or `tests/test_integration_cli.py` (fixtures under `tests/` as needed).
- Data flow: template acquired → required/example/IDE copies (existing behavior) → read `template_root/.metadata/migration.json` if present → apply **move** then **delete** (see Details) against `Path.cwd()` → optional stderr warnings when anything is quarantined under `.backup_spectask/`.
- Integration points: upstream Spectask template ships `migration.json`; CLI `main()` flow unchanged except through `run_template_bootstrap`; `--extend` still runs **after** template bootstrap (migration does not re-run for extend-only paths).

## Before → After
### Before
- Template updates may rename or remove tracked paths; consumers keep stale files with no automated cleanup or rename.

### After
- If the template provides `.metadata/migration.json`, the CLI performs listed moves and deletes after copies complete, never hard-deleting user content without quarantine, and surfaces clear warnings plus a `.gitignore` hint when backups are created.

## Details

### File presence and schema
- If `template_root/.metadata/migration.json` is **missing**, do nothing (no error).
- If present, it MUST be a JSON object. Optional keys:
  - **`move`**: array of objects, each with string **`from`** and **`to`** (POSIX-style relative paths using `/`, repository-root–relative, non-empty).
  - **`delete`**: array of strings (same path rules).
- Invalid JSON, non-object root, wrong element types, missing `from`/`to`, empty strings, absolute paths, or any path containing `..` or Windows drive semantics MUST fail with a **`RuntimeError`** and a clear message (same class of errors as other bootstrap JSON validation).
- Unknown extra keys SHOULD be ignored to allow forward-compatible additions.

### Path safety
- Resolve all targets under **`Path.cwd().resolve()`**; refuse any operation that would touch paths outside the cwd (same spirit as `copy_into_cwd`).
- Treat paths as referring to **files or directories** (use existence checks that cover both).

### Operation order
- Apply all **`move`** entries **in listed order**, then all **`delete`** entries **in listed order**. Template authors rely on this ordering; document it in code comments briefly if needed.
- **Template authoring note:** with **moves-before-deletes**, a **`delete`** entry for the same path as a **`move`**’s **`to`** will run **after** the move and will quarantine the newly moved content. Avoid that combination unless it is deliberate.

### `move` semantics
- If **`from`** does not exist: **no error** — skip the entry (optional: no warning to avoid noise on repeated `--update`; do not add stderr spam unless a single concise line is useful—**default: silent skip**).
- If **`from`** exists and **`to`** already exists: move the existing **`to`** path into `.backup_spectask/` first (see Backup naming), then emit a **warning** to stderr that the path was displaced because of migration and the user should decide whether to delete it; include the backup path.
- Then move `from` → `to` (create parent directories as needed). Use atomic/reasonable semantics (`shutil.move` or equivalent); failures MUST surface as **`OSError`/`RuntimeError`** with context.

### `delete` semantics
- If the path does not exist: **no error**, no output.
- If it exists: do **not** delete in place. Move the path into `.backup_spectask/` (same backup naming), then emit a **warning** to stderr that the template migration marked this path for removal and it was quarantined under `.backup_spectask/` for the user to review/delete.

### Backup directory and naming
- Backup root: **`.backup_spectask/`** under cwd (create if needed).
- Each quarantined path becomes a sibling under that root with name **`{basename}_{uuid}`** where `basename` is the final path component of the original **file or directory** and `uuid` is a new UUID4 (hex or standard string form—pick one and use consistently in tests).
- If a name collision is theoretically possible, the UUID MUST still make the final name unique; no extra logic required beyond UUID.

### Warning text and `.gitignore` hint (English only, per `spec/extend/conventions.md`)
- Warnings MUST be English and actionable.
- Whenever any path is placed under `.backup_spectask/` for **either** move-displacement or delete-quarantine, also print **one** stderr hint suggesting the user add **`.backup_spectask/`** to their `.gitignore` if they do not want quarantined files tracked (dedupe: at most once per CLI invocation after migration runs, not once per file).

### Relation to `--extend`
- `run_extend` remains **after** `run_template_bootstrap` in `cli.py`. Migration runs **only** as part of template bootstrap, using the **template’s** `migration.json`. Extend sources do not supply migration in this task.

### Testing expectations
- Unit tests: JSON validation errors; move with missing `from` (no-op); delete with missing path (no-op); delete moves existing file to `.backup_spectask/` and warns; move with existing `to` backs up `to` then moves `from`; order **moves before deletes** observable via a small scenario; path traversal `..` rejected.
- Integration (lightweight): optional fixture template ZIP or temp dir with `.metadata/migration.json` if the suite already supports that pattern; otherwise unit coverage is sufficient if integration cost is high.

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`). 
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): step `_DONE_1-migration-apply` → step `_DONE_2-tests`
