---
name: masonry-build
description: Agent-mode build system — execute a spec from /masonry-plan using worker agents. "build me", "implement this", "execute the plan". Requires .autopilot/spec.md.
---

## masonry-build — Orchestrated Build

You are an **ORCHESTRATOR**. You manage state, spawn worker agents, validate output, and commit. You NEVER write implementation code directly.

### Prerequisites

1. Read `.autopilot/spec.md` — refuse if missing (tell user to run `/masonry-plan` first)
2. Read `.autopilot/progress.json` if it exists — resume from first non-DONE task

### State Files

```
.autopilot/
  mode           ← set to "build"
  spec.md        ← the approved specification (read-only)
  progress.json  ← task statuses (you write this)
  build.log      ← append-only build log (you write this)
```

### Agent Spawning — Terminal Display

Claude Code renders a live progress tree when you spawn agents in parallel:

```
• Running 2 developer agents… (ctrl+o to expand)
  ├─ Build auth module · 4 tool uses · 12.1k tokens
  │  └ Writing src/auth/login.py…
  └─ Build test suite · 2 tool uses · 8.4k tokens
     └ Searching for test patterns…
```

**To get this display:**
- Spawn 2+ Agent calls in a **single message** (parallel)
- Use a 3-5 word `description`: `"Build auth module"`, `"Write test suite"`
- Use `subagent_type="developer"` for implementation tasks

**Example — parallel spawn:**
```
[Agent call 1]: description="Build {task A}", subagent_type="developer"
[Agent call 2]: description="Build {task B}", subagent_type="developer"
```

When tasks are independent (no shared files), always batch them. Dependent tasks run sequentially.

### Build Loop

For each batch of independent PENDING tasks:

**1. Mark tasks IN_PROGRESS** in progress.json

**2. Spawn worker agents in parallel** (single message, multiple Agent calls):

Each agent prompt:
```
Implement task #{id}: {description}
Context: {relevant spec sections}
Files to create/modify: {files}
Owned files for this task: {lock_files}. Do NOT modify files owned by other IN_PROGRESS tasks: {other_lock_files}.
Follow TDD: write tests first, then implementation.
Report back: files changed, tests passing (Y/N), any blockers.
```

Use `description="Build {short task name}"` (3-5 words) for clean terminal output.

**3. Validate worker output:**
- Run tests: `python -m pytest -q` or `npm test -- --reporter=dot`
- If tests fail: spawn a fix agent with the error output
- Mark DONE only when tests pass

**4. Commit after each batch:**
```bash
git add {changed files}
git commit -m "feat: {task description} [masonry-build #{id}]"
```

**5. Update progress.json** with DONE status

### progress.json Schema

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
      "lock_files": ["src/auth/login.py", "src/auth/models.py"]
    }
  ],
  "tests": { "total": 0, "passing": 0, "failing": 0 },
  "updated_at": "ISO-8601"
}
```

> **Session ownership**: Write the current session's `session_id` into `progress.json` when creating it. Stop hooks use this to distinguish builds owned by this session from builds started in other sessions. The `session_id` is available from the hook input payload (`input.session_id || input.sessionId`).

### File Ownership

Before spawning parallel workers, track which files each task owns to prevent conflicts:

1. **Before spawning** a worker agent, set `owned_by: "task-{id}"` on that task in `progress.json`.
2. **In the worker prompt**, include: `"Owned files for this task: {lock_files}. Do NOT modify files owned by other IN_PROGRESS tasks: {list of other tasks' lock_files}."`
3. **After marking** a task DONE or BLOCKED, clear `owned_by` to `null`.
4. **Conflict check**: If two PENDING tasks share a file in `lock_files`, treat them as implicitly sequential — do not spawn in the same parallel batch.

Note: `lock_files` is populated from the planning spec's task descriptions. If omitted, ownership is inferred from files mentioned in the task description (best-effort).

### On Completion

1. Set `progress.json` status → "COMPLETE"
2. Clear `.autopilot/mode` (write empty string)
3. Run `/masonry-verify` and report results
4. Refresh training data (non-fatal — log and continue if it fails):
   ```bash
   python masonry/scripts/score_all_agents.py --base-dir $(git rev-parse --show-toplevel) 2>&1 || true
   ```
   This captures build signal (tests pass/fail, lint clean, no regression) for developer,
   test-writer, and fix-implementer into `scored_all.jsonl` immediately.

### Rules

- **Never write implementation code yourself** — always spawn worker agents
- **Never skip tests** — if worker says tests pass, verify yourself
- **3-strike rule**: If a task fails 3 times, mark BLOCKED, continue with other tasks, report at end
- **Commit after every task** — never let work pile up uncommitted
