# Test Gap Report

Generated: 2026-03-28T02:08:55.655Z
Project: Bricklayer2.0

## Summary

- Source files scanned: 218
- Test files found: 72
- Files missing tests: 198
- Coverage: 9%

## Files Without Tests

### ./
- [ ] `onboard.py`
- [ ] `simulate.py`

### adbp/
- [ ] `analyze.py`
- [ ] `simulate.py`
- [ ] `simulate_v4.py`
- [ ] `token_sim.py`

### bl/
- [ ] `agent_db.py`
- [ ] `baseline.py`
- [ ] `campaign_context.py`
- [ ] `claim.py`
- [ ] `crucible.py`
- [ ] `findings.py`
- [ ] `fixloop.py`
- [ ] `followup.py`
- [ ] `git_hypothesis.py`
- [ ] `healloop.py`
- [ ] `history.py`
- [ ] `hypothesis.py`
- [ ] `nl_entry.py`
- [ ] `peer_review_watcher.py`
- [ ] `quality.py`
- [ ] `question_weights.py`
- [ ] `questions.py`
- [ ] `recall_bridge.py`
- [ ] `skill_forge.py`
- [ ] `training_export.py`
- [ ] `training_schema.py`

### bl-audit/
- [ ] `analyze.py`
- [ ] `evaluate.py`
- [ ] `simulate.py`
- [ ] `simulate_server.py`

### bl\ci/
- [ ] `run_campaign.py`

### bl\cli/
- [ ] `git_hypothesis_cmd.py`

### bl\runners/
- [ ] `agent.py`
- [ ] `base.py`
- [ ] `baseline_check.py`
- [ ] `benchmark.py`
- [ ] `browser.py`
- [ ] `contract.py`
- [ ] `correctness.py`
- [ ] `document.py`
- [ ] `http.py`
- [ ] `performance.py`
- [ ] `quality.py`
- [ ] `simulate.py`
- [ ] `subprocess_runner.py`
- [ ] `swarm.py`

### bricklayer-meta/
- [ ] `simulate.py`

### docs/
- [ ] `masonry-training-export.js`
- [ ] `training_export.py`
- [ ] `training_schema.py`

### masonry\bin/
- [ ] `masonry-fleet-cli.js`
- [ ] `masonry-init-wizard.js`
- [ ] `masonry-mcp.js`
- [ ] `masonry-setup.js`

### masonry\docs/
- [ ] `deterministic_layer.py`
- [ ] `routing_overview.py`
- [ ] `semantic_layer.py`

### masonry\hooks/
- [ ] `bricklayer-retro.js`

### masonry\scripts/
- [ ] `add_e8_records.py`
- [ ] `add_e9_3_records.py`
- [ ] `add_e9_4_calibration.py`
- [ ] `add_e9_4b_fixes.py`
- [ ] `add_e9_records.py`
- [ ] `add_pilot_records.py`
- [ ] `add_synth_records.py`
- [ ] `backfill_agent_fields.py`
- [ ] `backfill_registry.py`
- [ ] `discover_skill_candidates.py`
- [ ] `eval_agent_live.py`
- [ ] `eval_sft.py`
- [ ] `export_sharegpt.py`
- [ ] `finetune_lxc.py`
- [ ] `fix_synth_bl2_records.py`
- [ ] `fix_synth_bl2_w11.py`
- [ ] `gen_training_data.py`
- [ ] `generate_live_records.py`
- [ ] `generate_synth_records.py`
- [ ] `improve_agent.py`
- [ ] `merge_live_records.py`
- [ ] `optimize_with_claude.py`
- [ ] `score_all_agents.py`
- [ ] `score_code_agents.py`
- [ ] `score_ops_agents.py`
- [ ] `score_routing.py`
- [ ] `sync_verdicts_to_agent_db.py`
- [ ] `validate_agents.py`

### masonry\src/
- [ ] `metrics.py`
- [ ] `writeback.py`

### masonry\src\core/
- [ ] `config.js`
- [ ] `recall.js`
- [ ] `registry.js`
- [ ] `skill-surface.js`
- [ ] `state.js`

### masonry\src\daemon/
- [ ] `worker-benchmark.js`
- [ ] `worker-consolidate.js`
- [ ] `worker-deepdive.js`
- [ ] `worker-document.js`
- [ ] `worker-map.js`
- [ ] `worker-optimize.js`
- [ ] `worker-refactor.js`
- [ ] `worker-testgaps.js`
- [ ] `worker-ultralearn.js`

### masonry\src\dspy_pipeline\generated/
- [ ] `adaptive-coordinator.py`
- [ ] `bl-verifier.py`
- [ ] `database-specialist.py`
- [ ] `e2e.py`
- [ ] `hierarchical-coordinator.py`
- [ ] `mutation-tester.py`
- [ ] `production-validator.py`
- [ ] `python-specialist.py`
- [ ] `queen-coordinator.py`
- [ ] `quorum-manager.py`
- [ ] `tdd-london-swarm.py`
- [ ] `typescript-specialist.py`
- [ ] `verification.py`
- [ ] `worker-specialist.py`

### masonry\src\hooks/
- [ ] `masonry-agent-onboard.js`
- [ ] `masonry-approver.js`
- [ ] `masonry-context-monitor.js`
- [ ] `masonry-context-safety.js`
- [ ] `masonry-design-token-enforcer.js`
- [ ] `masonry-guard.js`
- [ ] `masonry-handoff.js`
- [ ] `masonry-lint-check.js`
- [ ] `masonry-mortar-enforcer.js`
- [ ] `masonry-observe.js`
- [ ] `masonry-pre-compact.js`
- [ ] `masonry-preagent-tracker.js`
- [ ] `masonry-prompt-router.js`
- [ ] `masonry-pulse.js`
- [ ] `masonry-recall-check.js`
- [ ] `masonry-register.js`
- [ ] `masonry-score-trigger.js`
- [ ] `masonry-session-end.js`
- [ ] `masonry-session-lock.js`
- [ ] `masonry-session-start.js`
- [ ] `masonry-session-summary.js`
- [ ] `masonry-statusline.js`
- [ ] `masonry-stop-guard.js`
- [ ] `masonry-subagent-tracker.js`
- [ ] `masonry-system-status.js`
- [ ] `masonry-tdd-enforcer.js`
- [ ] `masonry-teammate-idle.js`
- [ ] `masonry-tool-failure.js`
- [ ] `masonry-training-export.js`
- [ ] `masonry-ui-compose-guard.js`

### masonry\src\routing/
- [ ] `deterministic.py`
- [ ] `llm_router.py`
- [ ] `router.py`
- [ ] `semantic.py`

### masonry\src\schemas/
- [ ] `payloads.py`

### masonry\src\scoring/
- [ ] `rubrics.py`

### projects\ADBP/
- [ ] `simulate.py`

### projects\ADBP3/
- [ ] `advanced_sims.py`
- [ ] `analyze.py`
- [ ] `diagnose_failures.py`
- [ ] `evaluate.py`
- [ ] `expiry_analysis.py`
- [ ] `fee_optimization.py`
- [ ] `make_docx.py`
- [ ] `make_pdf.py`
- [ ] `monte_carlo.py`
- [ ] `operational_sims.py`
- [ ] `simulate.py`
- [ ] `simulate_server.py`
- [ ] `vendor_sims.py`

### projects\adbp2/
- [ ] `analyze.py`
- [ ] `evaluate.py`
- [ ] `mc_fallback.py`
- [ ] `monte_carlo.py`
- [ ] `simulate.py`
- [ ] `simulate_server.py`
- [ ] `sweep_admin_fee.py`
- [ ] `sweep_split.py`

### projects\agent-meta/
- [ ] `simulate.py`

### projects\bl2/
- [ ] `analyze.py`
- [ ] `evaluate.py`
- [ ] `simulate.py`

### projects\bricklayer/
- [ ] `analyze.py`

### recall/
- [ ] `simulate.py`

### recall-arch-frontier/
- [ ] `q180_benchmark.py`
- [ ] `q187_benchmark.py`
- [ ] `q192_benchmark.py`
- [ ] `q197_benchmark.py`
- [ ] `q205_benchmark.py`
- [ ] `q214_benchmark.py`
- [ ] `q215_model.py`
- [ ] `q245_sim.py`
- [ ] `q251_sim.py`
- [ ] `simulate.py`

### scripts/
- [ ] `pre-commit.py`

### template/
- [ ] `analyze.py`
- [ ] `evaluate.py`
- [ ] `simulate.py`
- [ ] `simulate_server.py`

### template-frontier/
- [ ] `evaluate.py`
- [ ] `simulate.py`
