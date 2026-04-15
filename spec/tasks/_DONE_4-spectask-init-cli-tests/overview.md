# 4: Spectask-init CLI tests (all parameters)

IMPORTANT: always use `spec/main.md` and `spec/navigation.md` for rules.

## Status
- [x] Spec created
- [x] Self spec review passed
- [x] Spec review passed
- [x] Code implemented
- [x] Self code review passed
- [ ] Code review passed
- [x] HLA updated

## Goal
Add a **pytest** suite that exercises **every** `spectask-init` CLI flag at least once, including a **ZIP template** URL and a **Git extend** URL with an explicit branch.

## Design overview
- Affected modules: **`pyproject.toml`** (dev / optional test dependency on **pytest**), new **`tests/`** tree (e.g. `tests/conftest.py`, `tests/test_*.py`), optionally **`.github/workflows/`** or CI docs only if the repo already runs tests — **do not** add new markdown docs beyond this spec.
- Data flow changes: none for end users; only developer test runs invoke `parse_args`, `main`, or bootstrapping helpers against temp directories.
- Integration points: **GitHub** (HTTP **archive ZIP** for template), **Git** (`git clone` for default template and for `--extend`), local **`pytest`** execution.

## Before → After
### Before
- No automated tests; CLI flags are only exercised manually.

### After
- **`pytest`** can run locally (and in CI if wired) with:
  - **Unit** tests: `parse_args`, `is_zip_url`, `resolve_zip_base`, `ide_files_for` / JSON edge cases — **no network**, using `tmp_path` and small on-disk fixtures.
  - **Integration** tests (marked, e.g. `@pytest.mark.integration`): real **`--template-url`** as GitHub **ZIP**, real **`--extend`** as Git **HTTPS** repo, **`--extend-branch`**, and checks on the resulting tree under a temp CWD. Separate cases or parametrization so **every** flag appears in at least one assertion path.

## Details
- **Canonical URLs in tests (do not substitute without updating this spec):**
  - **Template ZIP** (GitHub archive; single top-level folder like `spectask-main/` is unwrapped by existing `resolve_zip_base`):    `https://github.com/noant/spectask/archive/refs/heads/main.zip`
  - **Extend Git:**  
    `https://github.com/noant/spectask-my-extend.git`
- **Parameter coverage checklist** (each must be hit by at least one test):
  - `--template-url` — once as **ZIP** (URL above); once as **default** or explicit `.git` (exercises `git clone` + `--template-branch`).
  - `--ide` — at least one concrete key from the resolved template’s `skills-map.json` and one run with **`all`**.
  - `--template-branch` — non-default value in a **Git template** test (e.g. `main` vs another branch only if reliably available; prefer a branch that exists on `noant/spectask` or document skipping).
  - `--extend` — set to the extend Git URL above in an integration test.
  - `--extend-branch` — non-default only if `spectask-my-extend` has another branch; otherwise default `main` still satisfies “parameter used” if parsed and passed through (unit test on `CliOptions` + integration with `main`).
  - `--skip-example` — one run **with** and one **without**, asserting presence/absence of at least one path that comes **only** from `example-list.json`.
- **ZIP layout:** No manual “rename” in tests beyond using the correct **archive** URL; production code already unwraps one top-level directory when markers live inside it.
- **Isolation:** Integration tests **`chdir`** to `tmp_path` (or equivalent) so the real repo tree is never polluted.
- **Git availability:** Non-ZIP tests require **`git` on PATH**; mark them so default `pytest` can run unit-only (`-m "not integration"`) in constrained environments.
- **Stdlib-only package:** Keep **`pytest`** out of runtime `dependencies`; use **`[project.optional-dependencies]`** (e.g. `dev = ["pytest>=8"]`) or the project’s existing **`uv`** dev pattern if already present.

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`).
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): step `1-pytest-harness` → step `2-unit-tests` → step `3-integration-cli`
