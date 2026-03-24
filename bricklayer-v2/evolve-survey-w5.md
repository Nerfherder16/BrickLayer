# Evolve Wave 5 — Survey

**Date**: 2026-03-24
**Previous wave**: Wave 4 (E4.1: quant-analyst 0.10→0.70, E4.2: optimizer scope guard)

---

## Current State

| Agent | Score | Target | Gap |
|-------|-------|--------|-----|
| karen | 1.00 (20/20) | 0.85 | AT TARGET |
| quantitative-analyst | 0.70 (7/10) | 0.85 | -0.15 |
| research-analyst | 0.20 (1/5) | 0.85 | -0.65 |
| all others | no baseline | — | unknown |

---

## Signal Sources

### Training data analysis (quantitative-analyst, 61 records)

Verdict distribution:
- PROMISING: 26 records (42%) — NOT in `_RESEARCH_JSON_INSTRUCTION` allowed set
- WARNING: 16 records (26%) — in allowed set
- HEALTHY: 15 records (25%) — in allowed set
- FAILURE: 4 records (7%) — in allowed set
- INCONCLUSIVE: 1 record (1%) — in allowed set

All 61 records have `evidence_ok=True` (len >300, has numbers) EXCEPT one HEALTHY with len=89.

Key finding: `_RESEARCH_JSON_INSTRUCTION` constrains model to 4 verdicts
(`HEALTHY/WARNING/FAILURE/INCONCLUSIVE`). For 26 PROMISING records:
- Model CANNOT output PROMISING → verdict_match always 0 → max score 0.6
- All 26 score ~0.60 and PASS (≥0.50) — these aren't the 3 failures
- The 3 failures (0.46-0.48) are records where model evidence was weak AND verdict wrong

### E4.1 score breakdown (10-example sample)
- 0.97-0.99: 2 (correct verdict + excellent model-generated evidence)
- 0.92: 1 (correct verdict + good model evidence)
- 0.52-0.59: 4 (wrong verdict but good model evidence — likely PROMISING records)
- 0.46-0.48: 3 (weak model evidence → FAIL)

### Inference
The 4 scoring 0.52-0.59 are almost certainly PROMISING records where:
- verdict_match = 0 (model constrained, can't output PROMISING)
- evidence_quality = 0.4 (model generated good evidence)
- confidence ≈ 0.15 (0.2 × partial)

If PROMISING is added to the instruction, those 4 records might hit 0.8+.
The 3 failures likely have either PROMISING expected or wrong verdict AND weak model evidence.

---

## Candidate Questions

### E5.1 — Add PROMISING to eval instruction (HIGH ROI)

**Hypothesis**: Adding `PROMISING` to the allowed verdicts in `_RESEARCH_JSON_INSTRUCTION`
will allow the model to output the correct verdict for 26/61 quantitative-analyst records
(42% of the training set), pushing score from 0.70 toward 0.85.

**Change**: One-line addition to `_RESEARCH_JSON_INSTRUCTION` in `eval_agent.py`:
```python
'"verdict" (one of: "HEALTHY", "WARNING", "FAILURE", "INCONCLUSIVE", "PROMISING"), '
```

**Expected delta**: 7/10 → 9-10/10 (if 2-3 of the failures were PROMISING records where
the model now self-corrects with the right verdict). At minimum, the 4 records currently
scoring 0.52-0.59 could jump to 0.8+ if the model picks PROMISING correctly.

**Risk**: Adds PROMISING to ALL research-domain agents. For research-analyst (all HEALTHY
training records), unlikely to cause regression. For future agents, may be appropriate.

**Size**: 1-line code change + eval run.

---

### E5.2 — Filter HEALTHY len=89 outlier record (LOW ROI)

One record: `verdict=HEALTHY, evidence_ok=False, len=89`. This record will always fail
because the training evidence is too short to serve as a reference for quality.

**Change**: Filter this record from the eval pool for quantitative-analyst.
Could add a pre-filter in `_load_records()`: exclude records where `len(output.evidence) < 100`.

**Expected delta**: Removes 1/61 bad records. May slightly improve eval reliability.
Low impact on score since the eval draws random samples.

---

### E5.3 — Establish baseline for regulatory-researcher (MEDIUM ROI)

12 records, avg=60 in training data. No baseline established yet. Quick eval run
would reveal whether the eval infrastructure works for this agent or has the same
eval-design-mismatch issue as research-analyst.

**Expected delta**: Either HEALTHY (eval works, establishes baseline ≥0.50) or
WARNING (eval mismatch, identifies next fix). Medium ROI — broadens coverage.

---

## Priority Ranking

1. **E5.1** — Direct path to quant-analyst hitting 0.85 target. One code change + one eval run.
2. **E5.3** — Breadth-first: establish regulatory-researcher baseline while infrastructure is warm.
3. **E5.2** — Low ROI, defer.

Wave 5 plan: E5.1 first, then E5.3.

---

## Stop Condition

Wave 5 complete when:
- quantitative-analyst eval score ≥ 0.85 after PROMISING addition (or scored and gap understood)
- regulatory-researcher baseline established
