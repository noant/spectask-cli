from __future__ import annotations

import subprocess
import tempfile
import zipfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Literal
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import urlopen


def is_zip_url(url: str) -> bool:
    return urlparse(url).path.lower().endswith(".zip")


def resolve_zip_base(extract_dir: Path, layout: Literal["template", "extend"]) -> Path:
    def has_marker(base: Path) -> bool:
        if layout == "template":
            return (base / ".metadata").is_dir()
        return (base / "spec" / "extend").is_dir()

    base = extract_dir
    if has_marker(base):
        return base
    children = [p for p in base.iterdir() if p.is_dir()]
    if len(children) == 1:
        base = children[0]
        if has_marker(base):
            return base
    marker = ".metadata" if layout == "template" else "spec/extend/"
    raise RuntimeError(
        f"Cannot resolve {layout} root under {extract_dir}: expected {marker} "
        "(after unwrapping at most one single top-level folder if present)",
    )


def ensure_git_available() -> None:
    try:
        r = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError as e:
        raise RuntimeError("git is not installed or not on PATH; required for non-ZIP URLs.") from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError("git --version timed out; check your git installation.") from e
    if r.returncode != 0:
        msg = (r.stderr or r.stdout or "").strip() or f"exit code {r.returncode}"
        raise RuntimeError(f"git is not available ({msg}); required for non-ZIP URLs.")


@contextmanager
def acquire_source(
    url: str,
    *,
    git_branch: str,
    layout: Literal["template", "extend"],
) -> Generator[Path, None, None]:
    if is_zip_url(url):
        with tempfile.TemporaryDirectory(prefix="spectask-src-zip-") as td:
            td_path = Path(td)
            zip_path = td_path / "archive.zip"
            try:
                with urlopen(url, timeout=60) as resp:
                    zip_path.write_bytes(resp.read())
            except (HTTPError, URLError, TimeoutError, OSError) as e:
                raise RuntimeError(f"Failed to download archive {url!r}: {e}") from e
            extract_dir = td_path / "extract"
            extract_dir.mkdir()
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(extract_dir)
            yield resolve_zip_base(extract_dir, layout)
        return

    ensure_git_available()
    with tempfile.TemporaryDirectory(prefix="spectask-src-git-") as td:
        repo = Path(td) / "repo"
        try:
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "--branch",
                    git_branch,
                    "--single-branch",
                    url,
                    str(repo),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            err = (e.stderr or e.stdout or "").strip()
            detail = f": {err}" if err else ""
            raise RuntimeError(f"git clone failed for {url!r}{detail}") from e

        if layout == "template" and not (repo / ".metadata").is_dir():
            raise RuntimeError(f"Cloned template missing .metadata directory: {repo}")
        if layout == "extend" and not (repo / "spec" / "extend").is_dir():
            raise RuntimeError(f"Cloned extend source missing spec/extend: {repo}")
        yield repo
