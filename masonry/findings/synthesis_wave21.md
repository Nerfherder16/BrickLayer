# Wave 21 Synthesis -- Masonry Self-Research

**Wave**: 21
**Status**: COMPLETE (4/4 questions DONE)
**Date**: 2026-03-21
**Questions**: 4 total -- 1 WARNING (partial), 1 DIAGNOSIS_COMPLETE, 1 FIX_APPLIED (success), 1 HEALTHY (success)

## Questions Answered

| ID | Verdict | Summary |
|----|---------|---------|
| R21.1 | WARNING | DSPy MIPROv2 + Ollama qwen3:14b feasible with 2 config changes to optimizer.py; build_dataset() path produces fully shaped training records; raw scored_all.jsonl missing 3 fields (not the intended path); qwen3:14b structured output reliability under bootstrapping unverified |
| D21.1 | DIAGNOSIS_COMPLETE | masonry/masonry/training_data/ is a stale CWD artifact from score_all_agents.py line 215; same bug in run_optimization.py line 105; safe to rm -rf |
| F21.1 | FIX_APPLIED | Deleted stale masonry/masonry/ directory; applied dual-path CWD detection to score_all_agents.py and run_optimization.py matching run_vigil.py pattern |
| R21.2 | HEALTHY | Unknown thorn eliminated by excluding synthesis*.md from parse_findings_dir(); fleet now HEALTHY -- 7 roses, 10 buds, 0 thorns |

## Campaign Milestone: VIGIL HEALTHY (0 Thorns)

This is the first time the Masonry fleet has reached 0 thorns. The vigil verdict transitions from WARNING (carried since Wave 18) to HEALTHY. The sole thorn (`unknown`) was a phantom agent caused by 14 synthesis meta-files in `findings/` being parsed as agent findings. Excluding these files by filename pattern is the correct fix because synthesis files are campaign-level summaries, not per-question agent outputs.

Fleet state as of Wave 21:
- 7 roses (high-quality agents with consistent pass rates)
- 10 buds (agents with insufficient data or moderate pass rates)
- 0 thorns (no agents below quality thresholds)

## Critical Findings (must act)

None. All Wave 20 open issues have been resolved.

## Significant Findings (important but not blocking)

1. **R21.1** [WARNING] -- DSPy MIPROv2 Ollama integration requires exactly 2 config changes (configure_dspy function body + caller site), and the correct training path (build_dataset()) is fully compatible. The WARNING is driven by unverified qwen3:14b structured output reliability under MIPROv2 bootstrapping. A smoke-run is needed before committing to a full optimization trial.

2. **R21.1** [WARNING] -- The raw `scored_all.jsonl` file is a scoring artifact, not a training input. It lacks `project_context`, `constraints`, and `mitigation` fields required by `ResearchAgentSig`. The `build_dataset()` path in `training_extractor.py` reads findings from disk and populates all required fields. This distinction should be documented.

## Healthy / Verified

- **Vigil fleet health** (R21.2): HEALTHY verdict -- 7 roses, 10 buds, 0 thorns. First clean fleet assessment in the campaign.
- **Stale path artifact** (D21.1/F21.1): masonry/masonry/ directory removed; dual-path CWD detection applied to score_all_agents.py and run_optimization.py; stale directory no longer recreated on subsequent runs.
- **DSPy Ollama feasibility** (R21.1): Structurally confirmed -- 2 config changes, build_dataset() path works, Ollama endpoint live with qwen3:14b available. Ready for a smoke-run.

## Training Data Health (End of Wave 21)

| Metric | Wave 20 | Wave 21 | Change |
|--------|---------|---------|--------|
| Total training records (scored_all) | 435 | 435 | Stable |
| Routing 100pt records | 9 | 9 | Stable |
| Agents with 10+ records | 6 | 6 | Stable |
| Vigil verdict | WARNING | HEALTHY | Resolved |
| Vigil thorns | 1 (unknown) | 0 | Eliminated |

## Open Issues (Carried Forward)

1. **DSPy Ollama smoke-run** (from R21.1) -- A single-prediction smoke-run of `dspy.LM("ollama_chat/qwen3:14b")` against `ResearchAgentSig` is needed to verify structured output generation before committing to a full MIPROv2 trial. If qwen3:14b fails to produce parseable output, optimization cannot proceed.

2. **Confidence overcalibration** (carried from Wave 20) -- fix-implementer findings with confidence >= 0.96 score 10/40 on confidence_calibration, suppressing 55% of masonry findings below the 60-point training threshold. Design decision, not a bug, but limits training data volume.

## Recommendation

**STOP**

All four Wave 20 open issues are resolved:
- Stale masonry/masonry/training_data/ path: diagnosed, fixed, and verified (D21.1/F21.1)
- DSPy Ollama feasibility: structurally confirmed with a concrete 2-change spec (R21.1)
- Unknown vigil thorn: eliminated, fleet at HEALTHY for the first time (R21.2)
- Vigil CWD path: resolved as part of D21.1/F21.1 dual-path detection fix

The campaign has achieved all primary objectives:
- Scoring pipeline produces correct training data (Waves 16-18)
- Vigil fleet health is calibrated and actionable (Waves 19-21)
- Routing and findings scorers produce reliable, high-volume output (Wave 20)
- Fleet health is HEALTHY with 0 thorns (Wave 21)
- DSPy Ollama integration path is specified and ready for implementation (Wave 21)

The remaining work (DSPy smoke-run, confidence recalibration) is implementation, not research. It belongs in a `/build` task, not a campaign wave.

## Next Phase Hypotheses (if campaign resumes)

1. Does a single-prediction smoke-run of `dspy.LM("ollama_chat/qwen3:14b")` against `ResearchAgentSig` produce valid structured output?
2. What is the pre/post evaluation score delta when MIPROv2 optimizes quantitative-analyst using the 125-record corpus via Ollama?
3. Can the confidence_calibration rubric dimension be recalibrated to a sigmoid curve that doesn't penalize high-confidence correct findings?
4. Does source-tagging masonry vs ADBP training records improve or degrade DSPy optimization quality?
5. What is the minimum record count per agent for DSPy optimization to show measurable improvement?
