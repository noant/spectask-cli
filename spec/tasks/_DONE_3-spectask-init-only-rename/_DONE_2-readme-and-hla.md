# Step 2: README and HLA

## Goal
Document the single **`spectask-init`** distribution and remove **`spectask-bootstrap`** from user-facing architecture text.

## Approach
1. **`README.md`**: Title and body should describe **`spectask-init`** only. Primary **`uvx`** line: **`uvx spectask-init …`** (no **`--from spectask-bootstrap`**). Update **`pip install`** and PyPI links to **`spectask-init`**. Module example: **`python -m spectask_init`**.
2. **`spec/design/hla.md`**: Rename the CLI section to reflect **`spectask-init`**; update module bullets from **`spectask_bootstrap.*`** to **`spectask_init.*`**; canonical **`uvx`** / **`pip`** / **`python -m`** lines must match **`pyproject.toml`** after step 1.

## Affected files
- **`README.md`**
- **`spec/design/hla.md`**

## Constraints
- Do not edit **`spec/tasks/_DONE_*`**.
- Keep maintainer **`scripts/publish.py`** usage unchanged unless a string explicitly references the old distribution name (then align with **`spectask-init`**).

## Code examples

**README primary line:**

```bash
uvx spectask-init --ide cursor
```

**HLA (illustrative one-liner):**

```bash
uvx spectask-init --ide <key>
```
