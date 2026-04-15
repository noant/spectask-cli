# Step 2: Unified `acquire_source` + template copies

## Goal
Implement the shared **acquire source** primitive (ZIP download + extract vs `git clone` into system temp) and use it for the **template** URL. Then apply `required-list.json`, conditional `example-list.json`, and `skills-map.json` paths into `Path.cwd()`.

## Approach
- Add `is_zip_url(url: str) -> bool` using `urllib.parse.urlparse(url).path` and `path.lower().endswith(".zip")`.
- Add `acquire_source(url: str, *, git_branch: str, layout: Literal["template", "extend"])` as a **context manager** (or equivalent) that:
  - Uses one temp tree under the system temp directory.
  - **ZIP:** download (timeout), `zipfile.extractall` into an empty dir, then resolve root with the **ZIP root rules** from `overview.md` (`layout` selects whether `.metadata` or `spec/extend/` is required).
  - **Git:** `ensure_git_available()`, `git clone --depth 1 --branch <git_branch> --single-branch <url> <tmp_dir>`.
  - **Yields** the resolved root `Path`.
  - **Finally:** deletes the temp tree (context manager or `try`/`finally`).
- Reuse the JSON/copy helpers from the previous spec (`load_json`, `ide_files_for`, `copy_into_cwd`) — same ordering: required → examples → IDE files.
- Do **not** implement `--extend` in this step (only template URL).

## Affected files
- Python module(s): `acquire_source`, template bootstrap orchestration

## Code examples

### ZIP vs Git detection

```python
from urllib.parse import urlparse


def is_zip_url(url: str) -> bool:
    return urlparse(url).path.lower().endswith(".zip")
```

### Unified acquisition (illustrative)

```python
from contextlib import contextmanager
from pathlib import Path
import subprocess
import tempfile
import zipfile
from typing import Literal
from urllib.request import urlopen


def resolve_zip_base(extract_dir: Path, layout: Literal["template", "extend"]) -> Path:
    marker = ".metadata" if layout == "template" else "spec/extend"
    base = extract_dir
    for _ in range(2):
        if layout == "template" and (base / ".metadata").is_dir():
            return base
        if layout == "extend" and (base / "spec" / "extend").is_dir():
            return base
        children = [p for p in base.iterdir() if p.is_dir()]
        if len(children) == 1:
            base = children[0]
            continue
        break
    raise RuntimeError(f"Cannot resolve {layout} root under {extract_dir}")


@contextmanager
def acquire_source(url: str, *, git_branch: str, layout: Literal["template", "extend"]):
    if is_zip_url(url):
        with tempfile.TemporaryDirectory(prefix="spectask-src-zip-") as td:
            td_path = Path(td)
            zip_path = td_path / "archive.zip"
            with urlopen(url, timeout=60) as resp:
                zip_path.write_bytes(resp.read())
            extract_dir = td_path / "extract"
            extract_dir.mkdir()
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(extract_dir)
            yield resolve_zip_base(extract_dir, layout)
        return

    ensure_git_available()
    with tempfile.TemporaryDirectory(prefix="spectask-src-git-") as td:
        repo = Path(td) / "repo"
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", git_branch, "--single-branch", url, str(repo)],
            check=True,
        )
        if layout == "template" and not (repo / ".metadata").is_dir():
            raise RuntimeError(f"Cloned template missing .metadata: {repo}")
        if layout == "extend" and not (repo / "spec" / "extend").is_dir():
            raise RuntimeError(f"Cloned extend source missing spec/extend: {repo}")
        yield repo
```

### Template bootstrap entry

```python
def run_template_bootstrap(*, template_url: str, ide: str, skip_example: bool, template_branch: str) -> None:
    with acquire_source(template_url, git_branch=template_branch, layout="template") as template_root:
        meta = template_root / ".metadata"
        required = load_json(meta / "required-list.json")["required"]
        for rel in required:
            copy_into_cwd(template_root, rel)
        if not skip_example:
            for rel in load_json(meta / "example-list.json")["examples"]:
                copy_into_cwd(template_root, rel)
        skills = load_json(meta / "skills-map.json")
        for rel in ide_files_for(skills, ide):
            copy_into_cwd(template_root, rel)
```

*(Real code may factor `resolve_zip_base` next to `acquire_source` in one module used by step 3.)*
