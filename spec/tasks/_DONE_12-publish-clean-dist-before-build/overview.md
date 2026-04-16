# 12: Clean `dist/` before `uv build` in the publish script

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
Ensure **`uv publish`** only sees artifacts from the **current** run by removing stale wheels and sdists under **`dist/`** after the version bump and **before** **`uv build`**.

## Design overview
- Affected modules: **`scripts/publish.py`** only; optional **unit test** extension in **`tests/test_publish_version_bump.py`** (or equivalent) if a small pure helper is extracted.
- Data flow changes: after **`bump_pyproject_version`** succeeds and **before** **`uv build`**, the script deletes prior build outputs in **`dist/`** so the directory cannot accumulate multiple versions that **`uv publish`** would upload together.
- Integration points: unchanged **`uv build`** / **`uv publish`** invocation; no PyPI or network behavior change beyond publishing fewer files.

## Before → After
### Before
- **`dist/`** may contain **`.whl`** and **`.tar.gz`** files from earlier local builds; **`uv publish`** uploads **all** of them, risking duplicate-version errors and confusing logs.

### After
- Each **`publish.py`** run clears **build artifacts** from **`dist/`** (wheels and sdists) immediately before **`uv build`**, so **`uv publish`** targets only the freshly built package for the bumped version.

## Details
- **Scope of deletion:** Remove **files** under **`repo_root/dist/`** that are standard **`uv` / setuptools** outputs: at minimum **`*.whl`** and **`*.tar.gz`**. Do **not** remove **`dist/.gitignore`** or other non-artifact files the repo keeps (this project uses **`dist/.gitignore`** with `*` to ignore artifact noise).
- **Missing `dist/`:** If **`dist/`** does not exist, **do nothing** before build (or create nothing pre-emptively); **`uv build`** will create **`dist/`** as needed.
- **Order of operations (unchanged except insertion):** validate token → bump and write **`pyproject.toml`** → **clean `dist/` artifacts** → **`uv build`** → **`uv publish`** with **`UV_PUBLISH_TOKEN`**.
- **Implementation:** Prefer **`pathlib.Path`** and explicit suffix checks (**`.whl`**, **`.tar.gz`**) over blind **`rmtree(dist)`**, so the **`dist/.gitignore`** layout stays intact without a follow-up commit.
- **Documentation:** Extend the **`scripts/publish.py`** module docstring (English, per **`spec/extend/conventions.md`**) with one sentence that **`dist/`** build artifacts are removed before each build.
- **Tests:** If practical, add a unit test that runs the new “clean dist” logic against a **`tmp_path`** layout (dummy **`dist/`** with a **`.whl`**, a **`.tar.gz`**, and **`.gitignore`**) and asserts artifacts are gone while **`.gitignore`** remains; avoid subprocess **`uv`** in tests.
