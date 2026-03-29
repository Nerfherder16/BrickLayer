# Hook Inventory — Masonry Session Lifecycle

Generated: 2026-03-29
Source: `C:/Users/trg16/.claude/settings.json` (hooks section)

---

## Hook Events Overview

| Event | Hook Count | Blocking Hooks | Total Timeout Budget |
|-------|-----------|----------------|---------------------|
| SessionStart | 1 | 0 | 8s |
| UserPromptSubmit | 4 | 0 | 26s (parallel-ish) |
| Stop | 13 | 3 | ~182s sequential |
| PreToolUse (Write\|Edit) | 4 | 2 | 25s |
| PreToolUse (Bash) | 1 | 1 | 3s |
| PreToolUse (Write\|Edit\|Bash) | 1 | 1 | 5s |
| PreToolUse (ExitPlanMode) | 1 | 1 | 5s |
| PreToolUse (Agent) | 3 | 1 + 2 async | 11s |
| PostToolUse (Agent) | 2 | 0 (async) | 8s |
| PostToolUse (Write\|Edit) | 8 | 1 | 76s |
| PostToolUseFailure | 1 | 0 | 5s |
| SubagentStart | 1 | 0 | 3s |
| SubagentStop | 1 | 0 (async) | 5s |
| SessionEnd | 1 | 0 | 8s |
| PreCompact | 1 | 0 | 10s |

---

## SessionStart Hooks

### masonry-session-start.js
- **Event**: SessionStart
- **Timeout**: 8s
- **Blocking**: No (continueOnError: true)
- **Purpose**: Restores workflow context at session open. Reads active mode files (.autopilot/mode, .ui/mode, masonry-state.json), detects BL project, hydrates Recall patterns and ReasoningBank, scans for dead agent references.
- **Critical output**: Writes `$TMPDIR/masonry-snap-{sessionId}.json` — pre-existing dirty file list for stop-guard diffing.
- **BL silence**: Exits 0 if `program.md` AND `questions.md` exist in cwd.
- **Submodules invoked**: `session/build-state.js`, `session/project-detect.js`, `session/context-data.js`, `session/hotpaths.js`, `session/dead-refs.js`

---

## UserPromptSubmit Hooks

### recall-retrieve.js (Recall)
- **Event**: UserPromptSubmit
- **Timeout**: 8s
- **Blocking**: No (continueOnError: true)
- **Purpose**: Queries Recall for memories relevant to the current prompt. Injects up to 3 results (MIN_SIMILARITY=0.45) as `additionalContext`. Runs domain briefing (rehydrate) on first prompt of session. Periodic checkpoint every 25 prompts or 2 hours.
- **Key behaviors**:
  - Extracts key terms from prompt (strips stop words, filler phrases) before querying
  - Chronological sort for procedural memories and multi-session temporal arcs
  - Conflict detection: warns when two retrieved results conflict
  - Skip conditions: prompt < 15 chars, slash commands, trivial confirmations/greetings
  - State stored in `~/.cache/recall/` for cross-call tracking
- **BL silence**: Not explicitly BL-aware (relies on short-circuit from other hooks)

### masonry-register.js (Masonry)
- **Event**: UserPromptSubmit
- **Timeout**: 8s
- **Blocking**: No (continueOnError: true)
- **Purpose**: Every call — injects Mortar routing directive. First call only — hydrates from Recall (recent handoff < 24h + last 5 findings). Subsequent calls — flushes pending guard warnings from `masonry-guard-{sessionId}.ndjson`.
- **Key behaviors**:
  - BL context detection: reads masonry.json, masonry-state.json, .autopilot/mode, .autopilot/progress.json, .claude/agents/mortar.md
  - Campaign state injected: wave number, pending question count
  - Build state injected: task completion progress
  - Session state stored in `$TMPDIR/masonry-{sessionId}.json`
  - Fire-and-forget: stores session-start log to Recall (importance 0.3)
- **BL silence**: Exits early if `program.md` AND `questions.md` exist in cwd

### masonry-prompt-router.js (Masonry)
- **Event**: UserPromptSubmit
- **Timeout**: 5s
- **Blocking**: No (continueOnError: true)
- **Purpose**: Transparent intent router — classifies prompt intent against 12 INTENT_RULES and injects a one-line routing hint to Mortar. Also classifies effort level (low/medium/high/max).
- **Key behaviors**:
  - 12 intent categories: campaign, security-audit, architecture, UI/design, debugging, build, git, refactoring, docs, research, etc.
  - Effort classification: max/high/medium/low based on keyword patterns and prompt length
  - Strategy flag detection: writes `.autopilot/strategy` file if `--strategy {level}` is in prompt
  - Output format: `→ Mortar: routing to {agent} [effort:X]`
- **BL silence**: Exits 0 if `program.md` + `questions.md` exist, OR masonry-state.json has a `mode` set
- **Skip conditions**: empty, slash commands, prompts < 20 chars

### masonry-prompt-inject.js (Masonry)
- **Event**: UserPromptSubmit
- **Timeout**: 5s
- **Blocking**: No (continueOnError: true)
- **Purpose**: Not in primary audit scope. Registered in settings.json after masonry-prompt-router.js.

---

## Stop Hooks (ordered — runs sequentially)

### 1. recall/session-save.js
- **Event**: Stop
- **Timeout**: 10s
- **Blocking**: No (continueOnError: true)
- **Async**: No
- **Purpose**: Calls `/observe/session-snapshot` on the Recall API with the session ID. Triggers Recall's own session snapshot logic — captures what was worked on.
- **stop_hook_active guard**: Yes (exits 0 if set)
- **Failure mode**: Silent — never blocks stopping. No output on success.

### 2. recall/recall-session-summary.js
- **Event**: Stop
- **Timeout**: 10s
- **Blocking**: No (continueOnError: true)
- **Async**: No
- **Purpose**: Reads session transcript (NDJSON), extracts user/assistant messages (last 200 lines), generates a summary using Ollama, stores to Recall with domain mapping. Also submits per-memory feedback.
- **Key behaviors**:
  - Reads transcript from `~/.claude/projects/{hash}/transcript.jsonl`
  - OLLAMA_HOST: http://192.168.50.62:11434 (hardcoded default, not 100.70.195.84)
  - Domain mapping via PROJECT_DOMAINS table (diverges from masonry-session-summary.js)
  - Debug log written to `~/.cache/recall/session-summary-debug.log`
  - Detaches from parent process (fire-and-forget internally) to avoid 10s timeout kill
- **stop_hook_active guard**: Not directly observed in first 80 lines (needs full read to confirm)

### 3. masonry-stop-guard.js
- **Event**: Stop
- **Timeout**: 20s
- **Blocking**: YES (no continueOnError — exit 2 blocks stop)
- **Async**: No
- **Purpose**: Primary gate — blocks Stop if there are uncommitted git changes from THIS session. Uses session snapshot for precision; falls back to mtime if snapshot absent.
- **Key behaviors**:
  - Primary boundary: reads `$TMPDIR/masonry-snap-{sessionId}.json` (written by session-start)
  - Only files NOT in the snapshot AND currently dirty are flagged
  - If new session files found: auto-commits them with a descriptive message
  - Writes session close record to `session.json` and `history.jsonl`
  - Doc staleness check: warns if code was committed but CHANGELOG/ROADMAP/etc. not updated
  - Writes `karen-needed.json` flag for next session if docs are stale
  - Fallback (no snapshot): uses git mtime for today's files
- **stop_hook_active guard**: Yes (exits 0 if set — prevents re-trigger loop)
- **BL silence**: Exits 0 if `program.md` + `questions.md` exist in cwd

### 4. masonry-session-summary.js
- **Event**: Stop
- **Timeout**: 8s
- **Blocking**: No (continueOnError: true)
- **Async**: No
- **Purpose**: Reads activity log (NDJSON written by masonry-observe.js PostToolUse hook), derives a structured session summary without Ollama, stores to Recall.
- **Key behaviors**:
  - Reads `$TMPDIR/masonry-activity-{sessionId}.ndjson` or similar activity log
  - Domain mapping via DOMAIN_MAP (partially diverges from recall-session-summary.js entries)
  - Stores structured object (not LLM summary) — deterministic
  - Target completion: < 3 seconds
- **Note**: Potential duplication with recall-session-summary.js — both write session data to Recall

### 5. masonry-handoff.js
- **Event**: Stop
- **Timeout**: 8s
- **Blocking**: No (continueOnError: true)
- **Async**: YES (detached background process)
- **Purpose**: Packages loop state + recent findings into a Recall memory for next-session resume. The masonry-register.js UserPromptSubmit hook reads this handoff on the next session's first call.
- **Key behaviors**:
  - Reads masonry state, 3 most recent findings (by mtime), pending/done question counts
  - De-dup guard: `$TMPDIR/masonry-handoff-triggered-{sessionId}.json` prevents double-firing
  - Session ID passed as `process.argv[2]` (not from stdin — unusual invocation pattern)
  - Stores as `masonry:handoff` tag with importance 0.8
  - Enriches with synthesis.md recommendation if available

### 6. masonry-context-monitor.js
- **Event**: Stop
- **Timeout**: 5s
- **Blocking**: No (continueOnError: true) — but can return exit 2 in specific conditions
- **Async**: No
- **Purpose**: Estimates context window token usage and checks for semantic degradation. Blocks Stop only when context > 750K tokens AND uncommitted changes exist. Performs semantic degradation checks (lost-in-middle, poisoning, distraction, clash) via Ollama cosine similarity.
- **Key behaviors**:
  - Context estimate from transcript file size (heuristic — not exact token count)
  - Semantic checks are advisory (never block): lost-in-middle, poisoning, distraction, clash
  - Blocking threshold: 750K tokens (very high — rarely triggered)
  - Uses nomic-embed-text on Ollama for embeddings
- **stop_hook_active guard**: Not confirmed in first 80 lines

### 7. masonry-build-guard.js
- **Event**: Stop
- **Timeout**: 10s
- **Blocking**: YES (no continueOnError — exit 2 blocks stop)
- **Async**: No
- **Purpose**: Blocks Stop if `.autopilot/` build mode is active with pending tasks.
- **Key behaviors**:
  - Walks up directory tree (up to 10 levels) to find `.autopilot/`
  - Only blocks if `.autopilot/` is in the EXACT cwd (not a parent) — prevents cross-session interference
  - Only blocks if mode is "build" or "fix"
  - Only blocks if there are PENDING or IN_PROGRESS tasks in progress.json
- **stop_hook_active guard**: Yes (exits 0 if set)
- **BL silence**: Yes (exits 0 if `program.md` + `questions.md` exist)

### 8. masonry-ui-compose-guard.js
- **Event**: Stop
- **Timeout**: 10s
- **Blocking**: YES (no continueOnError — exit 2 blocks stop)
- **Async**: No
- **Purpose**: Blocks Stop if `.ui/` compose mode is active with pending tasks. Adapted from masonry-build-guard.js.
- **Key behaviors**:
  - Walks up directory tree (up to 10 levels) to find `.ui/`
  - Only blocks if mode is "compose"
  - Shows pending task list in stderr message
- **stop_hook_active guard**: Yes (exits 0 if set)
- **Note**: No BL research project silence guard — unlike build-guard

### 9. masonry-score-trigger.js
- **Event**: Stop
- **Timeout**: 5s
- **Blocking**: No (continueOnError: true)
- **Async**: No (spawns detached child process)
- **Purpose**: Auto-triggers `score_all_agents.py` when `scored_all.jsonl` is stale (> 24h). Also triggers `run_optimization.py` when DSPy threshold (50 new examples) is crossed.
- **Key behaviors**:
  - Stale check: `masonry/training_data/scored_all.jsonl` mtime > 24h
  - DSPy threshold state in `.mas/dspy-trigger-count.json`
  - Spawns scripts detached (fire-and-forget) — hook itself exits quickly
  - DSPY_FLAG_FILE at `.autopilot/TRIGGER_DSPY` (written when DSPy threshold hit)
- **stop_hook_active guard**: Not checked in first 80 lines
- **BL silence**: Yes (exits 0 for research projects)

### 10. masonry-pagerank-trigger.js
- **Event**: Stop
- **Timeout**: 5s
- **Blocking**: No (continueOnError: true)
- **Async**: No (spawns detached child process)
- **Purpose**: Triggers `pagerank.py` if > 60 minutes since last run.
- **Key behaviors**:
  - Last-run state in `~/.mas/pagerank-last-run.json` (global, not per-project)
  - Guards: `masonry/` directory must exist in cwd (BL repo root only)
  - Rate limit: 60 minutes minimum between runs
- **stop_hook_active guard**: Yes (exits 0 if set)
- **BL silence**: Yes (exits 0 for research projects)

### 11. masonry-system-status.js
- **Event**: Stop
- **Timeout**: 8s
- **Blocking**: No (continueOnError: true)
- **Async**: No
- **Purpose**: Writes unified system status snapshot to `.mas/system-status.json`. Mortar reads this at session start to orient itself. Captures campaign status, Recall status, training status.
- **Key behaviors**:
  - Reads masonry-state.json, `.mas/session.json`, `.mas/recall_degraded` flag
  - Optionally queries training DB via Python if `BRICKLAYER_TRAINING_DB` is set
  - All failures are silent — never blocks

### 12. masonry-training-export.js
- **Event**: Stop
- **Timeout**: 65s (longest in the stack — async)
- **Blocking**: No (continueOnError: true)
- **Async**: YES
- **Purpose**: Exports BrickLayer campaign traces to training system (SQLite at `~/.mas/training.db`).
- **Key behaviors**:
  - Rate limited: once per hour (`$BL_ROOT/.mas/training_export_last_run`)
  - Exits 0 if `bl/training_export.py` does not exist
  - Requires Python (auto-detects python3 or python)
  - Runs synchronously (`spawnSync`) despite being marked async in settings.json
- **Note**: 65s timeout is extremely long for a Stop hook; async flag mitigates but does not eliminate timeout risk

### 13. masonry-ema-collector.js
- **Event**: Stop
- **Timeout**: 5s
- **Blocking**: No (continueOnError: true)
- **Async**: No (spawns detached child)
- **Purpose**: Runs EMA (Exponential Moving Average) collector to update `ema_history.json` from `masonry/telemetry.jsonl`.
- **Key behaviors**:
  - Debounce: skips if run in last 5 minutes (`~/.mas/ema-last-run.json`)
  - Only runs if `masonry/telemetry.jsonl` exists and has entries
  - Spawns `collector.py` detached
- **stop_hook_active guard**: Needs confirmation
- **BL silence**: Yes (exits 0 for research projects)

---

## Cross-Hook Data Flow

```
SessionStart
  └─ writes: $TMPDIR/masonry-snap-{sessionId}.json
               ↓
Stop[3] masonry-stop-guard reads snap, auto-commits, closes session

UserPromptSubmit
  └─ masonry-register writes: $TMPDIR/masonry-{sessionId}.json (firstCall flag)
  └─ masonry-register writes: $TMPDIR/masonry-guard-{sessionId}.ndjson (guard warnings)
                               ↓
  masonry-register (next call) reads+deletes guard file, flushes warnings

PostToolUse (Write|Edit)
  └─ masonry-observe writes: $TMPDIR/masonry-activity-{sessionId}.ndjson
                              ↓
Stop[4] masonry-session-summary reads activity log

Stop[5] masonry-handoff
  └─ uses $TMPDIR/masonry-handoff-triggered-{sessionId}.json as de-dup guard
  └─ stores to Recall (tag: masonry:handoff)
              ↓
UserPromptSubmit[2] masonry-register reads from Recall on next session's first call
```

---

## Domain Mapping Inconsistencies

Three hooks maintain their own PROJECT_DOMAINS / DOMAIN_MAP tables:

| Project | recall-retrieve.js | recall-session-summary.js | masonry-session-summary.js |
|---------|-------------------|--------------------------|---------------------------|
| recall | "recall" | "development" | "recall" |
| system-recall | "recall" | "development" | "recall" |
| familyhub | "family-hub" | "ai-ml" | "family-hub" |
| sadie | "family-hub" | "ai-ml" | "family-hub" |
| relay | "relay" | "api" | "relay" |
| media-server | "media-server" | "infrastructure" | "media-server" |
| homelab | "homelab" | "infrastructure" | "homelab" |

`recall-session-summary.js` uses different domain names for system-recall ("development" not "recall") and familyhub ("ai-ml" not "family-hub"). Memories written by this hook land in different Recall domains than those read by recall-retrieve.js.
