# Step 1: Project layout and CLI surface

## Goal
Add a minimal Python package with packaging metadata and an argparse-based CLI: all flags (including optional `--template-url` with a documented default), and parsing only (no network/git) in this step beyond validation that is purely local.

## Approach
- Add `pyproject.toml` with project name, `requires-python >= 3.10`, console script entry point (e.g. `spectask-bootstrap`).
- Flags: optional `--template-url` (default `https://github.com/noant/spectask.git`); required `--ide`; optional `--template-branch` (default `main`); optional `--extend`, `--extend-branch` (default `main`); `--skip-example` (store_true).
- **`--help` / epilog:** state the default `--template-url` and the ZIP-vs-Git rule (see `overview.md`).
- Document that `--extend` follows the same ZIP-vs-Git rule and that `--extend-branch` applies only to Git extend URLs.
- Return a frozen dataclass / namespace consumed by later steps.

## Affected files
- `pyproject.toml` (new)
- Python package + CLI module (new)

## Code examples

### Invocation (shell)

```text
spectask-bootstrap --ide cursor
spectask-bootstrap --ide all --template-branch main
spectask-bootstrap --ide cursor --template-url https://github.com/noant/spectask/archive/refs/heads/main.zip
spectask-bootstrap --ide claude-code --extend https://example.com/overlay.zip
spectask-bootstrap --ide windsurf --extend https://example.com/rules.git --extend-branch develop
```

### `pyproject.toml` (illustrative)

```toml
[project]
name = "spectask-bootstrap"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = []

[project.scripts]
spectask-bootstrap = "spectask_bootstrap.cli:main"
```

### Argparse with epilog (illustrative)

```python
from __future__ import annotations

import argparse
from dataclasses import dataclass

DEFAULT_TEMPLATE_URL = "https://github.com/noant/spectask.git"


@dataclass(frozen=True)
class CliOptions:
    template_url: str
    ide: str
    template_branch: str
    extend: str | None
    extend_branch: str
    skip_example: bool


def build_parser() -> argparse.ArgumentParser:
    epilog = """
ZIP vs Git:
  If the URL path ends with .zip (case-insensitive), the tool downloads and extracts
  the archive. Otherwise it runs git clone (requires git on PATH), using
  --template-branch for --template-url and --extend-branch for --extend.

Default --template-url is the official Spectask GitHub repository (.git); use a .zip URL
  to avoid git for the template step only.
""".strip()
    p = argparse.ArgumentParser(
        description="Bootstrap Spectask template files into the current directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )
    p.add_argument(
        "--template-url",
        default=DEFAULT_TEMPLATE_URL,
        metavar="URL",
        help=f"Template source (ZIP or Git). Default: {DEFAULT_TEMPLATE_URL}",
    )
    p.add_argument("--ide", required=True, help="IDE key from skills-map.json, or 'all'.")
    p.add_argument("--template-branch", default="main", help="Git branch for template URL when not ZIP (default: main).")
    p.add_argument("--extend", default=None, help="Optional overlay source (ZIP or Git) for spec/extend/.")
    p.add_argument("--extend-branch", default="main", help="Git branch for --extend when not ZIP (default: main).")
    p.add_argument("--skip-example", action="store_true", help="Do not copy example-list.json paths.")
    return p


def parse_args(argv: list[str] | None = None) -> CliOptions:
    p = build_parser()
    ns = p.parse_args(argv)
    return CliOptions(
        template_url=ns.template_url,
        ide=ns.ide,
        template_branch=ns.template_branch,
        extend=ns.extend,
        extend_branch=ns.extend_branch,
        skip_example=ns.skip_example,
    )
```
