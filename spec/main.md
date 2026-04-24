# Spec-Tasks: AI-Oriented Development Methodology

## Folder Structure

- spec/main.md — this file.
- spec/navigation.yaml — strict YAML registry of this project’s concrete `spec/extend/*` and optional extra `spec/design/*.md` (`hla.md` required); the structure is fixed on purpose so scripts and other automation can parse it reliably; see Folder Structure here for all other paths (required).
- spec/design/hla.md — project high-level architecture (required).
- spec/design/{name}.md — other architecture documents (optional; ADRs, notes, etc.); each file besides `hla.md` must be listed in `spec/navigation.yaml`.
- spec/tasks/{X}-{name}/ — task folder.
- spec/tasks/{X}-{name}/overview.md — task overview (required).
- spec/tasks/{X}-{name}/{N}-{description}.md — subtask files (optional).
- spec/extend/{name}.md — team processes, code style, conventions (optional).

No other files are permitted in `spec/`: paths must match this Folder Structure, and any concrete `spec/extend/*.md` or optional extra `spec/design/*.md` (other than `hla.md`) must be listed in `spec/navigation.yaml`. Do not create READMEs or extra docs.

**New spec tasks:** follow **Step 1** and the **[overview.md Template](#overviewmd-template)** at the end of this file. Older `spec/tasks/_DONE_*` overviews may predate the template; **do not** copy their structure unless it already matches the template.

---

## Process Overview

```
[1] spec created → [2] self spec review → [3] spec review (user) → [4] code implemented → [5] self code review → [6] code review (user) → [7] hla updated
```

Mark each status [V] on completion. Prompt the user after steps 2, 5, and 6.

---

## Step 1: Spec Created

**Executor:** AI Agent (current context)

1.1 **Implementation clarifications** *(blocking)* — Before writing any spec content, identify ambiguous, optional, or convention-dependent aspects. Ask the user explicit questions and wait for answers. Record answers (or agreed defaults) in **Details**. Skip only if the task has a single obvious implementation path.
1.2 **Design overview** — in task `overview.md`, add **Design overview** section: affected modules, data flow changes, integration points.
1.3 **Overview** — `spec/tasks/{X}-{name}/overview.md` must follow [overview.md Template](#overviewmd-template): sections through `## Details` (before/after and code examples go there); **Goal** = one sentence. Add `## Execution Scheme` only when work splits into 2+ steps.
1.4 **Execution Plan** — If 2+ steps: `## Execution Scheme` step ids must match `{N}-{description}.md` from 1.5.
1.5 **Decomposition** — create {N}-{description}.md per step: goal, approach, affected files, code examples.

→ set [V] "Spec created"

---

## Step 2: Self Spec Review

**Executor:** AI Agent (New sub-agent)

Review the spec for: architectural impact, implementation errors, sequencing issues. Fix if needed.

→ set [V] "Self spec review passed"
→ prompt: "Self spec review passed — spec is ready for your review (Step 3). Reply 'spec review passed', 'lgtm', or 'ok' when satisfied."

---

## Step 3: Spec Review

**Executor:** User

On confirmation ("spec review passed", "lgtm", "ok"):
→ set [V] "Spec review passed"
→ prompt: "Reply 'implement' to start."

---

## Step 4: Code Implemented

**Executor:** AI Agent (current context) — reads `spec/extend/`, follows Execution Scheme, launches one sub-agent per step. 
**Each step in the Execution Scheme:** AI Agent (New sub-agent).

On "run it" / "implement" / "execute" / any direct instruction to start implementation:
0. If "Spec review passed" is not yet marked, set [V] "Spec review passed" automatically — the user's implementation command implies approval.
1. Read all files in spec/extend/ first.
2. MANDATORY! Launch a subagent per step — do NOT implement inline. No exceptions — even if a step seems trivial or small.
3. Follow Execution Scheme: → sequential, || parallel.

→ set [V] "Code implemented", rename done subtasks to _DONE_

---

## Step 5: Self Code Review

**Executor:** AI Agent (New sub-agent)

Review all changes: inconsistencies, naming, missing imports, broken contracts. Fix if needed.

→ set [V] "Self code review passed"
→ prompt: "Self review done. Reply 'code review passed' to proceed."

---

## Step 6: Code Review

**Executor:** User

On confirmation ("code review passed", "lgtm", "ok"):
→ set [V] "Code review passed"
→ prompt: "Will now update spec/design/hla.md."

---

## Step 7: HLA Updated

**Executor:** AI Agent (current context)

Do not start Step 7 until **Code review passed** is marked (Step 6).

1. Update spec/design/hla.md — create the file if it does not exist yet (always, regardless of scope).
2. Rename folder to _DONE_{X}-{name}.

→ set [V] "HLA updated"

---

## overview.md Template

```markdown
# {X}: {Title}

IMPORTANT: always use `spec/main.md` and `spec/navigation.yaml` for rules.

## Status
- [ ] Spec created
- [ ] Self spec review passed
- [ ] Spec review passed
- [ ] Code implemented
- [ ] Self code review passed
- [ ] Code review passed
- [ ] HLA updated

## Goal
{One concise sentence.}

## Design overview
- Affected modules: {list}
- Data flow changes: {description}
- Integration points: {list}

## Before → After
### Before
- {current state}
### After
- {desired state}

## Details
{Clarifying details, code examples, constraints.}

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`). 
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): step {N}-{description} → step {N}-{description}
- Phase 2 (parallel):   step {N}-{description} || step {N}-{description}
- Phase 3 (sequential): step review — inspect all changes, fix inconsistencies
```

Omit `## Execution Scheme` if no decomposition (single-file spec).
