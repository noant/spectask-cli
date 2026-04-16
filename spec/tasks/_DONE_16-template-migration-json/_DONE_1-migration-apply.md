# 1: Migration apply in `run_template_bootstrap`

## Goal
Implement reading and applying `.metadata/migration.json` at the end of `run_template_bootstrap` (after required, example, and IDE copies), including backup-to-`.backup_spectask/`, English warnings, and a deduped `.gitignore` hint when any quarantine occurs.

## Approach
1. Add focused helpers in `spectask_init/bootstrap.py` (or a small private module if it keeps `bootstrap.py` readable—prefer staying in `bootstrap.py` unless size forces split): validate migration JSON, validate relative paths, quarantine to `.backup_spectask/{basename}_{uuid}`, emit warnings to stderr.
2. Invoke migration apply while `template_root` is still available (inside the existing `acquire_source` context), after IDE file copies.
3. Preserve existing error classes and user-facing style; new messages in English only.

## Affected files
- `spectask_init/bootstrap.py`

## Constraints
- Do not change CLI flags or `run_extend` ordering.
- No new third-party dependencies (use stdlib `uuid`, `shutil`, `pathlib`).
- Match path-safety posture of `copy_into_cwd` for cwd-relative operations.
