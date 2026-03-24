# Roadmap — bricklayer-v2

BrickLayer 2.0 self-audit campaign roadmap. Items marked ✅ are completed based on campaign findings.

---

## Phase 1: Engine Diagnosis (Waves 1-5)

| # | Item | Status |
|---|------|--------|
| 1.1 | ✅ Diagnose Q1.x architecture gaps (mode dispatch, status normalization) | COMPLETE |
| 1.2 | ✅ Fix karen training data pipeline (parent commit files, bot labels, encoding) | COMPLETE |
| 1.3 | ✅ Expand eval pipeline to 10+ eval-able agents | COMPLETE |
| 1.4 | ✅ Fix quantitative-analyst eval instruction gap (0.10→0.70→0.90) | COMPLETE |
| 1.5 | ✅ Validate regulatory-researcher at 1.00 | COMPLETE |

---

## Phase 2: Live Eval Infrastructure (Waves 6-12)

| # | Item | Status |
|---|------|--------|
| 2.1 | ✅ Establish synthesizer-bl2 baseline (0.83) | COMPLETE |
| 2.2 | ✅ Build 2-stage eval harness (floor 0.00→0.40) | COMPLETE |
| 2.3 | ✅ Fix masonry-guard.js false positives (5.3/session → 0) | COMPLETE |
| 2.4 | ✅ Fix calibration inversion in build_metric() (wrong verdict → 0.00) | COMPLETE |
| 2.5 | ✅ Prototype live eval harness (eval_agent_live.py) | COMPLETE |
| 2.6 | ✅ Calibrate live eval: research-analyst 0.84, synthesizer-bl2 0.62 | COMPLETE |
| 2.7 | ✅ Generalize eval_agent_live.py with --agent flag (E13.4) | COMPLETE |

---

## Phase 3: Fleet Optimization (Waves 13+)

| # | Item | Status |
|---|------|--------|
| 3.1 | ✅ research-analyst: first optimization gain via optimize_with_claude.py (0.84→0.91) | COMPLETE |
| 3.2 | ✅ Establish routing accuracy baseline (75% deterministic, >60% target) | COMPLETE |
| 3.3 | 📋 Write .md instruction files for peer-reviewer, agent-auditor, retrospective (E13.8) | OPEN |
| 3.4 | 📋 Run fleet-wide baseline eval for 9 unscored agents (E13.9) | OPEN |
| 3.5 | 📋 Add 4 deterministic routing patterns to raise coverage from 75% to ~90% (E13.7) | OPEN |
| 3.6 | 📋 Diagnose synthesizer-bl2 regression (0.62→0.41 after PROSE re-labeling) (E13.5) | OPEN |
| 3.7 | 📋 Run improve_agent.py research-analyst --loops 3 convergence test (E13.10) | PENDING_EXTERNAL |
| 3.8 | 📋 Run improve_agent.py karen --loops 2 optimization (E-mid.1) | PENDING_EXTERNAL |

---

## Phase 4: CI Runner Fixes (Wave 14)

| # | Item | Status |
|---|------|--------|
| 4.1 | ✅ Mode dispatch in CI runner (F-mid.1) — Q1.1 diagnosis resolved | COMPLETE |
| 4.2 | ✅ BL 2.0 status normalization in CI runner (F-mid.2) — Q1.5 diagnosis resolved | COMPLETE |
| 4.3 | ✅ Fix scope-creep metric defined: fix_preflight_rejection_rate (M-mid.1) | COMPLETE |
| 4.4 | ✅ Predict subjectivity metric defined: predict_subjectivity_rate (M-mid.2) | COMPLETE |
| 4.5 | 📋 Collect baselines for fix_preflight_rejection_rate and predict_subjectivity_rate | OPEN |

---

*Last updated: Wave 13 synthesis (2026-03-25). Human-only file — agent only marks ✅, never adds or removes items.*
