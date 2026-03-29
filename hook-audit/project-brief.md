# Project Brief — Masonry Hook Audit

**Project**: hook-audit
**Type**: Pure research/audit campaign — no simulate.py
**Authority tier**: Tier 1 — human-authored, highest priority

---

## What This Campaign Audits

This campaign audits the full Masonry session lifecycle hook stack. The hook system
is the connective tissue between Claude Code events (SessionStart, UserPromptSubmit,
Stop, PreToolUse, PostToolUse, etc.) and the Masonry/BrickLayer/Recall subsystems.
It runs invisibly on every Claude Code interaction.

Hooks are evaluated across six focus areas:
1. Blocking mechanism correctness — which hooks can block session Stop and under what conditions
2. Stop hook execution order and dependencies — 13 Stop hooks fire in sequence; do they behave correctly as an ordered pipeline?
3. Session state symmetry — what SessionStart writes vs what Stop hooks read and consume
4. Cross-hook data dependencies — shared temp files, session IDs, activity logs, snapshot files
5. Analytics trigger viability — score-trigger, pagerank-trigger, ema-collector: do their rate limits and conditions actually fire?
6. Recall hook overlap/duplication — recall-retrieve, masonry-register, session-save, recall-session-summary, masonry-session-summary: five hooks touch Recall; is there redundancy?

---

## The Hook Stack (from settings.json)

### SessionStart (1 hook, timeout 8s, continueOnError: true)
- `masonry-session-start.js` — Restores workflow context; snapshots dirty file list for stop-guard diff; invokes build-state, project-detect, context-data submodules; dead-ref scan; hot-paths injection.

### UserPromptSubmit (4 hooks, all continueOnError: true)
- `recall-retrieve.js` (Recall, timeout 8s) — Queries Recall for relevant memories; periodic checkpoints every 25 prompts; rehydrates on first prompt of session. MAX_RESULTS=3, MIN_SIMILARITY=0.45.
- `masonry-register.js` (Masonry, timeout 8s) — BL context detection; injects Mortar routing directive; on first call hydrates from Recall (handoffs + findings); subsequent calls flush guard warnings.
- `masonry-prompt-router.js` (Masonry, timeout 5s) — Intent classification (12 INTENT_RULES), effort scoring (low/medium/high/max), strategy flag detection. Skips BL research projects and active campaigns.
- `masonry-prompt-inject.js` (Masonry, timeout 5s) — Not in audit scope (not listed in brief); registered in settings.json.

### Stop (13 hooks — the primary audit target)

| Order | Hook | Timeout | Blocking | Async |
|-------|------|---------|----------|-------|
| 1 | `recall/session-save.js` | 10s | no (continueOnError) | no |
| 2 | `recall/recall-session-summary.js` | 10s | no (continueOnError) | no |
| 3 | `masonry-stop-guard.js` | 20s | YES (no continueOnError) | no |
| 4 | `masonry-session-summary.js` | 8s | no (continueOnError) | no |
| 5 | `masonry-handoff.js` | 8s | no | YES (async) |
| 6 | `masonry-context-monitor.js` | 5s | no (continueOnError) | no |
| 7 | `masonry-build-guard.js` | 10s | YES (no continueOnError) | no |
| 8 | `masonry-ui-compose-guard.js` | 10s | YES (no continueOnError) | no |
| 9 | `masonry-score-trigger.js` | 5s | no (continueOnError) | no |
| 10 | `masonry-pagerank-trigger.js` | 5s | no (continueOnError) | no |
| 11 | `masonry-system-status.js` | 8s | no (continueOnError) | no |
| 12 | `masonry-training-export.js` | 65s | no | YES (async) |
| 13 | `masonry-ema-collector.js` | 5s | no (continueOnError) | no |

Three hooks can block Stop: masonry-stop-guard (exit 2), masonry-build-guard (exit 2), masonry-ui-compose-guard (exit 2).

---

## Key Mechanisms and Behaviors

### Session Snapshot Pattern (critical for stop-guard correctness)
`masonry-session-start.js` writes a snapshot of pre-existing dirty files to `$TMPDIR/masonry-snap-{sessionId}.json`.
`masonry-stop-guard.js` reads this snapshot and only flags files NOT in it (i.e., modified THIS session).
Failure mode: if session-start doesn't run or session ID is absent, stop-guard falls back to mtime-based detection.

### Temp File Bus
Hooks share state via `$TMPDIR`:
- `masonry-{sessionId}.json` — session state, firstCall flag (masonry-register.js)
- `masonry-snap-{sessionId}.json` — pre-existing dirty file snapshot (session-start → stop-guard)
- `masonry-guard-{sessionId}.ndjson` — guard warnings queued for next UserPromptSubmit (masonry-register.js)
- `masonry-handoff-triggered-{sessionId}.json` — de-dup guard for handoff (masonry-handoff.js)

### BL Research Project Detection
Multiple hooks detect BL research projects via the same sentinel: `program.md` AND `questions.md` both exist in cwd.
When detected, hooks silently exit 0 to avoid interfering with running campaigns.
This is implemented independently in: session-start, prompt-router, stop-guard, build-guard, score-trigger, pagerank-trigger, ema-collector.

### stop_hook_active Guard
Claude Code sets `stop_hook_active: true` in the Stop hook payload when a Stop hook previously blocked.
Hooks that can block must check this flag and exit 0 if set, to prevent infinite re-trigger loops.
Confirmed in: session-save, recall-session-summary, masonry-stop-guard, masonry-context-monitor, masonry-build-guard, masonry-ui-compose-guard, masonry-score-trigger, masonry-pagerank-trigger, masonry-ema-collector.

### Recall Overlap Risk
Five hooks interact with Recall at session boundaries:
- `recall-retrieve.js` — UserPromptSubmit: reads memories (search)
- `masonry-register.js` — UserPromptSubmit: reads (search) + writes (store session-start log)
- `session-save.js` — Stop: calls `/observe/session-snapshot`
- `recall-session-summary.js` — Stop: writes summarized transcript to Recall
- `masonry-session-summary.js` — Stop: writes structured activity summary to Recall
Domain mapping is duplicated across hooks (PROJECT_DOMAINS table appears in recall-retrieve, recall-session-summary, masonry-session-summary) with divergent entries — potential for domain mismatches.

### Analytics Trigger Conditions
- `masonry-score-trigger.js` — fires if `scored_all.jsonl` is older than 24h; also checks DSPy threshold (50 new examples).
- `masonry-pagerank-trigger.js` — fires if `~/.mas/pagerank-last-run.json` is older than 60 min; only runs if `masonry/` dir exists in cwd (BL repo root guard).
- `masonry-ema-collector.js` — fires if `telemetry.jsonl` has entries and last run > 5 min ago.
- `masonry-training-export.js` — fires if `bl/training_export.py` exists and last run > 1 hour ago.

---

## Invariants (Never Violate)

1. No hook may modify `masonry-state.json` or `questions.md` unless the campaign explicitly delegates it.
2. Blocking hooks (exit 2) MUST check `stop_hook_active` or risk infinite loops.
3. BL research project detection must remain consistent across all hooks — same sentinel files.
4. Session ID is the primary correlation key across all temp files — if absent, hooks degrade gracefully.
5. The stop-guard auto-commit path must never commit files owned by a different session.

---

## Known Risks / Past Issues

- Domain mapping is duplicated with divergent entries (PROJECT_DOMAINS in 3+ files) — risks domain mismatch causing memories to land in wrong buckets.
- masonry-handoff.js is async (detached) — it may not complete before the session actually closes. The session ID is passed as argv[2], not stdin, which is unusual.
- masonry-context-monitor.js can block Stop when context > 750K AND uncommitted changes, but only fires once per session (stop_hook_active guard). This is before masonry-build-guard and masonry-ui-compose-guard — ordering may matter.
- masonry-training-export.js has a 65-second timeout marked async — it spawns Python; if Python is unavailable, it exits 0 cleanly but the data is lost.
- masonry-register.js uses `CLAUDE_PROJECT_DIR` env var as cwd fallback — this may differ from the `cwd` field in the hook payload.

---

## What "Healthy" Looks Like

- Every Stop hook completes within its timeout without unhandled exceptions.
- stop_hook_active prevents all re-trigger loops.
- Session snapshot written by session-start is always consumable by stop-guard.
- Recall gets exactly one session summary per session (no duplicate writes from masonry-session-summary + recall-session-summary).
- Analytics triggers fire at expected intervals without stepping on each other.
- BL research projects are consistently detected and hooks exit silently.
- Auto-commits only include files from THIS session (no cross-session contamination).
