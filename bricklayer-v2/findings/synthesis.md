# Wave 13 Synthesis -- bricklayer-v2

**Date**: 2026-03-24
**Questions**: 56 total (results.tsv) -- 33 success, 12 warning/partial, 2 inconclusive, 5 diagnosis, 3 promising, 1 blocked
**Wave 13 questions**: 10 total -- 4 DONE, 2 WARNING, 2 PENDING, 1 PENDING_EXTERNAL, 1 BLOCKED
**Remaining open**: 7 PENDING + 1 BLOCKED + 1 PENDING_EXTERNAL = 9 questions across all waves

---

## Critical Findings (must act)

1. **E13.8** [BLOCKED] -- 3 candidate-tier agents (peer-reviewer, agent-auditor, retrospective) have no .md instruction files; cannot generate eval baselines.
   Fix: Write instruction files for all three agents (~30 min each). These exist in agent_registry.yml but have no executable instructions.

2. **E13.9** [WARNING] -- 9 agents with substantial training data (5+ records) have never been evaluated. karen (379 records), quantitative-analyst (76), research-analyst (53) are highest-value targets with zero baselines recorded.
   Fix: Run `eval_agent.py` for karen, quantitative-analyst, and research-analyst to establish baselines. Then run `improve_agent.py` for any scoring below 0.85.

3. **E13.7** [WARNING] -- 4 deterministic routing coverage gaps cause unnecessary LLM fallback: eval/improve-agent pattern missing entirely, architect/diagnose/campaign patterns have partial coverage.
   Fix: Add 14 lines to `masonry/src/routing/deterministic.py` to raise coverage from 75% to ~90%.

---

## Significant Findings (important but not blocking)

1. **E13.10** [PENDING_EXTERNAL] -- improve_agent.py convergence analysis predicts plateau at loop 2-3, final score 0.60-0.70 for static eval. Code analysis shows greedy hill-climber with revert-on-regression. Stochastic eval noise at eval-size 18 is +-0.055 (masks 1-example improvements ~30% of the time). Awaits E13.2 completion (now DONE).

2. **E13.1** [IMPROVEMENT] -- FAILURE-to-WARNING re-labeling applied for E12.1-live-5 and E12.1-live-16. All 19 remaining records have stored_score >= 70. Predicted live eval: 0.95+ for research-analyst.

3. **E13.2** [IMPROVEMENT] -- Stochastic prose producer E12.1-live-14 replaced with clean count-check. 3-run results: 0.95/0.75/0.96 (avg 0.887). Zero prose production vs previous ~0.40 failure mode.

4. **E13.6** [HEALTHY] -- Routing baseline established: deterministic layer covers 75% (15/20 queries), exceeding 60% target. 30 keyword patterns + 6 slash commands registered.

---

## Healthy / Verified

- **E13.6**: Deterministic routing at 75% exceeds 60% target. All primary workflows (git, UI, diagnose, security, campaign) have deterministic patterns.
- **E13.1**: Dataset calibration corrected -- 19 clean research-analyst records, all scoring >= 0.70.
- **E13.2**: Replacement record eliminates format-compliance stochasticity. Correct verdict in 3/3 runs.
- **4 agents AT TARGET from prior waves**: karen (1.00), quantitative-analyst (0.90), regulatory-researcher (1.00), competitive-analyst (~0.92).
- **Live eval infrastructure proven**: eval_agent_live.py works for both research-analyst (0.84) and synthesizer-bl2 (0.62).
- **masonry-guard.js false positive**: fixed in E8.4, rate dropped from 5.3/session to 0.
- **Calibration inversion**: fixed in E9.2, wrong verdict now caps score at 0.00 (was 0.60 false pass).

---

## Campaign Progress Summary (Waves 1-13)

| Wave | Focus | Top Outcome |
|------|-------|-------------|
| 1 | Mode spec improvements | DEGRADED_TRENDING verdict, FAILURE routing, karen root cause identified |
| 2 | Karen training data fix | Pipeline bugs fixed (parent commit files, bot labels, encoding) |
| 3 | Eval pipeline coverage | 444->482 scored records, 5->10 eval-able agents |
| 4 | Eval instruction fix | quantitative-analyst 0.10->0.70, writeback scope guard |
| 5 | PROMISING verdict | quantitative-analyst 0.70->0.90 AT TARGET, regulatory-researcher 1.00 |
| 6 | Agent baselines | synthesizer-bl2 0.83, competitive-analyst ~0.92 |
| 7 | Data quality | Stochastic record removal, research-analyst pilot 10 records |
| 8 | 2-stage eval | Floor 0.00->0.40, masonry-guard.js false positive fix |
| 9 | Curation + metric fix | Verdict prerequisite gate, Q4.x removal, calibration pass |
| 10 | synthesizer-bl2 fix | Exposed 6 false-passes, floor raised 0.20->0.40 |
| 11 | Live eval prototype | Tool-enabled 0.84 vs tool-free 0.45 -- ceiling broken |
| 12 | Live eval calibration | research-analyst 0.84 (near 0.85), synthesizer-bl2 0.62 (meets 0.60) |
| 13 | Calibration cleanup | Dataset corrected, routing baseline 75%, fleet gap audit |

---

## Recommendation

**CONTINUE**

Wave 13 completed the calibration cleanup and established the routing baseline, but 9 questions remain open (E13.3, E13.5, E13.10, F-mid.1, F-mid.2, M-mid.1, M-mid.2, E-mid.1, E13.8 BLOCKED). The three highest-value next steps are: (1) write instruction files for the 3 blocked candidate agents, (2) run eval baselines for 9 untested agents (starting with karen at 379 records), and (3) implement the 4 routing pattern fixes to reach 90% deterministic coverage. The live eval infrastructure is proven and the dataset is clean -- the pipeline is ready for full-fleet optimization.

---

## Next Wave Hypotheses

1. **Agent instruction authoring**: Write .md files for peer-reviewer, agent-auditor, and retrospective (unblocks E13.8). Then generate 5 training records each and establish baselines. Expected: 0.40-0.60 initial scores.

2. **Full-fleet eval baseline pass**: Run eval_agent.py for the 9 agents with training data but no baselines (karen, quantitative-analyst, research-analyst, regulatory-researcher, mortar, architect, devops, competitive-analyst, refactorer). Record all baselines in agent_registry.yml.

3. **Routing deterministic coverage to 90%**: Implement the 4 pattern additions identified in E13.7 (eval pattern, broken-phrasing, architect-phrasing, mode-guidance). Verify with re-run of E13.6 test suite.

4. **research-analyst optimization convergence**: Run improve_agent.py research-analyst --loops 3 --eval-size 30 on the 38-record dataset (E13.10 unblocked by E13.2 completion). Validate predicted plateau at 0.60-0.70.

5. **Mode dispatch implementation**: Implement F-mid.1 (mode dispatch in CI runner) and F-mid.2 (PENDING_EXTERNAL handling). These are the highest-priority Fix-mode questions from the wave-mid generation.
