from __future__ import annotations

import copy
import json
import os
import shutil
import sys
import tempfile
import uuid
from collections.abc import Sequence
from pathlib import Path, PurePosixPath
from typing import Any, TextIO

import yaml

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


def _load_yaml_document(path: Path) -> Any:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        raise RuntimeError(f"Cannot read {path}: {e}") from e
    try:
        return yaml.safe_load(raw)
    except yaml.YAMLError as e:
        raise RuntimeError(f"Invalid YAML in {path}: {e}") from e


def _navigation_root_mapping(data: Any, *, path: Path) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise RuntimeError(f"{path}: expected a mapping at root, not {type(data).__name__}")
    return data


def _normalize_extend_registry_path(rel: str, *, nav_file: Path, context: str) -> str:
    if not isinstance(rel, str) or not rel:
        raise RuntimeError(f"{nav_file}: {context}: 'path' must be a non-empty string")
    p = PurePosixPath(rel.replace("\\", "/"))
    if p.is_absolute():
        raise RuntimeError(f"{nav_file}: {context}: path must be relative, got {rel!r}")
    if ".." in p.parts:
        raise RuntimeError(f"{nav_file}: {context}: path must not contain '..': {rel!r}")
    return str(p)


def _coalesce_read(cwd_read: str | None, src_read: str | None) -> str | None:
    """``None`` for each arg means the row omits ``read`` (default optional).

    Return ``required``, ``optional``, or ``None`` to omit ``read`` in the merged row.
    """
    if cwd_read == "required" or src_read == "required":
        return "required"
    if cwd_read == "optional" or src_read == "optional":
        return "optional"
    return None


def _read_field_from_item(item: dict[str, Any], *, nav_file: Path, key: str, i: int) -> str | None:
    """Return validated ``read`` or ``None`` if the key is absent."""
    if "read" not in item:
        return None
    v = item["read"]
    if v == "required" or v == "optional":
        return v
    if not isinstance(v, str):
        raise RuntimeError(
            f"{nav_file}: {key}[{i}].read must be 'required' or 'optional', not {type(v).__name__}",
        )
    raise RuntimeError(f"{nav_file}: {key}[{i}].read must be 'required' or 'optional', got {v!r}")


def _parse_registry_section(
    data: dict[str, Any],
    *,
    nav_file: Path,
    key: str,
) -> tuple[bool, list[dict[str, Any]]]:
    """Return whether ``key`` is present and a validated list of row mappings."""
    if key not in data:
        return False, []
    raw = data[key]
    if raw is None:
        raise RuntimeError(f"{nav_file}: {key!r} must be a list if present, not null")
    if not isinstance(raw, list):
        raise RuntimeError(f"{nav_file}: {key!r} must be a list")
    out: list[dict[str, Any]] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise RuntimeError(f"{nav_file}: {key}[{i}] must be a mapping")
        p = item.get("path")
        if not isinstance(p, str) or not p:
            raise RuntimeError(f"{nav_file}: {key}[{i}] must have a non-empty string 'path'")
        _normalize_extend_registry_path(p, nav_file=nav_file, context=f"{key}[{i}]")
        _read_field_from_item(item, nav_file=nav_file, key=key, i=i)
        out.append(item)
    return True, out


def _merge_read_field_into_row(
    cwd_row: dict[str, Any],
    src_item: dict[str, Any],
    *,
    cwd_nav: Path,
    src_nav: Path,
    key: str,
    cwd_i: int,
    src_i: int,
) -> dict[str, Any]:
    """Deep-copy ``cwd_row`` and merge only ``read`` from cwd and src; never copy ``description`` from src."""
    out = copy.deepcopy(cwd_row)
    cwd_read = _read_field_from_item(cwd_row, nav_file=cwd_nav, key=key, i=cwd_i)
    src_read = _read_field_from_item(src_item, nav_file=src_nav, key=key, i=src_i)
    coalesced = _coalesce_read(cwd_read, src_read)
    if coalesced is None:
        out.pop("read", None)
    else:
        out["read"] = coalesced
    return out


def _source_has_non_empty_design_list(data: dict[str, Any], *, nav_file: Path) -> bool:
    explicit, items = _parse_registry_section(data, nav_file=nav_file, key="design")
    return explicit and len(items) > 0


def _write_navigation_yaml_atomic(target: Path, data: dict[str, Any]) -> None:
    text = yaml.safe_dump(
        data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    if not text.endswith("\n"):
        text += "\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=target.parent,
        prefix=".navigation-",
        suffix=".yaml.tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.replace(tmp_path, target)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _merge_navigation_registry_sections_from_src(
    *,
    cwd_doc: dict[str, Any],
    src_doc: dict[str, Any],
    cwd_nav: Path,
    src_nav: Path,
    keys: tuple[str, ...],
) -> tuple[dict[str, Any], bool]:
    """Merge registry sections: append new normalized paths from src; on duplicates, cwd keeps row data except merged ``read``."""
    merged_doc = copy.deepcopy(cwd_doc)
    any_change = False
    for key in keys:
        _, cwd_items = _parse_registry_section(merged_doc, nav_file=cwd_nav, key=key)
        _, src_items = _parse_registry_section(src_doc, nav_file=src_nav, key=key)
        merged_list = [copy.deepcopy(x) for x in cwd_items]
        path_to_index: dict[str, int] = {}
        for i, item in enumerate(merged_list):
            nk = _normalize_extend_registry_path(
                item["path"],
                nav_file=cwd_nav,
                context=f"{key}[{i}]",
            )
            if nk not in path_to_index:
                path_to_index[nk] = i
        section_changed = False
        for i, item in enumerate(src_items):
            nk = _normalize_extend_registry_path(
                item["path"],
                nav_file=src_nav,
                context=f"{key}[{i}]",
            )
            if nk not in path_to_index:
                merged_list.append(copy.deepcopy(item))
                path_to_index[nk] = len(merged_list) - 1
                section_changed = True
                continue
            j = path_to_index[nk]
            merged_row = _merge_read_field_into_row(
                merged_list[j],
                item,
                cwd_nav=cwd_nav,
                src_nav=src_nav,
                key=key,
                cwd_i=j,
                src_i=i,
            )
            if merged_row != merged_list[j]:
                merged_list[j] = merged_row
                section_changed = True
        if section_changed:
            merged_doc[key] = merged_list
            any_change = True
    return merged_doc, any_change


def merge_template_source_navigation(*, cwd: Path, template_root: Path) -> None:
    """Merge ``extend:`` and ``design:`` from the template navigation file into cwd when both exist."""
    cwd_nav = (cwd / NAVIGATION_FILE_RELPATH).resolve()
    src_nav = (template_root / "spec" / "navigation.yaml").resolve()
    if not cwd_nav.is_file():
        return
    if not src_nav.is_file():
        return
    cwd_doc = _navigation_root_mapping(_load_yaml_document(cwd_nav), path=cwd_nav)
    src_doc = _navigation_root_mapping(_load_yaml_document(src_nav), path=src_nav)
    merged_doc, any_change = _merge_navigation_registry_sections_from_src(
        cwd_doc=cwd_doc,
        src_doc=src_doc,
        cwd_nav=cwd_nav,
        src_nav=src_nav,
        keys=("extend", "design"),
    )
    if any_change:
        _write_navigation_yaml_atomic(cwd_nav, merged_doc)


def merge_extend_source_navigation(
    *,
    cwd: Path,
    extend_root: Path,
    stderr: TextIO,
) -> None:
    """Merge ``extend:`` from ``extend_root/spec/navigation.yaml`` into cwd registry if both exist."""
    cwd_nav = (cwd / NAVIGATION_FILE_RELPATH).resolve()
    src_nav = (extend_root / "spec" / "navigation.yaml").resolve()
    if not cwd_nav.is_file():
        return
    if not src_nav.is_file():
        return

    cwd_doc = _navigation_root_mapping(_load_yaml_document(cwd_nav), path=cwd_nav)
    src_doc = _navigation_root_mapping(_load_yaml_document(src_nav), path=src_nav)

    if _source_has_non_empty_design_list(src_doc, nav_file=src_nav):
        print(
            "spectask-init: warning: extend source spec/navigation.yaml lists design entries; "
            "those are not merged into this project, and spec/design files are not copied from "
            "the extend bundle. --extend only adds files under spec/extend/ plus extend: registry "
            "entries from the source navigation file.",
            file=stderr,
        )

    merged_doc, any_change = _merge_navigation_registry_sections_from_src(
        cwd_doc=cwd_doc,
        src_doc=src_doc,
        cwd_nav=cwd_nav,
        src_nav=src_nav,
        keys=("extend",),
    )
    if any_change:
        _write_navigation_yaml_atomic(cwd_nav, merged_doc)


def _reconcile_registry_list(
    *,
    entries: list[dict[str, Any]],
    disk_paths: set[str],
    project_root: Path,
    nav_file: Path,
    section_name: str,
    placeholder_description: str,
    stderr: TextIO,
) -> tuple[list[dict[str, Any]], bool]:
    """Drop rows whose files are missing; append on-disk paths not yet listed. Preserve row order."""
    dirty = False
    retained: list[dict[str, Any]] = []
    retained_paths: set[str] = set()
    for i, item in enumerate(entries):
        norm = _normalize_extend_registry_path(
            item["path"],
            nav_file=nav_file,
            context=f"{section_name}[{i}]",
        )
        target = project_root.joinpath(*PurePosixPath(norm).parts)
        if target.is_file():
            retained.append(item)
            retained_paths.add(norm)
            continue
        print(
            f"spectask-init: warning: navigation registry path {norm!r} in {section_name!r} "
            f"points to a missing file; the entry was removed from {NAVIGATION_FILE_RELPATH}.",
            file=stderr,
        )
        dirty = True

    additions: list[dict[str, Any]] = []
    for norm in sorted(disk_paths - retained_paths):
        additions.append({"path": norm, "description": placeholder_description})
        print(
            f"spectask-init: warning: {norm!r} was not listed in {NAVIGATION_FILE_RELPATH} "
            f"under {section_name!r}; it was added with a placeholder description. "
            f"Edit the `description` field for this path in {NAVIGATION_FILE_RELPATH}.",
            file=stderr,
        )
        dirty = True

    return retained + additions, dirty


def reconcile_navigation_with_spec_tree(cwd: Path, stderr: TextIO | None = None) -> None:
    """Sync ``extend:`` / ``design:`` in ``spec/navigation.yaml`` with ``spec/extend/**/*.md`` and ``spec/design/*.md``."""
    err = stderr if stderr is not None else sys.stderr
    nav_path = (cwd / NAVIGATION_FILE_RELPATH).resolve()
    if not nav_path.is_file():
        return

    project_root = cwd.resolve()
    disk_extend: set[str] = set()
    ext_dir = project_root / "spec" / "extend"
    if ext_dir.is_dir():
        for p in ext_dir.rglob("*.md"):
            if p.is_file():
                rel = p.resolve().relative_to(project_root).as_posix()
                disk_extend.add(
                    _normalize_extend_registry_path(
                        rel,
                        nav_file=nav_path,
                        context="spec/extend",
                    ),
                )

    disk_design: set[str] = set()
    design_dir = project_root / "spec" / "design"
    if design_dir.is_dir():
        for p in design_dir.glob("*.md"):
            if p.is_file():
                rel = p.resolve().relative_to(project_root).as_posix()
                disk_design.add(
                    _normalize_extend_registry_path(
                        rel,
                        nav_file=nav_path,
                        context="spec/design",
                    ),
                )

    doc = _navigation_root_mapping(_load_yaml_document(nav_path), path=nav_path)
    extend_explicit, extend_entries = _parse_registry_section(doc, nav_file=nav_path, key="extend")
    design_explicit, design_entries = _parse_registry_section(doc, nav_file=nav_path, key="design")

    new_extend, dirty_extend = _reconcile_registry_list(
        entries=extend_entries,
        disk_paths=disk_extend,
        project_root=project_root,
        nav_file=nav_path,
        section_name="extend",
        placeholder_description="additional conventions",
        stderr=err,
    )
    new_design, dirty_design = _reconcile_registry_list(
        entries=design_entries,
        disk_paths=disk_design,
        project_root=project_root,
        nav_file=nav_path,
        section_name="design",
        placeholder_description="additional design document",
        stderr=err,
    )

    dirty = dirty_extend or dirty_design
    out_doc = copy.deepcopy(doc)
    if extend_explicit or new_extend:
        out_doc["extend"] = copy.deepcopy(new_extend)
    elif "extend" in out_doc:
        del out_doc["extend"]

    if design_explicit or new_design:
        out_doc["design"] = copy.deepcopy(new_design)
    elif "design" in out_doc:
        del out_doc["design"]

    if not dirty:
        return
    _write_navigation_yaml_atomic(nav_path, out_doc)


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
    """Fail before copying if required-list would overwrite an existing HLA file."""
    _ = skip_navigation_file  # Navigation uses merge-on-existing; not a preflight overwrite conflict.
    conflicts: list[str] = []
    for rel in required:
        if rel == "spec/design/hla.md" and not skip_hla_file and (cwd / rel).exists():
            conflicts.append(rel)
    if not conflicts:
        return
    seen: set[str] = set()
    uniq: list[str] = []
    for c in conflicts:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    paths = " and ".join(uniq)
    raise RuntimeError(
        f"Refusing to overwrite existing {paths}. "
        "Pass --skip-hla-file to keep your file and skip copying it from the template, "
        "or pass --update (applies --skip-example and --skip-hla-file).",
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
    stderr: TextIO | None = None,
) -> None:
    err = stderr if stderr is not None else sys.stderr
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
            if rel == NAVIGATION_FILE_RELPATH and (Path.cwd() / rel).is_file():
                merge_template_source_navigation(cwd=Path.cwd(), template_root=template_root)
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

        apply_template_migration(template_root=template_root, cwd=Path.cwd(), stderr=err)
        reconcile_navigation_with_spec_tree(Path.cwd(), stderr=err)


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


def run_extend(*, extend_url: str | None, extend_branch: str, stderr: TextIO | None = None) -> None:
    if not extend_url:
        return
    err = stderr if stderr is not None else sys.stderr
    with acquire_source(extend_url, git_branch=extend_branch, layout="extend") as root:
        merge_extend_source_navigation(cwd=Path.cwd(), extend_root=root, stderr=err)
        copy_extend_overlay(root)
        reconcile_navigation_with_spec_tree(Path.cwd(), stderr=err)
