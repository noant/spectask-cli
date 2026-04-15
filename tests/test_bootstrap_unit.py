from __future__ import annotations

from pathlib import Path

import pytest

from spectask_init.bootstrap import copy_into_cwd, ide_files_for, load_json


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


def test_copy_into_cwd_rejects_escape(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "tpl"
    root.mkdir()
    other = tmp_path / "outside"
    other.mkdir()
    (other / "secret.txt").write_text("x", encoding="utf-8")
    with pytest.raises(RuntimeError, match="outside template root"):
        copy_into_cwd(root, "../outside/secret.txt")
