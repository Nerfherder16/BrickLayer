# Wave 9 Survey — Evolve Mode

**Date**: 2026-03-24
**Prior wave**: Wave 8 (E8.1–E8.4)

---

## State Assessment

### research-analyst (18 records)

Full classification (question_id: verdict [type]):

| ID | Verdict | Type | Notes |
|----|---------|------|-------|
| Q4.2–Q4.6 | HEALTHY×5 | reasoning | Old recall-dev records, clean JSON |
| E7.2-pilot-1 | WARNING | reasoning | eval_agent.py test coverage question |
| E7.2-pilot-2 | HEALTHY | **code-inspect** | Campaign completion rate — requires counting synthesis.md files |
| E7.2-pilot-3 | HEALTHY | **code-inspect** | optimize_with_claude.py write-back — requires reading file |
| E7.2-pilot-4 | FAILURE | **code-inspect** | masonry-guard.js false-positive rate — requires reading hook + logs |
| E7.2-pilot-5 | PROMISING | reasoning | 2-stage eval question |
| E8.2-rec-1 | HEALTHY | reasoning | BL2.0 wave structure soundness |
| E8.2-rec-2 | HEALTHY | reasoning | 4-layer routing soundness |
| E8.2-rec-3 | HEALTHY | reasoning | program.md lifecycle consistency |
| E8.2-rec-4 | HEALTHY | reasoning | scored_all.jsonl schema consistency |
| E8.2-rec-5 | WARNING | reasoning | build_metric() calibration bias |
| E8.2-rec-6 | WARNING | reasoning | eval infrastructure coverage gaps |
| E8.2-rec-7 | PROMISING | reasoning | Batched multi-run averaging |
| E8.2-rec-8 | INCONCLUSIVE | reasoning | Live eval (Path B) vs static data |

**Code-inspect records (targets for removal)**: pilot-2, pilot-3, pilot-4 (3 records)
- These always produce prose output → score 0.40 max with 2-stage eval → below 0.50 pass threshold
- Removal leaves 15 clean reasoning records

**Verdict distribution after removal**: HEALTHY×8, WARNING×3, FAILURE×0, PROMISING×3, INCONCLUSIVE×1 (15 total)

### synthesizer-bl2 (10 records)

Score variance root cause: same borderline record problem.
Borderline records (scoring 0.40–0.58 stochastically) cause ±30% run-to-run variance.
Target 0.90 not reached in Wave 8 (best: 0.60). Needs similar curation but secondary priority.

### Known Defect: Calibration Inversion in build_metric()

Identified in E8.2 finding (rec-5 training record):
- Wrong verdict + good evidence = 0.0 + 0.4 + 0.2 = **0.60 PASS** (false pass)
- Correct verdict + good evidence = 0.4 + 0.4 + 0.2 = **1.0 PASS**
- The eval can pass with wrong verdict if evidence quality is high

Fix: add verdict_match prerequisite gate — if verdict_match == 0, cap total at 0.2 regardless of evidence.

---

## Wave 9 Question Plan

### E9.1 — research-analyst curation
Remove 3 code-inspection records (pilot-2, pilot-3, pilot-4), replace with 3 pure reasoning records.
**Target**: stable score ≥ 0.65 with 15-18 clean records.

### E9.2 — Calibration inversion fix
Add verdict_match prerequisite gate to build_metric() in eval_agent.py.
**Target**: false-pass records (wrong verdict + good evidence) score ≤ 0.20, not 0.60.

### E9.3 — optimize_with_claude.py run (optional)
After E9.1+E9.2, if research-analyst has 15+ clean records and score ≥ 0.65:
Run `optimize_with_claude.py research-analyst` to embed optimized instructions.
