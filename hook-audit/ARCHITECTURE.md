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
| Wave 2 fix verification (W2*.x) | 8 | COMPLETE |

All 35 questions resolved (27 Wave 1 + 8 Wave 2). No PENDING questions remain.

---

## Key Findings

- **D1.3** [FIXED] Wave 2: masonry-handoff.js rewritten to read session_id from stdin; de-dup guard now per-session (verified W2D1.1)
- **A1.3** [FIXED] Wave 2: shared hooks/domains.js created; 57 orphaned memories remigrated; no stale broad-bucket entries (verified W2A1.1)
- **WM1.1** [FIXED] Wave 2: state.js writeState() uses atomic temp-rename; no torn writes under concurrent use (verified W2WM1.1)

---

## Open Items

*(none -- all questions resolved, all fixes verified)*
