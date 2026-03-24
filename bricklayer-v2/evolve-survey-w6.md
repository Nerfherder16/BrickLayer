# Evolve Wave 6 — Survey

**Date**: 2026-03-24
**Previous wave**: Wave 5 (E5.1: quant-analyst 0.90 AT TARGET, E5.2: regulatory-researcher 1.00)

---

## Current State

| Agent | Score | Target | Status |
|-------|-------|--------|--------|
| karen | 1.00 (20/20) | 0.85 | AT TARGET |
| quantitative-analyst | 0.90 (18/20) | 0.85 | AT TARGET |
| regulatory-researcher | 1.00 (10/10) | 0.85 | AT TARGET |
| competitive-analyst | not measured | 0.85 | PENDING |
| synthesizer-bl2 | not measured | 0.85 | PENDING |
| research-analyst | 0.20 (1/5) | 0.85 | BELOW — structural issue |
| developer, git-nerd, mortar, test-writer | — | — | Non-research domain |

---

## Signal Sources

### competitive-analyst (6 records)
- All have standard research schema (verdict/evidence/confidence)
- Verdicts: INCONCLUSIVE (5), HEALTHY (1)
- All records have good evidence (2000+ chars)
- No PROMISING — all in allowed set
- Likely eval works correctly (no agentic override)

### synthesizer-bl2 (6 records)
- Standard research schema
- Verdicts: HEALTHY (4), INCONCLUSIVE (1), WARNING (1)
- Evidence: 577+ chars
- Likely eval works correctly

### research-analyst (5 records, all HEALTHY)
- 17K system prompt overrides eval instruction → runs full agentic research
- Score 0.20 reflects eval-design-mismatch, not agent capability
- Two paths to improvement:
  1. Generate 20+ diverse training records with different verdicts
  2. Design a different eval approach (e.g., score on evidence quality only, not verdict)

### Non-research agents (developer, git-nerd, mortar, test-writer)
- `output` has no `verdict` field (these agents produce code/actions, not findings)
- Research metric inapplicable — would need custom metrics
- Low ROI for this campaign

---

## Candidate Questions

### E6.1 — synthesizer-bl2 baseline (HIGH ROI)
Run eval on synthesizer-bl2 (6 records, standard schema). Expected: IMPROVEMENT
or HEALTHY if eval works. Low effort, broadens coverage.

### E6.2 — competitive-analyst baseline (HIGH ROI)
Run eval on competitive-analyst (6 records, mostly INCONCLUSIVE). Expected: similar
to regulatory-researcher. 5/6 records are INCONCLUSIVE — model must correctly
output INCONCLUSIVE.

### E6.3 — research-analyst training data generation strategy (MEDIUM ROI)
Design a data generation plan to produce 20+ diverse research-analyst records with
varied verdicts (WARNING, FAILURE, INCONCLUSIVE, PROMISING). Without this, research-
analyst eval score remains meaningless. This is a planning/strategy question, not
a code change.

---

## Priority Ranking

1. **E6.1** — synthesizer-bl2 baseline (5 min)
2. **E6.2** — competitive-analyst baseline (5 min)
3. **E6.3** — research-analyst strategy (planning)

Wave 6 plan: E6.1 + E6.2 in parallel, then E6.3 as research.
