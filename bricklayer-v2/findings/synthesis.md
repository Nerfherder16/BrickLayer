# Wave 14 Synthesis -- bricklayer-v2

**Date**: 2026-03-24
**Questions**: 61 total (56 prior + 5 wave-mid) -- 35 success, 12 warning/partial, 2 inconclusive, 5 diagnosis, 3 promising, 1 blocked, 2 pending, 1 pending_external

## Critical Findings (must act)

1. **E13.8** [BLOCKED] -- 3 candidate-tier agents (peer-reviewer, agent-auditor, retrospective) have no .md instruction files; cannot generate eval baselines.
   Fix: Write instruction files for all three agents (~30 min each). These exist in agent_registry.yml but have no executable instructions.

2. **E13.9** [WARNING] -- 9 agents with substantial training data (5+ records) have never been evaluated. karen (379 records), quantitative-analyst (76), research-analyst (53) are highest-value targets with zero baselines recorded.
   Fix: Run `eval_agent.py` for karen, quantitative-analyst, and research-analyst to establish baselines. Then run `improve_agent.py` for any scoring below 0.85.

3. **E13.7** [WARNING] -- 4 deterministic routing coverage gaps cause unnecessary LLM fallback: eval/improve-agent pattern missing entirely, architect/diagnose/campaign patterns have partial coverage.
   Fix: Add 14 lines to `masonry/src/routing/deterministic.py` to raise coverage from 75% to ~90%.

---

## Significant Findings (important but not blocking)

1. **F-mid.1** [FIXED] -- Mode dispatch implemented in `bl/ci/run_campaign.py`. `_load_mode_context()` added, `_dispatch()` injects `mode_context`, `_parse_questions_table()` updated for 4-column BL 2.0 format. CI-runner-dispatched agents now receive mode program text in prompt; projects without `modes/` unchanged.

2. **F-mid.2** [FIXED] -- BL 2.0 status normalization fixed. Three bugs resolved: PENDING_EXTERNAL/DIAGNOSIS_COMPLETE/BLOCKED no longer silently converted to PENDING; `_TABLE_ROW_4COL_RE` added for 4-column table format; `_TERMINAL_STATUSES` frozenset defined with all 15 BL 2.0 status values.

3. **M-mid.1** [CALIBRATED] -- `fix_preflight_rejection_rate` metric defined in `monitor-targets.md` (WARNING >=0.20, FAILURE >=0.40). Baseline not yet established -- no Fix mode waves have run.

4. **M-mid.2** [CALIBRATED] -- `predict_subjectivity_rate` metric defined in `monitor-targets.md` (WARNING >=0.30, FAILURE >=0.60). Baseline not yet established -- no Predict mode waves have run.

5. **E-mid.1** [PENDING_EXTERNAL] -- `improve_agent.py karen --loops 2` requires manual execution from Git Bash (nested subprocess constraint). Current baseline confirmed at 1.00.

6. **E13.10** [PENDING_EXTERNAL] -- improve_agent.py convergence analysis predicts plateau at loop 2-3, final score 0.60-0.70 for static eval. Awaits manual run from Git Bash.

---

## Healthy / Verified

- **F-mid.1**: Mode dispatch in CI runner -- agents now receive operational mode program text. The Q1.1 diagnosis is fully resolved.
- **F-mid.2**: BL 2.0 status handling -- all 15 status values parsed correctly, PENDING_EXTERNAL questions no longer re-queued. The Q1.5 diagnosis is fully resolved.
- **M-mid.1, M-mid.2**: Monitor metrics for Fix scope-creep and Predict subjectivity now defined with thresholds. Addresses Q2.2 and Q2.4 warnings.
- **E13.6**: Deterministic routing at 75% exceeds 60% target.
- **4 agents AT TARGET from prior waves**: karen (1.00), quantitative-analyst (0.90), regulatory-researcher (1.00), competitive-analyst (~0.92).
- **Live eval infrastructure proven**: eval_agent_live.py works for both research-analyst (0.84) and synthesizer-bl2 (0.62).
- **masonry-guard.js false positive**: fixed in E8.4, rate dropped from 5.3/session to 0.
- **Calibration inversion**: fixed in E9.2, wrong verdict now caps score at 0.00 (was 0.60 false pass).

---

## Campaign Progress Summary (Waves 1-14)

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
| 14 | Wave-mid fixes | Mode dispatch + status normalization fixed, 2 monitor metrics calibrated |

---

## Recommendation

**CONTINUE**

Wave 14 closed the two highest-priority Fix-mode questions (mode dispatch and status normalization in the CI runner), resolving the Q1.1 and Q1.5 diagnoses that had been parked since Wave 1. Two monitor metrics are now defined for tracking Fix scope-creep and Predict subjectivity (Q2.2/Q2.4 warnings). However, 6 questions remain open: E13.3 and E13.5 (prompt optimization), E13.8 (BLOCKED -- agent instruction files), and E-mid.1/E13.10 (PENDING_EXTERNAL -- manual Git Bash runs). The pipeline is ready for full-fleet optimization once manual runs are executed.

---

## Next Wave Hypotheses

1. **Agent instruction authoring**: Write .md files for peer-reviewer, agent-auditor, and retrospective (unblocks E13.8). Then generate 5 training records each and establish baselines.

2. **Manual optimization runs**: Execute `improve_agent.py karen --loops 2` and `improve_agent.py research-analyst --loops 3` from Git Bash (resolves E-mid.1 and E13.10).

3. **Prompt optimization**: Run `improve_agent.py research-analyst --loops 2` (E13.3) and `improve_agent.py synthesizer-bl2 --loops 2` (E13.5) after manual baseline runs complete.

4. **Routing deterministic coverage to 90%**: Implement the 4 pattern additions identified in E13.7 (eval, broken-phrasing, architect, mode-guidance).

5. **Monitor metric baseline collection**: Run a Fix-mode and Predict-mode wave to establish baselines for `fix_preflight_rejection_rate` and `predict_subjectivity_rate`.
