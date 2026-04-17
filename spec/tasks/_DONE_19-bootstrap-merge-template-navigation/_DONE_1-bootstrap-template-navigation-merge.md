# Step 1: Bootstrap — template navigation merge

## Goal
Implement merge-on-existing for `spec/navigation.yaml` during template bootstrap and narrow preflight to HLA only.

## Approach
1. Add a helper (name at implementer discretion) that loads cwd and `template_root/spec/navigation.yaml`, validates with existing `_parse_registry_section` / normalization helpers, and merges **`extend`** and **`design`** lists by appending template rows whose normalized `path` is absent in cwd’s list; preserve cwd entries when paths match. Build output doc from cwd’s root mapping; write atomically only when lists change.
2. In `run_template_bootstrap`, for `rel == NAVIGATION_FILE_RELPATH`: if `skip_navigation_file`, continue (skip). Else if `(cwd / rel).is_file()`, call the merge helper with `template_root`; else `copy_into_cwd` as today.
3. In `_preflight_required_navigation_and_hla`, stop adding `NAVIGATION_FILE_RELPATH` to conflicts; simplify single- and multi-path error messages so navigation is not mentioned as an overwrite target.

## Affected files
- `spectask_init/bootstrap.py` (primary)

## Constraints
- Do not change HLA preflight or `copy_into_cwd` behavior for other required paths except the navigation branch above.
- Reuse existing YAML utilities; avoid duplicating path-normalization logic—factor shared “append missing registry rows” if it reduces duplication with `merge_extend_source_navigation` without risky refactors.
