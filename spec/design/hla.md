# High-Level Architecture (HLA)

This document reflects the current `spectask-init` codebase: package layout, runtime flow, and how the CLI talks to template sources.

## Package and entry points

- **Installable name:** `spectask-init` (`pyproject.toml`).
- **Console script:** `spectask-init` → `spectask_init.cli:main`.
- **Module run:** `python -m spectask_init` loads `spectask_init.__main__`, which calls the same `main()`.
- **Dependencies:** runtime has none; optional `dev` extra pulls in `pytest` for tests.

## Module map (`spectask_init/`)

| Module | Role |
|--------|------|
| `cli.py` | `argparse` wiring, `CliOptions` dataclass, `parse_args()`, `main()`. |
| `bootstrap.py` | Template bootstrap (`run_template_bootstrap`), extend overlay (`run_extend`, `copy_extend_overlay`), JSON helpers, `ide_files_for`, guarded `copy_into_cwd`. |
| `acquire.py` | Resolves a URL to a temporary tree: ZIP download + extract, or shallow `git clone`; validates layout for template vs extend. |

## CLI behavior (`cli.py`)

- **`--template-url`** is parsed twice in spirit: a lightweight pre-pass (`_template_url_from_argv`) reads only `--template-url` so the full parser can use **restricted `--ide` choices** when the URL equals `DEFAULT_TEMPLATE_URL` (official Spectask Git repo). Otherwise `--ide` is free-form and validated later against the acquired template’s `skills-map.json`.
- **`OFFICIAL_TEMPLATE_IDE_KEYS`** is a tuple in `cli.py`, documented as staying in sync with the official template’s `.metadata/skills-map.json` on `main`. Allowed values for the default URL are those keys plus **`all`** (union of all IDE path lists).
- **Other flags:** `--template-branch`, `--extend`, `--extend-branch`, `--skip-example`, `--skip-navigation-file` (see bootstrap below).
- **`main()`** runs `run_template_bootstrap` first, then optionally `run_extend`. Recoverable failures are caught as `OSError`, `RuntimeError`, or `zipfile.BadZipFile`, printed as `spectask-init: …` on stderr, and exit code **1**.

## Template bootstrap (`bootstrap.run_template_bootstrap`)

Runs inside `acquire_source(..., layout="template")` so all reads are from a resolved template root (ZIP or clone).

1. **Required paths** — `.metadata/required-list.json` → `required` list; each string path is copied with `copy_into_cwd`. If **`skip_navigation_file`** is true, the entry exactly equal to `spec/navigation.md` is skipped.
2. **Examples** — unless **`skip_example`**, `.metadata/example-list.json` → `examples` list; each path is copied the same way.
3. **IDE files** — `.metadata/skills-map.json` is loaded; `ide_files_for(skills, ide)` returns relative paths (supports `paths` or upstream `files` per IDE entry; **`all`** deduplicates across IDEs). Each path is copied.

**`copy_into_cwd`** resolves source under the template root and destination under `Path.cwd()`, rejects path escape, and copies files or directories (`dirs_exist_ok=True` for trees).

## Extend overlay (`bootstrap.run_extend`)

- Only runs when `--extend` is set.
- **`acquire_source(..., layout="extend")`** must yield a tree with `spec/extend/`.
- **`copy_extend_overlay`** copies every file under that directory into the current working tree under `spec/extend/`, preserving layout. It does not modify `spec/navigation.md` or other template paths by itself.

## Acquisition (`acquire.py`)

- **ZIP URLs** — path ends with `.zip` (case-insensitive): download to a temp file, extract, then **`resolve_zip_base`** finds the root that contains `.metadata` (template) or `spec/extend` (extend), unwrapping a single top-level folder if needed (e.g. GitHub archive layout).
- **Non-ZIP URLs** — **`git clone --depth 1 --branch <git_branch> --single-branch`** into a temp directory; checks for `.metadata` or `spec/extend` depending on `layout`. Requires **`git` on PATH** (`ensure_git_available`).
- Temp directories use prefixes `spectask-src-zip-` and `spectask-src-git-`.

## Repository tooling (not part of the wheel)

- **`scripts/publish.py`** — maintainer script: bumps `[project].version` in `pyproject.toml` (last dot-separated segment must be decimal digits), then `uv build` and `uv publish` to PyPI; token via env or CLI as documented in that file. Not imported by `spectask_init`.
