# 7: Publish script bumps patch version before build

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
Extend `scripts/publish.py` so it reads the project version from `pyproject.toml`, increments the integer after the last `.`, writes the file back, then runs `uv build` and `uv publish` using that new version.

## Design overview
- Affected modules: `scripts/publish.py` only (version I/O + existing build/publish flow).
- Data flow changes: before `uv build`, the script loads repo-root `pyproject.toml`, parses `[project].version`, applies the bump rule, saves the file (UTF-8), then proceeds unchanged with token checks, `uv build`, and `uv publish`.
- Integration points: PEP 621 `version` string is what `uv build` already uses; no separate “uv version” store exists beyond this file.

## Before → After
### Before
- `scripts/publish.py` runs `uv build` / `uv publish` with whatever `version` is already in `pyproject.toml`; maintainers must bump manually.

### After
- Each successful invocation of the publish script (after token validation) bumps the last dotted numeric segment once, persists it to `pyproject.toml`, then builds and publishes that release.

## Details
**Source of truth:** `[project].version` in repository-root `pyproject.toml` (same as today). “Version in uv” means this field—the value `uv build` packages.

**Bump rule:** Split `version` on `.`. The **last** segment must be a non-negative decimal integer (ASCII digits only, no sign). Replace it with `int(last) + 1`, rejoin with `.`. Examples: `0.1.0` → `0.1.1`; `2.0.9` → `2.0.10`; `1.0` → `1.1`. If there is no `.`, or the last segment is not purely digits (e.g. `1.0.0a1`, `1.0.dev0`), the script must exit with a **non-zero** status and a **clear English** error on stderr (no silent guess).

**Order of operations:** validate token and repo root → read and bump `pyproject.toml` → write file → `uv build` → `uv publish` (with `UV_PUBLISH_TOKEN`). If `uv build` or `uv publish` fails, the file may already show the new version; that is acceptable (maintainer fixes or reverts manually). No automatic git commit.

**TOML handling:** Prefer a correct read/write path that preserves valid TOML (stdlib `tomllib` can read; writing may need `tomli-w`, a small targeted rewrite, or another approach—implementation choice as long as the result is valid TOML and only the `version` value changes). If the project must stay on Python 3.10 for running the script, use a 3.10-compatible parser/writer or document that the publish script requires Python 3.11+.

**CLI / docs:** Update the script module docstring (English) to state that the version is auto-incremented before build. Optional: add `--dry-run` or `--no-bump` only if needed later—**out of scope** for this task.

**Tests:** No mandatory new tests unless an existing harness runs the script; if adding a small unit test is cheap (pure function `bump_patch_version(str) -> str`), do so in `tests/` without network.

**HLA:** After implementation and user code review (process Step 7), update `spec/design/hla.md` “Repository tooling” bullet to mention automatic patch bump in `publish.py`.

**Open questions:** none—all ambiguity resolved by the bump rule and error behavior above.
