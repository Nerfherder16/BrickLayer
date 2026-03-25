# Wave 38 Synthesis — Masonry Self-Research

**Date**: 2026-03-24
**Wave**: 38 (Mid-wave fix + validate cycle)
**Questions**: 5 total -- 3 FIX_APPLIED, 1 FAIL, 1 WARNING

---

## Executive Summary

Wave 38 was a targeted fix-and-validate cycle addressing the three interacting cascades identified in the Wave 37 predict-mode synthesis (P6 + P3 + P2). Two of three cascades are now remediated: the karen rubric contamination (P3) has been cleared and the rubric injection mechanism fixed, and the mock_campaign corpus pollution (P2) has been cleaned (135 records removed, not the 15 originally estimated) with a source-exclusion guard added. A secondary P6 mitigation -- MIN_VERDICTS_FOR_AUTO_OPTIMIZE threshold -- is in place, protecting low-sample agents like benchmark-engineer from premature auto-trigger.

The primary P6 defect remains open: `_score_verdicts()` in `drift_detector.py` still treats FAILURE as 0.0, and the confidence-weighted mean fix (F12.1) has not been implemented. Research-analyst remains at 45.2% CRITICAL drift under the current metric. The operational prohibition on `auto_trigger=true` is still in effect. V-mid.1 confirmed that the confidence data infrastructure exists in `agent_db.json` (29-element float array for research-analyst, mean 0.9131) -- only the consumption side is missing. With F12.1 applied, research-analyst drift would flip from 45.2% CRITICAL to -7.4% ok.

Additionally, V-mid.2 confirmed that the P5 double-fire cascade trigger is closed (F3.1 verified end-to-end), with two residual risks identified but independent of the optimization loop.

---

## Critical Findings (must act)

1. **V-mid.1** [FAIL, Critical] -- F12.1 (confidence-based drift metric) is NOT implemented. `_score_verdicts()` has no confidence parameter. `run_drift_check()` does not read confidences from `agent_db.json`. Research-analyst at 45.2% CRITICAL drift. CASCADE_ACTIVE.
   Fix: Add `confidences: list[float] | None` parameter to `_score_verdicts()`, thread through `detect_drift()` and `run_drift_check()`. Apply to both `masonry/src/drift_detector.py` (canonical) and `masonry/src/dspy_pipeline/drift_detector.py`.

## Significant Findings (important but not blocking)

2. **V-mid.2** [WARNING, Medium] -- P5 primary trigger (double-fire output collision) is CLOSED by F3.1. Two residual risks remain: (a) build-guard exits 0 on cross-session mismatch with stderr-only message not visible in conversation, (b) stop-guard auto-commits all session-touched files unconditionally with no test-pass or IN_PROGRESS task gate. Both are independent of the optimization loop.
   Fix: Add `hookSpecificOutput` to build-guard cross-session path; add IN_PROGRESS task guard before stop-guard auto-commit.

## Fixed This Wave

3. **F-mid.1** [FIX_APPLIED] -- Karen rubric contamination (P3 cascade) remediated. Stripped contaminated research-analyst rubric from `~/.claude/agents/karen.md`. Fixed `_build_prompt()` in `optimize_with_claude.py` to use signature-conditional rubric selection (4 module-level constants: `_RUBRIC_RESEARCH`, `_RUBRIC_KAREN`, `_FOCUS_RESEARCH`, `_FOCUS_KAREN`). Threaded `signature` parameter through `run()`, `_main()`, and `run_optimize()`.

4. **F-mid.2** [FIX_APPLIED] -- Mock campaign corpus contamination (P2) cleaned. Removed 135 records with `source: "mock_campaign"` from `scored_all.jsonl` (actual scope 9x larger than the 15-record estimate from P2). Added `_EXCLUDED_SOURCES = {"mock_campaign", "test_campaign"}` set and source-filter guard to `_load_records()` in `optimize_with_claude.py`.

5. **F-mid.3** [FIX_APPLIED] -- MIN_VERDICTS_FOR_AUTO_OPTIMIZE=10 guard added to `_tool_masonry_drift_check()` auto_trigger loop in `mcp_server/server.py`. Benchmark-engineer (2 verdicts) now excluded from auto-trigger. Partial P6 mitigation -- prevents low-sample agents from triggering optimization, but does not fix the scoring inversion itself.

## Healthy / Verified

- **F3.1 (hooks.json empty)**: Confirmed end-to-end. `hooks/hooks.json` contains `{"hooks": {}}`. SessionStart registered once in settings.json. Single-fire fast path produces valid JSON. Double-fire cascade path is permanently closed.
- **Routing pipeline** (waves 3-11): All four layers operational.
- **Training data pipeline** (waves 4-9, 29-35): Now clean of mock_campaign records. 471+ legitimate records across agents.
- **Write-back injection** (V32.1): End-to-end confirmed. Rubric injection now signature-conditional.
- **API key CLI** (F32.2): MIPROv2 execution unblocked.

---

## Cross-Cascade Status Update

The Wave 37 synthesis identified a self-reinforcing feedback loop across P6 + P3 + P2:

```
P6 (drift inversion) --[feeds]--> auto_trigger --[launches]--> improve_agent.py
                                                                       |
P3 (wrong rubric) --[corrupts]--------------------------> optimize_with_claude.py
                                                                       |
P2 (mock corpus) --[poisons]---> held-out eval + training tiers -------+
```

**Wave 38 status:**
- P2 (corpus): RESOLVED. 135 mock_campaign records removed. Source-exclusion guard prevents recurrence.
- P3 (rubric): RESOLVED. Karen.md cleared. Signature-conditional rubric selection shipped. Three project-level copies with legitimate karen MIPROv2 content left untouched.
- P6 (drift inversion): PARTIALLY MITIGATED. MIN_VERDICTS guard prevents premature auto-trigger for low-sample agents. Primary defect (FAILURE=0.0 in `_score_verdicts()`) unchanged. F12.1 not implemented.
- P5 (double-fire cascade): PRIMARY TRIGGER CLOSED. Two residual risks (build-guard visibility, stop-guard auto-commit) unaddressed but not blocking.

**The feedback loop is now broken at two of three points.** P2 and P3 cannot corrupt future optimization runs. The remaining risk is P6: if `auto_trigger=true` is called, drift scoring still inverts (FAILURE=0.0), causing the best-performing research agents to be flagged as CRITICAL and triggering optimization against them. The MIN_VERDICTS guard prevents this for benchmark-engineer but not for research-analyst (29 verdicts), diagnose-analyst (34), or design-reviewer (10).

**Fix ordering update**: P2 and P3 are complete. Only P6 remains. Implementing F12.1 is the single remaining prerequisite before MIPROv2 optimization runs can safely execute with auto_trigger enabled.

---

## Campaign-Wide Verdict Summary (Waves 1-38)

| Category | Count |
|----------|-------|
| Total questions answered | 214+ |
| FIX_APPLIED | ~53 |
| HEALTHY/COMPLIANT/CALIBRATED | ~40 |
| CONFIRMED (predict mode) | 4 |
| WARNING | ~21 |
| FAILURE/FAIL (open) | ~6 |
| Other (DIAGNOSIS_COMPLETE, DONE, etc.) | ~15 |

---

## Recommendation

**STOP**

The cascade remediation work is nearly complete. Two of three interacting cascades (P2 corpus, P3 rubric) are fully resolved. The remaining item -- F12.1 (confidence-weighted drift scoring) -- is a single-function fix with a clear specification, confirmed data infrastructure, and a known expected outcome (research-analyst flips from 45.2% CRITICAL to -7.4% ok). This is a maintenance task, not a research question. Implement it, then the MIPROv2 optimization loop is safe to engage.

**Preconditions before any optimization run (updated):**
1. ~~Clean mock_campaign records from scored_all.jsonl (P2)~~ DONE (F-mid.2)
2. ~~Clear contaminated DSPy section from karen.md on all machines (P3)~~ DONE (F-mid.1)
3. ~~Add signature-conditional rubric to optimize_with_claude.py (P3)~~ DONE (F-mid.1)
4. Replace `_score_verdicts()` with confidence-weighted mean in `drift_detector.py` (P6/F12.1) -- OPEN
5. Add circuit breaker to `semantic.py` (P1) -- OPEN (non-blocking for optimization)
6. Restore Ollama or cleanly disable Layer 2 (P1) -- OPEN (non-blocking for optimization)

**After item 4 is complete**, MIPROv2 optimization runs (research-analyst and karen) can safely execute. Items 5-6 are routing layer improvements, not optimization blockers.

## Next Wave Hypotheses

1. After F12.1 is implemented, does `improve_agent.py --dry-run` produce before_score >= 0.50 for research-analyst? (Direct validation of the cascade fix chain.)
2. After F12.1 ships, does `masonry_drift_check(auto_trigger=true)` correctly skip research-analyst (no longer CRITICAL) and only trigger optimization for genuinely degraded agents?
3. Do the V-mid.2 residual risks (build-guard cross-session, stop-guard auto-commit) manifest in practice during a real interrupted build? (Needs a live interruption test with an active `.autopilot/` directory.)
4. After MIPROv2 runs on the cleaned corpus with correct rubrics, does the optimized research-analyst outperform baseline on a held-out question set?
5. Is the P4 pre-agent tracker slot collision (16.7% rate) producing any observable downstream effect, or is the damage contained to analytics?
