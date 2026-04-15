from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from spectask_init.acquire import acquire_source


def _paths_from_entry(entry: dict[str, Any]) -> list[str] | None:
    """IDE entries use `paths` (spec) or `files` (upstream template)."""
    if "paths" in entry:
        v = entry["paths"]
    elif "files" in entry:
        v = entry["files"]
    else:
        return None
    if not isinstance(v, list):
        return None
    return [p for p in v if isinstance(p, str)]


def load_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        raise RuntimeError(f"Cannot read {path}: {e}") from e
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON in {path}: {e}") from e
    if not isinstance(data, dict):
        raise RuntimeError(f"Expected JSON object at root in {path}")
    return data


def ide_files_for(skills: dict[str, Any], ide: str) -> list[str]:
    ides = skills.get("ides")
    if not isinstance(ides, list):
        raise RuntimeError("skills-map.json: missing or invalid 'ides' array")

    if ide == "all":
        seen: set[str] = set()
        out: list[str] = []
        for entry in ides:
            if not isinstance(entry, dict):
                continue
            paths = _paths_from_entry(entry)
            if not paths:
                continue
            for p in paths:
                if p not in seen:
                    seen.add(p)
                    out.append(p)
        return out

    for entry in ides:
        if not isinstance(entry, dict):
            continue
        if entry.get("name") != ide:
            continue
        paths = _paths_from_entry(entry)
        if paths is None:
            raise RuntimeError(
                f"skills-map.json: IDE {ide!r} must have a 'paths' or 'files' array of strings",
            )
        return paths

    raise RuntimeError(f"Unknown IDE {ide!r} in skills-map.json (not in ides[].name, and not 'all')")


def copy_into_cwd(template_root: Path, rel_path: str) -> None:
    src = (template_root / rel_path).resolve()
    root = template_root.resolve()
    try:
        src.relative_to(root)
    except ValueError as e:
        raise RuntimeError(f"Refusing to copy path outside template root: {rel_path!r}") from e

    if not src.exists():
        raise RuntimeError(f"Template missing path {rel_path!r} (expected under {template_root})")

    dest = (Path.cwd() / rel_path).resolve()
    cwd = Path.cwd().resolve()
    try:
        dest.relative_to(cwd)
    except ValueError as e:
        raise RuntimeError(f"Refusing to copy outside current working directory: {rel_path!r}") from e

    if src.is_file():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    elif src.is_dir():
        shutil.copytree(src, dest, dirs_exist_ok=True)
    else:
        raise RuntimeError(f"Not a file or directory: {rel_path!r}")


def run_template_bootstrap(
    *,
    template_url: str,
    ide: str,
    skip_example: bool,
    skip_navigation_file: bool,
    template_branch: str,
) -> None:
    with acquire_source(template_url, git_branch=template_branch, layout="template") as template_root:
        meta = template_root / ".metadata"
        required_data = load_json(meta / "required-list.json")
        required = required_data.get("required")
        if not isinstance(required, list):
            raise RuntimeError("required-list.json: missing or invalid 'required' array")
        for rel in required:
            if not isinstance(rel, str):
                raise RuntimeError("required-list.json: 'required' must be a list of strings")
            if skip_navigation_file and rel == "spec/navigation.md":
                continue
            copy_into_cwd(template_root, rel)

        if not skip_example:
            example_data = load_json(meta / "example-list.json")
            examples = example_data.get("examples")
            if not isinstance(examples, list):
                raise RuntimeError("example-list.json: missing or invalid 'examples' array")
            for rel in examples:
                if not isinstance(rel, str):
                    raise RuntimeError("example-list.json: 'examples' must be a list of strings")
                copy_into_cwd(template_root, rel)

        skills = load_json(meta / "skills-map.json")
        for rel in ide_files_for(skills, ide):
            copy_into_cwd(template_root, rel)


def copy_extend_overlay(extend_root: Path) -> None:
    src_dir = extend_root / "spec" / "extend"
    if not src_dir.is_dir():
        raise FileNotFoundError(f"No spec/extend in extend source: {src_dir}")
    dest_root = Path.cwd()
    for path in src_dir.rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(src_dir)
        dest = dest_root / "spec" / "extend" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)


def run_extend(*, extend_url: str | None, extend_branch: str) -> None:
    if not extend_url:
        return
    with acquire_source(extend_url, git_branch=extend_branch, layout="extend") as root:
        copy_extend_overlay(root)
