---
name: pseudocode
description: SPARC Phase 2 — generate pseudocode.md from spec before /build
user-invocable: true
---

# /pseudocode — SPARC Phase 2: Pre-Build Logic Blueprint

Invoke the pseudocode-writer agent to produce `.autopilot/pseudocode.md` from the current `.autopilot/spec.md`.

Act as the pseudocode-writer agent defined in `~/.claude/agents/pseudocode-writer.md`. Read `.autopilot/spec.md`. Write `.autopilot/pseudocode.md` with per-task pseudocode following the format in the agent instructions.

---

## Step 1 — Pre-flight

Read `.autopilot/spec.md`. If missing:
```
No spec found. Run /plan first to write .autopilot/spec.md.
```

Read the project codebase to understand the existing architecture:
- Check for existing types/interfaces in `src/types/`, `app/models/`
- Identify the main modules each task will touch
- Note any patterns used in existing code (error handling, validation style)

---

## Step 2 — For Each Task, Write a Logic Blueprint

For every task in the spec's task list, produce a pseudocode block.

**Pseudocode rules:**
- Plain English only — no actual code syntax, no language-specific idioms
- Focus on: input → transformation → output
- Cover all error paths and edge cases explicitly
- List the files/interfaces the task reads from and writes to
- Each task's blueprint must fit in ≤ 30 lines
- If a task is trivial (e.g., "add a field to a model"), say so and keep the blueprint to 3 lines

**Blueprint structure per task:**
```markdown
## Task N — [description]

**Purpose:** One sentence explaining why this task exists.

**Logic:**
1. [Step 1 — what happens first]
2. [Step 2 — transformation or decision]
3. [Continue until output is produced]

**Edge cases:**
- [Condition] → [How to handle it]
- [Missing input] → [Return value or error]

**Interfaces:**
- Reads: [file/module] ([type/function used])
- Writes: [file/module] ([what is created/modified])
- Calls: [external service/API] (optional)
```

---

## Step 3 — Surface Ambiguities

Before writing the file, list any ambiguities found:
- Tasks that depend on interfaces not yet defined
- Edge cases the spec doesn't address
- Conflicting requirements between tasks

If ambiguities exist, present them to the user and ask for clarification before writing the file. Do not guess — surfacing ambiguities is the point of this step.

---

## Step 4 — Write `.autopilot/pseudocode.md`

Write the complete document:

```markdown
# Pseudocode — [project name from spec]
Generated: [ISO date]
Source: .autopilot/spec.md

This document contains plain-English logic blueprints for each build task.
The developer agent reads this before writing code to reduce blind implementation.

---

[Task 1 blueprint]

---

[Task 2 blueprint]

...
```

---

## Step 5 — Confirm

Output to the user:
```
Pseudocode written to .autopilot/pseudocode.md
[N] tasks documented, [M] ambiguities flagged.

Review the blueprints before running /build.
If any task logic looks wrong, edit the pseudocode file directly — the developer agent will read it.
```

---

## Notes

- Pseudocode is advisory, not binding. The developer agent uses it as a checklist, not a contract.
- If `.autopilot/pseudocode.md` already exists, overwrite it (spec may have changed).
- This skill does not modify spec.md or any source files.
