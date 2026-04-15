# 3: Rename distribution to spectask-init only

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
Replace every **public** `spectask-bootstrap` identifier with **`spectask-init`** as the sole PyPI project name and console script, and rename the import package to **`spectask_init`** so names stay aligned.

## Design overview
- Affected modules: **`pyproject.toml`** (`name`, `[project.scripts]`, `setuptools.packages.find`), Python package directory **`spectask_bootstrap/` → `spectask_init/`** (all modules and imports), **`spectask_init/cli.py`** (stderr prefix for expected errors), **`README.md`**, **`spec/design/hla.md`**.
- Data flow changes: none — same `main()` and CLI flags; only distribution metadata, import paths, and user-facing strings change.
- Integration points: **PyPI** (new canonical project **`spectask-init`**; old name **`spectask-bootstrap`** is abandoned for new installs — see Details), **`uv` / `uvx`** (canonical **`uvx spectask-init …`** without `--from`).

## Before → After
### Before
- PyPI / project name **`spectask-bootstrap`** with two console scripts: **`spectask-bootstrap`** and **`spectask-init`** (`--from` required for short `uvx` story).
- Import package **`spectask_bootstrap`**; docs and HLA describe both script names.

### After
- PyPI / project name **`spectask-init`**; **single** console script **`spectask-init`** (remove **`spectask-bootstrap`** entry point).
- Import package **`spectask_init`**; **`python -m spectask_init`** works via **`spectask_init/__main__.py`**.
- User docs and HLA describe **`uvx spectask-init …`**, **`pip install spectask-init`**, and the new module path only.

## Details
- **Migration / PyPI policy:** Treat **`spectask-bootstrap`** on PyPI as **superseded** by **`spectask-init`** (no dual publishing in this spec). Maintainers may yank/deprecate the old project or publish a final README pointing to **`spectask-init`**. **Recorded action for this implementation:** none in-repo; PyPI-side steps are left to the package owner.
- **Historical spec tasks:** Do **not** rewrite **`spec/tasks/_DONE_*`** files; they stay a snapshot of past decisions.
- **Generated metadata:** Remove or regenerate **`spectask_bootstrap.egg-info/`** (and any stale **`spectask_init.egg-info/`** after rename) via a clean **`uv build`** / editable install so the repo does not keep obsolete egg-info.
- **Internal temp prefixes** (e.g. `spectask-src-zip-` in acquire) and the verb “bootstrap” in function names (`run_template_bootstrap`) are **unchanged** unless a future spec scopes a pure naming refactor.

**Target `pyproject.toml` excerpts:**

```toml
[project]
name = "spectask-init"

[project.scripts]
spectask-init = "spectask_init.cli:main"

[tool.setuptools.packages.find]
include = ["spectask_init*"]
```

**`spectask_init/__main__.py`:**

```python
from spectask_init.cli import main

if __name__ == "__main__":
    main()
```

**CLI stderr prefix** (expected failures): use **`spectask-init:`** instead of **`spectask-bootstrap:`**.

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`).
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): step `_DONE_1-pyproject-and-package-rename` → step `_DONE_2-readme-and-hla` → step `_DONE_3-repo-wide-grep-and-clean-build`
