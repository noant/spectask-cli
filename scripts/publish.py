#!/usr/bin/env python3
"""Build the project with uv and publish wheels/sdists to PyPI.

Before building, bumps ``[project].version`` in ``pyproject.toml`` by incrementing
the last dot-separated segment (must be decimal digits), then writes the file back.
Stale ``*.whl`` and ``*.tar.gz`` files under ``dist/`` are removed before each
``uv build`` so ``uv publish`` uploads only the fresh artifacts.

Requires uv on PATH: https://docs.astral.sh/uv/

Authentication (CLI overrides environment):
  spectask_publish_pypi_token  Environment variable (preferred for interactive use).
  --token                      Same value via CLI (may appear in shell history and
                               process listings; avoid on shared machines).

The resolved token is passed to ``uv publish`` only via the ``UV_PUBLISH_TOKEN``
environment variable for that subprocess (see uv publish docs).

Usage:
  spectask_publish_pypi_token=... python scripts/publish.py
  python scripts/publish.py --token pypi-...
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

_TOKEN_ENV = "spectask_publish_pypi_token"
_UV_PUBLISH_TOKEN = "UV_PUBLISH_TOKEN"
_VERSION_LINE = re.compile(r'^(\s*version\s*=\s*")([^"]+)("[^\n]*)$')


def bump_patch_version(version: str) -> str:
    """Return version with the last ``.``-segment incremented by one (decimal digits only)."""
    parts = version.split(".")
    if len(parts) < 2:
        raise ValueError(f"version must contain at least one dot: {version!r}")
    last = parts[-1]
    if not last.isdigit():
        raise ValueError(f"last version segment must be decimal digits: {version!r}")
    parts[-1] = str(int(last) + 1)
    return ".".join(parts)


def _project_root_version_line_index(lines: list[str]) -> int | None:
    """Index of ``version`` key in the ``[project]`` root table (not ``[project.*]`` subtables)."""
    i = 0
    n = len(lines)
    while i < n:
        if lines[i].strip() == "[project]":
            i += 1
            in_root = True
            while i < n:
                raw = lines[i]
                s = raw.strip()
                if not s or s.startswith("#"):
                    i += 1
                    continue
                if s.startswith("[") and s.endswith("]"):
                    inner = s[1:-1].strip()
                    if inner == "project":
                        in_root = True
                    elif inner.startswith("project."):
                        in_root = False
                    else:
                        return None
                    i += 1
                    continue
                if in_root:
                    key = s.split("=", 1)[0].strip()
                    if key == "version":
                        return i
                i += 1
            return None
        i += 1
    return None


def bump_pyproject_version(pyproject: Path) -> str:
    """Increment patch segment in ``pyproject`` and save. Returns the new version string."""
    text = pyproject.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    idx = _project_root_version_line_index(lines)
    if idx is None:
        print(
            "publish: no version key in [project] root of pyproject.toml.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    line = lines[idx]
    body = line.rstrip("\r\n")
    trail = line[len(body) :]
    m = _VERSION_LINE.match(body)
    if not m:
        print(
            f"publish: expected version = \"...\" in pyproject.toml line {idx + 1}.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    try:
        new_ver = bump_patch_version(m.group(2))
    except ValueError as e:
        print(f"publish: {e}", file=sys.stderr)
        raise SystemExit(1) from e
    lines[idx] = f"{m.group(1)}{new_ver}{m.group(3)}{trail}"
    pyproject.write_text("".join(lines), encoding="utf-8")
    return new_ver


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def remove_dist_build_artifacts(dist: Path) -> None:
    """Delete ``*.whl`` and ``*.tar.gz`` directly under ``dist``; keep other files (e.g. ``.gitignore``)."""
    if not dist.is_dir():
        return
    for p in dist.iterdir():
        if not p.is_file():
            continue
        name = p.name
        if name.endswith(".whl") or name.endswith(".tar.gz"):
            p.unlink()


def _run(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
    r = subprocess.run(cmd, cwd=cwd, env=env)
    if r.returncode != 0:
        raise SystemExit(r.returncode)


def main() -> None:
    p = argparse.ArgumentParser(description="uv build + uv publish to PyPI")
    p.add_argument(
        "--token",
        default=None,
        metavar="TOKEN",
        help=f"PyPI API token (overrides {_TOKEN_ENV} if both are set)",
    )
    args = p.parse_args()

    token = args.token or os.environ.get(_TOKEN_ENV)
    if not token:
        print(
            f"publish: set {_TOKEN_ENV} or pass --token (see script docstring).",
            file=sys.stderr,
        )
        raise SystemExit(1)

    root = _repo_root()
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        print("publish: pyproject.toml not found next to repo root.", file=sys.stderr)
        raise SystemExit(1)

    bump_pyproject_version(pyproject)

    remove_dist_build_artifacts(root / "dist")

    _run(["uv", "build"], cwd=root)

    publish_env = {**os.environ, _UV_PUBLISH_TOKEN: token}
    _run(["uv", "publish"], cwd=root, env=publish_env)


if __name__ == "__main__":
    main()
