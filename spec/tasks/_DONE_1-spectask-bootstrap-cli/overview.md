# 1: Spectask bootstrap CLI (Python)

IMPORTANT: always use `spec/main.md` and `spec/navigation.md` for rules.

## Status
- [x] Spec created
- [ ] Self spec review passed
- [x] Spec review passed
- [x] Code implemented
- [x] Self code review passed
- [x] Code review passed
- [x] HLA updated

## Goal
Deliver a Python CLI that bootstraps Spectask template files into the current working directory from a configurable template source (ZIP URL or Git URL), optionally installs IDE-specific skill/rule files, optionally skips example files, and optionally merges `spec/extend/*` from a second source that also may be ZIP or Git.

## Design overview
- Affected modules: Python CLI package (entry point), packaging metadata (`pyproject.toml`), no application server.
- Data flow changes: none beyond local download/extract/copy and optional `git clone`.
- Integration points: template URL (default official Git remote), overridable via optional `--template-url`; optional extend URL; `git` on `PATH` whenever template or extend resolves to **Git** mode (including the default template URL unless overridden with a `.zip` URL).

## Before → After
### Before
- No automated way in this repo to pull the upstream Spectask skeleton and IDE mappings into an arbitrary project directory.
### After
- Running the CLI with required `--ide` (or `all`) resolves the template source (ZIP download + extract, or `git clone`), applies `required-list.json`, optionally `example-list.json`, and IDE-specific paths from `skills-map.json`, then optionally overlays `spec/extend/*` from `--extend` using the same ZIP-vs-Git rules.

## Details

### Unified source acquisition
- **ZIP vs Git:** For any URL, determine mode by the URL **path** (per `urllib.parse.urlparse`): if the path ends with `.zip` (ASCII case-insensitive), treat as **ZIP**: HTTP(S) download and local extract into a directory under the **system temporary directory**. Otherwise treat as **Git**: require `git` on `PATH`, **shallow clone** (`--depth 1`) with the relevant branch into system temp. Query strings do not affect the suffix check (only the path component).
- **Single implementation:** One internal API (e.g. context manager) must implement **both** ZIP and Git acquisition (shared download/extract vs `git clone`, shared tempdir lifecycle). Template and `--extend` must call this API — no parallel one-off clone/download paths. Branch arguments apply **only** in Git mode (ignored for ZIP).
- **Cleanup:** Always remove temp directories after the step finishes or on failure (`try`/`finally`).

### Root directory after acquisition

- **Git:** The clone target directory is the root (must contain `.metadata` for template; must contain `spec/extend` for extend).
- **ZIP:** Let `base` be the extract directory. If `base` already contains the required marker (`.metadata` for template, `spec/extend/` for extend), use `base`. Otherwise, if `base` has exactly **one** immediate subdirectory, treat that subdirectory as `base` and repeat the check once. If the marker is still missing, fail with a clear error. This covers GitHub’s single top-level folder without hardcoding its name.

### CLI interface
- `--template-url` (optional): template source URL (ZIP or Git). Default `https://github.com/noant/spectask.git`. **`--help` must show** this default and the ZIP-vs-Git rule (path ends with `.zip` → download + extract; otherwise `git clone` with `--template-branch`).
- `--ide` (required): one of the `name` values from `ides[]` in `{template-root}/.metadata/skills-map.json`, or the literal `all` (match JSON / `all` exactly as today).
- `--template-branch` (optional): branch for **Git** template URL only; default `main`. Ignored when template URL is ZIP.
- `--extend` (optional): second source URL (ZIP or Git). When Git, use `--extend-branch`.
- `--extend-branch` (optional): branch for **Git** extend URL only; default `main`. Ignored when extend URL is ZIP.
- `--skip-example` (optional): do not copy paths from `example-list.json`.

When `--extend` is set and the extend URL is **not** ZIP, verify `git` before cloning (same pattern as template Git).

### Copy order (template)
1. Paths from `required-list.json` → `required`.
2. Unless `--skip-example`: paths from `example-list.json` → `examples`.
3. IDE files from `skills-map.json` per `--ide` / `all`.
4. Delete template acquisition temp (via unified cleanup).

### Extend overlay
5. If `--extend` is set: acquire via the **same** `acquire_source` API with `layout="extend"`. Copy all files under `spec/extend/` from the yielded root into `./spec/extend/` under `Path.cwd()`, preserving relative paths, overwriting.
6. Temp cleanup is handled by `acquire_source`.

### Orchestration
Parse CLI args → `acquire_source(opts.template_url, …)` → apply JSON-driven copies → if `--extend`, `acquire_source` again → `copy_extend_overlay` → exit codes on first failure. Do not run extend if template bootstrap failed.

### Non-functional requirements
- **Python:** 3.10+, `pyproject.toml` with console script.
- **Dependencies:** prefer stdlib; justify any HTTP helper dependency.
- **Errors:** clear stderr for HTTP failures, corrupt zip, missing `.metadata` / `spec/extend`, invalid JSON, unknown `--ide`, missing `git` when Git mode is required.

### Reference metadata (upstream snapshot)
`skills-map.json` IDE names include `cursor`, `claude-code`, `qwen-code`, `qoder`, `windsurf`. Do not hardcode lists; read from acquired template tree.

## Execution Scheme
> Each step id is the subtask filename.
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline.
- Phase 1 (sequential): step `_DONE_1-project-and-cli` → step `_DONE_2-template-bootstrap` → step `_DONE_3-extend-overlay`

### Code examples (high-level wiring)

Illustrative only — names should match helpers from the step specs.

```python
def main() -> None:
    opts = parse_args()
    with acquire_source(opts.template_url, git_branch=opts.template_branch, layout="template") as template_root:
        run_template_copies(template_root, ide=opts.ide, skip_example=opts.skip_example)
    if opts.extend:
        with acquire_source(opts.extend, git_branch=opts.extend_branch, layout="extend") as extend_root:
            copy_extend_overlay(extend_root)
```
