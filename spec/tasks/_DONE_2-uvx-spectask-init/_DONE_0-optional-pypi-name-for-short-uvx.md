# 0 (optional): Shorter `uvx` via distribution name

## Goal
Allow the shortest **`uvx spectask-init …`** form (no `--from`) by aligning the **PyPI distribution name** with the console script name, **without** changing CLI logic in `spectask_bootstrap/cli.py`.

## Approach
1. **Clarify responsibility:** The length of the `uvx` command line is determined by **`pyproject.toml`** **`[project]` `name`** and **`[project.scripts]`**, not by edits to the main script (`cli.py`). Both `spectask-bootstrap` and `spectask-init` entry points can keep pointing at `spectask_bootstrap.cli:main`.
2. **Optional rename:** If the project chooses the short invocation as the primary story, set **`[project] name`** to **`spectask-init`** (the name users pass to `uv tool run` / the default package argument to `uvx` when it matches the command). Keep the **import package directory** as **`spectask_bootstrap`** unless a separate refactor is explicitly scoped.
3. **Tradeoffs:** Renaming the distribution breaks or supersedes **`pip install spectask-bootstrap`** / **`uvx spectask-bootstrap`** unless you publish two projects, yank/deprecate the old name, or accept a one-time migration. Record the chosen policy in the subtask outcome and in HLA (step `_DONE_2-hla-distribution-uvx`).
4. **If this step is skipped:** The canonical `uvx` line remains **`uvx --from spectask-bootstrap spectask-init …`** with **`[project] name = "spectask-bootstrap"`**.

## Affected files
- `pyproject.toml` (`[project]` `name`, and optionally `version`/metadata consistency)
- `spec/design/hla.md` (cross-reference when step `2` runs — document whichever naming choice step 0 produced)

## Constraints
- Do not change `spectask_bootstrap.cli` behavior solely to shorten `uvx`.
- Do not add npm or Node artifacts.
