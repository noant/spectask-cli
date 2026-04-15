from __future__ import annotations

import pytest

from spectask_init.cli import DEFAULT_TEMPLATE_URL, OFFICIAL_TEMPLATE_IDE_KEYS, parse_args


def test_parse_defaults() -> None:
    o = parse_args(["--ide", "cursor"])
    assert o.template_url == DEFAULT_TEMPLATE_URL
    assert o.ide == "cursor"
    assert o.template_branch == "main"
    assert o.extend is None
    assert o.extend_branch == "main"
    assert o.skip_example is False
    assert o.skip_navigation_file is False


def test_parse_custom_template_and_branches() -> None:
    o = parse_args(
        [
            "--template-url",
            "https://example.com/t.zip",
            "--ide",
            "windsurf",
            "--template-branch",
            "develop",
            "--extend-branch",
            "topic",
        ]
    )
    assert o.template_url == "https://example.com/t.zip"
    assert o.ide == "windsurf"
    assert o.template_branch == "develop"
    assert o.extend is None
    assert o.extend_branch == "topic"


def test_parse_extend_git() -> None:
    o = parse_args(
        [
            "--ide",
            "cursor",
            "--extend",
            "https://github.com/noant/spectask-my-extend.git",
            "--extend-branch",
            "main",
        ]
    )
    assert o.extend == "https://github.com/noant/spectask-my-extend.git"
    assert o.extend_branch == "main"


def test_parse_skip_example() -> None:
    o = parse_args(["--ide", "cursor", "--skip-example"])
    assert o.skip_example is True


def test_parse_skip_navigation_file() -> None:
    o = parse_args(["--ide", "cursor", "--skip-navigation-file"])
    assert o.skip_navigation_file is True


@pytest.mark.parametrize("ide", [*OFFICIAL_TEMPLATE_IDE_KEYS, "all"])
def test_parse_default_template_accepts_official_ide_keys(ide: str) -> None:
    o = parse_args(["--ide", ide])
    assert o.ide == ide


def test_parse_default_template_rejects_unknown_ide() -> None:
    with pytest.raises(SystemExit):
        parse_args(["--ide", "not-a-listed-ide"])


def test_parse_custom_template_accepts_arbitrary_ide() -> None:
    o = parse_args(
        ["--template-url", "https://example.com/t.zip", "--ide", "custom-vendor-ide"],
    )
    assert o.ide == "custom-vendor-ide"


def test_parse_ide_required() -> None:
    with pytest.raises(SystemExit):
        parse_args([])
