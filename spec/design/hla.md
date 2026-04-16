# High-Level Architecture (HLA)

This document describes the high-level architecture and interaction of abstractions in the project.

`spectask-init` parses `--ide` as one or more IDE keys (`argparse` `nargs="+"`), except that `--ide` may be omitted when `--update` is passed (then the CLI behaves as if `--ide auto` were given). The flag `--update` also forces `--skip-example` and `--skip-navigation-file`. `bootstrap.ide_files_for` merges the path lists from `skills-map.json` in key order without duplicate paths. The keys `all` and `auto` are exclusive (each must be the only value after `--ide`). For `auto`, `bootstrap.resolve_auto_ide_key` reads the acquired template’s `.metadata/ide-detection.json`, matches `file`/`directory` markers under the current working directory (OR within each IDE entry), and resolves to a single IDE name before copying.

**Tests:** `pytest` integration cases (marked, network for the canonical GitHub template ZIP) call `cli.main()` with `--ide auto` and with `--update` and no `--ide`, in addition to existing ZIP/Git template and skip-flag coverage.

**Publishing:** `scripts/publish.py` bumps the patch version in `pyproject.toml`, removes existing `*.whl` and `*.tar.gz` under `dist/` (leaving e.g. `dist/.gitignore`), then runs `uv build` and `uv publish` so PyPI uploads only the new artifacts.
