# Wave 11 Survey — Evolve Mode
**Date**: 2026-03-24

## Stop Condition Assessment

Per evolve.md: "Stop condition: all high-ROI candidates explored, OR marginal gain < 3%
across all remaining candidates."

### Current State
| Agent | Score | Gap to 0.85 | Marginal gain possible in tool-free eval |
|-------|-------|-------------|----------------------------------------|
| karen | 1.00 | — | AT TARGET |
| quantitative-analyst | 0.90 | — | AT TARGET |
| regulatory-researcher | 1.00 | — | AT TARGET |
| competitive-analyst | ~0.92 | — | AT TARGET |
| research-analyst | 0.44-0.61 | -0.24 | ~0% (structural ceiling confirmed Wave 9) |
| synthesizer-bl2 | 0.40-0.50 | -0.35 | ~0% (structural ceiling confirmed Wave 10) |

**Tool-free evolve exhausted** for both below-target agents. Further curation yields ~0
marginal gain based on 10-wave evidence (Wave 9 range: 0.44-0.61 across all attempts).

### Remaining High-ROI Candidates (NOT yet explored)

1. **Live eval prototype (Path B)**: Eval with tools enabled would eliminate the structural
   mismatch. High impact. Medium implementation effort. Has not been attempted in any wave.
   ROI: HIGH — unlocks both research-analyst and synthesizer-bl2.

2. **Data quality: E8.3-synth-5 (PROMISING consistently failing)**: Expected PROMISING
   but agent always predicts WARNING or INCONCLUSIVE. Fix: change expected to INCONCLUSIVE
   (3 stable fails → 2 stable fails). Marginal gain: 0.10.

3. **Data quality: Q6.5 (Pydantic deprecation → prose)**: Expected WARNING, agent produces
   prose (2-stage → 0.40). Replace with a question where WARNING is self-evident as JSON.
   Marginal gain: 0.10.

4. **Unevaluated agents**: Check if any active agents have no eval records yet. Adding
   baseline evals for new agents extends evolve coverage.

### Candidate Ranking

| Candidate | Impact | Ease | ROI |
|-----------|--------|------|-----|
| Live eval prototype (Path B) | HIGH | MEDIUM | HIGH → E11.1 |
| Fix E8.3-synth-5 expected verdict | LOW | EASY | LOW → E11.2a |
| Fix Q6.5 prose producer | LOW | EASY | LOW → E11.2b |
| Unevaluated agent baseline scan | MEDIUM | EASY | MEDIUM → E11.2c |

---

## Wave 11 Question Plan

- E11.1: Design and implement a live eval harness (Path B) for research-analyst — eval with
  tools enabled. Does the agent score ≥0.85 when it can read files and search code?
- E11.2: Fix 3 remaining synthesizer-bl2 data quality issues (E8.3-synth-5 verdict fix,
  Q6.5 replacement, Q6.5 stochastic analysis). Does score reach 0.60?
