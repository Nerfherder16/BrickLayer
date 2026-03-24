# Evolve Wave 7 — Survey

**Date**: 2026-03-24
**Previous wave**: Wave 6 (E6.1: synthesizer-bl2 0.83, E6.2: competitive-analyst 0.92, E6.3: research-analyst strategy)

---

## Current State

| Agent | Score | Target | Status |
|-------|-------|--------|--------|
| karen | 1.00 (20/20) | 0.85 | AT TARGET |
| quantitative-analyst | 0.90 (18/20) | 0.85 | AT TARGET |
| regulatory-researcher | 1.00 (10/10) | 0.85 | AT TARGET |
| competitive-analyst | ~0.92 avg | 0.85 | AT TARGET |
| synthesizer-bl2 | 0.83 (5/6) | 0.85 | APPROACHING — 1 bad record |
| research-analyst | 0.20 (1/5) | 0.85 | STRUCTURAL GAP — needs training data |

---

## Signal Sources

### synthesizer-bl2 (Record 4 data quality issue)

Inspecting the 1 persistent failure (Record 4 — same record fails both runs at 0.45):
```json
{
  "question_text": "Do the four Q5.4 roadmap changes each independently improve campaign_yield by >= 0.03?",
  "verdict": "HEALTHY",
  "evidence": ""  ← EMPTY
}
```

The expected evidence is **empty string** — a training data quality defect. The model cannot
produce high-quality evidence for a question requiring simulation code. The record should be
removed from training data:
- Without Record 4: 5 remaining records all pass → expect score 5/5 = 1.00

**Fix**: Remove Record 4 (index 3) from `scored_all.jsonl` and re-run eval.

### research-analyst (E6.3 execution)

5 records, all HEALTHY, all score=60, all from a single session. The E6.3 plan calls for
generating 25 diverse records. First step: pilot 10 records with 3-4 different verdict types to
verify the approach works before committing to the full 25.

The question templates from E6.3 targeting bricklayer-v2 infrastructure are the lowest-friction
starting point — questions about components we can directly inspect.

### Non-research agents (developer, git-nerd, mortar, test-writer)

All have N/A verdicts — research metric inapplicable. Low ROI: would need custom metrics,
small record counts (2-5 records each), and the campaign focus is research-domain agent quality.
Defer.

---

## Candidate Questions

### E7.1 — synthesizer-bl2 Record 4 removal (HIGH ROI, LOW EFFORT)
Remove the empty-evidence record and re-run eval. Expected: 0.83 → 1.00.
Simple data quality fix — no code change, no prompt change.

### E7.2 — research-analyst pilot data generation (HIGH ROI, MEDIUM EFFORT)
Generate 10 research-analyst records using WARNING and INCONCLUSIVE templates from E6.3.
Target: verify that the question framing reliably produces varied verdicts.
If pilot succeeds, extend to full 25-record plan in Wave 8.

---

## Priority Ranking

1. **E7.1** — synthesizer-bl2 Record 4 fix (10 min, high confidence improvement)
2. **E7.2** — research-analyst pilot data (30-60 min, moderate confidence)

Wave 7 plan: E7.1 first (quick win), then E7.2 pilot.
