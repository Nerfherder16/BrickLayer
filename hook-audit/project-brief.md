# Project Brief — hook-audit

## What This System Does

The Masonry hook pipeline is a set of Node.js scripts registered in `~/.claude/settings.json`
that fire on Claude Code lifecycle events (SessionStart, UserPromptSubmit, Stop). These hooks
handle session state management, Recall memory integration, build/UI/campaign guard rails,
background analytics triggers, and Mortar routing directives. They run as external subprocesses
via `hook-runner.exe node {script}` and communicate via stdin/stdout JSON envelopes.

These hooks run **every session** on every machine Tim uses Claude Code.

## Hook Inventory

### UserPromptSubmit (fires on every query)

| Hook | File | Purpose |
|------|------|---------|
| recall-retrieve | `Recall/hooks/recall-retrieve.js` | Fetch relevant Recall memories, inject as context |
| masonry-register | `masonry/src/hooks/masonry-register.js` | Register session with Masonry daemon, check campaign state |
| masonry-prompt-router | `masonry/src/hooks/masonry-prompt-router.js` | Detect intent, inject one-line routing hint |

### SessionStart (fires once at session open)

| Hook | File | Purpose |
|------|------|---------|
| masonry-session-start | `masonry/src/hooks/masonry-session-start.js` | Snapshot pre-existing dirty files to tmpdir (`masonry-snap-{sessionId}.json`), detect BL project, inject context |

### Stop (fires in order, ~13 hooks total)

| Hook | File | Blocks? | Timeout | continueOnError |
|------|------|---------|---------|----------------|
| session-save | `Recall/hooks/session-save.js` | No | 10s | yes |
| recall-session-summary | `Recall/hooks/recall-session-summary.js` | No | 10s | yes |
| masonry-stop-guard | `masonry/src/hooks/masonry-stop-guard.js` | **Yes** (exit 2) | 20s | no |
| masonry-session-summary | `masonry/src/hooks/masonry-session-summary.js` | No | 8s | yes |
| masonry-handoff | `masonry/src/hooks/masonry-handoff.js` | No | 8s | no, async |
| masonry-context-monitor | `masonry/src/hooks/masonry-context-monitor.js` | **Yes** (JSON decision:block) | 5s | yes |
| masonry-build-guard | `masonry/src/hooks/masonry-build-guard.js` | **Yes** (exit 2) | 10s | no |
| masonry-ui-compose-guard | `masonry/src/hooks/masonry-ui-compose-guard.js` | **Yes** (exit 2) | 10s | no |
| masonry-score-trigger | `masonry/src/hooks/masonry-score-trigger.js` | No | 5s | yes |
| masonry-pagerank-trigger | `masonry/src/hooks/masonry-pagerank-trigger.js` | No | 5s | yes |
| masonry-system-status | `masonry/src/hooks/masonry-system-status.js` | No | 8s | yes |
| masonry-training-export | `masonry/src/hooks/masonry-training-export.js` | No | 65s | no, async |
| masonry-ema-collector | `masonry/src/hooks/masonry-ema-collector.js` | No | 5s | yes |

## Key Invariants (Things That Cannot Be Wrong)

1. Stop hooks that block must exit 2 OR output `{"decision":"block"}` to stdout. Any other exit code allows the stop through regardless of intent.
2. `masonry-stop-guard.js` depends on `masonry-activity-{sessionId}.ndjson` written by `masonry-observe.js` (PostToolUse hook). Execution order: stop-guard must read the activity log BEFORE session-summary deletes it.
3. `masonry-snap-{sessionId}.json` (written at SessionStart) is the primary mechanism for distinguishing "this session's files" from pre-existing dirty files. Stop-guard accuracy depends on this.
4. Session IDs from Claude Code are unique per session. Any hook using session ID for tmpdir files relies on this for cross-session isolation.
5. `masonry-handoff.js` expects `process.argv[2]` = sessionId, but settings.json does NOT pass it. The script falls back to `'unknown'` — meaning the guard file is always `masonry-handoff-triggered-unknown.json`, breaking multi-session isolation.
6. `masonry-context-monitor.js` blocks via stdout JSON (`{decision:"block"}`), while other blocking guards use `process.exit(2)`. These are two different blocking mechanisms — correctness depends on which the current Claude Code version honors for Stop events.

## Known Issues Going In

- **masonry-prompt-inject.js** was registered in settings.json but never existed, causing a UserPromptSubmit hook error on every query. Fixed before this campaign started.
- **masonry-handoff.js session ID bug**: The settings.json command does not pass `{session_id}` as an argument, so the handoff guard is always keyed on `'unknown'`.
- **masonry-context-monitor.js blocking mechanism**: Uses `{decision:"block"}` stdout format while other guards use `process.exit(2)`. Need to verify which is correct for Stop hooks in current Claude Code.

## What This System Is NOT

- Not idempotent — Recall hooks store memories every session even if nothing interesting happened
- Not unified — Masonry hooks and Recall hooks are maintained separately; they have diverged in domain naming and summary formats
- Not validated end-to-end — the `hook-runner.exe` layer between Claude Code and the Node scripts is undocumented

## Out of Scope

- PreToolUse hooks (masonry-pre-protect, masonry-approver, masonry-content-guard, etc.)
- PostToolUse hooks (masonry-observe, masonry-style-checker, masonry-tdd-enforcer, etc.)
- The hook-runner.exe binary behavior
- Campaign-internal behavior of tools called by hooks (Recall API, Python scripts)

## Source Authority Hierarchy

| Tier | Source | Who edits |
|------|--------|-----------|
| Tier 1 | `settings.json` hooks section, hook source files | Ground truth |
| Tier 2 | `docs/hook-inventory.md`, `docs/settings-hooks.json` | Extracted from source |
| Tier 3 | findings/ | Agent output |
