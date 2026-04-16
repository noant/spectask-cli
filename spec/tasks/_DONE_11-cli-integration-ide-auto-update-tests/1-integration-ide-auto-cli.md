# 1: Integration tests — `--ide auto` via `main()`

## Goal
Exercise **`--ide auto`** through **`spectask_init.cli.main()`** against the real template **ZIP** fixture pattern used in `tests/test_integration_cli.py`: one test for **successful** resolution when the temp CWD satisfies the template’s detection rules, and one test for **failure** (no markers) with stderr content that guides the user to **`--ide all`** and explicit keys.

## Approach
- Add **`@pytest.mark.integration`** tests in **`tests/test_integration_cli.py`** (or split module only if the file becomes unwieldy — default is **same file**).
- Reuse **`_run_main`** / **`TEMPLATE_ZIP`** / path constants as in sibling tests.
- **Success:** Before `_run_main`, create under **`tmp_path`** the minimal marker(s) so **`resolve_auto_ide_key`** would select a single IDE (e.g. **Cursor**). Invoke with `["--template-url", TEMPLATE_ZIP, "--ide", "auto"]` (and **`--template-branch`** only if required for argparse parity with other ZIP tests — mirror **`test_zip_template_only`**). Assert baseline template files and at least one **IDE-specific** path that **`cursor`** would copy (reuse **`CURSOR_SKILL`** or equivalent).
- **Failure:** Empty project layout (only what `tmp_path` provides — **no** detection markers). Same argv with **`--ide auto`**. Expect **`SystemExit(1)`** and stderr containing **`--ide all`** and the **explicit IDE names** from the error path in **`bootstrap`** (assert substrings that remain stable; avoid overfitting to the full message if it includes volatile ordering — use **`pytest`’s** flexible matching if needed).

## Affected files
- `tests/test_integration_cli.py`

## Notes
- If capturing stderr is awkward with **`_run_main`**, refactor locally to call **`main()`** with **`monkeypatch.setattr(sys, "argv", …)`** the same way but allow **`capsys`** — keep changes minimal.
