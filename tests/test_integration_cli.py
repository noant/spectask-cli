from __future__ import annotations

import sys
from pathlib import Path

import pytest

from spectask_init.cli import main

TEMPLATE_ZIP = "https://github.com/noant/spectask/archive/refs/heads/main.zip"
TEMPLATE_GIT = "https://github.com/noant/spectask.git"
EXTEND_ZIP = "https://github.com/noant/spectask-my-extend/archive/refs/heads/main.zip"
EXTEND_GIT = "https://github.com/noant/spectask-my-extend.git"

EXAMPLE_ONLY = Path("spec/tasks/0-example-hello/overview.md")
EXTEND_OVERLAY = Path("spec/extend/0-misc.md")
CURSOR_SKILL = Path(".cursor/skills/spectask-create/SKILL.md")


def _mkdir_for_cursor_ide_auto(tmp_path: Path) -> None:
    """CWD layout so noant/spectask main ZIP resolves ``--ide auto`` to cursor (see .metadata/ide-detection.json)."""
    (tmp_path / ".cursor").mkdir()


def _run_main(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, argv: list[str]) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["spectask-init", *argv])
    main()


def _assert_baseline(cwd: Path) -> None:
    assert (cwd / "spec/main.md").is_file()
    assert (cwd / "spec/navigation.md").is_file()
    assert (cwd / "spec/design/hla.md").is_file()


@pytest.mark.integration
def test_zip_template_and_zip_extend(tmp_path, monkeypatch) -> None:
    _run_main(
        monkeypatch,
        tmp_path,
        [
            "--template-url",
            TEMPLATE_ZIP,
            "--template-branch",
            "unused-for-zip",
            "--ide",
            "cursor",
            "--extend",
            EXTEND_ZIP,
            "--extend-branch",
            "unused-for-zip",
        ],
    )
    _assert_baseline(tmp_path)
    assert (tmp_path / EXTEND_OVERLAY).is_file()
    assert (tmp_path / CURSOR_SKILL).is_file()


@pytest.mark.integration
def test_git_template_and_git_extend(tmp_path, monkeypatch, git_on_path) -> None:
    _run_main(
        monkeypatch,
        tmp_path,
        [
            "--template-url",
            TEMPLATE_GIT,
            "--template-branch",
            "main",
            "--ide",
            "cursor",
            "--extend",
            EXTEND_GIT,
            "--extend-branch",
            "main",
        ],
    )
    _assert_baseline(tmp_path)
    assert (tmp_path / EXTEND_OVERLAY).is_file()


@pytest.mark.integration
def test_zip_template_only(tmp_path, monkeypatch) -> None:
    _run_main(
        monkeypatch,
        tmp_path,
        ["--template-url", TEMPLATE_ZIP, "--ide", "cursor"],
    )
    _assert_baseline(tmp_path)
    assert not (tmp_path / EXTEND_OVERLAY).is_file()


@pytest.mark.integration
def test_git_template_only(tmp_path, monkeypatch, git_on_path) -> None:
    _run_main(
        monkeypatch,
        tmp_path,
        ["--template-url", TEMPLATE_GIT, "--template-branch", "main", "--ide", "cursor"],
    )
    _assert_baseline(tmp_path)
    assert not (tmp_path / EXTEND_OVERLAY).is_file()


@pytest.mark.integration
def test_zip_template_and_git_extend(tmp_path, monkeypatch, git_on_path) -> None:
    _run_main(
        monkeypatch,
        tmp_path,
        [
            "--template-url",
            TEMPLATE_ZIP,
            "--ide",
            "cursor",
            "--extend",
            EXTEND_GIT,
            "--extend-branch",
            "main",
        ],
    )
    _assert_baseline(tmp_path)
    assert (tmp_path / EXTEND_OVERLAY).is_file()


@pytest.mark.integration
def test_git_template_and_zip_extend(tmp_path, monkeypatch, git_on_path) -> None:
    _run_main(
        monkeypatch,
        tmp_path,
        [
            "--template-url",
            TEMPLATE_GIT,
            "--template-branch",
            "main",
            "--ide",
            "cursor",
            "--extend",
            EXTEND_ZIP,
        ],
    )
    _assert_baseline(tmp_path)
    assert (tmp_path / EXTEND_OVERLAY).is_file()


@pytest.mark.integration
def test_skip_example_off_includes_example_paths(tmp_path, monkeypatch) -> None:
    _run_main(
        monkeypatch,
        tmp_path,
        ["--template-url", TEMPLATE_ZIP, "--ide", "cursor"],
    )
    assert (tmp_path / EXAMPLE_ONLY).is_file()


@pytest.mark.integration
def test_skip_example_on_excludes_example_paths(tmp_path, monkeypatch) -> None:
    _run_main(
        monkeypatch,
        tmp_path,
        ["--template-url", TEMPLATE_ZIP, "--ide", "cursor", "--skip-example"],
    )
    assert not (tmp_path / EXAMPLE_ONLY).exists()


@pytest.mark.integration
def test_skip_navigation_file_omits_navigation(tmp_path, monkeypatch) -> None:
    _run_main(
        monkeypatch,
        tmp_path,
        ["--template-url", TEMPLATE_ZIP, "--ide", "cursor", "--skip-navigation-file"],
    )
    assert (tmp_path / "spec/main.md").is_file()
    assert (tmp_path / "spec/design/hla.md").is_file()
    assert not (tmp_path / "spec/navigation.md").exists()


@pytest.mark.integration
def test_skip_hla_file_omits_hla(tmp_path, monkeypatch) -> None:
    _run_main(
        monkeypatch,
        tmp_path,
        ["--template-url", TEMPLATE_ZIP, "--ide", "cursor", "--skip-hla-file"],
    )
    assert (tmp_path / "spec/main.md").is_file()
    assert (tmp_path / "spec/navigation.md").is_file()
    assert not (tmp_path / "spec/design/hla.md").exists()


@pytest.mark.integration
def test_init_refuses_overwrite_existing_navigation(tmp_path, monkeypatch, capsys) -> None:
    (tmp_path / "spec").mkdir(parents=True)
    (tmp_path / "spec" / "navigation.md").write_text("# existing\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["spectask-init", "--template-url", TEMPLATE_ZIP, "--ide", "cursor"],
    )
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert "Refusing" in err
    assert "spec/navigation.md" in err
    assert "--update" in err
    assert "--skip-navigation-file" in err


@pytest.mark.integration
def test_update_succeeds_when_navigation_already_exists(tmp_path, monkeypatch) -> None:
    _mkdir_for_cursor_ide_auto(tmp_path)
    (tmp_path / "spec").mkdir(parents=True)
    (tmp_path / "spec" / "navigation.md").write_text("# existing\n", encoding="utf-8")
    (tmp_path / "spec" / "design").mkdir(parents=True)
    (tmp_path / "spec" / "design" / "hla.md").write_text("# existing hla\n", encoding="utf-8")
    _run_main(
        monkeypatch,
        tmp_path,
        ["--template-url", TEMPLATE_ZIP, "--update"],
    )
    assert (tmp_path / "spec" / "navigation.md").read_text(encoding="utf-8") == "# existing\n"
    assert (tmp_path / "spec" / "design" / "hla.md").read_text(encoding="utf-8") == "# existing hla\n"
    assert (tmp_path / CURSOR_SKILL).is_file()


@pytest.mark.integration
def test_update_with_explicit_ide_skips_example_and_navigation(tmp_path, monkeypatch) -> None:
    _run_main(
        monkeypatch,
        tmp_path,
        ["--template-url", TEMPLATE_ZIP, "--update", "--ide", "cursor"],
    )
    assert not (tmp_path / EXAMPLE_ONLY).exists()
    assert (tmp_path / "spec/main.md").is_file()
    assert not (tmp_path / "spec/design/hla.md").exists()
    assert not (tmp_path / "spec/navigation.md").exists()


@pytest.mark.integration
def test_ide_auto_zip_resolves_cursor(tmp_path, monkeypatch) -> None:
    _mkdir_for_cursor_ide_auto(tmp_path)
    _run_main(
        monkeypatch,
        tmp_path,
        ["--template-url", TEMPLATE_ZIP, "--ide", "auto"],
    )
    _assert_baseline(tmp_path)
    assert (tmp_path / CURSOR_SKILL).is_file()


@pytest.mark.integration
def test_ide_auto_zip_fails_without_markers(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["spectask-init", "--template-url", TEMPLATE_ZIP, "--ide", "auto"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert "--ide all" in err
    assert "no markers matched" in err
    assert "cursor" in err


@pytest.mark.integration
def test_update_only_zip_defaults_ide_auto(tmp_path, monkeypatch) -> None:
    _mkdir_for_cursor_ide_auto(tmp_path)
    _run_main(
        monkeypatch,
        tmp_path,
        ["--template-url", TEMPLATE_ZIP, "--update"],
    )
    assert not (tmp_path / EXAMPLE_ONLY).exists()
    assert (tmp_path / "spec/main.md").is_file()
    assert not (tmp_path / "spec/design/hla.md").exists()
    assert not (tmp_path / "spec/navigation.md").exists()
    assert (tmp_path / CURSOR_SKILL).is_file()


@pytest.mark.integration
def test_ide_all_copies_union(tmp_path, monkeypatch) -> None:
    _run_main(
        monkeypatch,
        tmp_path,
        ["--template-url", TEMPLATE_ZIP, "--ide", "all"],
    )
    assert (tmp_path / CURSOR_SKILL).is_file()
    assert (tmp_path / "CLAUDE.md").is_file()


@pytest.mark.integration
def test_ide_multiple_keys_merges_subset(tmp_path, monkeypatch) -> None:
    _run_main(
        monkeypatch,
        tmp_path,
        ["--template-url", TEMPLATE_ZIP, "--ide", "cursor", "claude-code"],
    )
    assert (tmp_path / CURSOR_SKILL).is_file()
    assert (tmp_path / "CLAUDE.md").is_file()


@pytest.mark.integration
def test_zip_run_with_custom_tmp_env(tmp_path, monkeypatch) -> None:
    """ZIP extract uses tempfile; point TMP* at a writable dir (cleaned up after exit)."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    monkeypatch.setenv("TMPDIR", str(sandbox))
    monkeypatch.setenv("TEMP", str(sandbox))
    monkeypatch.setenv("TMP", str(sandbox))
    _run_main(
        monkeypatch,
        tmp_path,
        ["--template-url", TEMPLATE_ZIP, "--ide", "cursor"],
    )
    _assert_baseline(tmp_path)
