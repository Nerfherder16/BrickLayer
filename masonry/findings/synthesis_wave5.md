# Wave 5 Synthesis — Masonry Self-Research Campaign

**Wave**: 5
**Questions answered**: 5 (F5.1, F5.2, F5.3, R5.1, R5.2)
**Date**: 2026-03-21

---

## Verdicts Summary

| ID | Title | Verdict | Severity |
|----|-------|---------|----------|
| F5.1 | masonry-guard.js — atomic rename for strike counter | FIX_APPLIED | High |
| F5.2 | llm_router.py — registry membership validation | FIX_APPLIED | Medium |
| F5.3 | masonry-subagent-tracker.js — atomic write for agents.json | FIX_APPLIED | Medium |
| R5.1 | route_llm() post-F5.2 behavior validation | HEALTHY | Low |
| R5.2 | DSPy dry run — field mismatch for diagnose-analyst | FAILURE | Medium |

---

## Key Findings

### All Concurrent Write Races Eliminated

Waves 4–5 closed the full set of non-atomic shared-state writes identified in Wave 1–3:

| Component | Race condition | Fixed in |
|-----------|---------------|----------|
| masonry-guard.js | Strike counter torn write | F5.1 |
| masonry-subagent-tracker.js | agents.json read-modify-write | F5.3 |

Both now use the atomic rename pattern (`writeFileSync` to `.tmp.{pid}`, then `renameSync`). Concurrent hook invocations cannot produce split-brain state.

### Layer 3 Routing: Correct and Hardened

F5.2 added registry membership validation — the last open correctness gap in the four-layer routing pipeline. R5.1 confirmed all three edge cases (valid name → RoutingDecision, hallucinated name → None, empty registry → None) behave correctly. One minor inefficiency remains: `route_llm()` does not early-exit when `registry = []` (the LLM call is still made). This wastes ~20s on Windows but does not produce incorrect results.

### DSPy Phase 16 Blocked by Field Mismatch

R5.2 identified a structural mismatch in the DSPy optimization pipeline:
- `build_dataset()` always shapes training examples to `ResearchAgentSig` fields
- `optimize_all()` selects `DiagnoseAgentSig` for `diagnose-analyst` (13 examples — the largest training set)
- `DiagnoseAgentSig` expects `symptoms`/`affected_files`/`prior_attempts` — none present in the shaped examples

**Impact**: `diagnose-analyst` optimization silently falls back to the unoptimized module. Three other agents (`research-analyst`, `design-reviewer`, `fix-implementer`) would optimize correctly with the current code.

**Fastest fix (Option B)**: Remove the `DiagnoseAgentSig` branch from `optimize_all()` — always use `ResearchAgentSig`. This loses the specialized diagnose signature but unblocks training for all 4 agents (39 examples total, all correctly shaped).

---

## Status of Known Open Items

| Item | Status | Wave |
|------|--------|------|
| D1.1 Hook double-fire | DONE (HEALTHY — deduplication confirmed) | W1 |
| D1.2 Guard strike counter non-atomic | FIXED | W1 + F5.1 |
| D1.3 _load_registry CWD fallback silent empty | DONE (FAILURE — WARNING logged but path falls through silently) | W2 |
| D1.4 observe/guard shared state race | DONE (HEALTHY — files don't overlap) | W2 |
| D1.5 Schema extra="forbid" breaks unknown payloads | DONE (HEALTHY — extra ignored, not forbid) | W2 |
| D1.6 llm_router Windows shell=True injection | FIXED (F4.2) | W4 |
| D1.7 onboard_agent.py file locking | OPEN (P2) | — |
| D2.1 deterministic **Mode**: field case-sensitive | FIXED (F3.5) | W3 |
| D2.2 subagent-tracker agents.json non-atomic | FIXED (F5.3) | W5 |
| V1.3 semantic.py cache unbounded growth | OPEN (P2) | — |
| V1.4 _load_registry logging + CWD fallback | OPEN (P1) | — |
| R1.4 8 missing slash commands | OPEN (P2) | — |
| R1.5 Ollama circuit breaker | OPEN (P2) | — |
| R3.2 DSPy training extractor zero examples | FIXED (F4.1) | W4 |
| R5.2 DSPy diagnose-analyst field mismatch | OPEN (P2) | W5 |

---

## Wave 6 Priority Targets

**P1 (carry-forward)**:
1. **F6.1** — Fix `_load_registry` in `router.py`: add logging on empty-registry return and CWD fallback robustness (D1.3/V1.4 root cause)
2. **F6.2** — Fix `optimize_all()` field mismatch: remove `DiagnoseAgentSig` branch or align `build_dataset()` example shape for diagnose agents (R5.2 root cause)

**P2 (new investigations)**:
3. **D6.1** — Does `masonry-agent-onboard.js` have a file-lock race when multiple agents are onboarded simultaneously? (D1.7 follow-up)
4. **R6.1** — What is `configure_dspy()` call order in the MCP server `masonry_optimize_agent` handler? Is DSPy configured before `optimize_all()` is called?
5. **R6.2** — Empty `route_llm()` early-exit: should `route_llm()` return None immediately when `registry = []`? Assess whether this condition can arise in production.
6. **V6.1** — Validate `masonry-lint-check.js` behavior when ruff/prettier/eslint are not on PATH (Windows install paths differ from POSIX defaults)
