# 1: Pytest harness

## Goal
Declare **pytest** as a development-only dependency and add a minimal **`tests/`** layout (e.g. shared fixtures, markers for integration).

## Approach
- Extend **`pyproject.toml`** with optional dev deps (**pytest**), without adding runtime dependencies.
- Add **`tests/conftest.py`**: register `integration` marker; optional `chdir` fixture pattern documented for subtask3.
- Ensure **`pytest`** discovers tests under **`tests/`** with default config (no extra plugins required unless already in repo).

## Affected files
- `pyproject.toml`
- `tests/conftest.py` (new)

## Code examples
```toml
[project.optional-dependencies]
dev = ["pytest>=8"]
```

```python
# tests/conftest.py — marker registration only
def pytest_configure(config):
    config.addinivalue_line("markers", "integration: needs network and git on PATH")
```
