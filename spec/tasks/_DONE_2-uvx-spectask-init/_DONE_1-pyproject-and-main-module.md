# 1: pyproject entry points and `python -m`

## Goal
Add the **`spectask-init`** command and module entry **`python -m spectask_bootstrap`** without changing CLI logic.

Run after optional step **`_DONE_0-optional-pypi-name-for-short-uvx`** so **`[project] name`** is already decided (or unchanged).

## Approach
1. In **`pyproject.toml`**, under `[project.scripts]`, add  
   `spectask-init = "spectask_bootstrap.cli:main"`  
   next to the existing `spectask-bootstrap`.
2. Create **`spectask_bootstrap/__main__.py`**: import `main` from `spectask_bootstrap.cli`, call it under `if __name__ == "__main__":`.
3. Local verification (after `pip install -e .` or equivalent):
   - `spectask-init --help` and `spectask-bootstrap --help` show the same usage.
   - `python -m spectask_bootstrap --help` works.

## Affected files
- `pyproject.toml`
- `spectask_bootstrap/__main__.py` (new)

## Constraints
- Do not rename the `spectask_bootstrap` package or change `spectask_bootstrap.cli` for this task.
- Do not add dependencies.
