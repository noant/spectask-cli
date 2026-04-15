# 3: Integration tests (ZIP template + Git extend)

## Goal
Run **`spectask_init.cli.main()`** (or **`run_template_bootstrap` + `run_extend`**) from a **temporary working directory** using real remote sources so **ZIP template** and **Git extend** paths execute end-to-end.

## Approach
- **`@pytest.mark.integration`**
- Use **`monkeypatch.chdir(tmp_path)`** (or fixture) so imports/cwd are correct for **`Path.cwd()`**-based bootstrap.
- Prefer **`monkeypatch.setattr(sys, "argv", [...])`** then **`main()`** so the full stack (parse → bootstrap → extend) runs in-process.
- **Constants (canonical URLs):**
  - Template **Git:** `https://github.com/noant/spectask.git`
  - Template **ZIP:** `https://github.com/noant/spectask/archive/refs/heads/main.zip`
  - Extend **Git:** `https://github.com/noant/spectask-my-extend.git`
  - Extend **ZIP:** `https://github.com/noant/spectask-my-extend/archive/refs/heads/main.zip`

## Integration cases (implement as separate tests or parametrized rows)

### 1) ZIP end-to-end (template ZIP + extend ZIP)
- **`--template-url`:** template ZIP URL above.
- **`--extend`:** extend ZIP URL above (same `.zip` suffix rule as template; **no** `git clone` for extend).
- **`--ide`:** e.g. `cursor`.
- **Assert:** required template paths exist; **`spec/extend/`** contains files from the extend archive (same checks as for extend Git).
- **Note:** GitHub archive layout still has a single top-level folder; existing **`resolve_zip_base(..., layout="extend")`** unwraps it — no manual rename in the test.

### 2) Git end-to-end (template Git + extend Git)
- **`--template-url`:** template `.git` URL; **`--template-branch`** `main` (or another branch that reliably exists).
- **`--extend`:** extend `.git` URL; **`--extend-branch`** `main`.
- **`--ide`:** e.g. `cursor`.
- **Requires:** **`git` on PATH**. If missing, **`pytest.skip`** with a clear reason.
- **Assert:** same as case 1; extend files land under **`spec/extend/`**.

### 3) No extend (template only)
- Run **twice** (or parametrize) so both acquisition modes are covered without `--extend`:
  - **3a)** template **ZIP** only — no git needed for template.
  - **3b)** template **Git** only — exercises **`git clone`** + **`--template-branch`**.
- **Assert:** bootstrap output present; **no** extra overlay beyond template (e.g. extend-only filenames from **`spectask-my-extend`** must **not** appear if they are not part of the base template).

### 4) Mixed mode (optional but useful)
- **4a)** Template **ZIP** + extend **Git** (already the minimal “avoid git for template” story).
- **4b)** Template **Git** + extend **ZIP** — ensures branch flags apply only to the Git side and ZIP extend still works.

### 5) Flags-only variants (combine with any of 1–4 where meaningful)
- **`--skip-example`:** one run **with**, one **without**; assert a path that exists only in **`example-list.json`** is present or absent.
- **`--template-branch`:** only on **Git template** cases; use **`main`** at minimum; if a second branch is added to the spec later, use it only when it exists on the remote.
- **`--extend-branch`:** only on **Git extend** cases; same rule as template branch.

### 6) Environment variables (CLI does not read custom env vars today — test the stack underneath)
Implement at least one check per bullet where feasible; use **`monkeypatch.setenv`** / **`delenv`** so tests do not leak state.

- **`TMPDIR`** (Unix) / **`TEMP`** or **`TMP`** (Windows): point to a dedicated temp directory under **`tmp_path`** for one **ZIP** case so **`tempfile.TemporaryDirectory`** and extract paths stay under the test sandbox.
- **`GIT_TERMINAL_PROMPT=0`:** set for **all Git** integration cases to reduce risk of interactive hangs if **`git`** misbehaves.
- **Optional (CI / corporate proxy):** one **ZIP** download case may document **`NO_PROXY`** / **`HTTP(S)_PROXY`** — **skip** if unset to avoid flakiness; only assert success when env is already configured. Do not require proxy for default local runs.

## Affected files
- `tests/test_integration_cli.py` (new)

## Code examples
```python
import sys
import pytest
from spectask_init.cli import main

TEMPLATE_ZIP = "https://github.com/noant/spectask/archive/refs/heads/main.zip"
TEMPLATE_GIT = "https://github.com/noant/spectask.git"
EXTEND_ZIP = "https://github.com/noant/spectask-my-extend/archive/refs/heads/main.zip"
EXTEND_GIT = "https://github.com/noant/spectask-my-extend.git"

@pytest.mark.integration
def test_zip_template_and_zip_extend(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "spectask-init",
            "--template-url",
            TEMPLATE_ZIP,
            "--ide",
            "cursor",
            "--extend",
            EXTEND_ZIP,
        ],
    )
    main()
```

```python
@pytest.mark.integration
def test_git_only_no_extend(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "spectask-init",
            "--template-url",
            TEMPLATE_GIT,
            "--template-branch",
            "main",
            "--ide",
            "cursor",
        ],
    )
    main()
```
