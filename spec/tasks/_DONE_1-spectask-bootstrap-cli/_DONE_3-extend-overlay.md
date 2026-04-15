# Step 3: Extend overlay via unified `acquire_source`

## Goal
When `--extend` is set, use the **same** `acquire_source` helper as the template step. After acquisition, copy all files under `spec/extend/` from the resolved **extend root** into the current working directory under `./spec/extend/`, then rely on context-manager cleanup.

## Approach
- If `--extend` is absent, no-op.
- Call `acquire_source(extend_url, git_branch=extend_branch, layout="extend")` from the same module as step 2.
- The yielded path already satisfies the **ZIP root rules** / Git checks for `spec/extend/`.
- Walk files under `extend_root/spec/extend` (files only), copy with `shutil.copy2`, `mkdir(parents=True)`, overwrite.

## Affected files
- Python module(s): `copy_extend_overlay`, CLI `main` wiring

## Code examples

### Overlay copy (reuse pattern)

```python
import shutil
from pathlib import Path


def copy_extend_overlay(extend_root: Path) -> None:
    src_dir = extend_root / "spec" / "extend"
    if not src_dir.is_dir():
        raise FileNotFoundError(f"No spec/extend in extend source: {src_dir}")
    dest_root = Path.cwd()
    for path in src_dir.rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(src_dir)
        dest = dest_root / "spec" / "extend" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
```

### Orchestration snippet

```python
def run_extend(*, extend_url: str | None, extend_branch: str) -> None:
    if not extend_url:
        return
    with acquire_source(extend_url, git_branch=extend_branch, layout="extend") as root:
        copy_extend_overlay(root)
```
