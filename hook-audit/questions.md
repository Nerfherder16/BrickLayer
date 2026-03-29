# hook-audit — Question Bank

## Wave 1 — Registration, Blocking Mechanisms, Session Lifecycle

---

**H1.1** | Mode: audit | Priority: HIGH
Does masonry-context-monitor.js correctly block the Stop event?
It uses `process.stdout.write(JSON.stringify({decision:"block", ...}))` then `process.exit(0)` — while masonry-stop-guard.js uses `process.exit(2)`. Verify which mechanism Claude Code honors for Stop hooks. If `{decision:"block"}` stdout + exit 0 is not a valid Stop-blocking pattern, context-monitor never actually blocks.

---

**H1.2** | Mode: audit | Priority: HIGH
Does masonry-stop-guard.js read the activity log before masonry-session-summary.js deletes it?
Stop hooks run in the order registered in settings.json. masonry-stop-guard is hook #3 and masonry-session-summary is hook #4. Verify: does session-summary delete or overwrite `masonry-activity-{sessionId}.ndjson`? If yes, the ordering is correct. If session-summary runs first (async, early timeout?), stop-guard reads a missing file and falls back to snapshot-only detection — less accurate.

---

**H1.3** | Mode: audit | Priority: HIGH
masonry-handoff.js always uses sessionId='unknown' — what is the actual impact?
The settings.json command is `node masonry-handoff.js` with no arguments. `process.argv[2]` is undefined, so `sessionId = 'unknown'`. The guard file becomes `masonry-handoff-triggered-unknown.json` in tmpdir — shared across ALL sessions on the machine. Verify: (a) does this prevent multiple sessions from triggering handoffs, or does it prevent all handoffs after the first? (b) does the Recall store call use 'unknown' as the session tag, corrupting memory metadata?

---

**H1.4** | Mode: audit | Priority: HIGH
Are recall-session-summary.js and masonry-session-summary.js writing duplicate memories to Recall for Bricklayer2.0 sessions?
Both hooks call Recall's `/memory/store` endpoint. recall-session-summary stores with `domain:"development"` for Recall/BL projects; masonry-session-summary stores with `domain:"autoresearch"`. Verify: for a single BL session, are two separate session summary memories created in Recall? If yes, is this intentional, or does one supersede the other?

---

**H1.5** | Mode: audit | Priority: MEDIUM
Does masonry-session-start.js correctly detect and exclude pre-existing dirty files from stop-guard scope?
session-start writes `masonry-snap-{sessionId}.json` containing the list of pre-existing modified files at session open. stop-guard reads this snap to exclude files that were already dirty before the session. Verify: (a) does the snap capture ALL dirty files (staged, unstaged, untracked) or only a subset? (b) if session-start fails silently, stop-guard operates without a snap — what is the fallback behavior?

---

**H1.6** | Mode: audit | Priority: MEDIUM
Does recall-retrieve.js correctly handle Recall being unreachable at UserPromptSubmit time?
recall-retrieve.js fires on every query. If Recall (100.70.195.84:8200) is down, does it exit 0 silently within the 8s timeout, or does it hang until timeout causing perceptible query latency? Verify the error path and timeout behavior.

---

**H1.7** | Mode: audit | Priority: MEDIUM
Is masonry-ema-collector.js's telemetry gate ever satisfied?
The hook only fires if `masonry/telemetry.jsonl` exists and has entries. Verify: (a) which hook or script writes to `masonry/telemetry.jsonl` in the current codebase? (b) if nothing writes it, ema-collector silently exits every session and collector.py never runs — is this the actual current state?

---

**H1.8** | Mode: audit | Priority: MEDIUM
Does masonry-score-trigger.js correctly identify stale scores, and is the DSPy optimization trigger agent hardcoded?
score-trigger checks if `masonry/training_data/scored_all.jsonl` is >24h old, then spawns `score_all_agents.py`. It also checks example count to trigger `run_optimization.py` with `DSPY_DEFAULT_AGENT='research-analyst'` hardcoded. Verify: (a) does `scored_all.jsonl` exist in the current codebase? (b) is always optimizing only research-analyst correct, or should the agent be dynamic based on which agents have new traces?

---

**H1.9** | Mode: audit | Priority: MEDIUM
Does masonry-pagerank-trigger.js correctly locate `pagerank.py` using `process.cwd()` vs `parsed.cwd`?
pagerank-trigger uses `path.join(cwd, 'masonry', 'src', 'reasoning', 'pagerank.py')` where `cwd` comes from the stdin JSON. Verify: (a) does pagerank.py exist at that path? (b) if the hook fires from a non-Bricklayer project directory, does it silently exit or error?

---

**H1.10** | Mode: audit | Priority: MEDIUM
Does masonry-register.js clean up its tmpdir session file on Stop?
masonry-register.js writes `masonry-{sessionId}.json` to tmpdir at UserPromptSubmit. Verify: is this file cleaned up at session end by any Stop hook, or does it accumulate indefinitely in tmpdir? What happens when the same sessionId restarts (e.g., after a claude reload)?

---

**H1.11** | Mode: audit | Priority: MEDIUM
Does masonry-system-status.js write valid JSON to stdout or does it produce stdout noise that interferes with Claude Code?
Stop hooks should not write arbitrary text to stdout — only valid JSON decision objects or nothing. masonry-system-status.js is a `continueOnError:true` hook so stdout noise won't block, but it may appear in the session output. Verify what exactly the hook writes to stdout vs stderr.

---

**H1.12** | Mode: audit | Priority: LOW
Is masonry-training-export.js's 65-second timeout appropriate and is `async:true` correctly set?
masonry-training-export spawns `bl/training_export.py` as a fire-and-forget background process. It has `timeout:65` and `async:true`. Verify: (a) does `bl/training_export.py` actually exist? (b) if async:true, the 65s timeout should be irrelevant for blocking — confirm this is not blocking Stop. (c) is there a `continueOnError` missing — if hook-runner.exe errors on the async invocation, does it block?

---

**H1.13** | Mode: audit | Priority: LOW
Does masonry-prompt-router.js output valid UserPromptSubmit JSON that Claude Code accepts?
prompt-router injects a one-line routing hint by writing to stdout. Verify: (a) what exact JSON format does it output? (b) is this format accepted by the current Claude Code UserPromptSubmit hook protocol? (c) does it correctly handle slash commands (should be a no-op) vs regular prompts?

---

**H1.14** | Mode: diagnose | Priority: LOW
What happens to the full Stop hook chain when masonry-stop-guard.js blocks (exit 2)?
When stop-guard exits 2, Claude Code prevents the Stop. But the remaining hooks (masonry-session-summary, masonry-handoff, masonry-context-monitor, masonry-build-guard, etc.) — do they still run? If stop is blocked, do the downstream cleanup/summary hooks still fire, or is the entire hook chain aborted? If aborted, session-summary and recall-session-summary never run when stop-guard blocks.

---

**H1.15** | Mode: research | Priority: LOW
Is the hook-runner.exe layer adding meaningful value or is it a source of silent failures?
All hooks are invoked as `hook-runner.exe node {script}` rather than `node {script}` directly. Verify: (a) what does hook-runner.exe do that `node` alone doesn't? (b) are there known failure modes where hook-runner.exe exits non-zero and the hook appears to fail even though the Node script ran correctly? (c) is the binary up-to-date with the current Claude Code hook protocol?

---

**H1.16** | Mode: audit | Priority: HIGH
Do masonry-build-guard.js and masonry-ui-compose-guard.js correctly use `parsed.cwd` instead of `process.cwd()`?
Both guards need to check `.autopilot/` and `.ui/` in the **project** directory, not the hook-runner's working directory. If either uses `process.cwd()` instead of the `cwd` field from the stdin JSON payload, they will miss build/UI state when Claude Code's cwd differs from the hook-runner's cwd.

---

**H1.17** | Mode: audit | Priority: MEDIUM
Does the session-save.js Recall hook duplicate or conflict with masonry-stop-guard.js's uncommitted file detection?
session-save.js (Recall hook, fires first in Stop chain) may also check git state or write a summary. Verify its exact behavior and whether it conflicts with or duplicates stop-guard's uncommitted changes detection.

---

**H1.18** | Mode: diagnose | Priority: HIGH
What is the actual Stop hook execution order and are all 13 hooks in the correct sequence?
The settings.json Stop array defines execution order. Map the exact sequence and verify against the dependency graph: (1) recall hooks should run before masonry-stop-guard, (2) masonry-stop-guard must run before masonry-session-summary (activity log dependency), (3) blocking guards (build-guard, ui-compose-guard) should run after or alongside stop-guard, not before. Document the full sequence and flag any ordering violations.

---

## Status Legend
`PENDING` | `IN_PROGRESS` | `DONE`

All questions: **PENDING**
