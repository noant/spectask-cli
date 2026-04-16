# 1: Bootstrap — load `ide-detection.json` and resolve `auto`

## Goal
Implement IDE detection from the template’s `.metadata/ide-detection.json` and resolve `ide=("auto",)` to a single concrete key before copying IDE-specific paths.

## No hardcoding (mandatory)
- **At runtime, marker rules and IDE names for `--ide auto` come only from** `template_root / ".metadata" / "ide-detection.json"` **after** the template is acquired (same tree as `skills-map.json`). The implementation must **not** embed lists of paths, marker kinds, or IDE keys for auto-detection in Python (except the literal token `"auto"` where the CLI/bootstrap branch on user input).
- **Allowed:** generic parsing, validation, and evaluation logic driven entirely by the loaded JSON plus `skills-map.json` from that same template.
- **Tests:** may build minimal JSON files or in-memory dicts under a temporary `template_root`; that is fixture data, not shipped defaults in the package.

## Source of truth at runtime
The file is part of whatever template `--template-url` (or default) resolves to—e.g. the official Spectask repo ships it under `.metadata/ide-detection.json`, but **this project must not mirror that content in code**. If the upstream file changes, the CLI must pick up the new rules on the next run without a code change.

## JSON schema (normative for this task)
- **Root:** a JSON object.
- **`ides`:** required array. Each element is an object with:
  - **`name`:** non-empty string; must match an `ides[].name` entry in the same template’s `skills-map.json`. If unknown, fail with a message that names both files.
  - **`markers`:** required array (may be empty). Each element is an object with:
    - **`path`:** string, relative path segment(s) under the detection root (see below). Reject `..` segments or absolute paths after resolution (same safety instinct as `copy_into_cwd`: no path escape).
    - **`kind`:** exactly `"file"` or `"directory"` (reject unknown values with a clear error citing `ide-detection.json`).

## Semantics
- **Detection root:** `Path.cwd()` at bootstrap time (same as destination for copied files).
- **OR per IDE:** An IDE entry **matches** if **any** of its `markers` matches (logical OR across the `markers` array). Example: an entry with two markers matches if the file marker **or** the directory marker matches, as defined by the JSON loaded at runtime—not by constants in code.
- **Per-marker match:**
  - `kind == "directory"`: true iff `(cwd / path).is_dir()`.
  - `kind == "file"`: true iff `(cwd / path).is_file()`.
  - Use these predicates so a wrong type (e.g. path exists but is a file when `kind` is `directory`) does **not** count as a match.
- **Symlinks:** `is_dir()` / `is_file()` follow Python’s usual semantics (symlink to a directory counts as directory if that is what `Path` reports).
- **Selection across IDEs:** Collect all `ides[]` entries that match. Then apply parent overview rules: zero → user-facing error with `--ide all` and explicit keys; more than one → ambiguous error listing matched names; exactly one → use that `name` as the resolved IDE key.

## File I/O and integration in `run_template_bootstrap`
- Path: `template_root / ".metadata" / "ide-detection.json"`.
- If `--ide auto` but the file is **missing:** `RuntimeError` (or consistent project pattern): template does not define auto-detection; user must pass explicit `--ide` or `all`.
- Load with existing `load_json`; validate types before evaluating markers.
- After loading `skills` from `skills-map.json`, if `ide == ("auto",)`:
  1. Load and validate `ide-detection.json`.
  2. Cross-check every detection `name` against `skills`.
  3. Resolve to a single `name` or raise with the required English messages.
  4. Replace `ide` with `(resolved_name,)` and call `ide_files_for(skills, ide)` unchanged.

## Unit tests (minimum)
- **OR within one IDE:** fixture with two markers (file + directory): neither present → no match; only one kind satisfied → match.
- **Kind strictness:** path exists as wrong type → no match for that marker.
- **Cross-file validation:** detection `name` not in `skills-map.json` → error.
- **Ambiguous / zero matches:** two entries’ markers satisfied vs none, with deterministic message content.
- **Path safety:** marker path containing `..` → error (or no match + invalid schema error—pick one behavior and document in code/tests).
- **No hardcoding in tests’ production path:** tests may write a temp `ide-detection.json`; they must not assert behavior by comparing against a duplicated canonical list baked into test helpers as “the real template”—keep fixtures minimal and local to each case.

## Affected files
- `spectask_init/bootstrap.py` (primary)
- `tests/test_bootstrap_unit.py`

## Code sketch (replace naive string markers)
```python
def marker_matches(cwd: Path, path: str, kind: str) -> bool:
    p = cwd / path
    if kind == "directory":
        return p.is_dir()
    if kind == "file":
        return p.is_file()
    raise RuntimeError(...)  # invalid kind should be rejected at validate time


def entry_matches(cwd: Path, markers: list[dict]) -> bool:
    return any(marker_matches(cwd, m["path"], m["kind"]) for m in markers)
```
