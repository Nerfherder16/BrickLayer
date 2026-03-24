# Evolve Survey — Wave 4
**Date**: 2026-03-24
**Prior waves**: W1 (mode spec), W2 (karen training), W3 (eval coverage + audits)

---

## Wave 3 Outcomes

| Finding | Verdict | Action |
|---------|---------|--------|
| E3.1 training merge | IMPROVEMENT | Done — 10 agents covered |
| E3.2 quantitative-analyst | WARNING | Fix eval instruction (unblocked) |
| E3.3 research-analyst | WARNING | Fix eval instruction + build training data |
| E3.4 optimizer scope | WARNING | Add target_paths guard (unblocked) |

---

## Candidate Ranking

| # | Candidate | Impact | Ease | ROI | Wave 4? |
|---|-----------|--------|------|-----|---------|
| 1 | **Add `_RESEARCH_JSON_INSTRUCTION` to eval_agent.py** | High — unblocks quantitative-analyst eval | Easy (10-line fix) | HIGH | YES |
| 2 | **Add optimizer scope guard (target_paths)** | Medium — prevents future overwrites | Easy (2 files) | HIGH | YES |
| 3 | **Run quantitative-analyst eval with fixed instruction** | High — establishes real baseline | Easy (run eval) | HIGH | YES |
| 4 | Research-analyst training data growth | Medium — needs more campaigns | Hard (ongoing) | LOW | SKIP |

---

## Wave 4 Questions

| ID | Hypothesis |
|----|------------|
| E4.1 | Adding `_RESEARCH_JSON_INSTRUCTION` to `eval_agent.py` with explicit verdict/evidence/confidence/summary field list should raise quantitative-analyst eval score from 0.10 to >0.50 by eliminating wrong-schema predictions. |
| E4.2 | Adding `target_paths` optional parameter to `writeback_optimized_instructions()` and using it in `optimize_with_claude.py` should prevent cross-file contamination, addressing the E3.4 scope risk. |
