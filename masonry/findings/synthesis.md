# Wave 38–39 Synthesis — Masonry Self-Research

**Date**: 2026-03-24 (updated 2026-03-25)
**Wave**: 38–39 (Mid-wave + Next-wave fix/validate cycle)
**Questions**: 13 total -- 5 FIX_APPLIED, 1 FAIL→RESOLVED, 1 WARNING→FIXED, 2 PASS, 1 HEALTHY, 3 other

---

## Executive Summary

Wave 38 was a targeted fix-and-validate cycle addressing the three interacting cascades identified in the Wave 37 predict-mode synthesis (P6 + P3 + P2). Two of three cascades are now remediated: the karen rubric contamination (P3) has been cleared and the rubric injection mechanism fixed, and the mock_campaign corpus pollution (P2) has been cleaned (135 records removed, not the 15 originally estimated) with a source-exclusion guard added. A secondary P6 mitigation -- MIN_VERDICTS_FOR_AUTO_OPTIMIZE threshold -- is in place, protecting low-sample agents like benchmark-engineer from premature auto-trigger.

~~The primary P6 defect remains open: `_score_verdicts()` in `drift_detector.py` still treats FAILURE as 0.0, and the confidence-weighted mean fix (F12.1) has not been implemented.~~ **UPDATE (2026-03-24)**: F12.1 has been implemented and committed (`8a0457d`). `_score_verdicts()` now accepts `confidences: list[float] | None` parameter with confidence-weighted mean path. `run_drift_check()` reads `confidences` from `agent_db.json`. Research-analyst drift is now −7.4% (ok/improvement). The operational prohibition on `auto_trigger=true` is LIFTED. See F-next.1.md.

Additionally, V-mid.2 confirmed that the P5 double-fire cascade trigger is closed (F3.1 verified end-to-end). Wave-next addressed both residual risks: F-next.2 adds hookSpecificOutput visibility to `masonry-build-guard.js` cross-session path; F-next.3 adds an IN_PROGRESS task gate to `masonry-stop-guard.js` auto-commit block. V-next.1 confirms F12.1 end-to-end with all five tracked agents at ok/improvement. R-next.1 confirms research-analyst before_score = 0.5333 (≥ 0.50 threshold). The optimization pipeline is ready.

---

## Critical Findings (must act)

1. ~~**V-mid.1** [FAIL, Critical] -- F12.1 (confidence-based drift metric) is NOT implemented.~~ **RESOLVED (F-next.1, 2026-03-24)**: F12.1 implemented. `_score_verdicts()` has confidence path. Research-analyst drift = −7.4% (ok). CASCADE_RESOLVED.

## Significant Findings (important but not blocking)

2. **V-mid.2** [WARNING→FIXED, Medium] -- P5 primary trigger (double-fire output collision) is CLOSED by F3.1. ~~Two residual risks remain.~~ **UPDATE (2026-03-25)**: Both residual risks are now fixed. (a) F-next.2: `masonry-build-guard.js` now emits hookSpecificOutput on cross-session mismatch — visible in conversation. (b) F-next.3: `masonry-stop-guard.js` now blocks auto-commit if any task is IN_PROGRESS. P5 residual risks CLOSED.

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
- P6 (drift inversion): **RESOLVED**. F12.1 implemented (commit `8a0457d`). Confidence-weighted mean path live. Research-analyst at −7.4% (ok). MIN_VERDICTS guard also in place. auto_trigger=true operational prohibition LIFTED.
- P5 (double-fire cascade): FULLY RESOLVED. Primary trigger closed (F3.1). Both residual risks fixed (F-next.2: build-guard hookSpecificOutput; F-next.3: stop-guard IN_PROGRESS gate).

**The feedback loop is now broken at all three points.** P2, P3, and P6 are all resolved. MIPROv2 optimization runs (research-analyst and karen) can now safely execute with auto_trigger enabled, subject to the MIN_VERDICTS guard.

---

## Wave Next Additions (2026-03-25)

6. **V-next.1** [PASS] -- F12.1 confirmed end-to-end. All 5 tracked agents at ok/improvement: research-analyst −7.42%, diagnose-analyst −3.89%, design-reviewer −11.65%, benchmark-engineer −11.76%, fix-implementer −2.35%. MIN_VERDICTS guard excludes benchmark-engineer (2 verdicts) from auto_trigger. Zero CRITICAL alerts.

7. **R-next.1** [HEALTHY] -- research-analyst before_score = 0.5333 from eval_latest.json (post-cleanup, 36 records). ≥ 0.50 threshold met. Zero mock_campaign records remaining. Source-exclusion guard confirmed. Optimization pipeline is viable.

8. **F-next.2** [FIX_APPLIED] -- `masonry-build-guard.js` cross-session and legacy branches now emit hookSpecificOutput alongside stderr. Warning visible in Claude's conversation context at Stop time. process.exit(0) preserved (non-blocking).

9. **F-next.3** [FIX_APPLIED] -- `masonry-stop-guard.js` IN_PROGRESS gate added before auto-commit block. `tryRead`/`tryJSON` helpers added. If `.autopilot/mode` is "build"/"fix" AND any task is IN_PROGRESS, auto-commit is blocked with exit 1. Partial implementations cannot enter git history under generic stop-guard message.

---

## Campaign-Wide Verdict Summary (Waves 1-39)

| Category | Count |
|----------|-------|
| Total questions answered | 222+ |
| FIX_APPLIED | ~57 |
| HEALTHY/COMPLIANT/CALIBRATED | ~41 |
| PASS (validate mode) | 1 |
| CONFIRMED (predict mode) | 4 |
| WARNING (open) | ~19 |
| FAILURE/FAIL (open) | ~5 |
| Other (DIAGNOSIS_COMPLETE, DONE, etc.) | ~15 |

---

## Recommendation

**OPTIMIZE**

All three interacting cascades (P2 corpus, P3 rubric, P6 drift scoring) are resolved. The MIPROv2 optimization loop is now safe to engage. Run `python masonry/scripts/improve_agent.py research-analyst --loops 3` and `python masonry/scripts/improve_agent.py karen --signature karen --loops 3` from Git Bash to start optimization.

**Preconditions before any optimization run (updated):**
1. ~~Clean mock_campaign records from scored_all.jsonl (P2)~~ DONE (F-mid.2)
2. ~~Clear contaminated DSPy section from karen.md on all machines (P3)~~ DONE (F-mid.1)
3. ~~Add signature-conditional rubric to optimize_with_claude.py (P3)~~ DONE (F-mid.1)
4. ~~Replace `_score_verdicts()` with confidence-weighted mean in `drift_detector.py` (P6/F12.1)~~ DONE (F-next.1)
5. Add circuit breaker to `semantic.py` (P1) -- OPEN (non-blocking for optimization)
6. Restore Ollama or cleanly disable Layer 2 (P1) -- OPEN (non-blocking for optimization)

**After item 4 is complete**, MIPROv2 optimization runs (research-analyst and karen) can safely execute. Items 5-6 are routing layer improvements, not optimization blockers.

## Next Wave Hypotheses

~~1. After F12.1 is implemented, does `improve_agent.py --dry-run` produce before_score >= 0.50 for research-analyst?~~ ANSWERED: R-next.1 (HEALTHY, 0.5333)
~~2. After F12.1 ships, does `masonry_drift_check(auto_trigger=true)` correctly skip research-analyst?~~ ANSWERED: V-next.1 (PASS, zero CRITICAL)
~~3. Do the V-mid.2 residual risks manifest in practice?~~ ANSWERED: Both fixed (F-next.2, F-next.3)
3. Do the V-mid.2 residual risks (build-guard cross-session, stop-guard auto-commit) manifest in practice during a real interrupted build? (Needs a live interruption test with an active `.autopilot/` directory.)
4. After MIPROv2 runs on the cleaned corpus with correct rubrics, does the optimized research-analyst outperform baseline on a held-out question set?
5. Is the P4 pre-agent tracker slot collision (16.7% rate) producing any observable downstream effect, or is the damage contained to analytics?
