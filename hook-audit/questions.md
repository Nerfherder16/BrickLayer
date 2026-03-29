# Question Bank — hook-audit

**Campaign type**: BrickLayer 2.0
**Generated**: 2026-03-29
**Modes selected**: diagnose (5), audit (4), research (4), validate (2), frontier (1)
**Rationale**: This is a pure audit/research campaign with no simulation. The hook stack has pre-identified suspected issues (diagnose), systematic correctness checks (audit), behavioral assumptions to validate (research), architecture concerns (validate), and one novel failure scenario (frontier).

---

## Wave 1

---

### D1.1: Does masonry-stop-guard.js correctly implement the stop_hook_active re-trigger prevention, and is exit code 2 unreachable once the flag is set?

**Status**: DONE
**Mode**: diagnose
**Priority**: HIGH
**H0**: masonry-stop-guard.js correctly reads `stop_hook_active` from stdin payload and exits 0 immediately if set, making exit code 2 unreachable on re-trigger.
**H1**: The stop_hook_active check is incomplete, incorrectly positioned, or bypassed under specific conditions (e.g., stdin parse failure, missing session ID), allowing exit code 2 to fire on a second Stop attempt and trapping the session permanently.
**Prediction**: If H1 is true, at least one code path in masonry-stop-guard.js will reach the exit-2 block without passing through the stop_hook_active guard — visible by tracing the execution tree for the case where stdin JSON parse fails or session ID is absent.
**Agent**: diagnose-analyst
**Success criterion**: Full code path analysis confirms stop_hook_active is checked before ANY exit-2 path; OR identifies at least one code path where exit-2 is reachable after stop_hook_active is set.

---

### D1.2: Is there a scenario where masonry-build-guard and masonry-ui-compose-guard both block Stop simultaneously, and does Claude Code handle chained exit-2 responses correctly?

**Status**: DONE
**Mode**: diagnose
**Priority**: HIGH
**H0**: Claude Code correctly sequences the Stop hook chain — if hook 7 (masonry-build-guard) exits 2 and blocks, the user retries and stop_hook_active is set, causing both hooks to pass on retry. No infinite loop is possible.
**H1**: When both masonry-build-guard (position 7) and masonry-ui-compose-guard (position 8) have pending tasks, the retry with stop_hook_active does not correctly propagate to both, or one of them clears its guard while the other still blocks, creating a two-step trap.
**Prediction**: If H1 is true, it is possible to construct a state where `stop_hook_active = true` is set but masonry-ui-compose-guard still reaches exit code 2 — because it independently evaluates pending task state.
**Agent**: diagnose-analyst
**Success criterion**: Code analysis confirms both hooks check stop_hook_active and exit 0 when set, regardless of pending task state — OR identifies the scenario where one hook allows retry through while the other re-blocks.

---

### D1.3: Does masonry-handoff.js receive the session ID via process.argv[2] reliably, and what happens when it is invoked without a session ID argument?

**Status**: DONE
**Mode**: diagnose
**Priority**: HIGH
**H0**: masonry-handoff.js is always invoked with the session ID as process.argv[2] by the Stop hook runner, and falls back to 'unknown' gracefully when absent.
**H1**: The async detached invocation pattern for masonry-handoff.js does not pass session ID via argv. The hook runner invokes it as a direct command without argv arguments, causing the de-dup guard file to be named `masonry-handoff-triggered-unknown.json` — shared across ALL sessions and triggering only once per machine lifetime.
**Prediction**: If H1 is true, reading the settings.json hook command for masonry-handoff.js will show it is invoked WITHOUT `{session_id}` as an argument, unlike the documented pattern in its code comments.
**Agent**: diagnose-analyst
**Success criterion**: Confirms whether settings.json passes session ID to masonry-handoff.js; confirms what happens to the de-dup guard when ID is 'unknown'.

---

### D1.4: Does the masonry-stop-guard session snapshot round-trip work end-to-end — is the snapshot always written before Stop hooks run?

**Status**: DONE
**Mode**: diagnose
**Priority**: HIGH
**H0**: masonry-session-start.js always writes `$TMPDIR/masonry-snap-{sessionId}.json` before any Stop hook fires, and masonry-stop-guard.js always reads a valid snapshot file for the current session.
**H1**: The snapshot is only written if session-start completes successfully AND a session ID is available. If session-start exits early (BL detection, stdin timeout at 3s, or JSON parse failure), no snapshot is written, and masonry-stop-guard falls back to mtime-based detection — which checks ALL dirty files today, not just session files, risking auto-committing another session's work.
**Prediction**: If H1 is true, the mtime fallback path in masonry-stop-guard is reachable in normal usage (any session where session-start timed out or the project was initially detected as BL but then changed). The fallback labels files "today's" rather than "this session's".
**Agent**: diagnose-analyst
**Success criterion**: Code trace confirms under what conditions the snapshot is absent; confirms whether the mtime fallback correctly limits scope to THIS session or may include other-session files.

---

### D1.5: Does masonry-context-monitor.js check stop_hook_active, and what is the blocking threshold behavior when context is high but the repo is clean?

**Status**: DONE
**Mode**: diagnose
**Priority**: MEDIUM
**H0**: masonry-context-monitor.js checks stop_hook_active and exits 0 when set. It only blocks (exit 2) when context > 750K tokens AND uncommitted changes exist. A clean repo never produces exit 2 regardless of context size.
**H1**: masonry-context-monitor.js may not check stop_hook_active (not confirmed in first 80 lines of source). If it doesn't, it could block on retry after stop_hook_active is set, conflicting with the retry semantics of hooks 7 and 8.
**Prediction**: If H1 is true, the full source of masonry-context-monitor.js will not contain a `stop_hook_active` check, making it a latent re-trigger risk at context > 750K.
**Agent**: diagnose-analyst
**Success criterion**: Full source review confirms presence/absence of stop_hook_active guard; confirms the blocking condition logic is correct (AND — both conditions required, not OR).

---

### D1.3-FU1: Does hook-runner.exe support template variable injection (e.g., {session_id}) in hook commands, and is this used anywhere in settings.json?

**Status**: DONE
**Mode**: diagnose
**Priority**: HIGH
**H0**: hook-runner.exe supports template variable injection for session_id in hook commands, but masonry-handoff.js was not updated to use it.
**H1**: hook-runner.exe has no template injection support — session_id is never available via argv for async hooks, making the masonry-handoff.js design fundamentally flawed for session-scoped de-dup.
**Prediction**: Searching settings.json for template patterns like `{session_id}` or `$SESSION_ID` will find zero instances, confirming no hooks use this pattern.
**Agent**: diagnose-analyst
**Success criterion**: Confirms whether hook-runner.exe supports template expansion; confirms whether any hook in settings.json passes session_id via argv.

---

### D1.3-FU2: Does masonry-session-summary.js have a similar single-fire guard issue, or does it correctly deduplicate per session?

**Status**: DONE
**Mode**: diagnose
**Priority**: HIGH
**H0**: masonry-session-summary.js reads session_id from stdin (not argv) and correctly writes per-session summaries to Recall.
**H1**: masonry-session-summary.js has a similar or related deduplication issue — either it also fires only once, or its Recall writes are keyed incorrectly.
**Prediction**: Reading masonry-session-summary.js will show it reads session_id from parsed stdin payload (not argv), so it correctly identifies each session.
**Agent**: diagnose-analyst
**Success criterion**: Confirms masonry-session-summary.js session ID sourcing and deduplication mechanism.

---

### A1.3-FU1: Do orphaned wrong-domain Recall memories need migration, or are they benign dead entries?

**Status**: DONE
**Mode**: research
**Priority**: MEDIUM
**H0**: The wrong-domain Recall entries (e.g., system-recall summaries stored in "development") are benign orphans — no query path retrieves them, they'll be superseded once A1.3 is fixed, and no migration is needed.
**H1**: The accumulated wrong-domain memories should be purged or migrated because they consume vector storage and may surface in unrelated domain searches, polluting results for other projects.
**Agent**: research-analyst
**Success criterion**: Confirms whether orphaned wrong-domain Recall entries are retrievable by any current query path; recommends migrate vs. abandon vs. purge.

---

### A1.3-FU2: Does a shared PROJECT_DOMAINS module exist in the Recall codebase, or is the table independently maintained in each hook?

**Status**: DONE
**Mode**: research
**Priority**: MEDIUM
**H0**: A shared domains module (e.g., `domains.js`) already exists in the Recall codebase and is meant to be imported by both hooks — the divergence is a failure to import it correctly.
**H1**: No shared module exists. Both hooks maintain independent copies of PROJECT_DOMAINS, making future divergence structurally likely. A shared module would need to be created as part of the A1.3 fix.
**Agent**: research-analyst
**Success criterion**: Confirms whether a shared domains module exists in the Recall hooks directory; recommends the minimal fix to prevent recurrence.

---

### A1.1: Do all Stop hooks that can exit with code 2 implement the stop_hook_active guard, and is coverage complete across the full Stop chain?

**Status**: DONE
**Mode**: audit
**Priority**: HIGH
**H0**: Every hook in the Stop chain that can produce exit code 2 (masonry-stop-guard, masonry-build-guard, masonry-ui-compose-guard, and masonry-context-monitor) checks `stop_hook_active` and exits 0 immediately when the flag is true.
**H1**: At least one hook that can produce exit code 2 lacks the stop_hook_active check, creating a latent infinite-loop trap that manifests when context is high or both build and compose modes are active simultaneously.
**Prediction**: If H1 is true, grep for `stop_hook_active` across all 13 Stop hook files will show at least one blocking hook missing the check.
**Agent**: compliance-auditor
**Success criterion**: Exhaustive grep of all 13 Stop hooks confirms stop_hook_active coverage for every exit-2 path; list of any hooks missing the guard.

---

### A1.2: Is the BL research project silence detection (program.md + questions.md sentinel) consistent across all hooks that implement it?

**Status**: DONE
**Mode**: audit
**Priority**: HIGH
**H0**: All hooks that implement BL silence detection use the same sentinel (program.md AND questions.md both present) and check the same directory (the effective cwd of the hook process).
**H1**: At least one hook checks a different directory (e.g., `process.cwd()` vs `input.cwd` vs `process.env.CLAUDE_PROJECT_DIR`) or uses a different sentinel, causing it to fire inside a BL campaign when other hooks correctly silence themselves.
**Prediction**: If H1 is true, comparing the isResearchProject() implementation across masonry-session-start, masonry-prompt-router, masonry-stop-guard, masonry-build-guard, masonry-score-trigger, masonry-pagerank-trigger, and masonry-ema-collector will reveal at least one divergent cwd source.
**Agent**: compliance-auditor
**Success criterion**: Cross-hook audit table showing cwd source and sentinel logic for each hook; any divergences flagged as findings.

---

### A1.3: Does recall-session-summary.js have divergent domain mapping that causes Recall writes to land in wrong domains compared to what recall-retrieve.js reads?

**Status**: DONE
**Mode**: audit
**Priority**: MEDIUM
**H0**: The PROJECT_DOMAINS table in recall-session-summary.js maps all projects to the same canonical domains as recall-retrieve.js, ensuring memories written at Stop are retrievable at UserPromptSubmit.
**H1**: recall-session-summary.js maps system-recall → "development" and familyhub → "ai-ml", while recall-retrieve.js maps the same projects to "recall" and "family-hub" respectively. Session summaries land in wrong Recall domains and are never retrieved by recall-retrieve.js because the domain filters don't match.
**Prediction**: If H1 is true, a session working on the system-recall project will write its summary to domain "development" but recall-retrieve.js will search domain "recall" — the memory will exist in Recall but will never surface in future sessions.
**Agent**: compliance-auditor
**Success criterion**: Side-by-side comparison of all PROJECT_DOMAINS entries across recall-retrieve.js, recall-session-summary.js, and masonry-session-summary.js; explicit list of mismatches with severity.

---

### A1.4: Does masonry-ui-compose-guard.js implement the BL research project silence guard that masonry-build-guard.js has?

**Status**: DONE
**Mode**: audit
**Priority**: MEDIUM
**H0**: masonry-ui-compose-guard.js implements the same `isResearchProject()` early exit as masonry-build-guard.js, silencing itself inside BL campaigns.
**H1**: masonry-ui-compose-guard.js is missing the isResearchProject() guard (it was adapted from build-guard but the BL silence logic was not copied). A BL campaign running in a directory that also has a `.ui/compose` state file (e.g., from an interrupted UI build) will be blocked at Stop by masonry-ui-compose-guard.
**Prediction**: If H1 is true, masonry-ui-compose-guard.js source will not contain a check for `program.md` and `questions.md`, unlike masonry-build-guard.js which explicitly checks `isResearchProject(process.cwd())`.
**Agent**: compliance-auditor
**Success criterion**: Source comparison confirms presence/absence of BL silence guard in masonry-ui-compose-guard.js.

---

### R1.1: How does the masonry-register.js guard warning flush mechanism work in practice, and can a guard warning accumulate and never be delivered?

**Status**: DONE
**Mode**: research
**Priority**: HIGH
**H0**: masonry-register.js correctly writes guard warnings to `masonry-guard-{sessionId}.ndjson` during PreToolUse hooks, then flushes and deletes the file on the next UserPromptSubmit call, ensuring warnings are always delivered within one turn.
**H1**: The guard warning file can accumulate warnings that are never flushed if: (a) the next UserPromptSubmit fires before the guard file is written (race condition), (b) the session ends before another UserPromptSubmit fires, or (c) the guard file path is inconsistent across hooks (different session ID format).
**Prediction**: If H1 is true, examining the temp file naming convention used by the hooks that write guard warnings vs. masonry-register.js that reads them will reveal either a timing window or a file path mismatch.
**Agent**: research-analyst
**Success criterion**: Confirms the guard warning round-trip works correctly end-to-end; OR identifies specific conditions under which warnings are lost.

---

### R1.2: Does the masonry-training-export.js use spawnSync (blocking) despite being registered as async:true, and what is the actual behavior under the 65-second timeout?

**Status**: DONE
**Mode**: research
**Priority**: MEDIUM
**H0**: masonry-training-export.js uses async spawn (non-blocking) internally, making its 65-second timeout in settings.json irrelevant because the hook process exits quickly after spawning the background Python process.
**H1**: masonry-training-export.js uses spawnSync (blocking) internally despite being marked async:true in settings.json. The async:true flag only means Claude Code doesn't wait for it — but the hook process itself blocks for up to 65 seconds on the Python spawnSync call, consuming system resources until timeout.
**Prediction**: If H1 is true, reading the full source of masonry-training-export.js will show `spawnSync` rather than `spawn` for the Python export call, confirming it blocks the Node.js event loop until Python completes or 65s elapses.
**Agent**: research-analyst
**Success criterion**: Full source confirms spawn vs spawnSync; explains the interaction between async:true in settings.json and the hook's internal blocking/non-blocking behavior.

---

### R1.3: Under what realistic daily development conditions do masonry-score-trigger, masonry-pagerank-trigger, and masonry-ema-collector actually fire, given their rate limits?

**Status**: DONE
**Mode**: research
**Priority**: MEDIUM
**H0**: The analytics triggers (score-trigger: 24h, pagerank: 60min, ema: 5min) fire reliably in normal development workflow — multiple daily Stop events ensure they execute at least once per day each.
**H1**: The rate limits are misaligned with actual workflow patterns. Score-trigger's 24h window means it can only fire once per day regardless of campaign activity. Pagerank's `masonry/` directory guard means it only fires from the BL repo root — never from project subdirectories. EMA's 5-minute debounce is fine but telemetry.jsonl may not accumulate entries between short sessions.
**Prediction**: If H1 is true, the pagerank-trigger guard (`masonry/` dir must exist in cwd) means it never fires when Tim is working in a project subdirectory like `hook-audit/` — it only fires from `C:/Users/trg16/Dev/Bricklayer2.0/` directly.
**Agent**: research-analyst
**Success criterion**: Confirms the actual firing conditions for all three analytics triggers; identifies any conditions under which they silently never fire.

---

### R1.4: Does masonry-session-summary.js (Masonry) produce a duplicate session summary alongside recall-session-summary.js (Recall), and how do their Recall payloads differ?

**Status**: DONE
**Mode**: research
**Priority**: MEDIUM
**H0**: masonry-session-summary.js and recall-session-summary.js serve different purposes — masonry writes a structured activity summary (from masonry-observe.js activity log) while recall writes an LLM-generated transcript summary. They complement each other without duplication.
**H1**: Both hooks write a "session summary" to Recall for the same session, domain, and tags, resulting in two Recall entries per session that partially overlap. Recall search results at next session start may return both, consuming context budget with redundant information.
**Prediction**: If H1 is true, comparing the Recall store calls in both files will show overlapping `domain`, `tags`, and `memory_type` values — making it likely that recall-retrieve.js retrieves both on the following session's first prompt.
**Agent**: research-analyst
**Success criterion**: Side-by-side comparison of what each hook writes to Recall (domain, tags, memory_type, content structure); assessment of whether both would be retrieved by recall-retrieve.js.

---

### V1.1: Is the architecture of the temp file bus (shared state via $TMPDIR) sound for a multi-session, multi-machine environment?

**Status**: DONE
**Mode**: validate
**Priority**: HIGH
**H0**: The $TMPDIR-based temp file bus is architecturally sound for Tim's workflow — session IDs are unique per session, files are cleaned up correctly, and the system handles concurrent sessions (casaclaude + proxyclaude) without cross-contamination.
**H1**: The temp file bus has architectural weaknesses in a multi-machine environment: (a) $TMPDIR is local to each machine, so hooks on casaclaude and proxyclaude have isolated temp files — a session ID from proxyclaude cannot be found in casaclaude's $TMPDIR; (b) session-start writes a snap file that may collide with pre-existing snap files from a previous session with the same ID (UUID collision or reuse); (c) the masonry-{sessionId}.json "firstCall" tracking can only prevent per-session Recall hydration on one machine.
**Prediction**: If H1 is true, the stop-guard mtime fallback is triggered on any session where session-start ran on a different machine than stop fires on (cross-machine session migration) — since the snap file simply won't exist in that machine's $TMPDIR.
**Agent**: design-reviewer
**Success criterion**: Architecture assessment confirms whether the temp file bus is safe for Tim's multi-machine workflow; identifies any cross-contamination scenarios.

---

### V1.2: Is the Stop hook execution order correct — specifically, does running recall-session-summary (position 2) before masonry-stop-guard (position 3) introduce a race or correctness issue?

**Status**: DONE
**Mode**: validate
**Priority**: MEDIUM
**H0**: The Stop hook order (recall session-save → recall summary → masonry stop-guard → masonry session-summary → handoff → context-monitor → build-guard → ui-compose-guard → analytics triggers) is intentionally designed so non-blocking Recall writes complete before the potentially-blocking stop-guard runs. This is correct because the stop-guard may block, and Recall writes should not be lost.
**H1**: Running recall-session-summary.js (which internally detaches a long-running Ollama summary process) BEFORE masonry-stop-guard.js (which may auto-commit) creates a correctness issue: the detached summary process may still be running when the stop-guard auto-commits session files, potentially including partially-written Recall cache files in the commit.
**Prediction**: If H1 is true, recall-session-summary.js writes to `~/.cache/recall/` files (debug logs, session data) that are within the git working tree or in a location that masonry-stop-guard includes in its dirty file check — causing Recall's cache files to be auto-committed.
**Agent**: design-reviewer
**Success criterion**: Confirms whether Recall cache files are within the git scope of masonry-stop-guard; confirms whether the detached Ollama summary process can write to any git-tracked location before the stop-guard auto-commit runs.

---

### FR1.1: What failure modes emerge when the session ID is absent from ALL Stop hook inputs, and is there a safe degradation path?

**Status**: DONE
**Mode**: frontier
**Priority**: LOW
**H0**: All Stop hooks degrade gracefully when session ID is absent — they either skip session-specific operations or use fallback identifiers, and no hook blocks or throws an unhandled exception.
**H1**: Session ID absence causes a cascade of quiet failures: (a) session-save.js exits 0 immediately (no snapshot saved to Recall), (b) masonry-stop-guard falls back to mtime detection (imprecise scope), (c) masonry-handoff de-dup guard uses filename "unknown" (shared across all sessions → fires only once ever on the machine), (d) masonry-session-summary has no correlation key and may write a meaningless entry, (e) analytics triggers are unaffected (don't use session ID). The session produces no persistent state record in Recall, and the handoff payload is permanently stale.
**Prediction**: If H1 is true, a session where the stop hook payload contains no `session_id` field results in: zero Recall writes for session memory, stop-guard mtime fallback active, and a stale handoff entry keyed to "unknown" that blocks future sessions from getting fresh handoffs until manually cleared.
**Agent**: frontier-analyst
**Success criterion**: Maps the full degradation cascade when session ID is absent; identifies which hooks are resilient vs. fragile; recommends whether a session-ID fallback (e.g., timestamp-based) would improve resilience.

---

## Wave 1 Summary

| ID | Question | Mode | Priority | Agent |
|----|----------|------|----------|-------|
| D1.1 | stop_hook_active guard completeness in masonry-stop-guard | diagnose | HIGH | diagnose-analyst |
| D1.2 | Chained exit-2 from build-guard + ui-compose-guard | diagnose | HIGH | diagnose-analyst |
| D1.3 | masonry-handoff.js session ID via argv reliability | diagnose | HIGH | diagnose-analyst |
| D1.4 | Session snapshot round-trip correctness | diagnose | HIGH | diagnose-analyst |
| D1.5 | masonry-context-monitor stop_hook_active and blocking condition | diagnose | MEDIUM | diagnose-analyst |
| A1.1 | stop_hook_active coverage audit across all 13 Stop hooks | audit | HIGH | compliance-auditor |
| A1.2 | BL silence detection consistency across hooks | audit | HIGH | compliance-auditor |
| A1.3 | Recall domain mapping divergence between hooks | audit | MEDIUM | compliance-auditor |
| A1.4 | masonry-ui-compose-guard BL silence guard absence | audit | MEDIUM | compliance-auditor |
| R1.1 | Guard warning flush mechanism correctness | research | HIGH | research-analyst |
| R1.2 | masonry-training-export spawnSync vs async | research | MEDIUM | research-analyst |
| R1.3 | Analytics trigger firing conditions in real workflows | research | MEDIUM | research-analyst |
| R1.4 | Duplicate session summary investigation | research | MEDIUM | research-analyst |
| V1.1 | Temp file bus architecture for multi-session/multi-machine | validate | HIGH | design-reviewer |
| V1.2 | Stop hook execution order correctness | validate | MEDIUM | design-reviewer |
| FR1.1 | Failure cascade when session ID absent from all Stop hooks | frontier | LOW | frontier-analyst |

**Total**: 16 questions | 5 HIGH priority | 8 MEDIUM priority | 3 HIGH overall (D1.1, A1.1, A1.2 are campaign-critical)

---

## Wave Mid — Follow-up Questions (generated at N=16)

### WM1.1 — masonry-observe.js cross-session state corruption under concurrent multi-machine use

**Status**: DONE
**Mode**: monitor
**Priority**: HIGH
**H0**: masonry-observe.js correctly keys all mutable state to session_id. Under concurrent multi-machine use where session_id is absent or collides, the hook produces at worst a missed observe — no cross-session state mutation.
**H1**: masonry-observe.js writes to a shared state location (temp file or campaign state file) keyed by something other than session_id. When two sessions run concurrently (casaclaude + proxyclaude), one session's observation can overwrite the other's, causing silent state corruption in the campaign running on that machine.
**Prediction**: If H1 is true, concurrent /ultrawork runs across two machines would exhibit missing or interleaved observation records.
**Agent**: diagnose-analyst
**Success criterion**: Identifies what state masonry-observe.js mutates, what key it uses, and whether concurrent sessions from different machines can collide.

---

### WM1.2 — Temp-bus cold-start pollution from stale TTL-expired files

**Status**: DONE
**Mode**: monitor
**Priority**: MEDIUM
**H0**: The temp-bus (TMPDIR-based stop_hook_active flag files) is stateless between restarts. Any stale files from a prior session that failed to clean up are either ignored or expire within their TTL, producing no false positive.
**H1**: Stale temp-bus files from a crashed or force-killed session survive restart. Because the TTL check is mtime-based and the file was not re-created this session, a new session may read a stale "active" flag and skip exit-2 blocking — silently degrading the stop guard for the first real stop event.
**Prediction**: If H1 is true, a session started within 60 seconds of a force-killed prior session would have masonry-stop-guard skip the git dirty check.
**Agent**: research-analyst
**Success criterion**: Determines the TTL logic for temp-bus files and whether a cold-start can inherit a stale active flag from a prior crashed session.

---

### WM1.3 — /ultrawork throughput exceeds temp-bus 5s TTL

**Status**: DONE
**Mode**: monitor
**Priority**: MEDIUM
**H0**: The temp-bus TTL (5 seconds for stop_hook_active) is long enough that even under /ultrawork's maximum parallel agent throughput, the active flag survives between the exit-2 retry and the re-evaluation.
**H1**: Under /ultrawork with 6-8 parallel workers, sub-agent Stop events arrive faster than the 5s TTL. The stop_hook_active flag written by one worker's exit-2 expires before the next worker's Stop hook reads it — causing the second worker to block when it should not.
**Prediction**: If H1 is true, /ultrawork runs would exhibit spurious stop-guard blockage on some workers in high-parallelism builds.
**Agent**: research-analyst
**Success criterion**: Identifies the TTL value, the timing window between exit-2 and re-evaluation, and whether /ultrawork's throughput can exceed it.

---

### WD1.1 — masonry-subagent-tracker.js reads session_id from stdin or argv?

**Status**: DONE
**Mode**: diagnose
**Priority**: MEDIUM
**H0**: masonry-subagent-tracker.js reads session_id from stdin JSON (same pattern as masonry-session-summary.js), correctly keying subagent tracking entries to the parent session.
**H1**: masonry-subagent-tracker.js reads session_id from process.argv, producing the same "unknown" or empty-string keying defect as masonry-handoff.js (D1.3). Subagent tracking entries would pile up under the wrong key, making fleet analytics unreliable.
**Prediction**: If H1 is true, masonry-subagent-tracker.js has the same narrow async-timing window defect as D1.3-FU1 confirmed for masonry-handoff.js.
**Agent**: diagnose-analyst
**Success criterion**: Reads masonry-subagent-tracker.js source and confirms whether session_id is sourced from stdin JSON or argv. If argv, classifies as FAILURE with same severity as D1.3.

---

### WD1.2 — masonry-session-start.js queries Recall with stale domain list?

**Status**: DONE
**Mode**: diagnose
**Priority**: HIGH
**H0**: masonry-session-start.js derives the search domain for Recall rehydration from the current working directory using a correct, up-to-date domain map (matching recall-retrieve.js and masonry-session-summary.js).
**H1**: masonry-session-start.js maintains its own PROJECT_DOMAINS map that has the same staleness defect as recall-session-summary.js (A1.3): broad-bucket mappings like "development" or "ai-ml" rather than per-project domains. Recall rehydration at session start queries the wrong domain — the session briefing is populated from the wrong memory pool.
**Prediction**: If H1 is true, opening a Claude Code session in the recall/ or system-recall/ directory would rehydrate with "development" domain memories instead of "recall" domain memories, injecting wrong-project context at the most critical moment (session open).
**Agent**: diagnose-analyst
**Success criterion**: Reads masonry-session-start.js source (and any delegate files it calls) and compares its PROJECT_DOMAINS mapping against recall-retrieve.js lines 43-59. If maps diverge, classifies as FAILURE.

---

## Wave 2 — Fix Verification

---

### W2D1.1 — D1.3 fix: does masonry-handoff.js now read session_id from stdin and key the de-dup guard correctly?

**Status**: PENDING
**Mode**: diagnose
**Priority**: HIGH
**Wave**: 2
**H0**: masonry-handoff.js now reads session_id from stdin JSON (not argv) and keys the de-dup guard file as `handoff-triggered-{sessionId}.json` — the guard fires once per session, not once per machine lifetime.
**H1**: The fix is incomplete — either session_id is still read from a wrong source, the guard key still uses a static identifier, or the fallback to 'unknown' re-introduces the stuck-guard defect.
**Prediction**: If H0 is true, each session gets its own guard file and subsequent sessions are not blocked.
**Agent**: diagnose-analyst
**Success criterion**: Reads masonry-handoff.js source, confirms session_id sourced from stdin JSON, confirms guard key includes sessionId, and confirms the guard file path matches what masonry-stop-guard.js would check.

---

### W2A1.1 — A1.3 fix: do recall-session-summary.js and recall-retrieve.js now share domains.js?

**Status**: PENDING
**Mode**: diagnose
**Priority**: HIGH
**Wave**: 2
**H0**: Both recall-session-summary.js and recall-retrieve.js now require('./domains') and the shared module exports PROJECT_DOMAINS with correct per-project keys (no broad-bucket "development"/"ai-ml"/"infrastructure" entries). Session summaries will land in correct Recall domains.
**H1**: The require() is present but the domains.js module still contains stale entries, or one of the two hooks still has an inline fallback table that overrides the shared module.
**Prediction**: If H0 is true, a session in the recall/ directory produces summaries tagged domain="recall", not domain="development".
**Agent**: diagnose-analyst
**Success criterion**: Reads C:/Users/trg16/Dev/Recall/hooks/domains.js, recall-session-summary.js, and recall-retrieve.js. Confirms require('./domains') present in both hooks, confirms no stale broad-bucket keys in the shared module, and confirms no inline override tables remain.

---

### W2WM1.1 — WM1.1 fix: is state.js writeState() now atomic?

**Status**: PENDING
**Mode**: diagnose
**Priority**: HIGH
**Wave**: 2
**H0**: state.js writeState() now uses the temp-rename pattern: writes to `{stateFile}.tmp.{pid}`, then calls fs.renameSync to the final path. This is atomic on POSIX and effectively atomic on Windows NTFS. No lost-update race is possible between concurrent processes.
**H1**: The fix has an edge case — either the tmp file is left behind on crash (no cleanup), the rename is not truly atomic on the Windows NTFS path used by Tim's machines, or the pid suffix does not prevent collisions under rapid re-entry.
**Prediction**: If H0 is true, concurrent writes from casaclaude + proxyclaude always result in one full write winning, never a torn state file.
**Agent**: diagnose-analyst
**Success criterion**: Reads masonry/src/core/state.js writeState() implementation. Confirms tmp-rename pattern, assesses Windows NTFS atomicity guarantee, and checks for any remaining direct writeFileSync calls on the state file.

---

### W2R1.2 — R1.2 fix: does masonry-training-export.js now use non-blocking spawn?

**Status**: PENDING
**Mode**: diagnose
**Priority**: MEDIUM
**Wave**: 2
**H0**: masonry-training-export.js now uses spawn() (non-blocking) with stdout/stderr data listeners and a 'close' event handler. The hook exits via process.exit(0) in the close handler. spawnSync is no longer used anywhere in the file.
**H1**: The spawn replacement is structurally correct but has a race — if the child process writes a lot of stdout and the 'close' event fires before all data events are flushed, some output is lost. Or the 'error' event path does not call process.exit(0), leaving the hook hanging.
**Prediction**: If H0 is true, the hook process does not block the Node.js event loop during the 60s export window.
**Agent**: diagnose-analyst
**Success criterion**: Reads masonry-training-export.js. Confirms no spawnSync import or call, confirms spawn with close+error handlers, confirms process.exit(0) called in both success and error paths.

---

### W2R1.3 — R1.3 fix: does findMasonryDir() correctly resolve the masonry/ dir from all cwd positions?

**Status**: PENDING
**Mode**: diagnose
**Priority**: MEDIUM
**Wave**: 2
**H0**: masonry-observe-helpers.js exports findMasonryDir(startDir) which walks up the directory tree (up to 8 levels) checking for a masonry/ child dir or whether the dir itself IS masonry/. This correctly resolves from: (a) a project subdir like hook-audit/, (b) the BL2.0 root, (c) a self-research session where cwd is masonry/ itself.
**H1**: The walk-up logic has an off-by-one or stops too early — specifically, it finds masonry/ as a sibling but not as an ancestor's child when cwd is 2+ levels deep inside a BL project.
**Prediction**: If H0 is true, routing_log.jsonl entries are written from any cwd depth within a BL2.0 project tree.
**Agent**: diagnose-analyst
**Success criterion**: Reads masonry-observe-helpers.js findMasonryDir() implementation and traces the walk-up for: cwd=hook-audit/ (should find Bricklayer2.0/masonry/), cwd=Bricklayer2.0/ (should find Bricklayer2.0/masonry/), cwd=Bricklayer2.0/masonry/ (should return itself). Confirms all three cases resolve correctly.

---

### W2A1.4 — A1.4 fix: does masonry-ui-compose-guard.js isResearchProject() match masonry-build-guard.js exactly?

**Status**: PENDING
**Mode**: validate
**Priority**: MEDIUM
**Wave**: 2
**H0**: masonry-ui-compose-guard.js isResearchProject() checks for both program.md AND questions.md in process.cwd(), matching masonry-build-guard.js exactly. The guard exits at the top of main() before any .ui/ state is read.
**H1**: The guard checks only one sentinel file, or is placed after some .ui/ state is read (meaning BL project sessions still incur partial execution before silencing).
**Prediction**: If H0 is true, running masonry-ui-compose-guard.js in a BL research project directory exits 0 immediately without touching .ui/ state.
**Agent**: design-reviewer
**Success criterion**: Reads masonry-ui-compose-guard.js and masonry-build-guard.js, diffs the isResearchProject() implementations and placement, confirms they are functionally identical.

---

### W2D1.4 — D1.4 fix: does the session-{ppid} fallback produce a stable ID for the session lifetime?

**Status**: PENDING
**Mode**: diagnose
**Priority**: MEDIUM
**Wave**: 2
**H0**: masonry-session-start.js now sets sessionId = input.session_id || input.sessionId || `session-${process.ppid}`. The ppid (parent process ID) is stable for the lifetime of the Claude Code session — all hooks spawned by the same session share the same ppid. This allows the activity log and stop-guard to correlate correctly even when Claude Code omits session_id.
**H1**: process.ppid is not stable across hooks — each hook spawn may have a different ppid if Claude Code uses a process pool. The fallback ID would differ between masonry-session-start.js and masonry-stop-guard.js, breaking the correlation.
**Prediction**: If H1 is true, the fallback still degrades to mtime mode (same as before the fix) because the snap file written by session-start uses ppid=X but stop-guard looks for ppid=Y.
**Agent**: diagnose-analyst
**Success criterion**: Reads masonry-session-start.js and masonry-stop-guard.js. Confirms whether stop-guard also uses process.ppid as its fallback session ID (or reads it from the snap file). Assesses whether ppid is stable across hook invocations from the same Claude Code session.

---

### W2R1.1 — R1.1 fix: does removal of dead guard-flush code break the masonry-register subsequent-call path?

**Status**: PENDING
**Mode**: validate
**Priority**: LOW
**Wave**: 2
**H0**: Removing the guard-flush block from masonry-register.js leaves the subsequent-call path (sessionState.firstCall === false) correctly calling emit(contextParts) and returning. The removal is safe — no other code depended on the guard file being flushed here.
**H1**: The guard-flush block was also responsible for populating contextParts with something useful on subsequent calls. Its removal means subsequent calls return an empty context injection, degrading session continuity.
**Prediction**: If H0 is true, subsequent calls produce the same output as before (the guard file was always empty since masonry-guard.js was archived).
**Agent**: diagnose-analyst
**Success criterion**: Reads masonry-register.js lines around the subsequent-call path. Confirms contextParts is still populated (or intentionally empty) on subsequent calls. Confirms no reference to the guard file remains.
