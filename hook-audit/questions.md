# Question Bank — hook-audit

**Campaign type**: BrickLayer 2.0
**Generated**: 2026-03-29
**Modes selected**: diagnose (5), audit (4), research (4), validate (2), frontier (1)
**Rationale**: This is a pure audit/research campaign with no simulation. The hook stack has pre-identified suspected issues (diagnose), systematic correctness checks (audit), behavioral assumptions to validate (research), architecture concerns (validate), and one novel failure scenario (frontier).

---

## Wave 1

---

### D1.1: Does masonry-stop-guard.js correctly implement the stop_hook_active re-trigger prevention, and is exit code 2 unreachable once the flag is set?

**Status**: PENDING
**Mode**: diagnose
**Priority**: HIGH
**H0**: masonry-stop-guard.js correctly reads `stop_hook_active` from stdin payload and exits 0 immediately if set, making exit code 2 unreachable on re-trigger.
**H1**: The stop_hook_active check is incomplete, incorrectly positioned, or bypassed under specific conditions (e.g., stdin parse failure, missing session ID), allowing exit code 2 to fire on a second Stop attempt and trapping the session permanently.
**Prediction**: If H1 is true, at least one code path in masonry-stop-guard.js will reach the exit-2 block without passing through the stop_hook_active guard — visible by tracing the execution tree for the case where stdin JSON parse fails or session ID is absent.
**Agent**: diagnose-analyst
**Success criterion**: Full code path analysis confirms stop_hook_active is checked before ANY exit-2 path; OR identifies at least one code path where exit-2 is reachable after stop_hook_active is set.

---

### D1.2: Is there a scenario where masonry-build-guard and masonry-ui-compose-guard both block Stop simultaneously, and does Claude Code handle chained exit-2 responses correctly?

**Status**: PENDING
**Mode**: diagnose
**Priority**: HIGH
**H0**: Claude Code correctly sequences the Stop hook chain — if hook 7 (masonry-build-guard) exits 2 and blocks, the user retries and stop_hook_active is set, causing both hooks to pass on retry. No infinite loop is possible.
**H1**: When both masonry-build-guard (position 7) and masonry-ui-compose-guard (position 8) have pending tasks, the retry with stop_hook_active does not correctly propagate to both, or one of them clears its guard while the other still blocks, creating a two-step trap.
**Prediction**: If H1 is true, it is possible to construct a state where `stop_hook_active = true` is set but masonry-ui-compose-guard still reaches exit code 2 — because it independently evaluates pending task state.
**Agent**: diagnose-analyst
**Success criterion**: Code analysis confirms both hooks check stop_hook_active and exit 0 when set, regardless of pending task state — OR identifies the scenario where one hook allows retry through while the other re-blocks.

---

### D1.3: Does masonry-handoff.js receive the session ID via process.argv[2] reliably, and what happens when it is invoked without a session ID argument?

**Status**: PENDING
**Mode**: diagnose
**Priority**: HIGH
**H0**: masonry-handoff.js is always invoked with the session ID as process.argv[2] by the Stop hook runner, and falls back to 'unknown' gracefully when absent.
**H1**: The async detached invocation pattern for masonry-handoff.js does not pass session ID via argv. The hook runner invokes it as a direct command without argv arguments, causing the de-dup guard file to be named `masonry-handoff-triggered-unknown.json` — shared across ALL sessions and triggering only once per machine lifetime.
**Prediction**: If H1 is true, reading the settings.json hook command for masonry-handoff.js will show it is invoked WITHOUT `{session_id}` as an argument, unlike the documented pattern in its code comments.
**Agent**: diagnose-analyst
**Success criterion**: Confirms whether settings.json passes session ID to masonry-handoff.js; confirms what happens to the de-dup guard when ID is 'unknown'.

---

### D1.4: Does the masonry-stop-guard session snapshot round-trip work end-to-end — is the snapshot always written before Stop hooks run?

**Status**: PENDING
**Mode**: diagnose
**Priority**: HIGH
**H0**: masonry-session-start.js always writes `$TMPDIR/masonry-snap-{sessionId}.json` before any Stop hook fires, and masonry-stop-guard.js always reads a valid snapshot file for the current session.
**H1**: The snapshot is only written if session-start completes successfully AND a session ID is available. If session-start exits early (BL detection, stdin timeout at 3s, or JSON parse failure), no snapshot is written, and masonry-stop-guard falls back to mtime-based detection — which checks ALL dirty files today, not just session files, risking auto-committing another session's work.
**Prediction**: If H1 is true, the mtime fallback path in masonry-stop-guard is reachable in normal usage (any session where session-start timed out or the project was initially detected as BL but then changed). The fallback labels files "today's" rather than "this session's".
**Agent**: diagnose-analyst
**Success criterion**: Code trace confirms under what conditions the snapshot is absent; confirms whether the mtime fallback correctly limits scope to THIS session or may include other-session files.

---

### D1.5: Does masonry-context-monitor.js check stop_hook_active, and what is the blocking threshold behavior when context is high but the repo is clean?

**Status**: PENDING
**Mode**: diagnose
**Priority**: MEDIUM
**H0**: masonry-context-monitor.js checks stop_hook_active and exits 0 when set. It only blocks (exit 2) when context > 750K tokens AND uncommitted changes exist. A clean repo never produces exit 2 regardless of context size.
**H1**: masonry-context-monitor.js may not check stop_hook_active (not confirmed in first 80 lines of source). If it doesn't, it could block on retry after stop_hook_active is set, conflicting with the retry semantics of hooks 7 and 8.
**Prediction**: If H1 is true, the full source of masonry-context-monitor.js will not contain a `stop_hook_active` check, making it a latent re-trigger risk at context > 750K.
**Agent**: diagnose-analyst
**Success criterion**: Full source review confirms presence/absence of stop_hook_active guard; confirms the blocking condition logic is correct (AND — both conditions required, not OR).

---

### A1.1: Do all Stop hooks that can exit with code 2 implement the stop_hook_active guard, and is coverage complete across the full Stop chain?

**Status**: PENDING
**Mode**: audit
**Priority**: HIGH
**H0**: Every hook in the Stop chain that can produce exit code 2 (masonry-stop-guard, masonry-build-guard, masonry-ui-compose-guard, and masonry-context-monitor) checks `stop_hook_active` and exits 0 immediately when the flag is true.
**H1**: At least one hook that can produce exit code 2 lacks the stop_hook_active check, creating a latent infinite-loop trap that manifests when context is high or both build and compose modes are active simultaneously.
**Prediction**: If H1 is true, grep for `stop_hook_active` across all 13 Stop hook files will show at least one blocking hook missing the check.
**Agent**: compliance-auditor
**Success criterion**: Exhaustive grep of all 13 Stop hooks confirms stop_hook_active coverage for every exit-2 path; list of any hooks missing the guard.

---

### A1.2: Is the BL research project silence detection (program.md + questions.md sentinel) consistent across all hooks that implement it?

**Status**: PENDING
**Mode**: audit
**Priority**: HIGH
**H0**: All hooks that implement BL silence detection use the same sentinel (program.md AND questions.md both present) and check the same directory (the effective cwd of the hook process).
**H1**: At least one hook checks a different directory (e.g., `process.cwd()` vs `input.cwd` vs `process.env.CLAUDE_PROJECT_DIR`) or uses a different sentinel, causing it to fire inside a BL campaign when other hooks correctly silence themselves.
**Prediction**: If H1 is true, comparing the isResearchProject() implementation across masonry-session-start, masonry-prompt-router, masonry-stop-guard, masonry-build-guard, masonry-score-trigger, masonry-pagerank-trigger, and masonry-ema-collector will reveal at least one divergent cwd source.
**Agent**: compliance-auditor
**Success criterion**: Cross-hook audit table showing cwd source and sentinel logic for each hook; any divergences flagged as findings.

---

### A1.3: Does recall-session-summary.js have divergent domain mapping that causes Recall writes to land in wrong domains compared to what recall-retrieve.js reads?

**Status**: PENDING
**Mode**: audit
**Priority**: MEDIUM
**H0**: The PROJECT_DOMAINS table in recall-session-summary.js maps all projects to the same canonical domains as recall-retrieve.js, ensuring memories written at Stop are retrievable at UserPromptSubmit.
**H1**: recall-session-summary.js maps system-recall → "development" and familyhub → "ai-ml", while recall-retrieve.js maps the same projects to "recall" and "family-hub" respectively. Session summaries land in wrong Recall domains and are never retrieved by recall-retrieve.js because the domain filters don't match.
**Prediction**: If H1 is true, a session working on the system-recall project will write its summary to domain "development" but recall-retrieve.js will search domain "recall" — the memory will exist in Recall but will never surface in future sessions.
**Agent**: compliance-auditor
**Success criterion**: Side-by-side comparison of all PROJECT_DOMAINS entries across recall-retrieve.js, recall-session-summary.js, and masonry-session-summary.js; explicit list of mismatches with severity.

---

### A1.4: Does masonry-ui-compose-guard.js implement the BL research project silence guard that masonry-build-guard.js has?

**Status**: PENDING
**Mode**: audit
**Priority**: MEDIUM
**H0**: masonry-ui-compose-guard.js implements the same `isResearchProject()` early exit as masonry-build-guard.js, silencing itself inside BL campaigns.
**H1**: masonry-ui-compose-guard.js is missing the isResearchProject() guard (it was adapted from build-guard but the BL silence logic was not copied). A BL campaign running in a directory that also has a `.ui/compose` state file (e.g., from an interrupted UI build) will be blocked at Stop by masonry-ui-compose-guard.
**Prediction**: If H1 is true, masonry-ui-compose-guard.js source will not contain a check for `program.md` and `questions.md`, unlike masonry-build-guard.js which explicitly checks `isResearchProject(process.cwd())`.
**Agent**: compliance-auditor
**Success criterion**: Source comparison confirms presence/absence of BL silence guard in masonry-ui-compose-guard.js.

---

### R1.1: How does the masonry-register.js guard warning flush mechanism work in practice, and can a guard warning accumulate and never be delivered?

**Status**: PENDING
**Mode**: research
**Priority**: HIGH
**H0**: masonry-register.js correctly writes guard warnings to `masonry-guard-{sessionId}.ndjson` during PreToolUse hooks, then flushes and deletes the file on the next UserPromptSubmit call, ensuring warnings are always delivered within one turn.
**H1**: The guard warning file can accumulate warnings that are never flushed if: (a) the next UserPromptSubmit fires before the guard file is written (race condition), (b) the session ends before another UserPromptSubmit fires, or (c) the guard file path is inconsistent across hooks (different session ID format).
**Prediction**: If H1 is true, examining the temp file naming convention used by the hooks that write guard warnings vs. masonry-register.js that reads them will reveal either a timing window or a file path mismatch.
**Agent**: research-analyst
**Success criterion**: Confirms the guard warning round-trip works correctly end-to-end; OR identifies specific conditions under which warnings are lost.

---

### R1.2: Does the masonry-training-export.js use spawnSync (blocking) despite being registered as async:true, and what is the actual behavior under the 65-second timeout?

**Status**: PENDING
**Mode**: research
**Priority**: MEDIUM
**H0**: masonry-training-export.js uses async spawn (non-blocking) internally, making its 65-second timeout in settings.json irrelevant because the hook process exits quickly after spawning the background Python process.
**H1**: masonry-training-export.js uses spawnSync (blocking) internally despite being marked async:true in settings.json. The async:true flag only means Claude Code doesn't wait for it — but the hook process itself blocks for up to 65 seconds on the Python spawnSync call, consuming system resources until timeout.
**Prediction**: If H1 is true, reading the full source of masonry-training-export.js will show `spawnSync` rather than `spawn` for the Python export call, confirming it blocks the Node.js event loop until Python completes or 65s elapses.
**Agent**: research-analyst
**Success criterion**: Full source confirms spawn vs spawnSync; explains the interaction between async:true in settings.json and the hook's internal blocking/non-blocking behavior.

---

### R1.3: Under what realistic daily development conditions do masonry-score-trigger, masonry-pagerank-trigger, and masonry-ema-collector actually fire, given their rate limits?

**Status**: PENDING
**Mode**: research
**Priority**: MEDIUM
**H0**: The analytics triggers (score-trigger: 24h, pagerank: 60min, ema: 5min) fire reliably in normal development workflow — multiple daily Stop events ensure they execute at least once per day each.
**H1**: The rate limits are misaligned with actual workflow patterns. Score-trigger's 24h window means it can only fire once per day regardless of campaign activity. Pagerank's `masonry/` directory guard means it only fires from the BL repo root — never from project subdirectories. EMA's 5-minute debounce is fine but telemetry.jsonl may not accumulate entries between short sessions.
**Prediction**: If H1 is true, the pagerank-trigger guard (`masonry/` dir must exist in cwd) means it never fires when Tim is working in a project subdirectory like `hook-audit/` — it only fires from `C:/Users/trg16/Dev/Bricklayer2.0/` directly.
**Agent**: research-analyst
**Success criterion**: Confirms the actual firing conditions for all three analytics triggers; identifies any conditions under which they silently never fire.

---

### R1.4: Does masonry-session-summary.js (Masonry) produce a duplicate session summary alongside recall-session-summary.js (Recall), and how do their Recall payloads differ?

**Status**: PENDING
**Mode**: research
**Priority**: MEDIUM
**H0**: masonry-session-summary.js and recall-session-summary.js serve different purposes — masonry writes a structured activity summary (from masonry-observe.js activity log) while recall writes an LLM-generated transcript summary. They complement each other without duplication.
**H1**: Both hooks write a "session summary" to Recall for the same session, domain, and tags, resulting in two Recall entries per session that partially overlap. Recall search results at next session start may return both, consuming context budget with redundant information.
**Prediction**: If H1 is true, comparing the Recall store calls in both files will show overlapping `domain`, `tags`, and `memory_type` values — making it likely that recall-retrieve.js retrieves both on the following session's first prompt.
**Agent**: research-analyst
**Success criterion**: Side-by-side comparison of what each hook writes to Recall (domain, tags, memory_type, content structure); assessment of whether both would be retrieved by recall-retrieve.js.

---

### V1.1: Is the architecture of the temp file bus (shared state via $TMPDIR) sound for a multi-session, multi-machine environment?

**Status**: PENDING
**Mode**: validate
**Priority**: HIGH
**H0**: The $TMPDIR-based temp file bus is architecturally sound for Tim's workflow — session IDs are unique per session, files are cleaned up correctly, and the system handles concurrent sessions (casaclaude + proxyclaude) without cross-contamination.
**H1**: The temp file bus has architectural weaknesses in a multi-machine environment: (a) $TMPDIR is local to each machine, so hooks on casaclaude and proxyclaude have isolated temp files — a session ID from proxyclaude cannot be found in casaclaude's $TMPDIR; (b) session-start writes a snap file that may collide with pre-existing snap files from a previous session with the same ID (UUID collision or reuse); (c) the masonry-{sessionId}.json "firstCall" tracking can only prevent per-session Recall hydration on one machine.
**Prediction**: If H1 is true, the stop-guard mtime fallback is triggered on any session where session-start ran on a different machine than stop fires on (cross-machine session migration) — since the snap file simply won't exist in that machine's $TMPDIR.
**Agent**: design-reviewer
**Success criterion**: Architecture assessment confirms whether the temp file bus is safe for Tim's multi-machine workflow; identifies any cross-contamination scenarios.

---

### V1.2: Is the Stop hook execution order correct — specifically, does running recall-session-summary (position 2) before masonry-stop-guard (position 3) introduce a race or correctness issue?

**Status**: PENDING
**Mode**: validate
**Priority**: MEDIUM
**H0**: The Stop hook order (recall session-save → recall summary → masonry stop-guard → masonry session-summary → handoff → context-monitor → build-guard → ui-compose-guard → analytics triggers) is intentionally designed so non-blocking Recall writes complete before the potentially-blocking stop-guard runs. This is correct because the stop-guard may block, and Recall writes should not be lost.
**H1**: Running recall-session-summary.js (which internally detaches a long-running Ollama summary process) BEFORE masonry-stop-guard.js (which may auto-commit) creates a correctness issue: the detached summary process may still be running when the stop-guard auto-commits session files, potentially including partially-written Recall cache files in the commit.
**Prediction**: If H1 is true, recall-session-summary.js writes to `~/.cache/recall/` files (debug logs, session data) that are within the git working tree or in a location that masonry-stop-guard includes in its dirty file check — causing Recall's cache files to be auto-committed.
**Agent**: design-reviewer
**Success criterion**: Confirms whether Recall cache files are within the git scope of masonry-stop-guard; confirms whether the detached Ollama summary process can write to any git-tracked location before the stop-guard auto-commit runs.

---

### FR1.1: What failure modes emerge when the session ID is absent from ALL Stop hook inputs, and is there a safe degradation path?

**Status**: PENDING
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
