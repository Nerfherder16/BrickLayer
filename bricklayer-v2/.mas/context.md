# Campaign Context -- bricklayer-v2

**Last Wave**: 13
**Recommendation**: CONTINUE
**Updated**: 2026-03-24

## Active Focus

Close fleet evaluation gaps: write 3 missing agent instruction files, run eval baselines for 9 untested agents, implement 4 routing pattern fixes for 90% deterministic coverage.

## Critical Open Items

- E13.8 [BLOCKED]: peer-reviewer/agent-auditor/retrospective have no .md instruction files
- E13.9 [WARNING]: 9 agents with training data have never been evaluated
- E13.7 [WARNING]: 4 deterministic routing gaps cause unnecessary LLM fallback

## Confirmed Working

- Deterministic routing at 75% (exceeds 60% target)
- 4 agents AT TARGET: karen (1.00), quantitative-analyst (0.90), regulatory-researcher (1.00), competitive-analyst (~0.92)
- Live eval infrastructure proven for research-analyst (0.84) and synthesizer-bl2 (0.62)
- Calibration inversion fix working (E9.2)

## Next Wave Hypotheses

- Write instruction files for peer-reviewer, agent-auditor, retrospective
- Run full-fleet eval baseline pass for 9 agents
- Implement 4 routing pattern additions for 90% deterministic coverage
- Run improve_agent.py convergence test (E13.10)
- Implement mode dispatch in CI runner (F-mid.1, F-mid.2)