"""Focused tests for `--extend` navigation merge (spec/tasks/17 step 3)."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest
import yaml

from spectask_init.bootstrap import copy_extend_overlay, merge_extend_source_navigation


def test_merge_append_order_cwd_a_then_source_b_c(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    ext = tmp_path / "ext"
    (proj / "spec").mkdir(parents=True)
    (ext / "spec").mkdir(parents=True)
    (proj / "spec" / "navigation.yaml").write_text(
        "version: 1\n"
        "extend:\n"
        "  - path: spec/extend/a.md\n"
        "    description: from cwd\n"
        "design: []\n",
        encoding="utf-8",
    )
    (ext / "spec" / "navigation.yaml").write_text(
        "version: 1\n"
        "extend:\n"
        "  - path: spec/extend/b.md\n"
        "    description: B from source\n"
        "  - path: spec/extend/c.md\n"
        "    description: C from source\n",
        encoding="utf-8",
    )
    err = io.StringIO()
    merge_extend_source_navigation(cwd=proj, extend_root=ext, stderr=err)
    doc = yaml.safe_load((proj / "spec" / "navigation.yaml").read_text(encoding="utf-8"))
    paths = [row["path"] for row in doc["extend"]]
    assert paths == ["spec/extend/a.md", "spec/extend/b.md", "spec/extend/c.md"]
    assert doc["extend"][0]["description"] == "from cwd"
    assert doc["extend"][1]["description"] == "B from source"
    assert doc["extend"][2]["description"] == "C from source"
    assert err.getvalue() == ""


def test_merge_dedup_preserves_cwd_description_no_rewrite(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    ext = tmp_path / "ext"
    (proj / "spec").mkdir(parents=True)
    (ext / "spec").mkdir(parents=True)
    nav_cwd = (
        "version: 1\n"
        "extend:\n"
        "  - path: spec/extend/shared.md\n"
        "    description: cwd wins\n"
        "design: []\n"
    )
    (proj / "spec" / "navigation.yaml").write_text(nav_cwd, encoding="utf-8")
    (ext / "spec" / "navigation.yaml").write_text(
        "extend:\n"
        "  - path: spec/extend/shared.md\n"
        "    description: source should not apply\n",
        encoding="utf-8",
    )
    err = io.StringIO()
    merge_extend_source_navigation(cwd=proj, extend_root=ext, stderr=err)
    assert (proj / "spec" / "navigation.yaml").read_text(encoding="utf-8") == nav_cwd
    assert err.getvalue() == ""


def test_merge_path_normalization_backslashes_no_duplicate(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    ext = tmp_path / "ext"
    (proj / "spec").mkdir(parents=True)
    (ext / "spec").mkdir(parents=True)
    (proj / "spec" / "navigation.yaml").write_text(
        "extend:\n  - path: spec/extend/a.md\n    description: one\n",
        encoding="utf-8",
    )
    (ext / "spec" / "navigation.yaml").write_text(
        "extend:\n  - path: spec\\extend\\a.md\n    description: dup\n",
        encoding="utf-8",
    )
    err = io.StringIO()
    merge_extend_source_navigation(cwd=proj, extend_root=ext, stderr=err)
    doc = yaml.safe_load((proj / "spec" / "navigation.yaml").read_text(encoding="utf-8"))
    assert len(doc["extend"]) == 1
    assert doc["extend"][0]["description"] == "one"
    assert err.getvalue() == ""


def test_merge_source_design_warns_cwd_design_unchanged_no_design_files_from_extend(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    proj = tmp_path / "proj"
    ext = tmp_path / "ext"
    (proj / "spec").mkdir(parents=True)
    (ext / "spec").mkdir(parents=True)
    (ext / "spec" / "design").mkdir(parents=True)
    (ext / "spec" / "design" / "from_extend.md").write_text("x", encoding="utf-8")
    cwd_nav = (
        "version: 1\n"
        "extend:\n"
        "  - path: spec/extend/a.md\n"
        "design:\n"
        "  - path: spec/design/hla.md\n"
        "    description: only in cwd\n"
    )
    (proj / "spec" / "navigation.yaml").write_text(cwd_nav, encoding="utf-8")
    (ext / "spec" / "navigation.yaml").write_text(
        "extend:\n"
        "  - path: spec/extend/b.md\n"
        "    description: from extend\n"
        "design:\n"
        "  - path: spec/design/from_extend.md\n"
        "    description: should not merge\n",
        encoding="utf-8",
    )
    merge_extend_source_navigation(cwd=proj, extend_root=ext, stderr=sys.stderr)
    captured = capsys.readouterr()
    assert "design entries" in captured.err
    assert "not copied" in captured.err
    doc = yaml.safe_load((proj / "spec" / "navigation.yaml").read_text(encoding="utf-8"))
    assert doc["design"] == [{"path": "spec/design/hla.md", "description": "only in cwd"}]
    assert [row["path"] for row in doc["extend"]] == ["spec/extend/a.md", "spec/extend/b.md"]
    assert not (proj / "spec" / "design").exists()


def test_no_source_navigation_merge_noop_overlay_copies_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proj = tmp_path / "proj"
    ext = tmp_path / "ext"
    proj.mkdir()
    (proj / "spec").mkdir(parents=True)
    (ext / "spec" / "extend").mkdir(parents=True)
    (ext / "spec" / "extend" / "rule.md").write_text("body", encoding="utf-8")
    (proj / "spec" / "navigation.yaml").write_text(
        "extend:\n  - path: spec/extend/old.md\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(proj)
    err = io.StringIO()
    merge_extend_source_navigation(cwd=proj, extend_root=ext, stderr=err)
    assert not (ext / "spec" / "navigation.yaml").exists()
    assert err.getvalue() == ""
    nav_before = (proj / "spec" / "navigation.yaml").read_text(encoding="utf-8")
    copy_extend_overlay(ext)
    assert (proj / "spec" / "extend" / "rule.md").read_text(encoding="utf-8") == "body"
    assert (proj / "spec" / "navigation.yaml").read_text(encoding="utf-8") == nav_before


def test_no_cwd_navigation_merge_skipped_overlay_copies_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proj = tmp_path / "proj"
    ext = tmp_path / "ext"
    proj.mkdir()
    (ext / "spec").mkdir(parents=True)
    (ext / "spec" / "navigation.yaml").write_text(
        "extend:\n  - path: spec/extend/x.md\n",
        encoding="utf-8",
    )
    (ext / "spec" / "extend").mkdir(parents=True)
    (ext / "spec" / "extend" / "x.md").write_text("x", encoding="utf-8")
    monkeypatch.chdir(proj)
    err = io.StringIO()
    merge_extend_source_navigation(cwd=proj, extend_root=ext, stderr=err)
    assert not (proj / "spec" / "navigation.yaml").exists()
    assert err.getvalue() == ""
    copy_extend_overlay(ext)
    assert (proj / "spec" / "extend" / "x.md").read_text(encoding="utf-8") == "x"


def test_merge_invalid_yaml_in_source_raises_clear_message(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    ext = tmp_path / "ext"
    (proj / "spec").mkdir(parents=True)
    (ext / "spec").mkdir(parents=True)
    (proj / "spec" / "navigation.yaml").write_text("extend: []\n", encoding="utf-8")
    (ext / "spec" / "navigation.yaml").write_text("extend: [", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Invalid YAML") as exc:
        merge_extend_source_navigation(cwd=proj, extend_root=ext, stderr=io.StringIO())
    assert "navigation.yaml" in str(exc.value)


def test_merge_invalid_yaml_in_cwd_raises_clear_message(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    ext = tmp_path / "ext"
    (proj / "spec").mkdir(parents=True)
    (ext / "spec").mkdir(parents=True)
    (proj / "spec" / "navigation.yaml").write_text("extend: [", encoding="utf-8")
    (ext / "spec" / "navigation.yaml").write_text("extend: []\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Invalid YAML") as exc:
        merge_extend_source_navigation(cwd=proj, extend_root=ext, stderr=io.StringIO())
    assert "navigation.yaml" in str(exc.value)
