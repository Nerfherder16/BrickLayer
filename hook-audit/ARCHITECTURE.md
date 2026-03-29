# Architecture -- hook-audit

Campaign auditing the Masonry hook stack (13 hooks active in Claude Code settings.json).
Maintained by BrickLayer synthesizer at each wave end.

---

## Scope

This campaign audits the runtime behavior of all Masonry hooks registered in
`~/.claude/settings.json`. It does not modify hook source code -- it maps defects
and confirms correctness through code path analysis, cross-hook comparison, and
multi-session scenario tracing.

### Hook Stack Under Audit

| # | Hook | Event | Blocking |
|---|------|-------|----------|
| 1 | masonry-session-start.js | SessionStart | Yes |
| 2 | masonry-pre-protect.js | PreToolUse (Write/Edit) | Yes |
| 3 | masonry-approver.js | PreToolUse (Write/Edit/Bash) | Yes |
| 4 | masonry-content-guard.js | PreToolUse (Write/Edit) | Yes |
| 5 | masonry-context-safety.js | PreToolUse (ExitPlanMode) | Yes |
| 6 | masonry-style-checker.js | PostToolUse (Write/Edit) | No |
| 7 | masonry-observe.js | PostToolUse (Write/Edit) | No (async) |
| 8 | masonry-tool-failure.js | PostToolUseFailure | No |
| 9 | masonry-subagent-tracker.js | SubagentStart | No (async) |
| 10 | masonry-stop-guard.js | Stop | Yes (exit-2) |
| 11 | masonry-build-guard.js | Stop | Yes (exit-2) |
| 12 | masonry-ui-compose-guard.js | Stop | Yes (exit-2) |
| 13 | masonry-context-monitor.js | Stop | Yes (exit-2) |

Plus auxiliary Stop hooks: recall-session-save.js, recall-session-summary.js,
masonry-session-summary.js, masonry-handoff.js, analytics triggers (score, pagerank, ema).

---

## Agent Fleet

| Agent | Role | Questions | Score |
|-------|------|-----------|-------|
| diagnose-analyst | Root cause analysis, code path tracing | D1.1-D1.5, D1.3-FU1, D1.3-FU2, WD1.1, WD1.2, WM1.1 | -- |
| compliance-auditor | Audit mode, cross-hook consistency | A1.1-A1.4 | -- |
| research-analyst | Behavioral research, external patterns | R1.1-R1.4, A1.3-FU1, A1.3-FU2, WM1.2, WM1.3 | -- |
| design-reviewer | Architecture validation | V1.1, V1.2 | -- |
| frontier-analyst | Failure cascade exploration | FR1.1 | -- |

---

## Question Bank Summary

| Domain | Questions | Status |
|--------|-----------|--------|
| Stop hook guard chain (D1.x) | 8 | COMPLETE |
| Compliance audit (A1.x) | 6 | COMPLETE |
| Research/behavioral (R1.x) | 4 | COMPLETE |
| Architecture validation (V1.x) | 2 | COMPLETE |
| Frontier exploration (FR1.x) | 1 | COMPLETE |
| Wave-mid monitor (WM1.x) | 3 | COMPLETE |
| Wave-deep diagnose (WD1.x) | 2 | COMPLETE |

All 25 questions resolved. No PENDING questions remain.

---

## Key Findings

- **D1.3** [FAILURE] Wave 1: masonry-handoff.js reads session_id from argv; hook-runner has no template injection; de-dup guard fires once per machine lifetime
- **A1.3** [FAILURE] Wave 1: recall-session-summary.js stale domain mapping sends ALL session summaries to wrong Recall domains; no shared JS domains module
- **WM1.1** [FAILURE] Wave 1: masonry-observe.js non-atomic read-modify-write race loses counter increments under concurrent casaclaude+proxyclaude use

---

## Open Items

| ID | Verdict | Summary |
|----|---------|---------|
| D1.3 | FAILURE | masonry-handoff.js reads session_id from argv not stdin; de-dup guard fires once per machine |
| A1.3 | FAILURE | recall-session-summary.js stale domain mapping; session summaries in wrong Recall domains |
| WM1.1 | FAILURE | masonry-observe.js non-atomic R-M-W race on masonry-state.json under concurrent use |
| D1.4 | WARNING | Session snapshot absent on session-start timeout; mtime fallback cross-session imprecise |
| A1.4 | WARNING | masonry-ui-compose-guard.js missing isResearchProject() guard |
| R1.1 | WARNING | masonry-guard.js archived; guard warning flush is dead code |
| R1.2 | WARNING | masonry-training-export.js spawnSync blocks 60s despite async:true |
| R1.3 | WARNING | Analytics triggers require masonry/ dir in cwd; never fire from subdirs |
