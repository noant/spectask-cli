from __future__ import annotations

import shutil

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: needs network (and git when template/extend is not .zip)",
    )


@pytest.fixture
def git_on_path() -> None:
    if not shutil.which("git"):
        pytest.skip("git is not on PATH")


@pytest.fixture(autouse=True)
def _integration_env(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    if request.node.get_closest_marker("integration"):
        monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")
