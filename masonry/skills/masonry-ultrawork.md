---
name: masonry-ultrawork
description: High-throughput parallel build — spawns all independent tasks simultaneously with file ownership partitioning. Use when tasks are largely independent. Requires .autopilot/spec.md.
---

## masonry-ultrawork — High-Throughput Parallel Build

You are an **ORCHESTRATOR**. Ultrawork maximizes parallelism by spawning every unblocked task simultaneously rather than in sequential dependency batches.

**When to use over `/build`:** Tasks are largely independent (e.g., many separate modules, research questions, skill files). If most tasks share files or have strict ordering, use `/build` instead.

### Prerequisites

1. Read `.autopilot/spec.md` — refuse if missing (tell user to run `/masonry-plan` first)
2. Read `.autopilot/progress.json` if it exists — resume from first non-DONE task

### State Files

Same as `/build`:
```
.autopilot/
  mode           ← set to "ultrawork"
  spec.md        ← the approved specification (read-only)
  progress.json  ← task statuses (you write this)
  build.log      ← append-only build log (you write this)
```

### Ultrawork Loop

**1. Build ownership conflict map**

Read all IN_PROGRESS tasks and collect their `lock_files`. This is the conflict set for this cycle.

**2. Find all spawnable tasks**

A task is spawnable if:
- Status is PENDING
- Its `lock_files` do not overlap with the conflict set
- Adding it to the active pool would not exceed `max_concurrency`

**3. Spawn all spawnable tasks simultaneously**

Send a single message with all Agent calls in parallel. Use `description="Build {short name}"` (3-5 words).

Worker agent prompt:
```
Implement task #{id}: {description}
Context: {relevant spec sections}
Files to create/modify: {files}
Owned files for this task: {lock_files}. Do NOT modify files owned by other IN_PROGRESS tasks: {other_lock_files}.
Follow TDD: write tests first, then implementation.
Report back: files changed, tests passing (Y/N), any blockers.
```

**4. Refill the pool as tasks complete**

As each task returns DONE or BLOCKED:
- Clear its `owned_by` in progress.json
- Immediately check for newly spawnable tasks (no longer blocked by completed task's lock_files)
- Spawn them without waiting for the full batch to finish

This is the key difference from `/build`: the pool is continuously refilled, not batch-by-batch.

**5. Commit every 3 completed tasks** (or when pool drains)

```bash
git add {changed files}
git commit -m "feat: ultrawork batch [{task ids}] [masonry-ultrawork]"
```

**6. On completion**

1. Set `progress.json` status → "COMPLETE"
2. Clear `.autopilot/mode`
3. Run `/masonry-verify` and report results

### max_concurrency

- **Default:** 6
- **Override:** Add `max_concurrency: N` to the spec's Agent Hints section
- **Hard cap:** 10 — above this, parallel agent rendering becomes unwieldy

### progress.json Schema

Same as `/build` with ownership fields:

```json
{
  "project": "{name}",
  "status": "BUILDING",
  "branch": "masonry/{project}-YYYYMMDD",
  "session_id": "{current_session_id}",
  "tasks": [
    {
      "id": 1,
      "description": "...",
      "status": "PENDING|IN_PROGRESS|DONE|BLOCKED",
      "owned_by": "task-1",
      "lock_files": ["src/module/file.py"]
    }
  ],
  "tests": { "total": 0, "passing": 0, "failing": 0 },
  "updated_at": "ISO-8601"
}
```

> **Session ownership**: Write the current session's `session_id` into `progress.json` when creating it. Stop hooks use this to distinguish builds owned by this session from builds started in other sessions. The `session_id` is available from the hook input payload (`input.session_id || input.sessionId`).

### Conflict Resolution

If two PENDING tasks share a `lock_files` entry, only one can be active at a time. When selecting which to spawn, pick the lower-numbered task ID. The other becomes spawnable only after the first completes.

If `lock_files` is empty or omitted for a task, treat it as having no conflicts (safe to run in parallel with anything).

### 3-Strike Rule

Same as `/build`: if a task fails 3 times, mark BLOCKED, continue with remaining tasks, report all BLOCKED tasks at the end.

### Rules

- **Never write implementation code yourself** — always spawn worker agents
- **Never skip tests** — if worker says tests pass, verify yourself
- **Refill immediately** — don't wait for a full batch before spawning new work
- **Commit frequently** — every 3 completions maximum
