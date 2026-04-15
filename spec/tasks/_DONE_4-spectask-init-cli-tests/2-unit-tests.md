# 2: Unit tests (no network)

## Goal
Cover **pure logic** and **CLI parsing** so every **`CliOptions`** field is asserted from **`parse_args`** at least once, plus **`acquire`** helpers and **`bootstrap`** JSON/path logic using local fixtures.

## Approach
- **`parse_args`**: table-driven tests for `--template-url`, `--ide` (required), `--template-branch`, `--extend`, `--extend-branch`, `--skip-example` (store_true).
- **`spectask_init.acquire`**: `is_zip_url` (`.zip` case variants); `resolve_zip_base` with minimal directory trees under `tmp_path` for both `layout="template"` and `layout="extend"`.
- **`spectask_init.bootstrap`**: `ide_files_for` with inline **`skills-map.json`** dicts (`all`, unknown IDE error, missing `paths`/`files`).
- Optionally **`copy_into_cwd`** errors (path traversal) with tiny template roots — keep tests fast and deterministic.

## Affected files
- `tests/test_cli_parse.py` (new)
- `tests/test_acquire.py` (new)
- `tests/test_bootstrap_unit.py` (new)

## Code examples
```python
from spectask_init.cli import parse_args

def test_parse_extend_and_branches():
    o = parse_args(
        ["--ide", "cursor", "--extend", "https://github.com/noant/spectask-my-extend.git", "--extend-branch", "main"]
    )
    assert o.extend.endswith(".git")
    assert o.extend_branch == "main"
```
