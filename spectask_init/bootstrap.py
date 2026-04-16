from __future__ import annotations

import json
import shutil
import sys
import uuid
from collections.abc import Sequence
from pathlib import Path, PurePosixPath
from typing import Any, TextIO

from spectask_init.acquire import acquire_source

# Required-list path for the Spectask navigation registry (see upstream `required-list.json`).
NAVIGATION_FILE_RELPATH = "spec/navigation.yaml"


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


def _validate_migration_rel_path(rel: str, *, migration_file: Path, context: str) -> None:
    if not isinstance(rel, str) or not rel:
        raise RuntimeError(f"migration.json: {context} must be a non-empty string ({migration_file})")
    p = PurePosixPath(rel)
    if p.is_absolute() or ".." in p.parts:
        raise RuntimeError(
            f"migration.json: invalid path {rel!r} in {context} "
            f"(must be relative with no '..') ({migration_file})",
        )
    if len(rel) > 1 and rel[1] == ":":
        raise RuntimeError(
            f"migration.json: invalid path {rel!r} in {context} ({migration_file})",
        )


def _migration_target_under_cwd(cwd: Path, rel: str, *, migration_file: Path, context: str) -> Path:
    _validate_migration_rel_path(rel, migration_file=migration_file, context=context)
    root = cwd.resolve()
    target = root.joinpath(*PurePosixPath(rel).parts).resolve()
    try:
        target.relative_to(root)
    except ValueError as e:
        raise RuntimeError(
            f"migration.json: path escapes working directory: {rel!r} ({context}) ({migration_file})",
        ) from e
    return target


def _parse_migration_steps(data: dict[str, Any], migration_file: Path) -> list[tuple[str, str, str]]:
    """Return ordered steps: (\"move\", from, to) or (\"delete\", path, \"\")."""
    if "operations" in data:
        ops_raw = data["operations"]
        if ops_raw is None:
            ops_raw = []
        if not isinstance(ops_raw, list):
            raise RuntimeError(f"migration.json: 'operations' must be an array ({migration_file})")
        out: list[tuple[str, str, str]] = []
        for i, item in enumerate(ops_raw):
            if not isinstance(item, dict):
                raise RuntimeError(f"migration.json: operations[{i}] must be an object ({migration_file})")
            op = item.get("type")
            if not isinstance(op, str):
                raise RuntimeError(
                    f"migration.json: operations[{i}].type must be a string ({migration_file})",
                )
            if op == "delete":
                rel = item.get("path")
                if not isinstance(rel, str):
                    raise RuntimeError(
                        f"migration.json: operations[{i}] (delete) must have string 'path' ({migration_file})",
                    )
                _validate_migration_rel_path(
                    rel,
                    migration_file=migration_file,
                    context=f"operations[{i}].path",
                )
                out.append(("delete", rel, ""))
            elif op == "move":
                fr = item.get("from")
                to = item.get("to")
                if not isinstance(fr, str) or not isinstance(to, str):
                    raise RuntimeError(
                        f"migration.json: operations[{i}] (move) must have string 'from' and 'to' "
                        f"({migration_file})",
                    )
                _validate_migration_rel_path(
                    fr,
                    migration_file=migration_file,
                    context=f"operations[{i}].from",
                )
                _validate_migration_rel_path(
                    to,
                    migration_file=migration_file,
                    context=f"operations[{i}].to",
                )
                out.append(("move", fr, to))
            else:
                raise RuntimeError(
                    f"migration.json: operations[{i}].type must be 'delete' or 'move', not {op!r} "
                    f"({migration_file})",
                )
        return out

    moves_raw = data.get("move", [])
    deletes_raw = data.get("delete", [])
    if moves_raw is None:
        moves_raw = []
    if deletes_raw is None:
        deletes_raw = []
    if not isinstance(moves_raw, list):
        raise RuntimeError(f"migration.json: 'move' must be an array ({migration_file})")
    if not isinstance(deletes_raw, list):
        raise RuntimeError(f"migration.json: 'delete' must be an array ({migration_file})")
    legacy_moves: list[tuple[str, str]] = []
    for i, item in enumerate(moves_raw):
        if not isinstance(item, dict):
            raise RuntimeError(f"migration.json: move[{i}] must be an object ({migration_file})")
        fr = item.get("from")
        to = item.get("to")
        if not isinstance(fr, str) or not isinstance(to, str):
            raise RuntimeError(
                f"migration.json: move[{i}] must have string 'from' and 'to' ({migration_file})",
            )
        _validate_migration_rel_path(fr, migration_file=migration_file, context=f"move[{i}].from")
        _validate_migration_rel_path(to, migration_file=migration_file, context=f"move[{i}].to")
        legacy_moves.append((fr, to))
    legacy_deletes: list[str] = []
    for i, rel in enumerate(deletes_raw):
        if not isinstance(rel, str):
            raise RuntimeError(f"migration.json: delete[{i}] must be a string ({migration_file})")
        _validate_migration_rel_path(rel, migration_file=migration_file, context=f"delete[{i}]")
        legacy_deletes.append(rel)
    steps: list[tuple[str, str, str]] = [("move", a, b) for a, b in legacy_moves]
    steps.extend(("delete", d, "") for d in legacy_deletes)
    return steps


def _quarantine_under_backup(
    *,
    cwd: Path,
    path: Path,
    stderr: TextIO,
    message: str,
) -> Path:
    backup_root = (cwd / ".backup_spectask").resolve()
    backup_root.mkdir(parents=True, exist_ok=True)
    dest_name = f"{path.name}_{uuid.uuid4().hex}"
    dest = backup_root / dest_name
    shutil.move(str(path), str(dest))
    print(f"spectask-init: {message} Backup: {dest}", file=stderr)
    return dest


def apply_template_migration(
    *,
    template_root: Path,
    cwd: Path | None = None,
    stderr: TextIO | None = None,
) -> None:
    """Apply optional ``.metadata/migration.json`` under ``cwd``.

    Supports an ``operations`` array (``type``: ``move`` / ``delete``) in order, or legacy
    top-level ``move`` then ``delete`` arrays (all moves first, then all deletes).
    """
    cwd = cwd or Path.cwd()
    err = stderr if stderr is not None else sys.stderr
    migration_path = template_root / ".metadata" / "migration.json"
    if not migration_path.is_file():
        return
    data = load_json(migration_path)
    steps = _parse_migration_steps(data, migration_path)
    quarantined_any = False

    for kind, a, b in steps:
        if kind == "move":
            fr, to = a, b
            src = _migration_target_under_cwd(cwd, fr, migration_file=migration_path, context="move.from")
            dst = _migration_target_under_cwd(cwd, to, migration_file=migration_path, context="move.to")
            if not src.exists():
                continue
            if dst.exists():
                _quarantine_under_backup(
                    cwd=cwd,
                    path=dst,
                    stderr=err,
                    message=(
                        f"Existing destination {to!r} was moved aside to apply migration. "
                        "Review the backup and delete it if you no longer need that content."
                    ),
                )
                quarantined_any = True
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
        elif kind == "delete":
            rel = a
            target = _migration_target_under_cwd(cwd, rel, migration_file=migration_path, context="delete")
            if not target.exists():
                continue
            _quarantine_under_backup(
                cwd=cwd,
                path=target,
                stderr=err,
                message=(
                    f"Path {rel!r} is marked for removal by the template migration and was quarantined "
                    "(not deleted in place). Review the backup and delete it when ready."
                ),
            )
            quarantined_any = True

    if quarantined_any:
        print(
            "spectask-init: Consider adding `.backup_spectask/` to `.gitignore` "
            "if you do not want quarantined files tracked.",
            file=err,
        )


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


def _preflight_required_navigation_and_hla(
    *,
    cwd: Path,
    required: list[str],
    skip_navigation_file: bool,
    skip_hla_file: bool,
) -> None:
    """Fail before copying if required-list would overwrite existing navigation or HLA files."""
    conflicts: list[str] = []
    for rel in required:
        if rel == NAVIGATION_FILE_RELPATH and not skip_navigation_file and (cwd / rel).exists():
            conflicts.append(rel)
        elif rel == "spec/design/hla.md" and not skip_hla_file and (cwd / rel).exists():
            conflicts.append(rel)
    if not conflicts:
        return
    seen: set[str] = set()
    uniq: list[str] = []
    for c in conflicts:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    update_hint = (
        "Use --update (implies --skip-example, --skip-navigation-file, and --skip-hla-file)"
    )
    if len(uniq) == 1:
        path = uniq[0]
        skip_flag = "--skip-navigation-file" if path == NAVIGATION_FILE_RELPATH else "--skip-hla-file"
        raise RuntimeError(
            f"Refusing to overwrite existing {path}. {update_hint} "
            f"or {skip_flag} to keep your file and skip copying it from the template.",
        )
    paths = " and ".join(uniq)
    raise RuntimeError(
        f"Refusing to overwrite existing files: {paths}. {update_hint}, "
        "or pass --skip-navigation-file and/or --skip-hla-file to skip copying the matching "
        "files from the template.",
    )


def resolve_auto_ide_keys(*, template_root: Path, cwd: Path, skills: dict[str, Any]) -> tuple[str, ...]:
    """Resolve ``auto`` using template ``.metadata/ide-detection.json`` and marker checks under ``cwd``.

    Returns one or more IDE keys in ``ide-detection.json`` ``ides[]`` order for every entry that matches.
    """
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
    return tuple(matched)


def run_template_bootstrap(
    *,
    template_url: str,
    ide: tuple[str, ...],
    skip_example: bool,
    skip_navigation_file: bool,
    skip_hla_file: bool,
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
        _preflight_required_navigation_and_hla(
            cwd=Path.cwd(),
            required=required,
            skip_navigation_file=skip_navigation_file,
            skip_hla_file=skip_hla_file,
        )
        for rel in required:
            if skip_navigation_file and rel == NAVIGATION_FILE_RELPATH:
                continue
            if skip_hla_file and rel == "spec/design/hla.md":
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
            ide_effective = resolve_auto_ide_keys(template_root=template_root, cwd=Path.cwd(), skills=skills)
        for rel in ide_files_for(skills, ide_effective):
            copy_into_cwd(template_root, rel)

        apply_template_migration(template_root=template_root, cwd=Path.cwd())


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
