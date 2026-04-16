# spectask-init

**[Spectask](https://github.com/noant/spectask)** is the upstream methodology and template repository. This repo publishes the **`spectask-init`** CLI (Python 3.10+): it bootstraps Spectask-style files into the **current working directory**—fetch a template (ZIP or Git), copy required paths and IDE-specific files, and optionally merge a `spec/extend` overlay.

The PyPI project and console command are **`spectask-init`**. Run it from the directory that should receive the files (the tool uses your shell’s current working directory).

## Use with uvx (recommended)

[`uvx`](https://docs.astral.sh/uv/guides/tools/) runs the tool from PyPI without a permanent install. Install [**uv**](https://docs.astral.sh/uv/getting-started/installation/) first — the installer ships both `uv` and `uvx`.

**Install uv (includes `uvx`):**

Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

macOS / Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then open a new terminal and verify:

```bash
uv --version
uvx --version
```

**Run `spectask-init`:**

```bash
uvx spectask-init --help
uvx spectask-init --ide cursor
```

**Update the tool on the next `uvx` run** (pick up the latest PyPI release instead of a cached environment):

```bash
uvx spectask-init@latest --ide cursor
```

If resolution metadata for the package looks stale, refresh the cache for it:

```bash
uvx --refresh-package spectask-init spectask-init --ide cursor
```

**Requirements:**

- Network access (PyPI and template download).
- After the package is published, the command resolves **`spectask-init`** from [PyPI](https://pypi.org/project/spectask-init/). Until then, install from this repo (see below).
- For **Git** URLs (template or extend) that are **not** `.zip` archives, `git` must be on your `PATH`.

## CLI options

| Option | Purpose |
|--------|---------|
| **`--ide`** | Which IDE(s) to install files for. Each value picks paths from the template’s `.metadata/skills-map.json`. You can pass **several** keys to merge lists (order preserved, duplicates dropped). **`auto`** uses `.metadata/ide-detection.json` and markers in the **current directory**: every IDE entry that matches is included (in file order), and their path lists are merged the same way as passing those keys explicitly (must be used alone). **`all`** installs the union of every IDE’s files (must be used alone). **Required** unless you pass **`--update`** (then it defaults to `auto`). |
| **`--template-url`** | Where to fetch the template from: **`.zip` URL** (download + extract) or **Git** URL (clone). Default is the official Spectask repo (`.git`). A **ZIP** avoids needing `git` for the template step. |
| **`--template-branch`** | Git branch for **`--template-url`** when it is **not** a ZIP (default: `main`). Ignored for ZIP URLs. |
| **`--extend`** | Optional second source (ZIP or Git) merged into **`spec/extend/`** after the main template. **`spec/navigation.yaml`** is updated as well: **`extend:`** entries from the extend source are merged with those from the main template so the registry lists every extend path and its description from both sides (paths already present after the main install keep their existing row). |
| **`--extend-branch`** | Git branch for **`--extend`** when it is **not** a ZIP (default: `main`). |
| **`--skip-example`** | Do not copy paths listed in the template’s example list (keeps the tree minimal). |
| **`--skip-navigation-file`** | Do not copy **`spec/navigation.yaml`** from the template’s required list. For advanced workflows; a normal Spectask tree usually keeps this file. |
| **`--skip-hla-file`** | Do not copy **`spec/design/hla.md`**. For advanced workflows; a normal Spectask tree usually keeps this file. |
| **`--update`** | Shorthand for **`--skip-example`** and **`--skip-hla-file`** only (it does **not** imply **`--skip-navigation-file`**). Add **`--skip-navigation-file`** explicitly if you want the older behavior of refreshing IDE-related files without copying the template **`spec/navigation.yaml`**. If you **omit** **`--ide`**, it behaves like **`--ide auto`** (detection from the template + your cwd). If you pass **`--ide`**, only the skip behavior is combined with your IDE choice. |

If **`spec/navigation.yaml`** or **`spec/design/hla.md`** already exists in the current directory, a normal run **refuses to overwrite** it. The hint names the matching skip flag for each path. For **`spec/design/hla.md`**, **`--update`** is sufficient because it implies **`--skip-hla-file`**. For **`spec/navigation.yaml`**, you must pass **`--skip-navigation-file`**— **`--update`** alone does not skip copying the registry. Use **`--update --skip-navigation-file`** when you want the example and HLA skips from **`--update`** plus the legacy “do not copy the registry” behavior.

With the **default** **`--template-url`**, **`--ide`** must be one of: **`cursor`**, **`claude-code`**, **`qwen-code`**, **`qoder`**, **`windsurf`**, **`auto`**, or **`all`**. With a **custom** template URL, any IDE name present in that template’s **`skills-map.json`** is allowed (and **`auto`** / **`all`** follow the same rules if the template supports them).

## Examples

**New project, explicit IDE (default template over Git):**

```bash
uvx spectask-init --ide cursor
```

**Detect IDE from the current folder** (template ships marker rules; your project should match one IDE, e.g. a `.cursor` directory for Cursor on the official template):

```bash
uvx spectask-init --ide auto
```

**Install files for every IDE defined in the template:**

```bash
uvx spectask-init --ide all
```

**Merge paths from two IDE keys** (e.g. Cursor + Claude Code):

```bash
uvx spectask-init --ide cursor claude-code
```

**Use a ZIP template** (no `git` for the template fetch):

```bash
uvx spectask-init --template-url https://github.com/noant/spectask/archive/refs/heads/main.zip --ide cursor
```

**Refresh an existing Spectask tree** ( **`--skip-example`** and **`--skip-hla-file`** via **`--update`**; **`spec/navigation.yaml`** is still copied when the tool would install it unless you add **`--skip-navigation-file`**; default IDE = `auto`):

```bash
uvx spectask-init --update
```

Same refresh but force a specific IDE:

```bash
uvx spectask-init --update --ide cursor
```

**Add the main template and an extend overlay** (extend can be Git or ZIP):

```bash
uvx spectask-init --ide cursor \
  --extend https://github.com/noant/spectask-my-extend.git --extend-branch main
```

## Install from source

```bash
git clone <this-repo-url>
cd spectask-cli
pip install .
spectask-init --ide cursor
# or: python -m spectask_init --ide cursor
```

## pip install (global / venv)

```bash
pip install spectask-init
spectask-init --ide cursor
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
