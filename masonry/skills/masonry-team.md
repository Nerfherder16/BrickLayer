---
name: masonry-team
description: Partition a build spec across N coordinated worker instances for maximum throughput. "team build", "use N workers", "parallel team". Requires .autopilot/spec.md.
---

## masonry-team — Distributed Build Across N Workers

Partition a build spec across N coordinated Claude Code instances. Each worker runs `/build` on its assigned task partition. The coordinator polls for completion and merges results.

### Prerequisites

1. Read `.autopilot/spec.md` — refuse if missing
2. Read `.autopilot/progress.json` if it exists — resume PENDING tasks only

### Team Config (optional)

`.autopilot/team-config.json`:
```json
{
  "workers": 3,
  "partition_strategy": "tasks",
  "sync_interval_seconds": 30
}
```

**`workers` default:** 3. Balances parallelism vs. context overhead per instance.

### Partitioning Algorithm

**1. Collect all PENDING tasks** from `progress.json` (or all tasks if starting fresh).

**2. Estimate complexity** per task:
- Count files in `lock_files` (if present)
- Word count of `description`
- Assign weight: `lock_files.length * 3 + description.split(' ').length`

**3. Conflict merge rule**: If two tasks share any `lock_files` entry, they MUST be in the same partition — never split conflicting tasks across workers.

**4. Bin-pack** tasks into N partitions by weight, respecting conflict constraints. Aim for roughly equal total weight per partition.

**5. Write partition files**:
- `.autopilot/team-1-tasks.json` — `{ "partition": 1, "tasks": [task_ids] }`
- `.autopilot/team-2-tasks.json` — `{ "partition": 2, "tasks": [task_ids] }`
- etc.

### Launching Workers

Spawn N subagent instances in a single parallel message, one per partition:

Each worker prompt:
```
You are worker {n} of {total} in a coordinated /build team.
Your assigned tasks: {task_ids from partition file}
Spec: {relevant sections for your tasks only}
Run /build but ONLY process the tasks listed above. Skip all others.
Use the same progress.json — mark your tasks IN_PROGRESS before starting.
Report done when all your tasks are DONE or BLOCKED.
```

### Coordinator Behavior

After spawning workers:
1. Wait for all workers to complete
2. Read `progress.json` — validate all partitioned tasks are DONE or BLOCKED
3. Run test suite to confirm no regressions across partition boundaries
4. Commit all changes in one batch: `git commit -m "feat: team build [{worker_count} workers] [masonry-team]"`
5. Run `/masonry-verify` and report results
6. Clean up partition files (delete `.autopilot/team-*-tasks.json`)

### Conflict Prevention

The partition algorithm ensures no two workers own the same file. Workers are instructed to check `lock_files` before modifying any file — if a file is claimed by another partition, skip it and report BLOCKED.

### Usage

```
/masonry-team             — auto-detect worker count from spec size (tasks / 4, min 2, max 6)
/masonry-team 4           — explicitly 4 workers
/masonry-team status      — show per-worker progress (reads team-*-tasks.json + progress.json)
```

**Auto worker count formula:** `max(2, min(6, ceil(pending_tasks / 4)))`

### State Files

```
.autopilot/
  team-config.json      ← optional config (workers, strategy)
  team-1-tasks.json     ← partition 1 task IDs (created at start, deleted on completion)
  team-2-tasks.json     ← partition 2 task IDs
  ...
```

Workers share the same `progress.json` schema as `/build` (see `masonry-build.md`), including the `session_id` field.

> **Session ownership**: Write the current session's `session_id` into `progress.json` when creating it. Stop hooks use this to distinguish builds owned by this session from builds started in other sessions. The `session_id` is available from the hook input payload (`input.session_id || input.sessionId`).

### Rules

- **Coordinator never writes code** — only spawns workers, validates, commits
- **Workers use shared progress.json** — each marks its own tasks IN_PROGRESS/DONE
- **Conflict merge is mandatory** — file-conflicting tasks must be co-located in one partition
- **Always verify after merge** — cross-partition boundary bugs are the main risk
