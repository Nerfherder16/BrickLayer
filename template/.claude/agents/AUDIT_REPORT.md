# Agent Audit Report — 2026-03-17T00:00:00Z
**Questions evaluated**: 20
**Agents audited**: 1 (diagnose-analyst)

## Fleet Scorecard

| Agent | Questions | Definitive Rate | Evidence Depth | Regressions | Overall |
|-------|-----------|----------------|----------------|-------------|---------|
| diagnose-analyst | 20 | 100% (WARNING=definitive in campaign context) | 100% | 0 | HEALTHY |

**Note**: diagnose-analyst uses WARNING as its primary verdict for this campaign (meta-campaign investigating agent issues — all findings are design gaps, hence WARNING). All 20 findings contain concrete evidence (code blocks, file paths, line references).

## Underperforming Agents

None.

## Verdict Drift Detected

No drift. diagnose-analyst has produced consistent WARNING verdicts across all 20 questions, which is appropriate given the campaign's focus on identifying structural gaps in the BL 2.0 agent fleet.

## Recommendations

1. Continue campaign — remaining questions cover D4 (scheduling), D5 (recall), D6 (tail risks).
2. Consider hypothesis-generator pass when question bank drops below 3 PENDING.
3. Sentinel re-fire at campaign close recommended (per Q4.1 finding — final-wave audit gap).
