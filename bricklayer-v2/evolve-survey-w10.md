# Wave 10 Survey — Evolve Mode
**Date**: 2026-03-24
**Baseline scores** (post-Wave-9):

| Agent | Pre-W10 Score | Target | Gap |
|-------|--------------|--------|-----|
| karen | 1.00 | 0.85 | AT TARGET |
| quantitative-analyst | 0.90 | 0.85 | AT TARGET |
| regulatory-researcher | 1.00 | 0.85 | AT TARGET |
| competitive-analyst | ~0.92 | 0.85 | AT TARGET |
| research-analyst | 0.56 (this run) | 0.85 | -0.29 (structural ceiling) |
| synthesizer-bl2 | 0.20 (this run) | 0.85 | -0.65 (NEW DROP — investigate) |

---

## Signal Analysis

### 1. synthesizer-bl2: 0.20 (2/10) — Sharp Drop from Prior ~0.45

**Before E9.2 calibration fix**: ~0.45 avg
**After E9.2 calibration fix**: 0.20 (confirmed on two consecutive runs)

Per-record failure map:
| # | Record | Expected | Score | Failure mode hypothesis |
|---|--------|---------|-------|------------------------|
| 1 | Q6.1 | HEALTHY | 0.00 | Wrong verdict — agent predicts something else |
| 2 | Q6.4 | INCONCLUSIVE | 0.85 | PASSES |
| 3 | Q6.5 | WARNING | 0.40 | 2-stage partial (prose output) |
| 4 | Q6.3 | HEALTHY | 0.00 | Wrong verdict — cannot verify HEALTHY without tools |
| 5 | Q6.6 | HEALTHY | 0.00 | Wrong verdict — same pattern |
| 6 | E8.3-synth-1 | WARNING | 0.99 | PASSES |
| 7 | E8.3-synth-2 | HEALTHY | 0.00 | Wrong verdict — same HEALTHY problem |
| 8 | E8.3-synth-3 | FAILURE | 0.00 | Wrong verdict — severity judgment |
| 9 | E8.3-synth-4 | HEALTHY | 0.00 | Wrong verdict — HEALTHY problem |
| 10 | E8.3-synth-5 | PROMISING | 0.00 | Wrong verdict — PROMISING not in JSON instruction set? |

**Hypothesis**: Calibration inversion exposed 6 records that were PASS (0.60) before but now fail.
Q6.1, Q6.3, Q6.6 have "passed" autopilot session summaries (HEALTHY) but synthesizer-bl2
cannot verify session quality without reading campaign files.

### 2. research-analyst: 0.56 (10/18) — Best Run Yet

Top of structural ceiling (0.44-0.61). The 7d0e9e9 optimization (score: 76.37) may have
contributed marginally. Two more confirmation runs needed.

**Stable records** (scoring > 0.85): Records 4,6,7,8,9,11,12,13,16,17 — 10 of them
**Stochastic records** (0.00): Records 2,5,10,14,15,18 — all expected WARNING/FAILURE where
adjacent verdicts are defensible.

### 3. optimize_with_claude.py: Untested on synthesizer-bl2

The optimize_with_claude.py script runs against current training data. If applied to
synthesizer-bl2, it would:
- See 10 records (2 pass, 8 fail)
- Very low pass rate means optimizer has weak signal for what "good" looks like
- Risk: optimizer could make instructions WORSE (optimize for wrong pattern)
- Safer approach: fix training data first, then optimize

---

## Candidate Ranking

| Candidate | Impact | Ease | ROI | Action |
|-----------|--------|------|-----|--------|
| synthesizer-bl2 calibration exposure diagnosis | HIGH | EASY | HIGH | E10.1 — immediate |
| synthesizer-bl2 training data fix (HEALTHY records) | HIGH | MEDIUM | HIGH | E10.2 — this wave |
| optimize_with_claude.py for synthesizer-bl2 | MEDIUM | EASY | MEDIUM | E10.3 — after data fix |
| research-analyst 2nd confirmation run | LOW | EASY | LOW | Check in E10.1 |
| Live eval design (Path B) | HIGH | HARD | HIGH | Future wave — architectural |

---

## Wave 10 Questions

- E10.1: Which synthesizer-bl2 records fail after calibration fix? Same structural mismatch?
- E10.2: Fix synthesizer-bl2 HEALTHY records (cannot verify without tools). Add WARNING/FAILURE
  records with clear evidence. Does score stabilize at ≥0.50?
- E10.3: Apply optimize_with_claude.py to synthesizer-bl2 after data fix. Does prompt quality
  improve measurably in eval?
