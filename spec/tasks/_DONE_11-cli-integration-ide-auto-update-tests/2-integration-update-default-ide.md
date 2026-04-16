# 2: Integration tests — `--update` without `--ide`

## Goal
Add an integration test that runs **`main()`** with **only** **`--update`** and **`--template-url`** set to **`TEMPLATE_ZIP`**, proving that default **`ide == ("auto",)`** flows through bootstrap together with **both skip flags**, when the CWD is prepared so **auto** resolves (same marker setup as step **`1-integration-ide-auto-cli`** success case).

## Approach
- In **`tests/test_integration_cli.py`**, add **`@pytest.mark.integration`** test: after creating the same markers under **`tmp_path`** as in the **`--ide auto`** success test, call **`_run_main`** with `["--template-url", TEMPLATE_ZIP, "--update"]` (**no** `--ide`).
- Assert:
  - Example-only paths are **absent** (reuse **`EXAMPLE_ONLY`** or the same assertion style as **`test_update_with_explicit_ide_skips_example_and_navigation`**).
  - **`spec/navigation.md`** is **absent**.
  - Core template files still present (**`spec/main.md`**, **`spec/design/hla.md`**, or **`_assert_baseline`** if navigation skip is already excluded there — align assertions with **`test_skip_navigation_file_omits_navigation`** and the explicit-IDE update test so the suite stays consistent).
  - At least one resolved-IDE artifact is present (e.g. **`CURSOR_SKILL`**) to prove **`auto`** did not silently no-op.

## Affected files
- `tests/test_integration_cli.py`

## Notes
- Do **not** duplicate large assertion blocks: factor a small private helper in the test module **only if** it reduces copy-paste between the **`--ide auto`** success test and this test without obscuring readability.
