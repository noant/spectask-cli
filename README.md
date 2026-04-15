# spectask-init

Python3.10+ CLI to bootstrap [Spectask](https://github.com/noant/spectask)-style template files into the **current working directory** (ZIP or Git sources, optional `spec/extend` overlay, IDE paths from `skills-map.json`).

The PyPI project and console command are **`spectask-init`**.

## Use with uvx (recommended)

[`uvx`](https://docs.astral.sh/uv/guides/tools/) runs the tool from PyPI without a permanent install. Install [**uv**](https://docs.astral.sh/uv/getting-started/installation/) first (it includes `uvx`).

```bash
uvx spectask-init --ide <key>
```

Examples:

```bash
uvx spectask-init --ide cursor
uvx spectask-init --ide cursor --template-branch main
uvx spectask-init --help
```

**Requirements:**

- Network access (PyPI).
- After the package is published, the command resolves **`spectask-init`** from [PyPI](https://pypi.org/project/spectask-init/). Until then, install from this repo (see below).
- For **Git** template URLs (not ending in `.zip`), `git` must be on your `PATH`.

## Install from source

```bash
git clone <this-repo-url>
cd spectask-cli
pip install .
spectask-init --ide <key>
# or: python -m spectask_init --ide <key>
```

## pip install (global / venv)

```bash
pip install spectask-init
spectask-init --ide <key>
```

## Installing uv (quick reference)

| Platform | Command |
|----------|---------|
| **Windows** (PowerShell) | `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` |
| **macOS / Linux** | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

More options: [uv installation](https://docs.astral.sh/uv/getting-started/installation/).

## Docs

- Architecture: [`spec/design/hla.md`](spec/design/hla.md)
- Spec methodology: [`spec/main.md`](spec/main.md)

## Maintainer: tests and publishing

From the repo root, with [uv](https://docs.astral.sh/uv/) on `PATH`.

**Tests** — install dev dependencies (includes pytest), then run the suite:

```bash
uv sync --extra dev
uv run pytest tests
```

Skip integration tests (no network or `git clone`; unit tests only):

```bash
uv run pytest tests -m "not integration"
```

**Publish to PyPI** — set a [PyPI API token](https://pypi.org/manage/account/) and run:

```bash
export spectask_publish_pypi_token=pypi-...   # or: python scripts/publish.py --token pypi-...
python scripts/publish.py
```

Do not commit tokens. See [uv publish](https://docs.astral.sh/uv/guides/publish/).
