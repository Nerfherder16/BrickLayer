# Deep Dive Report

Generated: 2026-03-28T02:08:55.999Z
Project: Bricklayer2.0
Files scanned: 323

## Summary

| Severity | Count |
|----------|-------|
| HIGH | 217 |
| MEDIUM | 279 |
| LOW | 30 |
| **Total** | **526** |

## HIGH Severity (217)

- **file-size** `adbp\analyze.py` — 752 lines (limit: 300)
- **long-function** `adbp\analyze.py:157` — make_styles() is 105 lines (limit: 40)
- **long-function** `adbp\analyze.py:281` — build_executive_summary() is 97 lines (limit: 40)
- **high-complexity** `adbp\analyze.py:443` — build_domain_findings() has complexity 12 (limit: 10)
- **long-function** `adbp\analyze.py:511` — build_best_way_forward() is 144 lines (limit: 40)
- **file-size** `adbp\simulate.py` — 1061 lines (limit: 300)
- **long-function** `adbp\simulate.py:259` — _run_legacy_scenario() is 172 lines (limit: 40)
- **high-complexity** `adbp\simulate.py:259` — _run_legacy_scenario() has complexity 15 (limit: 10)
- **long-function** `adbp\simulate.py:431` — _run_geo_scenario() is 188 lines (limit: 40)
- **high-complexity** `adbp\simulate.py:431` — _run_geo_scenario() has complexity 15 (limit: 10)
- **long-function** `adbp\simulate.py:832` — run_fixed_growth() is 104 lines (limit: 40)
- **file-size** `adbp\simulate_v4.py` — 560 lines (limit: 300)
- **long-function** `adbp\simulate_v4.py:124` — run_q9_1() is 98 lines (limit: 40)
- **long-function** `adbp\simulate_v4.py:222` — run_q9_2() is 109 lines (limit: 40)
- **long-function** `adbp\simulate_v4.py:331` — run_q9_3() is 108 lines (limit: 40)
- **long-function** `bl\agent_db.py:190` — get_trend() is 85 lines (limit: 40)
- **long-function** `bl\baseline.py:122` — diff_against_baseline() is 90 lines (limit: 40)
- **file-size** `bl\ci\run_campaign.py` — 545 lines (limit: 300)
- **long-function** `bl\ci\run_campaign.py:51` — _parse_questions_bl2() is 86 lines (limit: 40)
- **long-function** `bl\ci\run_campaign.py:374` — main() is 125 lines (limit: 40)
- **file-size** `bl\crucible.py` — 725 lines (limit: 300)
- **high-complexity** `bl\crucible.py:532` — _score_compliance_auditor() has complexity 11 (limit: 10)
- **file-size** `bl\findings.py` — 573 lines (limit: 300)
- **long-function** `bl\findings.py:59` — classify_failure_type() is 103 lines (limit: 40)
- **high-complexity** `bl\findings.py:59` — classify_failure_type() has complexity 12 (limit: 10)
- **long-function** `bl\findings.py:162` — classify_confidence() is 152 lines (limit: 40)
- **high-complexity** `bl\findings.py:162` — classify_confidence() has complexity 17 (limit: 10)
- **long-function** `bl\findings.py:346` — write_finding() is 124 lines (limit: 40)
- **long-function** `bl\followup.py:165` — _parse_followup_blocks() is 98 lines (limit: 40)
- **file-size** `bl\nl_entry.py` — 1241 lines (limit: 300)
- *...and 187 more*

## MEDIUM Severity (279)

- **long-function** `adbp\analyze.py:73` — parse_finding() is 59 lines (limit: 40)
- **long-function** `adbp\analyze.py:378` — build_failure_boundary_map() is 65 lines (limit: 40)
- **long-function** `adbp\analyze.py:443` — build_domain_findings() is 68 lines (limit: 40)
- **long-function** `adbp\analyze.py:655` — build_raw_data() is 45 lines (limit: 40)
- **long-function** `adbp\simulate.py:83` — build_scenarios() is 58 lines (limit: 40)
- **long-function** `adbp\simulate.py:141` — _get_geo_state() is 42 lines (limit: 40)
- **long-function** `adbp\simulate.py:742` — print_summary() is 64 lines (limit: 40)
- **long-function** `adbp\token_sim.py:90` — compute_burn_rate() is 66 lines (limit: 40)
- **file-size** `bl\agent_db.py` — 338 lines (limit: 300)
- **long-function** `bl\agent_db.py:130` — record_run() is 52 lines (limit: 40)
- **long-function** `bl\campaign_context.py:171` — generate() is 55 lines (limit: 40)
- **long-function** `bl\ci\run_campaign.py:137` — _parse_questions_table() is 67 lines (limit: 40)
- **long-function** `bl\ci\run_campaign.py:241` — _dispatch() is 47 lines (limit: 40)
- **long-function** `bl\ci\run_campaign.py:299` — _format_pr_comment() is 75 lines (limit: 40)
- **long-function** `bl\crucible.py:188` — check_block() is 52 lines (limit: 40)
- **long-function** `bl\crucible.py:240` — _score_question_designer() is 77 lines (limit: 40)
- **long-function** `bl\crucible.py:346` — _score_quantitative_analyst() is 63 lines (limit: 40)
- **long-function** `bl\crucible.py:418` — _is_bl2_diag_row() is 57 lines (limit: 40)
- **long-function** `bl\crucible.py:483` — _is_fix_row() is 49 lines (limit: 40)
- **long-function** `bl\crucible.py:532` — _score_compliance_auditor() is 56 lines (limit: 40)
- **long-function** `bl\crucible.py:588` — _score_design_reviewer() is 75 lines (limit: 40)
- **long-function** `bl\findings.py:470` — update_results_tsv() is 55 lines (limit: 40)
- **long-function** `bl\fixloop.py:44` — _spawn_fix_agent() is 59 lines (limit: 40)
- **file-size** `bl\followup.py` — 347 lines (limit: 300)
- **long-function** `bl\followup.py:94` — _build_followup_prompt() is 51 lines (limit: 40)
- **file-size** `bl\git_hypothesis.py` — 415 lines (limit: 300)
- **long-function** `bl\git_hypothesis.py:134` — parse_diff_files() is 42 lines (limit: 40)
- **long-function** `bl\git_hypothesis.py:176` — match_patterns() is 43 lines (limit: 40)
- **long-function** `bl\git_hypothesis.py:219` — generate_questions() is 71 lines (limit: 40)
- **long-function** `bl\git_hypothesis.py:316` — append_to_questions_md() is 66 lines (limit: 40)
- *...and 249 more*

## LOW Severity (Tech Debt Markers) (30)

- **tech-debt-markers** `bl\nl_entry.py` — 2 markers: BUG:46, BUG:364
- **tech-debt-markers** `bl\question_sharpener.py` — 2 markers: TEMP:176, TEMP:184
- **tech-debt-markers** `bl\runners\simulate.py` — 2 markers: TEMP:230, TEMP:278
- **tech-debt-markers** `bl-audit\evaluate.py` — 1 markers: TODO:61
- **tech-debt-markers** `bl-audit\simulate.py` — 1 markers: TODO:95
- **tech-debt-markers** `bricklayer-meta\simulate.py` — 1 markers: TEMP:446
- **tech-debt-markers** `masonry\bin\masonry-init-wizard.js` — 1 markers: BUG:109
- **tech-debt-markers** `masonry\scripts\add_e9_3_records.py` — 1 markers: BUG:43
- **tech-debt-markers** `masonry\scripts\add_pilot_records.py` — 1 markers: TEMP:63
- **tech-debt-markers** `masonry\scripts\add_synth_records.py` — 3 markers: BUG:37, BUG:38, BUG:53
- **tech-debt-markers** `masonry\scripts\eval_agent_live.py` — 1 markers: TEMP:213
- **tech-debt-markers** `masonry\scripts\fix_synth_bl2_records.py` — 1 markers: BUG:117
- **tech-debt-markers** `masonry\scripts\fix_synth_bl2_w11.py` — 1 markers: BUG:35
- **tech-debt-markers** `masonry\scripts\generate_live_records.py` — 1 markers: TEMP:182
- **tech-debt-markers** `masonry\src\daemon\worker-deepdive.js` — 3 markers: TODO:13, TODO:66, TODO:69
- **tech-debt-markers** `masonry\src\hooks\masonry-preagent-tracker.js` — 2 markers: TEMP:6, BUG:15
- **tech-debt-markers** `masonry\src\routing\deterministic.py` — 2 markers: BUG:59, BUG:362
- **tech-debt-markers** `projects\adbp2\evaluate.py` — 1 markers: TODO:61
- **tech-debt-markers** `projects\ADBP3\evaluate.py` — 1 markers: TODO:61
- **tech-debt-markers** `projects\ADBP3\operational_sims.py` — 1 markers: BUG:649
- **tech-debt-markers** `projects\bl2\evaluate.py` — 1 markers: TODO:61
- **tech-debt-markers** `projects\bl2\simulate.py` — 1 markers: TODO:95
- **tech-debt-markers** `recall-arch-frontier\simulate.py` — 4 markers: BUG:1218, TEMP:1266, BUG:2792, BUG:2904
- **tech-debt-markers** `scripts\pre-commit.py` — 3 markers: TODO:166, TODO:167, TODO:188
- **tech-debt-markers** `template\evaluate.py` — 1 markers: TODO:61
- **tech-debt-markers** `template\simulate.py` — 1 markers: TODO:95
- **tech-debt-markers** `template-frontier\evaluate.py` — 1 markers: TODO:61
- **tech-debt-markers** `tests\test_mas_integration.js` — 2 markers: TEMP:5, TEMP:39
- **tech-debt-markers** `tests\test_registry_regen.py` — 2 markers: TEMP:20, TEMP:22
- **tech-debt-markers** `tests\test_routing_router.py` — 2 markers: BUG:103, BUG:114

## Actions

Run `/fix` or spawn a `refactorer` agent to address HIGH severity issues.
MEDIUM issues can be addressed in the next `/build` cycle.