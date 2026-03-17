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

### Build Loop

For each PENDING task in spec.md:

**1. Mark task IN_PROGRESS** in progress.json

**2. Spawn a worker agent** via Task tool:
```
Task: "Implement task #{id}: {description}
Context: {relevant spec sections}
Files to create/modify: {files}
Follow TDD: write tests first, then implementation.
Report back: files changed, tests passing (Y/N), any blockers."
```

**3. Validate worker output:**
- Run tests: `python -m pytest -q` or `npm test -- --reporter=dot`
- If tests fail: spawn a fix agent with the error output
- Mark DONE only when tests pass

**4. Commit after each task:**
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
  "tasks": [
    { "id": 1, "description": "...", "status": "PENDING|IN_PROGRESS|DONE|BLOCKED" }
  ],
  "tests": { "total": 0, "passing": 0, "failing": 0 },
  "updated_at": "ISO-8601"
}
```

### On Completion

1. Set `progress.json` status → "COMPLETE"
2. Clear `.autopilot/mode` (write empty string)
3. Run `/masonry-verify` and report results

### Rules

- **Never write implementation code yourself** — always spawn worker agents
- **Never skip tests** — if worker says tests pass, verify yourself
- **3-strike rule**: If a task fails 3 times, mark BLOCKED, continue with other tasks, report at end
- **Commit after every task** — never let work pile up uncommitted
