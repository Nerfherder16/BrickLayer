# Campaign Plan — hook-audit — 2026-03-29

## System Summary

The Masonry hook stack is a 40+ hook system wired into every Claude Code event (SessionStart, UserPromptSubmit, Stop, PreToolUse, PostToolUse, and others). It acts as the connective tissue between Claude Code, BrickLayer research campaigns, and the Recall memory system. The Stop hook chain alone runs 13 hooks sequentially, three of which can block session termination with exit code 2. A malfunction in any blocking hook can trap Tim in an unresolvable stop loop, or silently lose session data (Recall writes, handoff payloads, training exports) if non-blocking hooks fail.

## Prior Recall Context

Recall is reachable (100.70.195.84:8200). No prior campaign findings for hook-audit domain — cold start.

## Domain Risk Ranking

This is an audit campaign, not a financial simulation. BL standard domains (D1-D6) are remapped for the hook audit context:

| Domain | BL Equivalent | Hook Audit Interpretation | Likelihood | Impact | Priority | Rationale |
|--------|---------------|--------------------------|-----------|--------|----------|-----------|
| D1 | Revenue/financial | Stop hook blocking correctness | 3 | 3 | 9 | Three hooks can trap Tim in an unresolvable stop loop. stop_hook_active guard is the only defense. |
| D2 | Regulatory/legal | Session state symmetry (start vs stop) | 3 | 2 | 6 | Session snapshot written by start is consumed by stop-guard; if the link breaks, auto-commit uses wrong baseline and may commit other sessions' files. |
| D3 | Competitive/market | Recall overlap/duplication | 2 | 2 | 4 | Five hooks interact with Recall; domain mapping diverges across three files; risk of double-writes and domain mismatch. |
| D4 | Operational/execution | Analytics trigger viability | 2 | 2 | 4 | Score-trigger, pagerank-trigger, ema-collector, training-export all fire at stop; rate limits may prevent them from ever running in normal workflows. |
| D5 | Technical/architecture | Cross-hook data dependencies | 3 | 3 | 9 | Temp file bus (masonry-snap, masonry-activity, guard files) is the shared state layer — any temp file race, naming collision, or stale residue breaks multiple hooks. |
| D6 | Tail risk | BL silence detection reliability | 2 | 3 | 6 | Seven hooks independently implement BL project detection (program.md + questions.md sentinel). If detection fails, hooks interfere with running campaigns. |

## Targeting Brief for Question-Designer

### High-priority areas (generate 3-5 questions each)

1. **Stop hook blocking mechanism correctness (D1, Priority 9)**
   - Focus: stop_hook_active guard completeness, exit-code 2 logic correctness, re-trigger loop scenarios, ordering dependencies between masonry-stop-guard / masonry-build-guard / masonry-ui-compose-guard.
   - Why: A missing or incorrect stop_hook_active check in any blocking hook can make the session permanently unstoppable without manual kill. This is the highest-severity failure mode.

2. **Temp file data bus reliability (D5, Priority 9)**
   - Focus: session snapshot write/read round-trip, temp file naming consistency across hooks, stale temp file residue across sessions, session ID propagation, the masonry-handoff.js argv invocation anomaly.
   - Why: The entire stop-guard precision depends on the snapshot. Activity log consumed by masonry-session-summary depends on masonry-observe writing correctly. Guard warnings depend on masonry-{sessionId}.json being written before the second UserPromptSubmit fires.

3. **Session state symmetry — start vs stop (D2, Priority 6)**
   - Focus: What session-start initializes vs what stop hooks expect. Specifically: if session-start fails or exits early (BL detection, stdin timeout), does stop-guard still function? Does masonry-register still hydrate correctly?
   - Why: The snapshot is only written after stdin parsing and session ID extraction — both can fail silently.

4. **BL research project silence reliability (D6, Priority 6)**
   - Focus: Consistency of the `program.md + questions.md` sentinel across all 7+ hooks that implement it. Is the cwd they check the same? Is it process.cwd() or input.cwd or CLAUDE_PROJECT_DIR?
   - Why: Hooks use different cwd sources — some use `process.cwd()`, some use `input.cwd`, some use `CLAUDE_PROJECT_DIR`. A hook that checks the wrong directory may fire inside a BL campaign.

### Medium-priority areas (generate 1-2 questions each)

5. **Recall hook overlap/duplication (D3, Priority 4)**
   - Focus: Domain mapping divergence between recall-session-summary.js and masonry-session-summary.js. Risk of double session summaries. What does Recall actually receive at session end?

6. **Analytics trigger viability (D4, Priority 4)**
   - Focus: Under what real conditions do score-trigger, pagerank-trigger, ema-collector, and training-export actually fire? Are their rate limits compatible with normal development workflow cadence?

### Skip or defer

- masonry-prompt-inject.js: Not in audit scope, behavior unknown from available sources.
- PreToolUse / PostToolUse hooks (non-Stop): Not the primary audit target — complex but lower risk of catastrophic failure.
- TeammateIdle / TaskCompleted hooks: Thin wrappers, low risk.

## Known Landmines (from prior campaigns)

None — cold start. No prior hook-audit Recall findings.

**Pre-identified issues from code reading (not settled — must be audited):**
- `recall-session-summary.js` domain mapping diverges from `recall-retrieve.js` — specifically system-recall ("development" vs "recall") and familyhub ("ai-ml" vs "family-hub")
- `masonry-handoff.js` receives sessionId as `process.argv[2]` rather than from stdin — this is structurally different from every other hook
- `masonry-training-export.js` uses `spawnSync` (blocking) despite being registered as `async: true` in settings.json
- `masonry-ui-compose-guard.js` is missing the BL research project silence guard that masonry-build-guard.js has

## Recommended Wave Structure

- Wave 1 (15-18 questions): Focus on D1 (Stop blocking), D5 (temp file bus), D2 (state symmetry), D6 (BL silence) — highest priority domains. Include 3 diagnostic deep-dives and targeted audits per focus area.
- Wave 2 (8-10 questions): D3 (Recall overlap follow-ups), D4 (analytics triggers), tail risk scenarios (network failure, Python missing, concurrent sessions)
- Estimated total questions: 23-28 across two waves

## BL 2.0 Mode Allocation

| Mode | Suggested question count | Rationale |
|------|--------------------------|-----------|
| diagnose | 5 | Deep behavioral analysis of blocking hooks, temp file flow, state symmetry |
| audit | 4 | Systematic correctness checks: BL silence consistency, stop_hook_active coverage, domain mapping |
| research | 4 | Recall overlap behavior, analytics trigger cadence, handoff payload round-trip |
| validate | 2 | Architecture validation: async vs sync invocation patterns, timeout adequacy |
| frontier | 1 | Novel failure modes: concurrent sessions, multi-machine cwd overlap |
| simulate | 0 | No simulate.py — skip |
| benchmark | 0 | No performance benchmarking needed in Wave 1 |

Total Wave 1 target: 15-18 questions

## Constraints to Keep in Mind

- Timeout budgets: 3 blocking hooks at 20s + 10s + 10s = 40s maximum blocking wall time per Stop event
- Session ID is the primary correlation key — its absence degrades ALL cross-hook state sharing
- stop_hook_active is the only re-trigger prevention mechanism — its absence in any blocking hook is Critical severity
- BL silence sentinel (program.md + questions.md) must be checked against consistent cwd source
- auto-commit in stop-guard must NEVER include files from another session — session boundaries are sacred

---

## Instruction Block for Question-Designer-BL2

Read the "High-priority areas" section above before generating questions.md.
Generate questions in priority order — D1/D5 first (blocking and temp file bus), D2/D6 second (state symmetry and BL silence), D3/D4 third (Recall overlap and analytics).
For each high-priority area, generate at minimum one DIAGNOSE question and one AUDIT question.
Do not generate questions for PreToolUse/PostToolUse hooks unless they directly impact Stop behavior.
Use the "BL 2.0 Mode Allocation" table above to set Mode fields.
Target 15-18 questions for Wave 1. Prioritize depth over breadth — 3 focused questions per domain beats 8 shallow ones.
