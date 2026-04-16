from __future__ import annotations

import json
import shutil
from collections.abc import Sequence
from pathlib import Path, PurePosixPath
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


def _ide_paths_union_all(skills: dict[str, Any]) -> list[str]:
    ides = skills.get("ides")
    if not isinstance(ides, list):
        raise RuntimeError("skills-map.json: missing or invalid 'ides' array")
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


def _ide_paths_for_name(skills: dict[str, Any], ide: str) -> list[str]:
    ides = skills.get("ides")
    if not isinstance(ides, list):
        raise RuntimeError("skills-map.json: missing or invalid 'ides' array")

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


def ide_files_for(skills: dict[str, Any], ide: str | Sequence[str]) -> list[str]:
    keys: tuple[str, ...] = (ide,) if isinstance(ide, str) else tuple(ide)
    if len(keys) == 0:
        raise RuntimeError("At least one IDE key is required")
    if "auto" in keys:
        if len(keys) != 1:
            raise RuntimeError(
                "When using 'auto', it must be the only --ide value (do not combine with other IDE keys)",
            )
        raise RuntimeError(
            "'auto' must be resolved using .metadata/ide-detection.json before selecting IDE files",
        )
    if "all" in keys:
        if len(keys) != 1:
            raise RuntimeError(
                "When using 'all', it must be the only --ide value (do not combine with other IDE keys)",
            )
        return _ide_paths_union_all(skills)

    seen: set[str] = set()
    out: list[str] = []
    for k in keys:
        for p in _ide_paths_for_name(skills, k):
            if p not in seen:
                seen.add(p)
                out.append(p)
    return out


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


def _explicit_ide_names_from_skills(skills: dict[str, Any]) -> list[str]:
    ides = skills.get("ides")
    if not isinstance(ides, list):
        raise RuntimeError("skills-map.json: missing or invalid 'ides' array")
    out: list[str] = []
    for entry in ides:
        if isinstance(entry, dict):
            name = entry.get("name")
            if isinstance(name, str) and name:
                out.append(name)
    return out


def _cwd_marker_target(cwd: Path, path_str: str) -> Path:
    p = PurePosixPath(path_str)
    if not path_str or p.is_absolute() or ".." in p.parts:
        raise RuntimeError(
            f"ide-detection.json: invalid marker path {path_str!r} "
            "(must be non-empty, relative, and must not contain '..')",
        )
    return cwd.joinpath(*p.parts) if p.parts else cwd


def _marker_matches(cwd: Path, path_str: str, kind: str) -> bool:
    target = _cwd_marker_target(cwd, path_str)
    if kind == "directory":
        return target.is_dir()
    if kind == "file":
        return target.is_file()
    raise RuntimeError(f"ide-detection.json: marker kind must be 'file' or 'directory', got {kind!r}")


def _ide_entry_matches_cwd(cwd: Path, markers: list[dict[str, Any]]) -> bool:
    return any(_marker_matches(cwd, m["path"], m["kind"]) for m in markers)


def _load_and_validate_ide_detection(
    path: Path,
    skills: dict[str, Any],
) -> list[dict[str, Any]]:
    data = load_json(path)
    ides = data.get("ides")
    if not isinstance(ides, list):
        raise RuntimeError(f"ide-detection.json: missing or invalid 'ides' array ({path})")
    known = _explicit_ide_names_from_skills(skills)
    known_set = set(known)
    validated: list[dict[str, Any]] = []
    for i, entry in enumerate(ides):
        if not isinstance(entry, dict):
            raise RuntimeError(f"ide-detection.json: ides[{i}] must be an object ({path})")
        name = entry.get("name")
        if not isinstance(name, str) or not name:
            raise RuntimeError(f"ide-detection.json: ides[{i}] must have a non-empty string 'name' ({path})")
        if name not in known_set:
            raise RuntimeError(
                f"ide-detection.json: unknown IDE name {name!r} (not in skills-map.json ides[].name)",
            )
        markers_raw = entry.get("markers")
        if not isinstance(markers_raw, list):
            raise RuntimeError(f"ide-detection.json: ides[{i}].markers must be an array ({path})")
        markers: list[dict[str, Any]] = []
        for j, m in enumerate(markers_raw):
            if not isinstance(m, dict):
                raise RuntimeError(
                    f"ide-detection.json: ides[{i}].markers[{j}] must be an object ({path})",
                )
            p = m.get("path")
            k = m.get("kind")
            if not isinstance(p, str) or not p:
                raise RuntimeError(
                    f"ide-detection.json: ides[{i}].markers[{j}].path must be a non-empty string ({path})",
                )
            if k not in ("file", "directory"):
                raise RuntimeError(
                    f"ide-detection.json: ides[{i}].markers[{j}].kind must be 'file' or 'directory' ({path})",
                )
            markers.append({"path": p, "kind": k})
        validated.append({"name": name, "markers": markers})
    return validated


def resolve_auto_ide_key(*, template_root: Path, cwd: Path, skills: dict[str, Any]) -> str:
    """Resolve ``auto`` using template ``.metadata/ide-detection.json`` and marker checks under ``cwd``."""
    detection_path = template_root / ".metadata" / "ide-detection.json"
    if not detection_path.is_file():
        keys = ", ".join(_explicit_ide_names_from_skills(skills))
        raise RuntimeError(
            "This template does not include .metadata/ide-detection.json; cannot use --ide auto. "
            f"Use --ide all or an explicit IDE key: {keys}",
        )
    entries = _load_and_validate_ide_detection(detection_path, skills)
    matched: list[str] = []
    for e in entries:
        if _ide_entry_matches_cwd(cwd, e["markers"]):
            matched.append(e["name"])
    explicit = ", ".join(_explicit_ide_names_from_skills(skills))
    if len(matched) == 0:
        raise RuntimeError(
            "Could not detect IDE from the current directory (no markers matched). "
            f"Use --ide all to install files for every IDE, or pass one of: {explicit}",
        )
    if len(matched) > 1:
        listed = ", ".join(matched)
        raise RuntimeError(
            f"IDE detection is ambiguous; multiple environments match: {listed}. "
            "Pass an explicit --ide value instead of auto.",
        )
    return matched[0]


def run_template_bootstrap(
    *,
    template_url: str,
    ide: tuple[str, ...],
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
        ide_effective = ide
        if ide == ("auto",):
            ide_effective = (resolve_auto_ide_key(template_root=template_root, cwd=Path.cwd(), skills=skills),)
        for rel in ide_files_for(skills, ide_effective):
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
