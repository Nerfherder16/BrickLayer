# Finding: M-mid.1 — fix_preflight_rejection_rate added to monitor-targets.md

**Question**: Add Fix mode scope-creep metric to `monitor-targets.md`: `fix_preflight_rejection_rate` with WARNING threshold ≥0.20 and FAILURE ≥0.40. Measurement: Fix findings with verdict=FIX_FAILED at pre-flight gate / total Fix questions per wave.
**Agent**: quantitative-analyst
**Verdict**: CALIBRATED
**Severity**: Medium
**Mode**: monitor
**Target**: `bricklayer-v2/monitor-targets.md`

## Summary

`monitor-targets.md` created (file did not exist) with `fix_preflight_rejection_rate` as the first entry. Thresholds set at WARNING ≥0.20 and FAILURE ≥0.40 as specified. Baseline not yet established — no Fix mode waves have run to date. The metric will become meaningful after the first wave that includes Fix mode questions.

## Evidence

### File created: `monitor-targets.md`

New file at `bricklayer-v2/monitor-targets.md` with:
- Table entry for `fix_preflight_rejection_rate` (WARNING ≥0.20, FAILURE ≥0.40)
- Full metric definition section explaining what constitutes a pre-flight rejection
- Baseline section awaiting first Monitor run

### Threshold rationale

| Threshold | Value | Rationale |
|-----------|-------|-----------|
| WARNING | ≥0.20 | More than 1 in 5 Fix questions failing pre-flight indicates Diagnose-to-Fix transition criteria are being applied too loosely |
| FAILURE | ≥0.40 | More than 2 in 5 failing is a campaign-level quality problem; at this rate, Fix mode work is mostly wasted |

The 0.20 WARNING threshold assumes Fix questions are created with at least basic specification quality. F-mid.1 and F-mid.2 (this wave) passed pre-flight, establishing an implicit 0/2 = 0.00 rate for Wave-mid.

### Measurement method

Defined as: count Fix findings with `Verdict: FIX_FAILED` where failure reason includes "pre-flight" or "insufficient specification" ÷ total Fix questions run per wave.

This requires Fix mode agents to explicitly annotate FIX_FAILED findings with a pre-flight failure reason — consistent with the Fix mode program in `modes/fix.md`.

## Verdict Threshold

CALIBRATED: metric defined, thresholds established, measurement method documented. Baseline values will be populated after the first Monitor run. No action required until a wave crosses the WARNING threshold.

## Open Follow-up Questions

None. M-mid.2 covers the complementary Predict mode subjectivity metric.
