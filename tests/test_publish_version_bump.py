from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_PUBLISH = _ROOT / "scripts" / "publish.py"


def _load_publish():
    spec = importlib.util.spec_from_file_location("_spectask_publish", _PUBLISH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_pub = _load_publish()
bump_patch_version = _pub.bump_patch_version
_project_root_version_line_index = _pub._project_root_version_line_index
bump_pyproject_version = _pub.bump_pyproject_version


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("0.1.0", "0.1.1"),
        ("2.0.9", "2.0.10"),
        ("1.0", "1.1"),
    ],
)
def test_bump_patch_version_ok(before: str, after: str) -> None:
    assert bump_patch_version(before) == after


@pytest.mark.parametrize(
    "bad",
    ["1", "1.0a1", "1.0.dev0", ""],
)
def test_bump_patch_version_rejects(bad: str) -> None:
    with pytest.raises(ValueError):
        bump_patch_version(bad)


def test_project_root_version_line_index_finds_version() -> None:
    lines = [
        "[build-system]\n",
        'requires = ["setuptools"]\n',
        "\n",
        "[project]\n",
        'name = "x"\n',
        'version = "0.1.0"\n',
        "\n",
        "[project.scripts]\n",
        'foo = "bar"\n',
    ]
    assert _project_root_version_line_index(lines) == 5


def test_bump_pyproject_version_roundtrip(tmp_path) -> None:
    p = tmp_path / "pyproject.toml"
    p.write_text(
        '[project]\nname = "spectask-init"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    assert bump_pyproject_version(p) == "0.1.1"
    text = p.read_text(encoding="utf-8")
    assert 'version = "0.1.1"' in text
    assert "0.1.0" not in text
