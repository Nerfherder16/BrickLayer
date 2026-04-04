---
name: build
description: >-
  Autopilot SPARC build. 5-stage pipeline: Spec → Pseudocode → Architecture →
  Refinement (TDD per task) → Completion. Senior escalation tier, strategy flag,
  dependency-aware task graph, phase checkpoint commits, telemetry.
---

# /build — Autopilot SPARC Build

Orchestrates `.autopilot/spec.md` through a 5-stage SPARC pipeline:
**Specification → Pseudocode → Architecture → Refinement → Completion**

## Arguments

```
/build                          — default (balanced strategy)
/build --strategy conservative  — extra verification, security scan, slower
/build --strategy aggressive    — skip redundant checks, fastest path
/build with swarm               — parallel task dispatch (independent tasks only)
```

Parse the `--strategy` flag from the invocation arguments. Write to `.autopilot/strategy`.
If no flag: default to `balanced`.

---

## Pre-flight Checks

1. **Spec must exist** — read `.autopilot/spec.md`. If missing, stop:
   ```
   No spec found. Run /plan first to write .autopilot/spec.md.
   ```

2. **Check for in-progress build** — read `.autopilot/progress.json` if it exists.
   - If status is `BUILDING` or `PAUSED`, show current task list and ask:
     ```
     Found an in-progress build (task N of M — STATUS).
     Resume from task N, or start fresh?
     ```
   - If status is `COMPLETE`, show summary and stop:
     ```
     Build already complete. Run /verify to check, or /plan for a new spec.
     ```
   - If no `progress.json`, this is a new build — proceed.

3. **Compaction recovery** — if any task shows `IN_PROGRESS` in `progress.json` at start:
   - Call `TaskList` to check if any corresponding subagents are still running.
   - If a subagent is still running: **wait for it** — do NOT re-dispatch.
   - If a task is `IN_PROGRESS` but has no running subagent: reset to `PENDING`, re-dispatch.
   - **Never do task work inline** — every task goes through the full pipeline.

---

## Initialization

Write `.autopilot/strategy` with the parsed strategy value.

Create `progress.json`:

```json
{
  "project": "{spec title slug}",
  "status": "BUILDING",
  "strategy": "balanced",
  "branch": "current git branch",
  "tasks": [
    { "id": 1, "description": "Task 1 name from spec", "status": "PENDING", "depends_on": [] },
    { "id": 2, "description": "Task 2 name from spec", "status": "PENDING", "depends_on": [1] }
  ],
  "tests": { "total": 0, "passing": 0, "failing": 0 },
  "updated_at": "ISO-8601"
}
```

Parse `depends_on` from spec task annotations:
```
- [ ] **Task 2** [depends:1] — integration tests
```
If no annotation, `depends_on: []`.

Write `.autopilot/mode` = `build`.
Write `.autopilot/build.log` with: `[timestamp] BUILD_START: N tasks, strategy={strategy}`.
Create `.autopilot/telemetry.jsonl` (empty) if it doesn't exist.

**Register tasks in Claude Code task manager** — call `TaskCreate` for every task immediately.

Immediately after all `TaskCreate` calls, write `.autopilot/task-ids.json` with the returned IDs:
```json
{
  "1": "{id returned by TaskCreate for task 1}",
  "2": "{id returned by TaskCreate for task 2}",
  "...": "..."
}
```
**This file is the only source of truth for task panel IDs that survives compaction.** All `TaskUpdate` calls must read from this file, not from in-memory state.

---

## Phase 0 — SPARC Context Generation

Run this phase **once before the task loop**, only if the docs don't already exist.

### Phase 0a — Pseudocode (skip if `.autopilot/pseudocode.md` exists)

```
subagent_type: pseudocode-writer
prompt: |
  Read .autopilot/spec.md and write .autopilot/pseudocode.md.
  For each task: plain-English logic, flow, edge cases, failure modes.
  No code syntax. Focus on "what happens", not "how to implement it".
  Return: path written, one-line summary per task.
```

### Phase 0b — Architecture (skip if `.autopilot/architecture.md` exists)

```
subagent_type: architecture-writer
prompt: |
  Read .autopilot/spec.md and .autopilot/pseudocode.md.
  Write .autopilot/architecture.md covering:
  - Component boundaries and interface contracts
  - Data flow between components
  - Out-of-scope list (explicit)
  Return: path written, component list.
```

After both docs are written, create a phase checkpoint commit:
```bash
git add .autopilot/pseudocode.md .autopilot/architecture.md
git commit -m "phase(architecture): SPARC context generated"
git tag phase/architecture
```

**Load both docs into orchestrator memory** — they are injected into every worker prompt for the rest of the build.

---

## Per-Task Loop

Process tasks in dependency order: a task with `depends_on: [N]` must not start until task N is `DONE`.

For each PENDING task (respecting depends_on):

### Step 0 — SPARC Mode Detection

Read the task description from `spec.md`. Check for a `[mode:X]` annotation:

```
- [ ] **Task N** [mode:python] — implement pricing service
- [ ] **Task N** [mode:typescript] — build StatCard component
- [ ] **Task N** [mode:tdd] — implement auth with London-school TDD
- [ ] **Task N** [mode:security] — audit auth for OWASP Top 10
- [ ] **Task N** [mode:architect] — design event-sourcing schema
- [ ] **Task N** [mode:devops] — write Dockerfile and compose config
- [ ] **Task N** [mode:database] — write Alembic migration + SQLAlchemy model
- [ ] **Task N** [mode:review-only] — code review without implementation
```

If no `[mode:X]` annotation: use default dispatch (Steps 2–3 below).
If `[mode:X]` found: use the **SPARC Mode Dispatch Table** to override Steps 2–3.

### Step 0.5 — Pre-task telemetry

Append to `.autopilot/telemetry.jsonl`:
```json
{"phase": "pre", "task_id": "t-{N}", "description": "{task description}", "timestamp": "ISO", "strategy": "{strategy}"}
```

### Step 1 — Update status

Mark task `IN_PROGRESS` in `progress.json`. Log `[timestamp] TASK_START: #N — description`.
Call `TaskUpdate` with `status: "in_progress"` for this task's ID.

### Step 2 — Spawn test-writer agent

**Default (no mode annotation):**
```
subagent_type: test-writer
prompt: |
  Task: {task description from spec}
  Files to create/modify: {files list from spec}

  Write a FAILING test suite that captures the desired behavior described in the task.
  Test file locations follow project convention (tests/ prefix for Python, __tests__/ for TS).

  Do NOT read any existing implementation files.
  Return: list of test files created + brief description of what each test covers.
```

**[mode:security] or [mode:architect] or [mode:review-only]:** Skip Step 2.
**[mode:tdd]:** Use `tdd-london-swarm` instead — it handles test writing internally.

Confirm test files were created. If test-writer fails or returns nothing, log BLOCKED and stop.

### Step 3 — Spawn developer agent

**Default (no mode annotation):**
```
subagent_type: developer
prompt: |
  Task: {task description from spec}
  Files to create/modify: {files list from spec}
  Test files written: {list from test-writer}

  ## Architecture Context
  {full contents of .autopilot/architecture.md}

  ## Pseudocode Blueprint
  {blueprint for this specific task from .autopilot/pseudocode.md}

  Implement the minimal code to make all tests pass.
  Follow TDD: RED → GREEN → REFACTOR.

  Return: files modified, test results (passing/failing counts), any blockers.
```

**SPARC Mode Dispatch Table:**

| Mode | Replace Step 2 with | Replace Step 3 with |
|------|---------------------|---------------------|
| `[mode:python]` | test-writer (default) | `python-specialist` |
| `[mode:typescript]` | test-writer (default) | `typescript-specialist` |
| `[mode:database]` | test-writer (default) | `database-specialist` |
| `[mode:tdd]` | (tdd-london-swarm handles) | `tdd-london-swarm` — London-school, outside-in, mockist |
| `[mode:tdd-deep]` | (tdd-orchestrator handles) | `tdd-orchestrator` — mutation testing + property-based + chaos + ATDD/BDD |
| `[mode:security]` | (skip) | `security` — OWASP audit, read-only |
| `[mode:devops]` | test-writer (default) | `devops` |
| `[mode:architect]` | (skip) | `architect` — design only, no code |
| `[mode:review-only]` | (skip) | `peer-reviewer` — review only |

### Step 4a — Guard (did anything break?)

Run the **full test suite** to detect regressions introduced by this task:

```bash
# Python
python -m pytest -q --tb=short

# TypeScript / Node
npm test
```

**Guard is a BLOCKER.** If any test that was passing before now fails:
- Distinguish runner errors (setup failure, import error) from test failures before escalating — a non-zero exit due to a missing module is a runner error, not a Guard failure
- Spawn fix agent with the full failure output
- Do NOT continue to Step 4b until Guard passes

Guard escalation chain (max cycles shown):
```
Attempt 1-3: developer (standard fix prompt)
  → still failing: spawn senior-developer
  → senior-developer fails: spawn architect (design review)
  → architect recommendation → spawn developer with architect context
  → still failing: DIAGNOSIS_COMPLETE required → spawn diagnose-analyst
  → diagnose-analyst → DIAGNOSIS_COMPLETE → spawn fix-implementer
  → fix-implementer fails → HUMAN_ESCALATE: mark BLOCKED, report to user
```

**Never mark BLOCKED before exhausting the escalation chain.**

**Exempt modes** — Guard still runs; Verify (4b) is skipped for: `[mode:security]`, `[mode:architect]`, `[mode:review-only]`.

### Step 4b — Verify (did this task's goal improve?)

Run **only the test file(s) written specifically for this task** to confirm the task's goal was achieved:

```bash
# Python
python -m pytest {task-specific test files} -q --tb=short

# TypeScript / Node
npm test -- --testPathPattern={pattern matching task test files}
```

**Verify is a WARNING only.** If task-specific tests do not pass:
- Log: `Verify: task metric not improved — {task description}`
- Do NOT spawn a fix agent
- Continue to Step 4.5

**Skip Verify entirely** when:
- No task-specific test file exists (e.g., config-only changes, doc tasks)
- Task mode is `[mode:security]`, `[mode:architect]`, or `[mode:review-only]`

**Record the Guard/Verify outcome** — it determines the commit prefix in Step 6:
- Guard pass + Verify pass → `both_pass`
- Guard pass + Verify fail/skipped → `guard_only`

Senior-developer prompt:
```
subagent_type: senior-developer
prompt: |
  Task: {task description}
  The developer agent failed 3 times. Read all related files and diagnose.
  Files involved: {list}
  Failing test output: {output}
  Architecture context: {architecture.md contents}
  Return: SENIOR_DONE (with fix applied) or SENIOR_ESCALATE (with diagnosis).
```

### Step 4.5 — 7-point verification

Run all checks that apply to this task. Fail-fast order:

| # | Check | Tool | Fail threshold |
|---|-------|------|----------------|
| 1 | Unit tests pass | pytest / vitest | any failure |
| 2 | No regressions | full suite -q | any new failure |
| 3 | Type check clean | mypy / tsc --noEmit | any error |
| 4 | Lint clean | ruff / eslint | any error |
| 5 | Security scan | `bandit -r src/ -q` (Python) / `eslint --plugin security` (JS) | HIGH severity |
| 6 | Performance baseline | compare test duration to prior task — warn if >20% slower | warning only |
| 7 | Docker build | `docker build .` — only if Dockerfile present | build failure |

**Strategy modifiers:**
- `conservative` — all 7 checks required; check 5 blocks on MEDIUM+ severity
- `balanced` (default) — checks 1-5; check 5 blocks on HIGH only; 6-7 are warnings
- `aggressive` — checks 1-4 only; 5-7 skipped

If a check fails → spawn developer with the specific failure output for targeted fix (1 cycle).
If still failing → mark as warning and continue (unless check 1 or 2 fails — those always block).

### Step 5 — Code review

```
subagent_type: code-reviewer
prompt: |
  Review the implementation for task: {task description}
  Files changed: {list}
  All tests pass. Strategy: {strategy}
  Check for: correctness, security issues, style problems, regressions.
  Return: APPROVED, NEEDS_REVISION (with specific issues), or BLOCKED (critical issue).
```

- `APPROVED` → continue.
- `NEEDS_REVISION` → spawn developer with reviewer feedback (1 cycle), re-validate, re-review.
- `BLOCKED` → mark task BLOCKED, stop, report to user.

### Step 5a — Spec compliance check

After code-reviewer returns APPROVED, run spec-reviewer to confirm the implementation matches the spec.

```
subagent_type: spec-reviewer
prompt: |
  Task: {task description from spec}
  Files listed in spec for this task: {files list from spec}
  Files actually changed: {files changed by developer}

  Read the spec task description carefully. Review the diff of changed files.
  Return: COMPLIANT, OVER_BUILT, UNDER_BUILT, or SCOPE_DRIFT with a one-line reason.
```

Outcomes:
- `COMPLIANT` → proceed to Step 6 (commit).
- `OVER_BUILT` → spawn developer with instruction to revert the extra scope (1 cycle), re-run Steps 4–5a.
- `UNDER_BUILT` → spawn developer with the missing elements listed (1 cycle), re-run Steps 4–5a.
- `SCOPE_DRIFT` → spawn developer with instruction to revert out-of-scope changes (1 cycle), re-run Steps 4–5a.

If spec-reviewer returns OVER_BUILT/UNDER_BUILT/SCOPE_DRIFT after 2 correction cycles: mark task BLOCKED, report to user.

spec-reviewer is **read-only** — it never modifies files. It runs only after code-reviewer APPROVED and does not replace code-reviewer.

### Step 6 — Commit + telemetry

Use the Guard/Verify outcome recorded in Step 4b to choose the commit prefix:

- **Guard + Verify both pass** (`both_pass`) → use `feat:` prefix
- **Guard passes but Verify failed or was skipped** (`guard_only`) → use `experiment:` prefix

```bash
git add {files changed in this task}

# When both Guard and Verify passed:
git commit -m "feat: {task description summary} (task {N}/{total})"

# When Guard passed but Verify did not (task goal metric not confirmed):
git commit -m "experiment: {task description summary} (task {N}/{total})"
```

Never include `.autopilot/` files in the commit.

**Mark task `DONE` in `progress.json` BEFORE running `git commit`** — this ensures that if compaction
interrupts between the DONE write and the commit, the task is not re-dispatched on resume. A committed
task with DONE status is safe. A committed task still showing IN_PROGRESS gets re-dispatched.

```bash
# 1. Write DONE first (compaction-safe checkpoint)
# Update progress.json task status to DONE, update updated_at

# 2. Now commit
git add {files changed in this task}
git commit -m "feat: {task description summary} (task {N}/{total})"   # or experiment: prefix
```

Append to `.autopilot/telemetry.jsonl`:
```json
{"phase": "post", "task_id": "t-{N}", "timestamp": "ISO", "duration_ms": {elapsed}, "success": true, "agent": "{agent used}", "strategy": "{strategy}", "escalated": false}
```

If `phase_end` annotation present on this task in spec.md:
```bash
git tag phase/{phase_name}
```

Log `[timestamp] TASK_DONE: #N — description`.
Call `TaskUpdate` with `status: "completed"` — read this task's ID from `.autopilot/task-ids.json`.

---

## Completion

When all tasks are DONE:

1. Update `progress.json` status to `COMPLETE`.
2. Write `.autopilot/mode` = `""`.
3. Log `[timestamp] COMPLETE: All N tasks done, strategy={strategy}`.
4. Tag the final commit:
   ```bash
   git tag phase/completion
   ```
5. Print summary:
   ```
   Build complete — N tasks done, N tests passing.
   Strategy: {strategy} | Escalations: {count} | Phase tags: {list}

   Next: Run /verify to independently validate the implementation.
   ```

---

## Orchestrator Rules

- **Never write implementation code** — delegate all code writing to worker agents
- **Never read implementation files** — only read spec, progress.json, test results, and agent outputs
- **Context stays lean** — worker agents handle all file I/O; orchestrator only manages state
- **No silent failures** — if any agent returns an error, surface it immediately
- **Commit after every task** — never batch multiple tasks into one commit
- **Exhaust escalation chain before BLOCKED** — BLOCKED is a last resort, not a 3-strike rule

## Error Handling

- Worker agent timeout or no response → retry once, then escalate to senior-developer
- Git commit fails → report to user (do not force-push or use --no-verify)
- Test runner not found → detect project type (pyproject.toml → pytest, package.json → npm test)
- Telemetry write fails → log warning and continue (telemetry is non-blocking)

## Resuming

When resuming a PAUSED build (including after context compaction):
1. Read `progress.json` — find first non-DONE task
2. Read `build.log` — understand what happened before the pause
3. Read `.autopilot/strategy` — restore strategy setting
4. **Restore task panel IDs from disk** — read `.autopilot/task-ids.json` if it exists:
   - For every task that is `DONE` in progress.json: call `TaskUpdate(id, "completed")` using the ID from task-ids.json. This syncs the panel to reality without re-creating tasks.
   - For every task that is `PENDING` or `IN_PROGRESS`: call `TaskCreate` with a fresh title, store the new ID back into `task-ids.json` (overwrite that task's entry only).
   - If `task-ids.json` doesn't exist (older build): re-call `TaskCreate` for all non-DONE tasks and write a new `task-ids.json`.
   - **Never re-create tasks that are already DONE** — duplicate panel entries create confusion.
5. Reset any `IN_PROGRESS` task (that has no running subagent per `TaskList`) back to `PENDING` in `progress.json`.
6. Re-run tests on DONE tasks to verify no drift (skip if `aggressive` strategy)
7. Resume from first PENDING task (respecting `depends_on`)

---

## SPARC Mode Reference

Mode annotations on individual tasks in `spec.md`:

```markdown
- [ ] **Task N** [mode:python] [depends:1] — implement pricing service
```

### Mode Behaviors

**`[mode:python]`** — `python-specialist`: FastAPI, asyncio, SQLAlchemy 2.x, Pydantic v2, pytest
**`[mode:typescript]`** — `typescript-specialist`: React 19, TypeScript strict, Tailwind v4, Vitest
**`[mode:database]`** — `database-specialist`: PostgreSQL, Qdrant, Neo4j, Redis, Alembic
**`[mode:tdd]`** — `tdd-london-swarm`: London-school parallel TDD (handles its own tests)
**`[mode:security]`** — `security`: OWASP audit, read-only, no code modifications
**`[mode:devops]`** — `devops`: Docker, docker-compose, CI/CD, nginx, Tailscale
**`[mode:architect]`** — `architect`: design decisions, ADR writing, no implementation
**`[mode:review-only]`** — `peer-reviewer`: code review only, no modifications

### Escalation Chain Reference

```
developer (attempt 1) → developer (attempt 2) → developer (attempt 3)
  → parallel-debugger (3 simultaneous diagnose-analyst with competing hypotheses)
    → winning hypothesis → developer (attempt 1-2 with hypothesis context)
      → still failing: senior-developer (broader context, can propose refactors)
        → SENIOR_DONE: apply fix, continue
        → SENIOR_ESCALATE: architect review
          → architect (design diagnosis, returns recommendation)
            → developer (with architect context, attempt 1-2)
              → diagnose-analyst (root cause analysis)
                → DIAGNOSIS_COMPLETE → fix-implementer
                  → HUMAN_ESCALATE: mark BLOCKED, report to user with full log
```

`parallel-debugger` spawns 3 `diagnose-analyst` subagents simultaneously with different failure hypotheses (environment, logic, integration). Fastest to converge wins. Trigger: 3rd `DEV_ESCALATE`.

### Strategy Reference

| Strategy | Test scope | Security check | Verification | Speed |
|----------|-----------|----------------|--------------|-------|
| `conservative` | Full suite + regression | MEDIUM+ blocks | All 7 points | Slow |
| `balanced` | Task files + regression | HIGH blocks | Points 1-5 | Normal |
| `aggressive` | Task files only | Skipped | Points 1-4 | Fast |
