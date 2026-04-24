---
name: spectask-extend
description: Use when adding a new rule file under spec/extend/ (per spec/main.md).
---

Read `spec/navigation.yaml`, then `spec/main.md`; add `spec/extend/{name}.md`, register it in the `spec/extend/` list in `spec/navigation.yaml`, and obey Folder Structure and allowlist rules in `main.md`.

If the user does **not** explicitly say whether the extension must always be read (`read: required`) or only when agents infer from task context that it applies (omit `read`), **ask before** writing the navigation entry: should agents read this file **at every session start**, or **infer applicability from task context and read only then**? If required, set `read: required`; if context-only, **omit** `read` entirely (do not set `read: optional`).
