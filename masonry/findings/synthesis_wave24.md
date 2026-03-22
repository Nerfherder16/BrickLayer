# Masonry Self-Research -- Wave 24 Synthesis

**Wave**: 24
**Date**: 2026-03-22
**Status**: COMPLETE (7/7 questions DONE)
**Questions**: 7 total -- 3 FIX_APPLIED, 2 DIAGNOSIS_COMPLETE, 1 WARNING, 1 NOT_VALIDATED

## Wave Summary

Wave 24 addressed the four open issues from Wave 23: CLI flags for optimization iteration (F24.1), training data attribution gap (D24.1), metric ceiling validation (R24.1), and multi-agent optimization readiness (V24.1). Three code fixes were shipped (CLI flags, Agent field extraction recovering 603 training records, and expanduser() false-positive elimination). Two structural gaps were diagnosed but deferred (routing ground-truth labels, KarenSig definition). The Phase 17 metric ceiling was revised downward from 75-80% to 70-73% based on evidence that verdict accuracy (~35-40%) is the binding constraint, not evidence scoring.

## Findings Table

| ID | Verdict | Severity | Summary |
|----|---------|----------|---------|
| M24.1 | DOCS_UPDATED | Low | monitor-targets.md updated with miprov2_run_duration WARNING=120min, FAILURE=480min |
| F24.1 | FIX_APPLIED | Medium | --num-trials and --valset-size CLI flags wired end-to-end in run_optimization.py and optimizer.py |
| D24.1 | FIX_APPLIED | High | training_extractor.py Agent field extraction added; 137/162 masonry findings now attributed (was 134/135 from qid_map only); 603 cross-project records recoverable |
| D24.2 | DIAGNOSIS_COMPLETE | High | score_routing.py awards 70pts by checking if dispatched agent is recognized, not correct; no ground-truth target_agent exists in pipeline |
| D24.3 | FIX_APPLIED | Medium | expanduser() added to detect_stale_registry_entries(); 14 false-positive stale entries on Windows eliminated |
| R24.1 | WARNING | High | Phase 17 metric changes yield +1-4pts (69-73%), not +5-8pts (75-80%); verdict accuracy ~35-40% is the binding constraint |
| V24.1 | NOT_VALIDATED | High | karen (191 records) is NOT viable for MIPROv2 via ResearchAgentSig; all records use ops-domain schema; KarenSig required |

## Key Outcomes

### Fixed

1. **F24.1 -- CLI optimization flags**: `--num-trials` and `--valset-size` arguments added to `run_optimization.py`, forwarded through `run()` into `optimize_agent()` into `optimizer.compile()`. Enables short test runs (3 trials, 20 valset) in ~15-30 minutes without source edits. Existing callers (Kiln OPTIMIZE button) unaffected by defaults.

2. **D24.1 -- Training data attribution recovery**: Added `_AGENT_RE` regex to `extract_finding()` in `training_extractor.py`. The `**Agent**:` field in finding files is now the primary attribution source, with `_build_qid_to_agent_map()` as fallback. Impact: 137 of 162 masonry findings now have agent attribution (up from 134 via qid_map only). Cross-project: 603 of 914 previously dropped records are now recoverable. The remaining 311 records lack Agent fields entirely and require manual annotation.

3. **D24.3 -- Windows expanduser() fix**: Single-line change in `onboard_agent.py:106` from `Path(file_val).exists()` to `Path(file_val).expanduser().exists()`. Eliminates 14 false-positive stale entries for global agents (`~/.claude/agents/*.md` paths). Zero regression risk -- expanduser() is a no-op for non-tilde paths.

4. **M24.1 -- Monitor targets**: `monitor-targets.md` updated with `dspy_optimization_wall_time_minutes` (WARNING=120, FAILURE=480) and `dspy_bootstrap_failure_rate` (WARNING=0.1, FAILURE=0.5).

### Diagnosed (Pending Fix)

**D24.2 -- Routing scoring circular logic**: The 70-point `correct_agent_dispatched` score is awarded based on `agent in AGENT_CATEGORIES` -- a trivially true check for any dispatched agent. The routing log (`masonry-subagent-tracker.js`) captures only dispatch events, not request text or routing intent. Fix specification has two parts: (A) capture `request_text` in routing log entries for retrospective labelling, (B) replace circular scoring with ground-truth-aware logic (35pts partial credit when no label, 70pts only when ground-truth match confirmed). Fix deferred -- structural change requiring hook modification + scorer rewrite.

### Research Insights

**R24.1 -- Metric ceiling reality check**: The 66.07% composite metric score decomposes to approximately 35-40% true verdict accuracy, with evidence quality (>100 chars, ~0.90 pass rate) and confidence calibration providing a floor of ~0.52-0.56 even on wrong verdicts. This floor compresses the metric range such that moving from 66% to 75% requires fundamentally higher verdict accuracy, not metric weight redistribution. Key findings per planned change:
- Content signal replacement: Only genuine improvement, but penalizes 16.9% of valid qualitative findings
- Severity validation: 91.1% already pass; adds noise not signal; partly redundant with verdict
- Verdict-conditioned confidence: Actively penalizes FAILURE findings (39.2% of corpus, mean conf=0.958 vs target 0.70)
- Score < 0.4 filter: Removes 17% of training data without proportional signal gain; thins HEALTHY class below bootstrap threshold

**V24.1 -- Multi-agent optimization prerequisites**: Karen's 191 training records contain `commit_subject`/`doc_files_written`/`reverted` fields from the ops scorer -- zero overlap with ResearchAgentSig's `verdict`/`severity`/`evidence`/`confidence` fields. Attempting optimization would produce a degenerate prompt optimized for empty outputs. Five prerequisite steps identified: KarenSig definition, karen-specific metric, karen-specific data loader, optimize_all() dispatch by agent name, and generated stub. The 191 records are a genuine asset once the correct signature exists.

## DSPy Pipeline State After Wave 24

**Unblocked components:**
- MIPROv2 bootstrapping: functional (Wave 23 fix)
- Ollama backend: functional (Wave 22 fix)
- CLI iteration: functional (Wave 24 F24.1 -- --num-trials/--valset-size flags)
- Training data attribution: substantially improved (Wave 24 D24.1 -- 603 additional records recoverable)
- Agent registry stale detection: correct on Windows (Wave 24 D24.3)

**Known gaps:**
- Routing training data: 17 records with no ground truth (D24.2 -- diagnosed, fix deferred)
- Metric ceiling: 70-73% realistic vs 75-80% projected (R24.1 -- requires verdict accuracy improvement)
- Multi-agent optimization: blocked on per-agent signature definitions (V24.1 -- KarenSig first)
- optimize_all() hardcoded to ResearchAgentSig for all agents

**Current best metric score**: 68.3% (Trial 3, Wave 23, qwen3:14b) vs 59.5% baseline (+8.8pt lift)

## Open Issues / Wave 25 Seeds

1. **D24.2 routing ground-truth fix**: Implement the two-part fix (request_text capture in routing log + ground-truth-aware scoring). This is the prerequisite for routing optimization to produce meaningful training signal.

2. **Phase 17 metric changes -- selective implementation**: Implement only the content signal replacement (change #1), drop severity validation and verdict-conditioned confidence. Keep score < 0.4 filter but gate on corpus size >= 100 research findings.

3. **KarenSig definition**: Define the ops-domain signature, metric, and data loader for karen. With 191 records, karen becomes the second optimization target after quantitative-analyst once the schema work is complete.

4. **Verdict accuracy improvement path**: The D24.1 attribution fix restores question_text to training records. Re-run MIPROv2 with the enriched dataset to measure whether verdict accuracy improves from the ~35-40% baseline. This is higher leverage than any metric weight change.

5. **Next ResearchAgentSig candidate**: Identify which agent (after quantitative-analyst) has the most scored_all.jsonl records with populated verdict/evidence/confidence fields for the next optimization run.

6. **Overnight optimization re-run**: With F24.1 CLI flags and D24.1 attribution fix both applied, schedule a fresh MIPROv2 run with `--num-trials 10` to measure the compound effect on the metric ceiling.
