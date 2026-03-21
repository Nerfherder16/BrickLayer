# Synthesis — Masonry Self-Research Wave 3

**Campaign type**: BrickLayer 2.0
**Wave**: 3
**Questions**: 9 (F: 5, D: 2, R: 2 — all DONE)
**Date**: 2026-03-21

---

## Executive Summary

Wave 3 completed 9 questions: 5 implementations (F3.1–F3.5), 2 diagnostics (D3.1–D3.2), and 2 research investigations (R3.1–R3.2). Every implementation question yielded FIX_APPLIED. The two diagnostic questions revealed double-fire side effects in the UserPromptSubmit and SessionStart hooks. The two research questions produced hard empirical data: only 15% of queries reach the 0.70 threshold (confirming it needs lowering), and the DSPy training extractor is structurally broken — producing zero training examples from all 35 accumulated findings.

The dominant themes of Wave 3 are: **(1) the double-fire root cause is now eliminated** (F3.1 is the most impactful change in the three-wave campaign); **(2) the training pipeline is completely non-functional** (R3.2), making DSPy optimization a zero-value operation until fixed; and **(3) live calibration data (R3.1) provides the first empirical basis for routing threshold recommendations**.

---

## Verdicts Table — Wave 3

| ID | Question (short) | Verdict | Severity |
|----|-----------------|---------|----------|
| F3.1 | Empty plugin hooks.json — double-fire eliminated across all 10 hooks | FIX_APPLIED | High |
| F3.2 | masonry-approver complete fix: corrected dir patterns + Bash exclusion | FIX_APPLIED | High |
| F3.3 | DSPy verdict taxonomy: UNCALIBRATED, DIAGNOSIS_COMPLETE, baseline=0.0 | FIX_APPLIED | Medium |
| F3.4 | RoutingDecision.fallback_reason field + router population | FIX_APPLIED | Low |
| F3.5 | _MODE_FIELD_RE re.IGNORECASE + mode_value.lower() | FIX_APPLIED | Low |
| D3.1 | masonry-register.js: duplicate Mortar directives per prompt (stdout) | FAILURE | Medium |
| D3.2 | masonry-session-start.js: interrupted-build auto-resume silently broken | WARNING | Medium |
| R3.1 | Live calibration: 0.70 threshold reaches only 15% of queries | FAILURE | High |
| R3.2 | build_dataset() produces zero training examples — agent field missing | FAILURE | High |

---

## Cross-Wave Synthesis

### The Double-Fire Era Ends (F3.1)

F3.1 emptied `hooks/hooks.json`, eliminating all 10 duplicate hook registrations. This single JSON change resolves six prior findings across three waves:

| Resolved finding | Root effect |
|-----------------|-------------|
| D1.1 | masonry-observe + masonry-guard fired on all PostToolUse (not just Write/Edit) |
| D1.2 | masonry-guard strike counter race amplified by double-fire |
| D1.4 | masonry-observe sent duplicate campaign observations |
| D2.2 | masonry-subagent-tracker agents.json race due to double SubagentStart |
| D3.1 | masonry-register duplicate Mortar directives per prompt |
| D3.2 | masonry-session-start interrupted-build auto-resume silently broken |

Additionally, the PostToolUse match is now more precise: global settings.json uses `matcher: "Write|Edit"`, while the plugin had no matcher (fire on all PostToolUse including Bash, Read, Glob). Removing the plugin registration narrows observe and guard to file-write events only — a correctness improvement beyond the race fix.

**The remaining race conditions (D1.2 for guard strikes, D2.2 for agents.json) still exist** as underlying non-atomic writes, but they now require genuinely concurrent PostToolUse or SubagentStart events — a much rarer condition than the guaranteed double-fire.

### D3.1 and D3.2: Behavioral Side Effects Now Moot (Post-F3.1)

D3.1 and D3.2 document behavioral side effects of double-fire in the UserPromptSubmit and SessionStart hooks respectively. These are now resolved by F3.1:

- **D3.1** (masonry-register.js): Duplicate Mortar routing directives written to stdout on every user prompt. Claude received the routing injection twice per message. **Fixed by F3.1.**
- **D3.2** (masonry-session-start.js): The interrupted-build auto-resume path wrote two JSON objects to stdout — the hook framework received malformed JSON and silently dropped the auto-resume directive. **Fixed by F3.1.**

The session snapshot write in D3.2 was confirmed safe (write-once identical data, no corruption). Neither D3.1 nor D3.2 requires standalone fixes.

### masonry-approver Is Now Fully Protected (F3.2)

The three-iteration security fix is complete:

| Wave | Finding | Issue added |
|------|---------|------------|
| V1.5 (Wave 1) | Auto-approval of Tier 1/2 files during builds | Initial diagnosis |
| F2.2 (Wave 2) | Directory patterns 5+6 missed relative paths (`src/hooks/foo.js`) | Pattern correction |
| V2.1 (Wave 2) | Bash tool calls bypassed entire blocklist | Bash exclusion |
| F3.2 (Wave 3) | All three fixes implemented | FIX_APPLIED |

The implemented protection covers:
- All named Tier 1/2 files by suffix: `project-brief.md`, `agent_registry.yml`, `hooks.json`, `constants.py`
- All files in `src/` or `docs/` directories — by relative, absolute, or traversal paths
- All Bash tool calls — excluded from auto-approval entirely

### DSPy Training Pipeline Structural Failure (R3.2)

R3.2 is the most consequential new finding of Wave 3. `build_dataset()` has been returning `{}` (empty dict) since the first finding was ever written. The failure chain:

1. `extract_finding()` does not extract an `"agent"` field from finding markdown files
2. `score_example()` returns `0.0` for any finding without `"agent"` field
3. `build_dataset()` skips all findings with `weight == 0.0`

**All 35 findings across three waves have been excluded.** No training data has ever been produced. Every call to `masonry_optimize_agent` or the Kiln "OPTIMIZE" button has operated on an empty training set.

The fix is straightforward — add agent attribution lookup from `questions.md` (Option A) or add `**Agent**:` to the finding template (Option B, cleaner long-term). This is the highest-priority finding to fix before attempting any DSPy optimization.

### Live Calibration Confirms Routing Threshold Too High (R3.1)

First empirical routing calibration with 46 agents and 20 prompts:

| Metric | Value | Implication |
|--------|-------|-------------|
| Mean top-1 similarity | 0.607 | Most queries well below 0.70 |
| % with top-1 >= 0.70 | 15% | Threshold is too restrictive |
| Mean margin | 0.043 | Slightly below proposed 0.05 margin |
| % with margin >= 0.05 | 40% | Margin check captures 40% of traffic |

The recommended change: `_DEFAULT_THRESHOLD = 0.60` + `_MARGIN_THRESHOLD = 0.05`. This would route ~40% of queries through Layer 2 (up from 15%), with the margin check ensuring those 40% are high-confidence routes. The remaining 60% fall to Layer 3 (currently dead) → Layer 4.

Notable routing failures at any threshold: "Write a Python function to parse JSON" → spreadsheet-wizard (0.32); "Refactor the semantic routing layer" → pointer with 0.0002 margin vs trowel; "What is the current status" → kiln-engineer with 0.0004 margin vs trowel. These require Layer 3 or human clarification regardless of threshold.

### DSPy Taxonomy Fixed (F3.3)

Three correctness defects patched:
1. `DIAGNOSIS_COMPLETE`, `FIX_APPLIED`, `COMPLETE` added to `_OK_VERDICTS` (score 1.0)
2. `UNCALIBRATED`, `INCONCLUSIVE` added to `_PARTIAL_VERDICTS` (score 0.5)
3. `baseline_score == 0.0` now returns `alert_level = "calibrating"` with `drift_pct = None` instead of silently reporting `"ok"`

All known verdict strings from the 35-finding corpus now score correctly. The calibrating level surfaces in Kiln for newly onboarded agents.

---

## Cumulative Priority Fix Order (Waves 1–3)

### P0 — Already applied in Wave 3

| Fix | Wave | Status |
|-----|------|--------|
| F3.1: Empty plugin hooks.json | 3 | ✅ APPLIED |
| F3.2: masonry-approver complete fix | 3 | ✅ APPLIED |
| F3.3: DSPy verdict taxonomy patch | 3 | ✅ APPLIED |
| F3.4: fallback_reason in RoutingDecision | 3 | ✅ APPLIED |
| F3.5: _MODE_FIELD_RE re.IGNORECASE | 3 | ✅ APPLIED |

### P0 — Still open (highest priority for next session)

| ID | Fix | Lines changed |
|----|-----|--------------|
| **R3.2** | Add agent attribution to finding template OR add questions.md lookup to training_extractor.py | ~20 lines |
| **D1.6** | Replace `shlex.quote + shell=True` with list-form subprocess in `llm_router.py` | ~8 lines |
| **R1.3/R2.2** | `_LLM_TIMEOUT = 20` on Windows (after D1.6) | 2 lines |

### P1 — High value, fix in next maintenance window

| ID | Fix | Lines changed |
|----|-----|--------------|
| **R3.1** | Lower `_DEFAULT_THRESHOLD = 0.60` + add `_MARGIN_THRESHOLD = 0.05` in `semantic.py` | 8 lines |
| **D1.2** | Atomic rename-based strike counter in masonry-guard.js | 5 lines |
| **D1.3** | Add logging + CWD fallback in `_load_registry` | 4 lines |
| **R1.5** | Circuit breaker for Ollama (fast-fail after 2 consecutive timeouts) | ~30 lines |
| **V1.4** | Registry membership check for `target_agent` in llm_router.py | 5 lines |
| **D2.2** | File locking or append-only format for agents.json in masonry-subagent-tracker.js | ~20 lines |

### P2 — Polish

| ID | Fix | Lines changed |
|----|-----|--------------|
| **R1.4** | Add 8 missing slash commands to `_SLASH_COMMANDS` | 8 lines |
| **D1.7** | File locking for `onboard_agent.py` registry append | ~10 lines |
| **V1.3/M2.1** | Add 200-entry cache size limit to `semantic.py` | 3 lines |
| **D3.2** | Add deduplication guard for interrupted-build resume (moot after F3.1) | Deferred — F3.1 already fixes |

---

## Three-Wave Campaign Summary

| Wave | Questions | FIX_APPLIED | FAILURE | WARNING | HEALTHY | COMPLETE |
|------|-----------|-------------|---------|---------|---------|----------|
| Wave 1 | 15 | 0 | 13 | 1 | 2 | 0 |
| Wave 2 | 9 | 0 | 6 | 0 | 1 | 1 |
| Wave 3 | 9 | 5 | 3 | 1 | 0 | 0 |
| **Total** | **33** | **5** | **22** | **2** | **3** | **1** |

The campaign identified 22 failures, implemented 5 fixes (all P0/P1 priority), and validated 1 HEALTHY behavior. The ratio of findings-to-fixes (22:5) reflects the Wave 1–2 focus on discovery and Wave 3 focus on repair. The 5 implemented fixes address the highest-impact issues: the double-fire root cause, the security bypass, the DSPy taxonomy, the schema gap, and the deterministic routing case-sensitivity.

## Wave 4 Recommendations

If Wave 4 runs, highest-value questions:

1. **After R3.2 fix applied**: Verify `build_dataset()` produces non-empty training examples — count by agent and verify verdict labels
2. **After D1.6 fix applied**: Re-measure Layer 3 latency with list-form subprocess to confirm cmd.exe overhead contribution
3. **R3.1 implementation**: Apply threshold 0.60 + margin 0.05 — then re-run the 20-query benchmark to measure improvement in routing coverage
4. **After R3.2 + R3.1 + D1.6/R2.2 fixes**: Run full end-to-end routing pipeline trace — measure what % of requests each layer now handles empirically
5. **D2.2 race under real concurrent load**: Confirm that masonry-subagent-tracker's agents.json race only manifests under true parallel agent spawns (not double-fire), and measure the actual occurrence rate
