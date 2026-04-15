# 2: uvx entry for Spectask bootstrap (Python-native)

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
The default user story: install **uv**, run the initializer in one shot — **`uvx … spectask-init`** with the same flags as the current CLI, **without npm/Node and without a separate npm package**.

## Design overview
- Affected modules: **`pyproject.toml`** (`[project]` name optionally, `[project.scripts]`), new **`spectask_bootstrap/__main__.py`** (module invocation), **`spec/design/hla.md`** (section on distribution and invocation via uv), **`scripts/publish.py`** (maintainer-only build + publish to PyPI via **uv**).
- Optional first step **`_DONE_0-optional-pypi-name-for-short-uvx`**: shorten **`uvx`** by aligning distribution name with **`spectask-init`** (no `cli.py` changes); see subtask file.
- Data flow: **user → `uv` / `uvx` → isolated tool environment → console script `spectask-init` → `spectask_bootstrap.cli:main()`**; stdin/stdout/stderr and exit code match a normal CLI.
- Integration points: **PyPI** (distribution name is currently **`spectask-bootstrap`** in `pyproject.toml`); **uv CLI** (`uvx` is shorthand for `uv tool run`), see [guides/tools](https://docs.astral.sh/uv/guides/tools/).

## Before → After
### Before
- The spec and discussion included an **npm + `npx`** path: a separate Node wrapper package.
- One Python console script: **`spectask-bootstrap`**.
### After
- **No** npm-oriented tasks or artifacts for this scenario.
- Two console scripts from one distribution: **`spectask-bootstrap`** (unchanged) and **`spectask-init`** (same `main`, shorter command name for “init”).
- HLA records the **canonical** **`uvx`** invocation and fallbacks (`pip install`, local `uv run`).
- Maintainers can run **`scripts/publish.py`** to **`uv build`** and **`uv publish`** the project to PyPI; token via **`spectask_publish_pypi_token`** and/or **`--token`** (never committed).

## Details

### Why uvx
- **`uvx`** installs/reuses a cached environment and runs a command from PyPI — UX is close to **`npx`**, but **native to Python** and does not require a second registry (npm).

### Package vs command name (exact invocation matters)
- **uv** assumes by default that the **command name matches the package name** on the index (`uvx black`, `uvx ruff`).
- For distribution **`spectask-bootstrap`**, the **`spectask-init`** command **does not** match the package name → use **`--from`** (official Astral pattern: command provided under a different package name).

**Canonical command (while `name` in `pyproject.toml` is `spectask-bootstrap`):**

```bash
uvx --from spectask-bootstrap spectask-init --ide <key>
```

Example with a template branch (arguments are the same as for the CLI):

```bash
uvx --from spectask-bootstrap spectask-init --ide cursor --template-branch main
```

If the PyPI distribution is **renamed** later to **`spectask-init`** with a same-named command, this is enough:

```bash
uvx spectask-init --ide <key>
```

Whether to rename the distribution is **optional** — subtask **`_DONE_0-optional-pypi-name-for-short-uvx`**. If step 0 is **not** done, the primary contract stays **`uvx --from spectask-bootstrap spectask-init …`**. If step 0 **is** done, the primary contract becomes **`uvx spectask-init …`** and HLA must match.

### Packaging requirements
1. In **`pyproject.toml`**, add a second entry point:
   - `spectask-init = "spectask_bootstrap.cli:main"`
   - Do **not** remove the existing `spectask-bootstrap = …`.
2. Add **`spectask_bootstrap/__main__.py`** that calls `cli.main()` to support **`python -m spectask_bootstrap`** and **`uv run`** with a module (secondary to `uvx`, but a single small file).

### Documentation in the repo
- Extend **`spec/design/hla.md`**: prerequisite “**uv** is installed”, canonical **`uvx`** line per step **0** outcome, briefly **fallback**: `pip install <distribution-name>` and `spectask-init` / `spectask-bootstrap` on `PATH`.
- **Do not** add a separate npm package or describe `npx` as the primary path for this task.

### Non-functional requirements
- Python and project dependencies **unchanged** (stdlib-only per HLA).
- CLI behavior **identical** to current `spectask-bootstrap` (only the executable name under `uvx` is `spectask-init`).

### Out of scope
- **Release/version policy** (when to bump, changelogs, Git tags) — only automation for **build + upload** is in scope via step **`_DONE_3-pypi-publish-script`**. Migration policy for an old PyPI name is only required if step 0 renames the distribution.
- **CI** (GitHub Actions, etc.) for unattended publishes — optional future work unless explicitly added later.
- `pipx run` as first-class docs (optional one-liner in HLA).

## Execution Scheme
> Each step id is the subtask filename.
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline.
- Phase 1 (sequential): step `_DONE_0-optional-pypi-name-for-short-uvx` → step `_DONE_1-pyproject-and-main-module` → step `_DONE_2-hla-distribution-uvx` → step `_DONE_3-pypi-publish-script`
>
> Step **0** is **optional** (decision + optional `[project] name` change). If skipped, implementers proceed from **`_DONE_1-pyproject-and-main-module`** and keep **`--from spectask-bootstrap`** as the documented primary `uvx` line.

### Code examples

`pyproject.toml` (snippet):

```toml
[project.scripts]
spectask-bootstrap = "spectask_bootstrap.cli:main"
spectask-init = "spectask_bootstrap.cli:main"
```

`spectask_bootstrap/__main__.py`:

```python
from spectask_bootstrap.cli import main

if __name__ == "__main__":
    main()
```
