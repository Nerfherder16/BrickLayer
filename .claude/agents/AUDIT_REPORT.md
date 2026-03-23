# Agent Audit Report — 2026-03-21T15:30:00Z
**Questions evaluated**: ~500 (recall + adbp + recall-arch-frontier campaigns)
**Agents audited**: 30 (BL 2.0 global fleet)

## Fleet Scorecard

| Agent | Questions | Definitive Rate | Evidence Depth | Regressions | Overall |
|-------|-----------|----------------|----------------|-------------|---------|
| quantitative-analyst | 280 | 87% | 95% | 0 | HEALTHY |
| research-analyst | 130 | 98% | 98% | 0 | HEALTHY |
| competitive-analyst | 35 | 94% | 80% | 0 | HEALTHY |
| peer-reviewer | 24 | 100% | 90% | 0 | HEALTHY |
| hypothesis-generator-bl2 | 15 | 70% | 70% | 0 | WARNING |
| benchmark-engineer | 5 | 100% | 100% | 0 | HEALTHY |
| synthesizer-bl2 | 2 | 100% | 95% | 0 | HEALTHY |
| diagnose-analyst | 3 | 100% | 75% | 0 | HEALTHY |
| regulatory-researcher | 0 | N/A | N/A | 0 | HEALTHY |
| cascade-analyst | 0 | N/A | N/A | 0 | HEALTHY |
| code-reviewer | 0 | N/A | N/A | 0 | HEALTHY |
| compliance-auditor | 0 | N/A | N/A | 0 | HEALTHY |
| design-reviewer | 0 | N/A | N/A | 0 | HEALTHY |
| evolve-optimizer | 0 | N/A | N/A | 0 | HEALTHY |
| fix-implementer | 0 | N/A | N/A | 0 | HEALTHY |
| forge-check | 0 | N/A | N/A | 0 | HEALTHY |
| frontier-analyst | 0 | N/A | N/A | 0 | HEALTHY |
| git-nerd | 0 | N/A | N/A | 0 | HEALTHY |
| health-monitor | 0 | N/A | N/A | 0 | HEALTHY |
| hypothesis-generator | 0 | N/A | N/A | 0 | HEALTHY |
| kiln-engineer | 0 | N/A | N/A | 0 | HEALTHY |
| mcp-advisor | 0 | N/A | N/A | 0 | HEALTHY |
| mortar | 0 | N/A | N/A | 0 | HEALTHY |
| overseer | 0 | N/A | N/A | 0 | HEALTHY |
| planner | 0 | N/A | N/A | 0 | HEALTHY |
| question-designer-bl2 | 0 | N/A | N/A | 0 | HEALTHY |
| skill-forge | 0 | N/A | N/A | 0 | HEALTHY |
| synthesizer | 0 | N/A | N/A | 0 | HEALTHY |
| trowel | 0 | N/A | N/A | 0 | HEALTHY |
| agent-auditor | 0 | N/A | N/A | 0 | HEALTHY |

## Underperforming Agents

None.

## WARNING Agents

### hypothesis-generator-bl2 — WARNING
**Definitive rate**: 70% (threshold: 80% for HEALTHY)
**Evidence depth**: 70% (borderline)
**Root cause**: Mid-loop wave questions it generates tend to produce INCONCLUSIVE verdicts when the campaign data is thin — the questions are valid but the simulation/research infrastructure can't always answer them definitively. This is partially a structural issue (question quality) rather than agent failure.
**Recommended action**: Review wave-mid question quality on next campaign. Questions should be scoped to what the current data can answer definitively.

## Verdict Drift Detected

None detected across audited campaigns.

## Fleet Gaps (Agents with 0 findings)

Large portion of the fleet (22 agents) has no finding history because:
1. Many are Masonry/dev-workflow agents (kiln-engineer, git-nerd, code-reviewer) invoked conversationally, not in campaigns
2. Some are sentinel/meta agents (forge-check, agent-auditor, overseer) that produce reports, not findings
3. Regulatory, compliance, cascade-analyst, health-monitor were not needed in recall/adbp/frontier campaigns

These agents are not UNDERPERFORMING — they simply haven't been exercised yet. Score defaults to 0.85 (HEALTHY) pending real data.

## Corpus Statistics

| Project | Findings Sampled | Dominant Mode | Primary Agent |
|---------|-----------------|---------------|---------------|
| recall | ~100 | performance/hypothesis | benchmark-engineer / research-analyst |
| adbp | ~99 | quantitative/simulation | quantitative-analyst |
| recall-arch-frontier | ~275 | research/competitive | research-analyst / competitive-analyst |

## Recommendations

1. **hypothesis-generator-bl2**: Scope wave-mid questions to what current campaign data can answer — reduce INCONCLUSIVE rate.
2. **regulatory-researcher**: No campaign has exercised this agent yet. ADBP has regulatory risk questions in docs/ — consider a dedicated regulatory wave.
3. **Fleet unexercised agents**: Normal for a young fleet. Scores will self-correct as campaigns run.
4. **Next audit**: Run after the next full campaign completes to capture in-flight agent performance.

## Fleet Verdict: FLEET_HEALTHY

All audited agents at or above WARNING threshold. One agent (hypothesis-generator-bl2) flagged for question-scoping improvement — not a critical failure.
