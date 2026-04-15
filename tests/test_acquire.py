from __future__ import annotations

import pytest

from spectask_init.acquire import is_zip_url, resolve_zip_base


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://github.com/o/r/archive/refs/heads/main.zip", True),
        ("https://example.com/path.ZIP", True),
        ("https://github.com/noant/spectask.git", False),
        ("https://example.com/archive.zip/extra", False),
    ],
)
def test_is_zip_url(url: str, expected: bool) -> None:
    assert is_zip_url(url) is expected


def test_resolve_zip_base_template_at_root(tmp_path) -> None:
    root = tmp_path / "extract"
    root.mkdir()
    (root / ".metadata").mkdir()
    assert resolve_zip_base(root, "template") == root


def test_resolve_zip_base_template_one_wrapper(tmp_path) -> None:
    extract = tmp_path / "extract"
    extract.mkdir()
    inner = extract / "repo-main"
    inner.mkdir()
    (inner / ".metadata").mkdir()
    assert resolve_zip_base(extract, "template") == inner


def test_resolve_zip_base_extend_at_root(tmp_path) -> None:
    root = tmp_path / "extract"
    root.mkdir()
    (root / "spec" / "extend").mkdir(parents=True)
    assert resolve_zip_base(root, "extend") == root


def test_resolve_zip_base_extend_one_wrapper(tmp_path) -> None:
    extract = tmp_path / "extract"
    extract.mkdir()
    inner = extract / "repo-main"
    inner.mkdir()
    (inner / "spec" / "extend").mkdir(parents=True)
    assert resolve_zip_base(extract, "extend") == inner


def test_resolve_zip_base_template_fails(tmp_path) -> None:
    root = tmp_path / "extract"
    root.mkdir()
    with pytest.raises(RuntimeError, match="Cannot resolve template root"):
        resolve_zip_base(root, "template")
