# 2: HLA — distribution and uvx invocation

## Goal
Record in **`spec/design/hla.md`** the native **uv / uvx** flow and the canonical user-facing command.

## Approach
1. Add a short subsection (e.g. **Distribution** or **Running the CLI**) to `hla.md`:
   - Prerequisite: **[uv](https://docs.astral.sh/uv/)** is installed.
   - **Primary `uvx` example** must match the outcome of step **`_DONE_0-optional-pypi-name-for-short-uvx`**:
     - If step **0** was **skipped** or left **`[project] name` as `spectask-bootstrap`:**  
       `uvx --from spectask-bootstrap spectask-init --ide <key>`  
       (explain **`spectask-bootstrap`** = distribution, **`spectask-init`** = console script).
     - If step **0** renamed the distribution to **`spectask-init`:**  
       `uvx spectask-init --ide <key>`  
       as the primary line; optionally still document `--from` only if a second distribution name remains published.
   - Fallback: `pip install <distribution-as-published>` and `spectask-init` / `spectask-bootstrap` on `PATH` (use the actual **`[project] name`** from `pyproject.toml` for the pip example).
   - **Maintainers:** one line referencing **`scripts/publish.py`** (from step **`_DONE_3-pypi-publish-script`**) for **`uv build`** + **`uv publish`** to PyPI; token via env **`spectask_publish_pypi_token`** and/or CLI **`--token`** (prefer env); never commit secrets.
2. Omit npm/`npx` as part of this project's architecture (if HLA never mentioned them, do not add them).

## Affected files
- `spec/design/hla.md`

## Constraints
- Do not create new markdown files outside paths allowed by `spec/main.md`.
- Align wording with current uv docs: when the command name differs from the package, use **`uvx --from <package> <command>`**.
