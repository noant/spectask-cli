from __future__ import annotations

import json
from pathlib import Path

import pytest

from spectask_init.bootstrap import (
    copy_into_cwd,
    ide_files_for,
    load_json,
    resolve_auto_ide_key,
)


def test_ide_files_for_named() -> None:
    skills = {
        "ides": [
            {"name": "cursor", "paths": ["a.md", "b.md"]},
            {"name": "other", "files": ["c.md"]},
        ]
    }
    assert ide_files_for(skills, "cursor") == ["a.md", "b.md"]
    assert ide_files_for(skills, "other") == ["c.md"]


def test_ide_files_for_all_dedupes() -> None:
    skills = {
        "ides": [
            {"name": "a", "paths": ["shared.md", "only-a.md"]},
            {"name": "b", "files": ["shared.md", "only-b.md"]},
        ]
    }
    assert ide_files_for(skills, "all") == ["shared.md", "only-a.md", "only-b.md"]


def test_ide_files_for_multiple_merges_and_dedupes() -> None:
    skills = {
        "ides": [
            {"name": "cursor", "paths": ["shared.md", "only-cursor.md"]},
            {"name": "other", "files": ["shared.md", "only-other.md"]},
        ]
    }
    assert ide_files_for(skills, ("cursor", "other")) == [
        "shared.md",
        "only-cursor.md",
        "only-other.md",
    ]
    assert ide_files_for(skills, ("cursor", "cursor")) == ["shared.md", "only-cursor.md"]


def test_ide_files_for_all_must_be_alone() -> None:
    skills = {"ides": [{"name": "cursor", "paths": ["x.md"]}]}
    with pytest.raises(RuntimeError, match="only --ide value"):
        ide_files_for(skills, ("all", "cursor"))


def test_ide_files_for_auto_must_be_resolved() -> None:
    skills = {"ides": [{"name": "cursor", "paths": ["x.md"]}]}
    with pytest.raises(RuntimeError, match="ide-detection"):
        ide_files_for(skills, "auto")


def test_ide_files_for_auto_must_be_alone() -> None:
    skills = {"ides": [{"name": "cursor", "paths": ["x.md"]}]}
    with pytest.raises(RuntimeError, match="only --ide value"):
        ide_files_for(skills, ("auto", "cursor"))


def test_ide_files_for_unknown_ide() -> None:
    skills = {"ides": [{"name": "cursor", "paths": ["x.md"]}]}
    with pytest.raises(RuntimeError, match="Unknown IDE"):
        ide_files_for(skills, "missing")


def test_ide_files_for_missing_ides() -> None:
    with pytest.raises(RuntimeError, match="ides"):
        ide_files_for({}, "cursor")


def test_ide_files_for_named_without_paths() -> None:
    skills = {"ides": [{"name": "cursor", "oops": []}]}
    with pytest.raises(RuntimeError, match="must have a 'paths' or 'files'"):
        ide_files_for(skills, "cursor")


def test_load_json_invalid(tmp_path) -> None:
    p = tmp_path / "bad.json"
    p.write_text("not json", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Invalid JSON"):
        load_json(p)


def test_copy_into_cwd_file(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "tpl"
    (root / "dir").mkdir(parents=True)
    src = root / "dir" / "f.txt"
    src.write_text("hi", encoding="utf-8")
    copy_into_cwd(root, "dir/f.txt")
    assert (tmp_path / "dir" / "f.txt").read_text(encoding="utf-8") == "hi"


def _write_detection(meta: Path, data: dict) -> None:
    meta.mkdir(parents=True, exist_ok=True)
    (meta / "ide-detection.json").write_text(json.dumps(data), encoding="utf-8")


def test_resolve_auto_single_match(tmp_path: Path) -> None:
    tpl = tmp_path / "tpl"
    meta = tpl / ".metadata"
    skills = {
        "ides": [
            {"name": "cursor", "paths": ["a.md"]},
            {"name": "other", "paths": ["b.md"]},
        ],
    }
    _write_detection(
        meta,
        {
            "ides": [
                {"name": "cursor", "markers": [{"path": ".cursor", "kind": "directory"}]},
                {"name": "other", "markers": [{"path": ".other", "kind": "directory"}]},
            ],
        },
    )
    cwd = tmp_path / "proj"
    cwd.mkdir()
    (cwd / ".cursor").mkdir()
    assert resolve_auto_ide_key(template_root=tpl, cwd=cwd, skills=skills) == "cursor"


def test_resolve_auto_or_file_or_directory(tmp_path: Path) -> None:
    tpl = tmp_path / "tpl"
    meta = tpl / ".metadata"
    skills = {"ides": [{"name": "ws", "paths": ["a.md"]}]}
    _write_detection(
        meta,
        {
            "ides": [
                {
                    "name": "ws",
                    "markers": [
                        {"path": ".rules", "kind": "file"},
                        {"path": ".wsdir", "kind": "directory"},
                    ],
                },
            ],
        },
    )
    cwd = tmp_path / "proj1"
    cwd.mkdir()
    (cwd / ".rules").write_text("x", encoding="utf-8")
    assert resolve_auto_ide_key(template_root=tpl, cwd=cwd, skills=skills) == "ws"
    cwd2 = tmp_path / "proj2"
    cwd2.mkdir()
    (cwd2 / ".wsdir").mkdir()
    assert resolve_auto_ide_key(template_root=tpl, cwd=cwd2, skills=skills) == "ws"


def test_resolve_auto_wrong_kind_no_match(tmp_path: Path) -> None:
    tpl = tmp_path / "tpl"
    meta = tpl / ".metadata"
    skills = {"ides": [{"name": "cursor", "paths": ["a.md"]}]}
    _write_detection(
        meta,
        {"ides": [{"name": "cursor", "markers": [{"path": ".cursor", "kind": "directory"}]}]},
    )
    cwd = tmp_path / "proj"
    cwd.mkdir()
    (cwd / ".cursor").write_text("file-not-dir", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Could not detect IDE"):
        resolve_auto_ide_key(template_root=tpl, cwd=cwd, skills=skills)


def test_resolve_auto_ambiguous(tmp_path: Path) -> None:
    tpl = tmp_path / "tpl"
    meta = tpl / ".metadata"
    skills = {
        "ides": [
            {"name": "a", "paths": ["x.md"]},
            {"name": "b", "paths": ["y.md"]},
        ],
    }
    _write_detection(
        meta,
        {
            "ides": [
                {"name": "a", "markers": [{"path": ".a", "kind": "directory"}]},
                {"name": "b", "markers": [{"path": ".b", "kind": "directory"}]},
            ],
        },
    )
    cwd = tmp_path / "proj"
    cwd.mkdir()
    (cwd / ".a").mkdir()
    (cwd / ".b").mkdir()
    with pytest.raises(RuntimeError, match="ambiguous"):
        resolve_auto_ide_key(template_root=tpl, cwd=cwd, skills=skills)


def test_resolve_auto_unknown_detection_name(tmp_path: Path) -> None:
    tpl = tmp_path / "tpl"
    meta = tpl / ".metadata"
    skills = {"ides": [{"name": "cursor", "paths": ["a.md"]}]}
    _write_detection(
        meta,
        {"ides": [{"name": "not-in-skills", "markers": [{"path": ".x", "kind": "directory"}]}]},
    )
    cwd = tmp_path / "proj"
    cwd.mkdir()
    with pytest.raises(RuntimeError, match="skills-map"):
        resolve_auto_ide_key(template_root=tpl, cwd=cwd, skills=skills)


def test_resolve_auto_missing_detection_file(tmp_path: Path) -> None:
    tpl = tmp_path / "tpl"
    (tpl / ".metadata").mkdir(parents=True)
    skills = {"ides": [{"name": "cursor", "paths": ["a.md"]}]}
    cwd = tmp_path / "proj"
    cwd.mkdir()
    with pytest.raises(RuntimeError, match="does not include .metadata/ide-detection.json"):
        resolve_auto_ide_key(template_root=tpl, cwd=cwd, skills=skills)


def test_resolve_auto_invalid_marker_path(tmp_path: Path) -> None:
    tpl = tmp_path / "tpl"
    meta = tpl / ".metadata"
    skills = {"ides": [{"name": "cursor", "paths": ["a.md"]}]}
    _write_detection(
        meta,
        {"ides": [{"name": "cursor", "markers": [{"path": "../outside", "kind": "file"}]}]},
    )
    cwd = tmp_path / "proj"
    cwd.mkdir()
    with pytest.raises(RuntimeError, match="invalid marker path"):
        resolve_auto_ide_key(template_root=tpl, cwd=cwd, skills=skills)


def test_copy_into_cwd_rejects_escape(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "tpl"
    root.mkdir()
    other = tmp_path / "outside"
    other.mkdir()
    (other / "secret.txt").write_text("x", encoding="utf-8")
    with pytest.raises(RuntimeError, match="outside template root"):
        copy_into_cwd(root, "../outside/secret.txt")
