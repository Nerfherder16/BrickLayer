# Phase 1 — Ruflo Quick Wins

## Tasks

- [ ] **Task 1** — Create masonry-pre-edit.js pre-edit backup hook and register in settings.json
- [ ] **Task 2** — Create masonry-pre-task.js and masonry-post-task.js telemetry hooks and register in settings.json
- [ ] **Task 3** — Add --strategy flag to masonry-prompt-router.js and masonry-teammate-idle.js
- [ ] **Task 4** — Create masonry-agent-complete.js SubagentStop result cache hook and register in settings.json
- [ ] **Task 5** — Add phase checkpoint tagging to masonry-build-guard.js and git-nerd.md

---

# Phase 1 — Ruflo Quick Wins Implementation

Implement all 5 Phase 1 items from DEV_EXECUTION_ROADMAP.md.
All hooks are in: C:/Users/trg16/Dev/Bricklayer2.0/masonry/src/hooks/
Settings file: C:/Users/trg16/.claude/settings.json

## Task 1 — Pre-edit Backup Hook (masonry-pre-edit.js)

Create a new PreToolUse hook that fires on Write|Edit and backs up the target file before modification.

**Create**: masonry/src/hooks/masonry-pre-edit.js

Hook behavior:
- Reads stdin JSON (Claude Code PreToolUse payload)
- Only fires when .autopilot/mode exists and is "build" or "fix" — otherwise exit(0)
- Extracts the file path from the tool input (input.file_path for Write, input.file_path for Edit)
- If the file exists, copies it to .autopilot/backups/{relative_path_with_underscores}.{ISO_timestamp}
  e.g. src/api/users.py backed up to .autopilot/backups/src_api_users.py.2026-03-27T14-30-00
- Creates .autopilot/backups/ dir if it doesn't exist
- Always exits 0 (never blocks writes)
- Uses the same readStdin() + findAutopilotDir() pattern as other hooks in this directory

**Extend**: masonry/src/hooks/masonry-build-guard.js

After the existing pending-task check, add a cleanup step at Stop time:
- Read .autopilot/backups/ if it exists
- Delete backup files older than 7 days
- Log count of deleted files (silent if none)

**Register** in C:/Users/trg16/.claude/settings.json:
Add a new PreToolUse entry for matcher "Write|Edit" with the pre-edit hook BEFORE the existing masonry-session-lock.js entry.

---

## Task 2 — Pre-task / Post-task Telemetry Hooks

Create two hooks that track task execution time and outcomes.

**Create**: masonry/src/hooks/masonry-pre-task.js

Fires on PreToolUse(Agent) — when Claude spawns an agent.
Behavior:
- Read stdin JSON to get the agent invocation details (tool_input)
- Generate a task_id: "t-" + Date.now()
- Estimate task type from the prompt: look for keywords (frontend/backend/test/fix/data/config)
- Estimate complexity: count lines in prompt — <100=low, <300=medium, else=high
- Append JSONL record to .autopilot/telemetry.jsonl:
  {"task_id": "t-123", "phase": "pre", "timestamp": "ISO", "agent_type": "general-purpose", "task_type": "backend", "complexity": "medium"}
- Also write the task_id to .autopilot/current-task-id (overwrite) so post-task can pick it up
- Exit 0 always

**Create**: masonry/src/hooks/masonry-post-task.js

Fires on PostToolUse(Agent).
Behavior:
- Read current-task-id from .autopilot/current-task-id
- Calculate duration_ms: read .autopilot/telemetry.jsonl, find the pre record with matching task_id, diff timestamps
- Determine success: look at tool_result in stdin — if it contains "DONE" or "success" or no "ERROR"/"FAIL" text, success=true
- Append JSONL record:
  {"task_id": "t-123", "phase": "post", "timestamp": "ISO", "duration_ms": 4200, "success": true, "agent": "general-purpose"}
- Exit 0 always

**Register** in C:/Users/trg16/.claude/settings.json:
- Add PreToolUse matcher "Agent" hook for masonry-pre-task.js (async: true, timeout: 3)
  IMPORTANT: This is a SECOND matcher under PreToolUse "Agent" — masonry-mortar-enforcer.js and masonry-preagent-tracker.js are already there. Add pre-task alongside them.
- Add PostToolUse matcher "Agent" hook for masonry-post-task.js (async: true, timeout: 3)

---

## Task 3 — Execution Strategy Flag

Add --strategy flag support to the build pipeline.

**Extend**: masonry/src/hooks/masonry-prompt-router.js

In the main() function, after parsing the prompt text, add strategy detection:
- Check if prompt contains "--strategy conservative", "--strategy balanced", or "--strategy aggressive"
- If found: write the strategy string to .autopilot/strategy (create if needed)
- Also inject a routing hint: "[STRATEGY: conservative] Build with extra verification steps."
- Strategy descriptions to write to .autopilot/strategy:
  conservative = extra verification steps, security scan, slower but thorough
  balanced     = default path, standard test suite  
  aggressive   = skip redundant checks, parallel tasks, fastest path
- If no --strategy flag: check if .autopilot/strategy already exists (from prior setting); don't overwrite
- Always exit 0

**Extend**: masonry/src/hooks/masonry-teammate-idle.js

After reading the task from progress.json and before outputting the assignment:
- Check if .autopilot/strategy exists
- If it does, append to the output: "
[STRATEGY: {strategy}] Apply {strategy} execution mode for this task."
- The strategy descriptions are the same as above

---

## Task 4 — Agent-complete Hook (masonry-agent-complete.js)

Create a SubagentStop hook that caches agent results for dependency signaling.

**Create**: masonry/src/hooks/masonry-agent-complete.js

Fires on SubagentStop (PostToolUse for Agent tool).
Behavior:
- Read stdin JSON — extract agent_id (use tool_use_id or generate from timestamp), task output
- Create .autopilot/results/ directory if it doesn't exist
- Write result file: .autopilot/results/{agent_id}.json
  {"agent_id": "a-123", "completed_at": "ISO", "success": true, "summary": "first 200 chars of output"}
- Check progress.json for tasks with depends_on fields — if any dependency just completed, log: "[UNBLOCKED] Task #N is now ready"
- Exit 0 always (never blocks)

**Register** in C:/Users/trg16/.claude/settings.json:
Add PostToolUse matcher "Agent" hook for masonry-agent-complete.js (async: true, timeout: 5)

---

## Task 5 — Phase Checkpoint Commits

Extend the build pipeline to tag git checkpoints at phase boundaries.

**Extend**: masonry/src/hooks/masonry-build-guard.js

Add a phase checkpoint check to the PostToolUse side (this hook fires at Stop, but we need to detect phase completions). Actually, detect it within the existing Stop flow:
- After reading progress.json, check for tasks with "phase_end" field that are DONE
- For each phase_end that doesn't yet have a git tag phase/{name}, run:
  git tag phase/{name} -m "Phase {name} complete"
- Store processed tags in .autopilot/phase-tags.json to avoid double-tagging
- If git tag fails (no git, already exists), log and continue — never block

**Extend**: ~/.claude/agents/git-nerd.md

Add a section on phase checkpoints:

## Phase Checkpoints

When invoked with a phase checkpoint request (e.g. "tag phase/architecture complete"):
1. Run: git add -A && git commit -m "checkpoint: {phase} phase complete" (if uncommitted changes)
2. Run: git tag phase/{name} -m "BrickLayer phase checkpoint: {name}"
3. Confirm the tag was created: git tag -l phase/*
