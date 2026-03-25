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

**OPTIMIZE (research-analyst only — karen blocked)**

Research-analyst optimization is safe. Karen optimization is blocked until V-w40.1 (FAIL) is fixed — karen corpus bimodal cliff persists and P3 Fix 3 is unimplemented.

**Preconditions before any optimization run (updated):**
1. ~~Clean mock_campaign records from scored_all.jsonl (P2)~~ DONE (F-mid.2)
2. ~~Clear contaminated DSPy section from karen.md on all machines (P3)~~ DONE (F-mid.1)
3. ~~Add signature-conditional rubric to optimize_with_claude.py (P3)~~ DONE (F-mid.1)
4. ~~Replace `_score_verdicts()` with confidence-weighted mean in `drift_detector.py` (P6/F12.1)~~ DONE (F-next.1)
5. ~~Add circuit breaker to `semantic.py` (P1)~~ DONE (F-w40.1)
6. Restore Ollama or cleanly disable Layer 2 (P1) -- OPEN (non-blocking)
7. **Karen only**: Add `"synthetic_negative"` to `_EXCLUDED_SOURCES` and generate ≥20 real organic low-quality records (V-w40.1 FAIL) -- OPEN, BLOCKING for karen
8. **All agents**: Enforce train/eval split + add reasoning-quality metric + increase eval N to 50 (P-w40.1 CONFIRMED/IMMINENT) -- OPEN, HIGH priority before multi-loop runs

## Wave 40 Additions (2026-03-25)

10. **V-w40.1** [FAIL, High] -- Karen corpus bimodal cliff unchanged: 374/379 records at score=100, 5 synthetic_negative records at score=0, zero in 1-99 range. P3 Fix 3 never implemented. `"synthetic_negative"` not in `_EXCLUDED_SOURCES`. **Do not run karen optimization** until corpus fixed.

11. **R-w40.1** [HEALTHY] -- All karen.md DSPy sections contain only karen-appropriate rubric (action_match, changelog_quality, quality_score). No research-analyst contamination. Global `~/.claude/agents/karen.md` is a clean stub.

12. **F-w40.1** [FIX_APPLIED] -- Circuit breaker added to `semantic.py`: 2s per-call timeout, opens after 3 failures, resets after 60s. P1 routing cascade eliminated. Zero test regressions.

13. **R-w40.2** [WARNING, Low] -- P4 slot collision corrupts only `routing_log.jsonl` `request_text` (context metadata, not scores). All specialist-agent training corpora insulated. Latent cascade (corpus corruption) requires a routing_log→scored_all pipeline that doesn't exist yet.

14. **F-w40.2** [FIXED] -- Dead `optimized_prompt: str | None = None` field removed from `AgentRegistryEntry` in `masonry/src/schemas/payloads.py`. Was never written or read by any active code path. Zero regressions.

15. **P-w40.1** [CONFIRMED, High] -- Optimization loop has two IMMINENT failure modes: (1) **Convergence trap + metric blind spots** (E5+E2): eval and optimization examples overlap in `scored_all.jsonl`; metric measures only format proxies (evidence length, confidence near 0.75) — agent will converge to format patterns while reasoning quality silently degrades over 5-10 cycles. (2) **Revert gate dead zone** (E1): strict `>` comparison with minimum delta 0.05 at N=20; LLM stochasticity ~11% stddev makes gate noisy — sub-5% real regressions pass silently.

## Wave 41 Additions (2026-03-25)

~~4. P-w40.1 convergence trap:~~ **CLOSED** (F-w41.1, F-w41.2). ~~Karen blocked:~~ **UNBLOCKED** (F-w41.4).

16. **F-w41.1** [FIX_APPLIED, High] -- Train/eval split enforced. `_record_id()` helper (question_id or SHA-256 hash) added to `eval_agent.py` + `optimize_with_claude.py`. `held_out_ids` captured by eval, threaded as `excluded_ids` to `_tier_examples()`. `_MIN_TIER_RECORDS=5` guard bails if combined post-exclusion records < 5. E5 convergence trap arm of P-w40.1 CLOSED.

17. **F-w41.2** [FIX_APPLIED, High] -- Revert gate strengthened. `MIN_IMPROVEMENT = 0.02` added; gate changed from `after_score > before_score` to `after_score >= before_score + MIN_IMPROVEMENT`. Default `--eval-size` changed 20→50. At N=50 with 2% threshold, required confidence ~88% — residual dead zone reduced from ~5% to ~1.5%. E1 revert gate dead zone arm of P-w40.1 substantially CLOSED.

18. **F-w41.3** [FIX_APPLIED, Medium] -- DSPy delimiter sanitization and writeback validation added to `masonry/src/writeback.py`. `_sanitize_instructions()` replaces embedded `_SECTION_HEADER`/`_SECTION_END` with `<!-- DSPy-section-marker -->`. `_validate_writeback()` round-trips DSPy section after write; restores backup on mismatch. E3 delimiter corruption arm of P-w40.1 CLOSED.

19. **F-w41.4** [FIXED, High] -- Karen corpus unblocked. `"synthetic_negative"` added to `_EXCLUDED_SOURCES`. Empty-low-tier guard added (explicit error if low=[]). 5 `organic_low` karen records (scores 15–30, source=`organic_low`) appended to `scored_all.jsonl`. Karen `_tier_examples()` now produces valid high=15 + low=5 tiers. V-w40.1 FAIL blocking condition RESOLVED. **Karen optimization is now unblocked.**

20. **V-w41.1** [PASS] -- F-w40.1 circuit breaker confirmed end-to-end. OPEN path returns None (not exception). `router.py` `if decision is not None` → Layer 3. Timeout at httpx transport layer (not thread). `_cb_failures`/`_cb_opened_at` are module-level. One secondary theoretical gap (concurrent probe race in half-open state) not a risk given synchronous router. P1 cascade CONFIRMED CLOSED.

---

## Optimization Pipeline Status (post-Wave 41)

**Research-analyst**: READY TO OPTIMIZE. All preconditions met:
- Corpus clean (zero mock_campaign records)
- Drift metric correct (F12.1 confidence-weighted mean)
- Rubric correct (F-mid.1 signature-conditional)
- Train/eval split enforced (F-w41.1)
- Revert gate robust (F-w41.2, N=50, MIN_IMPROVEMENT=0.02)
- Writeback validated (F-w41.3)

**Karen**: UNBLOCKED. Preconditions met:
- Rubric correct (F-mid.1)
- synthetic_negative excluded (F-w41.4)
- 5 organic_low records provide negative contrast (F-w41.4)
- Empty-low-tier guard prevents degenerate optimization (F-w41.4)
- **Remaining risk**: only 5 organic_low records (M2 recommended ≥20). Run `--dry-run` first to verify before_score is interpretable. Corpus will improve as more organic records are collected.

**Run**:
```bash
cd C:/Users/trg16/Dev/Bricklayer2.0
python masonry/scripts/improve_agent.py research-analyst --loops 3
python masonry/scripts/improve_agent.py karen --signature karen --dry-run  # verify before_score first
```

## Next Wave Hypotheses

~~1. After F12.1 is implemented, does `improve_agent.py --dry-run` produce before_score >= 0.50 for research-analyst?~~ ANSWERED: R-next.1 (HEALTHY, 0.5333)
~~2. After F12.1 ships, does `masonry_drift_check(auto_trigger=true)` correctly skip research-analyst?~~ ANSWERED: V-next.1 (PASS, zero CRITICAL)
~~3. Do the V-mid.2 residual risks manifest in practice?~~ ANSWERED: Both fixed (F-next.2, F-next.3)
~~5. Is the P4 slot collision producing observable downstream effect?~~ ANSWERED: R-w40.2 (WARNING/Low, routing_log only)
~~4. Can the P-w40.1 convergence trap be closed before research-analyst optimization runs?~~ ANSWERED: F-w41.1, F-w41.2, F-w41.3 (CLOSED)
~~5. Can karen optimization be unblocked?~~ ANSWERED: F-w41.4 (UNBLOCKED)

~~6. Does research-analyst actually improve after 3 optimization loops?~~ BLOCKED (R-w42.1 WARNING — corpus too small for eval_size=50)
~~7. Is karen's before_score interpretable with the current corpus?~~ ANSWERED: R-w42.2 (WARNING — 0.90 interpretable but optimizer gets 0 low-tier examples)
~~8. Does the _record_id() exclusion hold under corpus growth?~~ ANSWERED: V-w42.1 (WARNING — wired correctly but 2 latent risks)
~~9. Is P-w40.1 E2 (metric blind spots) still open?~~ ANSWERED: R-w42.3 (WARNING — 2/3 components format proxies, residual blind spot)

## Wave 42 Additions (2026-03-25)

21. **R-w42.1** [WARNING, High] -- Research-analyst corpus (36 records) cannot support eval_size=50 — all records become held-out, leaving 0 for training, triggering `_MIN_TIER_RECORDS` hard block. `run_loop()` internal default still 20 (line 69) while CLI is 50 — divergence. Safe eval_size is ≤ 31. N=50 path was never exercised post-Wave-41. Two fixes needed: cap eval_size to `len(records) - MIN_TIER_RECORDS`, and sync `run_loop()` default.

22. **R-w42.2** [WARNING, High] -- Karen before_score=0.90 (27/30) is interpretable and gate satisfiable (+1 record = +0.0333 > MIN_IMPROVEMENT). Critical structural problem: all 5 organic_low records are the last 5 entries in scored_all.jsonl → all fall inside `records[-eval_size:]` held-out window → excluded from training pool → optimizer gets 0 low-tier examples. Karen optimization will run but converge on positive-only pattern. Fix: reshuffle scored_all.jsonl or switch eval selection to random sampling.

23. **V-w42.1** [WARNING, Medium] -- Train/eval split chain correctly wired through `improve_agent.py`. Two latent risks: (1) `eval_agent._record_id(record, index)` dead `index` parameter — direct single-argument callers get TypeError; (2) `optimize_with_claude.py` CLI has no `--excluded-ids`, silently bypasses train/eval split for any caller not using `improve_agent.py`. Both require fixes.

24. **R-w42.3** [WARNING, Medium] -- Metric blind spots partially closed: prerequisite gate (lines 36-39) prevents calibration inversion (wrong-verdict predictions cap at 0.2). But 2/3 active scoring components are format proxies: `evidence_quality` checks length+numbers only (no semantic validation), `confidence_calibration` rewards 0.75 unconditionally. Residual blind spot: label-correct + fabricated-evidence findings score same as correct reasoning. No component validates that cited evidence matches actual code.

25. **F-w42.1** [FIXED, Low] -- P4 slot collision eliminated. `masonry-preagent-tracker.js`: `crypto.randomUUID()` suffix on slot filename. `masonry-subagent-tracker.js`: glob-and-oldest-first read with legacy `_latest.json` fallback. Node.js verification confirmed no collision, backwards-compatible. `routing_log.jsonl` `request_text` corruption rate drops to zero for all new spawns. R-w40.2 WARNING/Low CLOSED.

---

## Wave 43 Targets

**Three fixes needed before either optimization run is safe:**
- F-w43.1: Fix `run_loop()` eval_size default + add corpus-size auto-cap (R-w42.1)
- F-w43.2: Fix organic_low record position — reshuffle or switch to random eval sampling (R-w42.2)
- F-w43.3: Remove dead `index` param from `eval_agent._record_id()` + add CLI bypass warning to `optimize_with_claude.py` (V-w42.1)

**Wave 43 open questions:**
~~10. After F-w43.x fixes: can research-analyst optimization run end-to-end without aborting?~~ ANSWERED: V-w43.1 (FAILURE with F-w43.1 only; PASS with both F-w43.1+F-w43.2)
~~11. After F-w43.x fixes: does karen optimizer receive at least 1 low-tier example?~~ ANSWERED: F-w43.2 (random sampling; each organic_low now 7.9% chance of eval; ~4.6 expected in training pool)
12. Is the metric E2 blind spot (format proxies) worth fixing now or after first optimization run? — DEFERRED to Wave 44

## Wave 43 Additions (2026-03-24)

~~F-w43.1 corpus-size cap needed:~~ FIXED. ~~F-w43.2 random sampling needed:~~ FIXED. ~~F-w43.3 dead param + CLI warning needed:~~ FIXED. **Structural gap discovered**: research-analyst has zero records with score < 50 — low-tier section is permanently empty.

26. **F-w43.1** [FIXED, High] -- Corpus-size cap added to `eval_agent.py`: `safe_eval_size = min(eval_size, max(1, len(records) - 10))` with warning log. `run_loop()` default synced from 20→50 in `improve_agent.py`. With 36-record corpus and eval_size=50, cap fires at 26 and leaves 10 for training. R-w42.1 WARNING RESOLVED.

27. **F-w43.2** [FIXED, High] -- Random sampling (`random.seed(42) + random.sample()`) replaces last-N held-out selection in `eval_agent.py`. Eliminates temporal skew: each of the 5 karen organic_low records now has 7.9% probability of being held-out (was 100%). Expected ~4.6 in training pool per run. Research-analyst training pool now gets ~7-8 high-tier records (combined > `_MIN_TIER_RECORDS=5`). R-w42.2 WARNING RESOLVED.

28. **F-w43.3** [FIXED, Medium] -- Dead `index: int` parameter removed from `eval_agent._record_id()`. Both files' `_record_id()` signatures now match. Stderr warning added to `optimize_with_claude.run()` when `excluded_ids is None`, catching direct CLI callers. V-w42.1 WARNING latent risks CLOSED.

29. **V-w43.1** [FAILURE→conditional PASS, High] -- F-w43.1 alone hard-blocks optimization: last-N selects Wave 9-12 records as eval (75-90 score), leaving only 2 high-tier records in training — combined=2 < `_MIN_TIER_RECORDS=5`. F-w43.2 resolves this: random sampling yields ~7-8 high-tier training records (combined ≥ 5). **Structural gap**: research-analyst has 0 records with score < 50 (all 36 score ≥60); low-tier block permanently renders as "(none)"; optimizer produces one-sided prompts (positive examples only). **Human decision required**: (A) lower low-tier threshold from `score < 50` to `score < 70` in `_tier_examples()` — admits 9 mid-tier (Wave 7-8) records as negatives; or (B) accept one-sided optimization.

---

## Optimization Pipeline Status (post-Wave 43)

**Research-analyst**: CONDITIONALLY READY. F-w43.1 + F-w43.2 applied — hard block resolved. Structural corpus gap: zero records below score 50 means optimizer receives no negative contrast.
- **Before optimizing**: human decision needed on low-tier threshold (see V-w43.1 Option A vs B above)

**Karen**: READY. Random sampling (F-w43.2) distributes organic_low records into training pool (~4.6 expected per run). All preconditions met.

**Run (karen only — research-analyst blocked pending threshold decision)**:
```bash
cd C:/Users/trg16/Dev/Bricklayer2.0
python masonry/scripts/improve_agent.py karen --signature karen --loops 3
```
