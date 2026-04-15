# Step 1: pyproject and Python package rename

## Goal
Align build metadata and the import tree with **`spectask-init`** / **`spectask_init`**.

## Approach
1. Set **`[project] name`** to **`spectask-init`**.
2. Replace **`[project.scripts]`** with a **single** entry: **`spectask-init = "spectask_init.cli:main"`** (remove **`spectask-bootstrap`**).
3. Update **`[tool.setuptools.packages.find] include`** to **`["spectask_init*"]`**.
4. Rename directory **`spectask_bootstrap/`** → **`spectask_init/`**.
5. In every module under **`spectask_init/`**, replace imports **`spectask_bootstrap`** → **`spectask_init`**.
6. Update **`spectask_init/__main__.py`** to import **`spectask_init.cli`**.
7. In **`spectask_init/cli.py`**, change stderr prefixes from **`spectask-bootstrap:`** to **`spectask-init:`**.

## Affected files
- **`pyproject.toml`**
- **`spectask_init/`** (renamed from **`spectask_bootstrap/`**): **`__init__.py`**, **`__main__.py`**, **`cli.py`**, **`acquire.py`**, **`bootstrap.py`**, and any other files in that package

## Constraints
- Do not change CLI arguments, defaults, or exit-code behavior beyond the error prefix string.
- Ensure the package remains importable as **`spectask_init`** after the rename.

## Code examples

**Import fix (pattern in `spectask_init/cli.py`, `bootstrap.py`, etc.):**

```python
from spectask_init.bootstrap import run_extend, run_template_bootstrap
```

**Stderr prefix:**

```python
print(f"spectask-init: {e}", file=sys.stderr)
```
