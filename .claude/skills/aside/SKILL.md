---
name: aside
description: >-
  Temporarily freeze an active /build task to answer a question in read-only mode,
  then resume. Prevents derailing active builds with unrelated questions.
---

# /aside — Freeze, Answer, Resume

**Invocation**: `/aside <question>`

## Purpose

When you need an answer to something during an active /build without derailing the build.
The aside is read-only — no implementation code is written, no files are modified. After
answering, the build task is resumed exactly where it was.

---

## Behavior

### When a /build task is active

Check `.autopilot/mode` — if it equals `"build"`, read `.autopilot/progress.json` to find
any task with status `IN_PROGRESS`.

**Step 1 — Freeze**: Save the current task state to `.autopilot/aside-state.json`:

```json
{
  "task_id": 5,
  "task_description": "Task description from spec",
  "task_status": "IN_PROGRESS",
  "saved_at": "2026-03-28T00:00:00.000Z"
}
```

Append to `.autopilot/build.log`:

```
[timestamp] ASIDE_START: Freezing task #N to answer question.
```

If `.autopilot/aside-state.json` already exists (prior incomplete aside), overwrite it with
the current task state — a prior incomplete aside must not block a new one.

**Step 2 — Answer**: Answer the question using only read tools.

Permitted:
- Read files
- Grep
- Glob
- Bash (read-only commands: `git log`, `git status`, `cat`, `ls`)

NOT permitted:
- Write
- Edit
- Creating files
- Running tests
- Spawning worker agents
- Any modification to the codebase

If the question itself asks the agent to make a code change, decline and remind the user
that `/aside` is read-only. Suggest using `/plan` for a new spec if code changes are needed.

**Step 3 — Resume**: After answering, print:

```
━━━ Aside complete ━━━
Resume build: task #N — {task description}
Run /build to continue, or ask another /aside question.
```

The `/build` skill, on startup, checks for `.autopilot/aside-state.json`. If found, it reads
the task ID recorded there, clears the file (deletes it), and resumes from that task.

### When no /build is active

If `.autopilot/mode` is not `"build"`, or the file is not readable, or no task has status
`IN_PROGRESS`: answer the question normally without saving any state and without printing
the "Aside complete" message.

---

## aside-state.json Schema

```json
{
  "task_id": 5,
  "task_description": "Description of the frozen task",
  "task_status": "IN_PROGRESS",
  "saved_at": "2026-03-28T00:00:00.000Z"
}
```

Fields:
- `task_id` — integer task ID from progress.json
- `task_description` — description string from the task in progress.json
- `task_status` — always `"IN_PROGRESS"` at freeze time
- `saved_at` — ISO-8601 timestamp of when the aside was initiated

---

## Limitations

- Does NOT pause a running background agent — it only pauses the orchestrator's next action.
- If the aside question requires implementing code, decline and suggest `/plan` for a new spec.
- Maximum one aside context at a time. If `aside-state.json` already exists, overwrite it
  with the current task state (do not accumulate stacked asides).
- `.autopilot/mode` unreadable: treat as no active build, answer normally.
