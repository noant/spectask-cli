"""Focused tests for `--extend` navigation merge (spec/tasks/17 step 3)."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest
import yaml

from spectask_init.bootstrap import (
    copy_extend_overlay,
    merge_extend_source_navigation,
    merge_template_source_navigation,
)


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


# --- read: merge (template + extend), task 20-navigation-read-merge step 2 ---


def _proj_tpl(tmp_path: Path) -> tuple[Path, Path]:
    proj = tmp_path / "proj"
    tpl = tmp_path / "tpl"
    (proj / "spec").mkdir(parents=True)
    (tpl / "spec").mkdir(parents=True)
    return proj, tpl


def test_merge_template_cwd_omits_read_template_required(tmp_path: Path) -> None:
    proj, tpl = _proj_tpl(tmp_path)
    (proj / "spec" / "navigation.yaml").write_text(
        "version: 1\n"
        "extend:\n"
        "  - path: spec/extend/shared.md\n"
        "    description: from cwd\n"
        "design: []\n",
        encoding="utf-8",
    )
    (tpl / "spec" / "navigation.yaml").write_text(
        "version: 1\n"
        "extend:\n"
        "  - path: spec/extend/shared.md\n"
        "    read: required\n"
        "design: []\n",
        encoding="utf-8",
    )
    merge_template_source_navigation(cwd=proj, template_root=tpl)
    doc = yaml.safe_load((proj / "spec" / "navigation.yaml").read_text(encoding="utf-8"))
    row = doc["extend"][0]
    assert row["read"] == "required"
    assert row["description"] == "from cwd"


def test_merge_template_cwd_optional_template_required(tmp_path: Path) -> None:
    proj, tpl = _proj_tpl(tmp_path)
    (proj / "spec" / "navigation.yaml").write_text(
        "version: 1\n"
        "extend:\n"
        "  - path: spec/extend/shared.md\n"
        "    description: from cwd\n"
        "    read: optional\n"
        "design: []\n",
        encoding="utf-8",
    )
    (tpl / "spec" / "navigation.yaml").write_text(
        "version: 1\n"
        "extend:\n"
        "  - path: spec/extend/shared.md\n"
        "    read: required\n"
        "design: []\n",
        encoding="utf-8",
    )
    merge_template_source_navigation(cwd=proj, template_root=tpl)
    doc = yaml.safe_load((proj / "spec" / "navigation.yaml").read_text(encoding="utf-8"))
    assert doc["extend"][0]["read"] == "required"
    assert doc["extend"][0]["description"] == "from cwd"


@pytest.mark.parametrize(
    "source_tail",
    [
        "    read: optional\n",
        "",
    ],
    ids=["source_optional", "source_omits_read"],
)
def test_merge_extend_cwd_required_source_optional_or_omits(
    tmp_path: Path, source_tail: str
) -> None:
    proj = tmp_path / "proj"
    ext = tmp_path / "ext"
    (proj / "spec").mkdir(parents=True)
    (ext / "spec").mkdir(parents=True)
    (proj / "spec" / "navigation.yaml").write_text(
        "version: 1\n"
        "extend:\n"
        "  - path: spec/extend/shared.md\n"
        "    description: cwd\n"
        "    read: required\n"
        "design: []\n",
        encoding="utf-8",
    )
    (ext / "spec" / "navigation.yaml").write_text(
        "extend:\n"
        "  - path: spec/extend/shared.md\n"
        "    description: ignored\n"
        f"{source_tail}",
        encoding="utf-8",
    )
    err = io.StringIO()
    merge_extend_source_navigation(cwd=proj, extend_root=ext, stderr=err)
    doc = yaml.safe_load((proj / "spec" / "navigation.yaml").read_text(encoding="utf-8"))
    assert doc["extend"][0]["read"] == "required"
    assert doc["extend"][0]["description"] == "cwd"
    assert err.getvalue() == ""


def test_merge_extend_cwd_omits_source_optional_and_reverse(tmp_path: Path) -> None:
    # cwd omits, source optional -> optional
    proj = tmp_path / "proj_a"
    ext = tmp_path / "ext_a"
    (proj / "spec").mkdir(parents=True)
    (ext / "spec").mkdir(parents=True)
    (proj / "spec" / "navigation.yaml").write_text(
        "version: 1\n"
        "extend:\n"
        "  - path: spec/extend/shared.md\n"
        "    description: cwd\n"
        "design: []\n",
        encoding="utf-8",
    )
    (ext / "spec" / "navigation.yaml").write_text(
        "extend:\n"
        "  - path: spec/extend/shared.md\n"
        "    read: optional\n",
        encoding="utf-8",
    )
    merge_extend_source_navigation(cwd=proj, extend_root=ext, stderr=io.StringIO())
    doc = yaml.safe_load((proj / "spec" / "navigation.yaml").read_text(encoding="utf-8"))
    assert doc["extend"][0]["read"] == "optional"

    # reverse: cwd optional, source omits -> optional
    proj2 = tmp_path / "proj_b"
    ext2 = tmp_path / "ext_b"
    (proj2 / "spec").mkdir(parents=True)
    (ext2 / "spec").mkdir(parents=True)
    (proj2 / "spec" / "navigation.yaml").write_text(
        "version: 1\n"
        "extend:\n"
        "  - path: spec/extend/y.md\n"
        "    read: optional\n"
        "design: []\n",
        encoding="utf-8",
    )
    (ext2 / "spec" / "navigation.yaml").write_text(
        "extend:\n  - path: spec/extend/y.md\n    description: src\n",
        encoding="utf-8",
    )
    merge_extend_source_navigation(cwd=proj2, extend_root=ext2, stderr=io.StringIO())
    doc2 = yaml.safe_load((proj2 / "spec" / "navigation.yaml").read_text(encoding="utf-8"))
    assert doc2["extend"][0]["read"] == "optional"


def test_merge_extend_duplicate_both_omit_read(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    ext = tmp_path / "ext"
    (proj / "spec").mkdir(parents=True)
    (ext / "spec").mkdir(parents=True)
    (proj / "spec" / "navigation.yaml").write_text(
        "version: 1\n"
        "extend:\n"
        "  - path: spec/extend/dup.md\n"
        "    description: one\n"
        "  - path: spec/extend/only-cwd.md\n"
        "    description: b\n"
        "design: []\n",
        encoding="utf-8",
    )
    (ext / "spec" / "navigation.yaml").write_text(
        "extend:\n"
        "  - path: spec/extend/dup.md\n"
        "    description: ignored\n"
        "  - path: spec/extend/new-from-ext.md\n"
        "    description: new\n",
        encoding="utf-8",
    )
    merge_extend_source_navigation(cwd=proj, extend_root=ext, stderr=io.StringIO())
    doc = yaml.safe_load((proj / "spec" / "navigation.yaml").read_text(encoding="utf-8"))
    by_path = {row["path"]: row for row in doc["extend"]}
    assert "read" not in by_path["spec/extend/dup.md"]
    assert "read" not in by_path["spec/extend/only-cwd.md"]
    assert "read" not in by_path["spec/extend/new-from-ext.md"]


def test_merge_extend_appends_new_path_deep_copies_read(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    ext = tmp_path / "ext"
    (proj / "spec").mkdir(parents=True)
    (ext / "spec").mkdir(parents=True)
    (proj / "spec" / "navigation.yaml").write_text(
        "version: 1\n"
        "extend:\n  - path: spec/extend/a.md\n    description: A\n"
        "design: []\n",
        encoding="utf-8",
    )
    (ext / "spec" / "navigation.yaml").write_text(
        "version: 1\n"
        "extend:\n"
        "  - path: spec/extend/b.md\n"
        "    description: B from source\n"
        "    read: required\n",
        encoding="utf-8",
    )
    merge_extend_source_navigation(cwd=proj, extend_root=ext, stderr=io.StringIO())
    doc = yaml.safe_load((proj / "spec" / "navigation.yaml").read_text(encoding="utf-8"))
    assert [r["path"] for r in doc["extend"]] == ["spec/extend/a.md", "spec/extend/b.md"]
    assert doc["extend"][1]["read"] == "required"
    assert doc["extend"][1]["description"] == "B from source"


def test_merge_template_invalid_read_in_cwd_raises(tmp_path: Path) -> None:
    proj, tpl = _proj_tpl(tmp_path)
    (proj / "spec" / "navigation.yaml").write_text(
        "extend:\n  - path: spec/extend/x.md\n    read: maybe\n",
        encoding="utf-8",
    )
    (tpl / "spec" / "navigation.yaml").write_text("extend: []\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match=r"read must be 'required' or 'optional'"):
        merge_template_source_navigation(cwd=proj, template_root=tpl)


def test_merge_template_invalid_read_in_template_raises(tmp_path: Path) -> None:
    proj, tpl = _proj_tpl(tmp_path)
    (proj / "spec" / "navigation.yaml").write_text("extend: []\n", encoding="utf-8")
    (tpl / "spec" / "navigation.yaml").write_text(
        "extend:\n  - path: spec/extend/x.md\n    read: 1\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match=r"read must be 'required' or 'optional'"):
        merge_template_source_navigation(cwd=proj, template_root=tpl)


def test_merge_extend_invalid_read_in_cwd_raises(tmp_path: Path) -> None:
    proj, ext_root = _proj_tpl(tmp_path)
    (proj / "spec" / "navigation.yaml").write_text(
        "extend:\n  - path: spec/extend/x.md\n    read: bad\n",
        encoding="utf-8",
    )
    (ext_root / "spec" / "navigation.yaml").write_text("extend: []\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match=r"read must be 'required' or 'optional'"):
        merge_extend_source_navigation(cwd=proj, extend_root=ext_root, stderr=io.StringIO())


def test_merge_extend_invalid_read_in_source_raises(tmp_path: Path) -> None:
    proj, ext_root = _proj_tpl(tmp_path)
    (proj / "spec" / "navigation.yaml").write_text("extend: []\n", encoding="utf-8")
    (ext_root / "spec" / "navigation.yaml").write_text(
        "extend:\n  - path: spec/extend/x.md\n    read: []\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match=r"read must be 'required' or 'optional'"):
        merge_extend_source_navigation(cwd=proj, extend_root=ext_root, stderr=io.StringIO())
