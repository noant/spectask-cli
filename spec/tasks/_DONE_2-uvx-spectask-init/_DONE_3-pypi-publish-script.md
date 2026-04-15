# 3: PyPI publish script (`uv build` + `uv publish`)

## Goal
Add a **small, repo-local script** that builds the distribution and uploads it to **PyPI** using **uv**, so maintainers do not rely on ad-hoc copy-paste from memory.

## Approach
1. Add **`scripts/publish.py`** (stdlib only: e.g. `subprocess`, `sys`, `os`, `argparse`) at the repository root layout:
   - **Working directory:** repository root (where `pyproject.toml` lives).
   - **Steps:** run **`uv build`**, then **`uv publish`** (or a single documented sequence if uv documents a combined flow — prefer what current uv supports).
   - **Exit codes:** propagate failure if either command fails; print stderr from the child on failure where helpful.
2. **Authentication (PyPI token):**
   - **Environment variable:** read **`spectask_publish_pypi_token`** (exact name, case-sensitive in the spec; implementer documents that users must `export` / set it in the shell or CI secrets).
   - **CLI:** support a **token argument** (e.g. **`--token`** with optional short form if desired) that supplies the same secret when set.
   - **Precedence:** if both are set, **CLI wins** over the environment variable (document in docstring).
   - Do **not** embed tokens in the repo. Map the resolved token into whatever **`uv publish`** expects (subprocess env and/or `uv publish` flags — verify against current **[uv publish](https://docs.astral.sh/uv/guides/publish/)** docs).
   - **Security note** in docstring: a token on the CLI may appear in shell history and process listings; prefer **`spectask_publish_pypi_token`** for interactive use.
3. **Optional:** support **TestPyPI** via an environment variable (e.g. `SPECTASK_PUBLISH_INDEX=testpypi`) or a CLI flag on the script that passes the appropriate `--publish-url` / index flags to `uv publish` **only if** uv’s CLI exposes them; otherwise document manual `uv publish …` for TestPyPI in the docstring.

## Affected files
- `scripts/publish.py` (new)
- `spec/design/hla.md` — maintainer line is specified in step **`_DONE_2-hla-distribution-uvx`**; after implementing this script, verify that line matches the real entrypoint and env-var names.

## Constraints
- No new third-party Python dependencies for the script.
- Do not commit API tokens, `.pypirc` with secrets, or `dist/` artifacts.
- Script must be safe to run on **Windows and Unix** (avoid bash-only; Python entrypoint is preferred).
