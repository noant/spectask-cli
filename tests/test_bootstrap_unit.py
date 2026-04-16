from __future__ import annotations

import io
import json
from contextlib import contextmanager
from pathlib import Path

import pytest

from spectask_init.bootstrap import (
    apply_template_migration,
    copy_into_cwd,
    ide_files_for,
    load_json,
    resolve_auto_ide_keys,
    run_template_bootstrap,
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
    assert resolve_auto_ide_keys(template_root=tpl, cwd=cwd, skills=skills) == ("cursor",)


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
    assert resolve_auto_ide_keys(template_root=tpl, cwd=cwd, skills=skills) == ("ws",)
    cwd2 = tmp_path / "proj2"
    cwd2.mkdir()
    (cwd2 / ".wsdir").mkdir()
    assert resolve_auto_ide_keys(template_root=tpl, cwd=cwd2, skills=skills) == ("ws",)


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
        resolve_auto_ide_keys(template_root=tpl, cwd=cwd, skills=skills)


def test_resolve_auto_multi_match_returns_keys_in_detection_order(tmp_path: Path) -> None:
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
    assert resolve_auto_ide_keys(template_root=tpl, cwd=cwd, skills=skills) == ("a", "b")

    _write_detection(
        meta,
        {
            "ides": [
                {"name": "b", "markers": [{"path": ".b", "kind": "directory"}]},
                {"name": "a", "markers": [{"path": ".a", "kind": "directory"}]},
            ],
        },
    )
    assert resolve_auto_ide_keys(template_root=tpl, cwd=cwd, skills=skills) == ("b", "a")


def test_resolve_auto_multi_match_merges_paths_like_explicit_keys(tmp_path: Path) -> None:
    tpl = tmp_path / "tpl"
    meta = tpl / ".metadata"
    skills = {
        "ides": [
            {"name": "a", "paths": ["shared.md", "only-a.md"]},
            {"name": "b", "paths": ["shared.md", "only-b.md"]},
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
    keys = resolve_auto_ide_keys(template_root=tpl, cwd=cwd, skills=skills)
    assert ide_files_for(skills, keys) == ide_files_for(skills, ("a", "b"))


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
        resolve_auto_ide_keys(template_root=tpl, cwd=cwd, skills=skills)


def test_resolve_auto_missing_detection_file(tmp_path: Path) -> None:
    tpl = tmp_path / "tpl"
    (tpl / ".metadata").mkdir(parents=True)
    skills = {"ides": [{"name": "cursor", "paths": ["a.md"]}]}
    cwd = tmp_path / "proj"
    cwd.mkdir()
    with pytest.raises(RuntimeError, match="does not include .metadata/ide-detection.json"):
        resolve_auto_ide_keys(template_root=tpl, cwd=cwd, skills=skills)


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
        resolve_auto_ide_keys(template_root=tpl, cwd=cwd, skills=skills)


def test_copy_into_cwd_rejects_escape(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "tpl"
    root.mkdir()
    other = tmp_path / "outside"
    other.mkdir()
    (other / "secret.txt").write_text("x", encoding="utf-8")
    with pytest.raises(RuntimeError, match="outside template root"):
        copy_into_cwd(root, "../outside/secret.txt")


def _minimal_template_root(tmp_path: Path) -> Path:
    root = tmp_path / "tpl"
    meta = root / ".metadata"
    meta.mkdir(parents=True)
    (meta / "required-list.json").write_text(
        json.dumps(
            {
                "required": [
                    "spec/navigation.yaml",
                    "spec/design/hla.md",
                ],
            },
        ),
        encoding="utf-8",
    )
    (meta / "example-list.json").write_text(
        json.dumps({"examples": []}),
        encoding="utf-8",
    )
    (meta / "skills-map.json").write_text(
        json.dumps({"ides": [{"name": "cursor", "paths": ["only-cursor.md"]}]}),
        encoding="utf-8",
    )
    (root / "spec").mkdir(parents=True)
    (root / "spec" / "navigation.yaml").write_text("tpl-nav\n", encoding="utf-8")
    (root / "spec" / "design").mkdir()
    (root / "spec" / "design" / "hla.md").write_text("tpl-hla\n", encoding="utf-8")
    (root / "only-cursor.md").write_text("skill\n", encoding="utf-8")
    return root


def _fake_acquire_root(template_root: Path):
    @contextmanager
    def _acquire(url: str, *, git_branch: str, layout: str):
        yield template_root

    return _acquire


def test_preflight_existing_navigation_refuses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tpl = _minimal_template_root(tmp_path)
    proj = tmp_path / "proj"
    proj.mkdir()
    monkeypatch.chdir(proj)
    (proj / "spec").mkdir()
    (proj / "spec" / "navigation.yaml").write_text("existing\n", encoding="utf-8")
    monkeypatch.setattr("spectask_init.bootstrap.acquire_source", _fake_acquire_root(tpl))
    with pytest.raises(RuntimeError, match="spec/navigation.yaml") as exc:
        run_template_bootstrap(
            template_url="https://example.com/x.zip",
            ide=("cursor",),
            skip_example=True,
            skip_navigation_file=False,
            skip_hla_file=False,
            template_branch="main",
        )
    msg = str(exc.value)
    assert "--update" in msg
    assert "--skip-navigation-file" in msg


def test_preflight_existing_hla_refuses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tpl = _minimal_template_root(tmp_path)
    proj = tmp_path / "proj"
    proj.mkdir()
    monkeypatch.chdir(proj)
    (proj / "spec").mkdir(parents=True)
    (proj / "spec" / "design").mkdir()
    (proj / "spec" / "design" / "hla.md").write_text("existing\n", encoding="utf-8")
    monkeypatch.setattr("spectask_init.bootstrap.acquire_source", _fake_acquire_root(tpl))
    with pytest.raises(RuntimeError, match="spec/design/hla.md") as exc:
        run_template_bootstrap(
            template_url="https://example.com/x.zip",
            ide=("cursor",),
            skip_example=True,
            skip_navigation_file=False,
            skip_hla_file=False,
            template_branch="main",
        )
    msg = str(exc.value)
    assert "--update" in msg
    assert "--skip-hla-file" in msg


def test_preflight_both_existing_refuses_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tpl = _minimal_template_root(tmp_path)
    proj = tmp_path / "proj"
    proj.mkdir()
    monkeypatch.chdir(proj)
    (proj / "spec").mkdir()
    (proj / "spec" / "navigation.yaml").write_text("n\n", encoding="utf-8")
    (proj / "spec" / "design").mkdir()
    (proj / "spec" / "design" / "hla.md").write_text("h\n", encoding="utf-8")
    monkeypatch.setattr("spectask_init.bootstrap.acquire_source", _fake_acquire_root(tpl))
    with pytest.raises(RuntimeError) as exc:
        run_template_bootstrap(
            template_url="https://example.com/x.zip",
            ide=("cursor",),
            skip_example=True,
            skip_navigation_file=False,
            skip_hla_file=False,
            template_branch="main",
        )
    msg = str(exc.value)
    assert "spec/navigation.yaml" in msg
    assert "spec/design/hla.md" in msg
    assert "--skip-navigation-file" in msg
    assert "--skip-hla-file" in msg


def test_preflight_skip_navigation_allows_existing_navigation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tpl = _minimal_template_root(tmp_path)
    proj = tmp_path / "proj"
    proj.mkdir()
    monkeypatch.chdir(proj)
    (proj / "spec").mkdir()
    (proj / "spec" / "navigation.yaml").write_text("keep-me\n", encoding="utf-8")
    monkeypatch.setattr("spectask_init.bootstrap.acquire_source", _fake_acquire_root(tpl))
    run_template_bootstrap(
        template_url="https://example.com/x.zip",
        ide=("cursor",),
        skip_example=True,
        skip_navigation_file=True,
        skip_hla_file=False,
        template_branch="main",
    )
    assert (proj / "spec" / "navigation.yaml").read_text(encoding="utf-8") == "keep-me\n"
    assert (proj / "spec" / "design" / "hla.md").read_text(encoding="utf-8") == "tpl-hla\n"


def test_preflight_skip_hla_allows_existing_hla(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tpl = _minimal_template_root(tmp_path)
    proj = tmp_path / "proj"
    proj.mkdir()
    monkeypatch.chdir(proj)
    (proj / "spec").mkdir()
    (proj / "spec" / "design").mkdir()
    (proj / "spec" / "design" / "hla.md").write_text("keep-me\n", encoding="utf-8")
    monkeypatch.setattr("spectask_init.bootstrap.acquire_source", _fake_acquire_root(tpl))
    run_template_bootstrap(
        template_url="https://example.com/x.zip",
        ide=("cursor",),
        skip_example=True,
        skip_navigation_file=False,
        skip_hla_file=True,
        template_branch="main",
    )
    assert (proj / "spec" / "design" / "hla.md").read_text(encoding="utf-8") == "keep-me\n"
    assert (proj / "spec" / "navigation.yaml").read_text(encoding="utf-8") == "tpl-nav\n"


def _migration_file(meta: Path, data: dict) -> None:
    (meta / "migration.json").write_text(json.dumps(data), encoding="utf-8")


def test_migration_missing_file_noop(tmp_path: Path) -> None:
    tpl = tmp_path / "tpl"
    (tpl / ".metadata").mkdir(parents=True)
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    err = io.StringIO()
    apply_template_migration(template_root=tpl, cwd=cwd, stderr=err)
    assert err.getvalue() == ""


def test_migration_invalid_move_type(tmp_path: Path) -> None:
    tpl = tmp_path / "tpl"
    (tpl / ".metadata").mkdir(parents=True)
    _migration_file(tpl / ".metadata", {"move": "nope"})
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    with pytest.raises(RuntimeError, match="'move' must be an array"):
        apply_template_migration(template_root=tpl, cwd=cwd, stderr=io.StringIO())


def test_migration_rejects_dotdot(tmp_path: Path) -> None:
    tpl = tmp_path / "tpl"
    meta = tpl / ".metadata"
    meta.mkdir(parents=True)
    _migration_file(meta, {"move": [{"from": "../x", "to": "y"}], "delete": []})
    cwd = tmp_path / "proj"
    cwd.mkdir()
    with pytest.raises(RuntimeError, match=r"\.\."):
        apply_template_migration(template_root=tpl, cwd=cwd, stderr=io.StringIO())


def test_migration_move_skips_missing_from(tmp_path: Path) -> None:
    tpl = tmp_path / "tpl"
    meta = tpl / ".metadata"
    meta.mkdir(parents=True)
    _migration_file(meta, {"move": [{"from": "nope.txt", "to": "out.txt"}], "delete": []})
    cwd = tmp_path / "proj"
    cwd.mkdir()
    err = io.StringIO()
    apply_template_migration(template_root=tpl, cwd=cwd, stderr=err)
    assert err.getvalue() == ""
    assert not (cwd / "out.txt").exists()


def test_migration_delete_missing_noop(tmp_path: Path) -> None:
    tpl = tmp_path / "tpl"
    meta = tpl / ".metadata"
    meta.mkdir(parents=True)
    _migration_file(meta, {"move": [], "delete": ["gone.txt"]})
    cwd = tmp_path / "proj"
    cwd.mkdir()
    err = io.StringIO()
    apply_template_migration(template_root=tpl, cwd=cwd, stderr=err)
    assert err.getvalue() == ""


def test_migration_delete_quarantines_and_warns(tmp_path: Path) -> None:
    tpl = tmp_path / "tpl"
    meta = tpl / ".metadata"
    meta.mkdir(parents=True)
    _migration_file(meta, {"move": [], "delete": ["old.txt"]})
    cwd = tmp_path / "proj"
    cwd.mkdir()
    (cwd / "old.txt").write_text("bye", encoding="utf-8")
    err = io.StringIO()
    apply_template_migration(template_root=tpl, cwd=cwd, stderr=err)
    assert not (cwd / "old.txt").exists()
    backup_dir = cwd / ".backup_spectask"
    assert backup_dir.is_dir()
    backed = list(backup_dir.iterdir())
    assert len(backed) == 1
    assert backed[0].name.startswith("old.txt_")
    assert backed[0].read_text(encoding="utf-8") == "bye"
    out = err.getvalue()
    assert "quarantined" in out
    assert "`.backup_spectask/`" in out
    assert ".gitignore" in out


def test_migration_move_displaces_destination(tmp_path: Path) -> None:
    tpl = tmp_path / "tpl"
    meta = tpl / ".metadata"
    meta.mkdir(parents=True)
    _migration_file(meta, {"move": [{"from": "src.txt", "to": "dst.txt"}], "delete": []})
    cwd = tmp_path / "proj"
    cwd.mkdir()
    (cwd / "src.txt").write_text("new", encoding="utf-8")
    (cwd / "dst.txt").write_text("old", encoding="utf-8")
    err = io.StringIO()
    apply_template_migration(template_root=tpl, cwd=cwd, stderr=err)
    assert (cwd / "dst.txt").read_text(encoding="utf-8") == "new"
    backup_dir = cwd / ".backup_spectask"
    backed = list(backup_dir.iterdir())
    assert len(backed) == 1
    assert backed[0].name.startswith("dst.txt_")
    assert backed[0].read_text(encoding="utf-8") == "old"
    assert "Existing destination" in err.getvalue()
    assert ".gitignore" in err.getvalue()


def test_migration_operations_delete(tmp_path: Path) -> None:
    tpl = tmp_path / "tpl"
    meta = tpl / ".metadata"
    meta.mkdir(parents=True)
    _migration_file(
        meta,
        {"version": 1, "operations": [{"type": "delete", "path": "gone.txt"}]},
    )
    cwd = tmp_path / "proj"
    cwd.mkdir()
    (cwd / "gone.txt").write_text("x", encoding="utf-8")
    err = io.StringIO()
    apply_template_migration(template_root=tpl, cwd=cwd, stderr=err)
    assert not (cwd / "gone.txt").exists()
    assert "quarantined" in err.getvalue()


def test_migration_operations_unknown_type(tmp_path: Path) -> None:
    tpl = tmp_path / "tpl"
    meta = tpl / ".metadata"
    meta.mkdir(parents=True)
    _migration_file(meta, {"operations": [{"type": "purge", "path": "x"}]})
    cwd = tmp_path / "proj"
    cwd.mkdir()
    with pytest.raises(RuntimeError, match="must be 'delete' or 'move'"):
        apply_template_migration(template_root=tpl, cwd=cwd, stderr=io.StringIO())


def test_migration_operations_order_interleaved(tmp_path: Path) -> None:
    tpl = tmp_path / "tpl"
    meta = tpl / ".metadata"
    meta.mkdir(parents=True)
    _migration_file(
        meta,
        {
            "operations": [
                {"type": "move", "from": "src.txt", "to": "out.txt"},
                {"type": "delete", "path": "src.txt"},
            ],
        },
    )
    cwd = tmp_path / "proj"
    cwd.mkdir()
    (cwd / "src.txt").write_text("data", encoding="utf-8")
    err = io.StringIO()
    apply_template_migration(template_root=tpl, cwd=cwd, stderr=err)
    assert (cwd / "out.txt").read_text(encoding="utf-8") == "data"
    assert not (cwd / "src.txt").exists()
    assert err.getvalue() == ""


def test_migration_moves_before_deletes(tmp_path: Path) -> None:
    tpl = tmp_path / "tpl"
    meta = tpl / ".metadata"
    meta.mkdir(parents=True)
    _migration_file(
        meta,
        {
            "move": [{"from": "src.txt", "to": "out.txt"}],
            "delete": ["src.txt"],
        },
    )
    cwd = tmp_path / "proj"
    cwd.mkdir()
    (cwd / "src.txt").write_text("data", encoding="utf-8")
    err = io.StringIO()
    apply_template_migration(template_root=tpl, cwd=cwd, stderr=err)
    assert (cwd / "out.txt").read_text(encoding="utf-8") == "data"
    assert not (cwd / "src.txt").exists()
    assert err.getvalue() == ""


def test_run_template_bootstrap_runs_migration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tpl = _minimal_template_root(tmp_path)
    _migration_file(
        tpl / ".metadata",
        {
            "move": [{"from": "legacy.txt", "to": "kept.txt"}],
            "delete": [],
        },
    )
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "legacy.txt").write_text("L", encoding="utf-8")
    monkeypatch.chdir(proj)
    monkeypatch.setattr("spectask_init.bootstrap.acquire_source", _fake_acquire_root(tpl))
    run_template_bootstrap(
        template_url="https://example.com/x.zip",
        ide=("cursor",),
        skip_example=True,
        skip_navigation_file=True,
        skip_hla_file=True,
        template_branch="main",
    )
    assert (proj / "kept.txt").read_text(encoding="utf-8") == "L"
    assert not (proj / "legacy.txt").exists()
