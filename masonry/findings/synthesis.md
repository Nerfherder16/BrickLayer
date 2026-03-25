# Wave 37 Synthesis — Masonry Self-Research

**Date**: 2026-03-24
**Wave**: 37 (Predict Mode -- cascade-analyst)
**Questions**: 7 total -- 4 CONFIRMED, 3 WARNING, 0 failed

---

## Executive Summary

Wave 37 was the first predict-mode wave, deploying the cascade-analyst to answer seven forward-looking questions about unresolved risks identified across waves 1-36. The results reveal that the Masonry optimization loop has three independently active failure cascades that interact destructively, and two more that are imminent or latent. The most urgent finding (P6) shows that drift scoring is already inverted for 4 of 5 agents with verdict histories -- a single `auto_trigger=true` call would launch optimization processes that directionally suppress FAILURE verdicts, starving the fix pipeline of inputs. The second most urgent (P3) confirms that karen optimization has already executed with the wrong scoring rubric, and contaminated instructions are live on all machines. These are not future risks; they are active cascades requiring immediate intervention before any further optimization runs.

The predict-mode wave changes the campaign recommendation from CONTINUE to STOP with conditions. The core research campaign (waves 1-36) successfully built and validated the Masonry orchestration layer. The predict wave reveals that the optimization feedback loop -- the system that is supposed to improve agent quality over time -- has three structural flaws that would compound if left unaddressed. Fixing these flaws is a maintenance task, not a research question.

---

## Critical Findings (must act)

1. **P6** [CONFIRMED, Critical] -- Drift scoring treats FAILURE verdicts as 0.0 (bad performance), but research agents return FAILURE to indicate correctly-found defects. 4 agents already at CRITICAL drift (45-100%). Auto-trigger would launch `improve_agent.py` against the campaign's best performers.
   Fix: Replace `_score_verdicts()` in `drift_detector.py` with confidence-weighted mean (confidence data already present in agent_db.json). Until shipped, `masonry_drift_check` must NOT be called with `auto_trigger=true`. Add minimum sample threshold (>=10 verdicts) before auto-trigger fires.

2. **P3** [CONFIRMED, High] -- Karen optimization already executed with the research-analyst rubric (verdict/evidence/confidence) instead of the karen rubric (quality_score_proximity/action_match/changelog_quality). Contaminated instructions are live in karen.md on all machines since 2026-03-24T23:17:33Z. The revert gate could not detect the regression because the bimodal corpus (98.7% at score=100) produces near-1.0 before/after scores.
   Fix: (a) Immediately clear the DSPy Optimized Instructions section from karen.md on all machines. (b) Add signature-conditional rubric to `_build_prompt()` in `optimize_with_claude.py`. (c) Replace synthetic_negative records with real organic low-scoring examples.

3. **P1** [CONFIRMED, High] -- Ollama offline cascade is active. Every non-deterministic routing request blocks 15s at Layer 2 before falling through to Layer 3. Both MIPROv2 execution paths are blocked simultaneously. The day-7 FAILURE runbook action references a non-existent `SEMANTIC_ROUTING_ENABLED` constant.
   Fix: (a) Add circuit breaker to `semantic.py` (first failure blocks 15s, subsequent within 60s are instant). (b) Add `SEMANTIC_ROUTING_ENABLED` to `constants.py`. (c) Restore Ollama host.

## Significant Findings (important but not blocking)

4. **P2** [WARNING, High] -- Mock campaign corpus contamination has frozen the optimization loop. 15 `source: mock_campaign` records in scored_all.jsonl degraded before_score from 0.35 to 0.15 (loop 2 was reverted). The held-out eval draws last-N chronologically, so mock records dominate the eval set. Running MIPROv2 on this corpus would train on 40% mislabeled contrast signal.
   Fix: Filter mock_campaign records from scored_all.jsonl before any optimization run. Add source-filtering to `_load_records()`.

5. **P5** [CONFIRMED, High] -- D3.2 interrupted-build cascade is imminent with zero additional preconditions. The double-fire output defect produces invalid JSON on session-start, silently discarding the auto-resume directive. Build-guard session-ID gating then permits new sessions to overwrite interrupted build state. Stop-guard may auto-commit partial, unverified implementations.
   Fix: Verify F3.1 (empty hooks.json) is fully applied. If double-fire persists, add write-once lock to session-start interrupted-build fast path.

6. **P4** [WARNING, Medium] -- Pre-agent tracker one-slot-per-type collision confirmed at 16.7% rate (7 of 42 spawns within 10s TTL). 26.2% of research-analyst routing_log entries already have empty request_text. Training corpus corruption is currently latent (requires live record pipeline coupling to routing_log, which does not exist yet).
   Fix: Replace single-slot with UUID-keyed slot in masonry-preagent-tracker.js. Add warning log on slot overwrite detection.

7. **P7** [WARNING, Low] -- `AgentRegistryEntry.optimized_prompt` is a dead schema field. No write path, no read path, no current consumer. Cascade is dormant. Secondary gap: 21 of 47 agents lack `dspy_status` key in YAML, making `update_registry_dspy_status()` silently skip them.
   Fix: Remove the dead field from payloads.py. Backfill `dspy_status` for all 47 agents.

## Healthy / Verified

The predict wave found no false alarms -- all seven hypotheses identified real mechanisms. However, several prior-wave accomplishments remain solid:

- **Routing pipeline** (waves 3-11): All four layers operational. L1 15-20%, L2 30% (when Ollama online), L3 35%, L4 35%.
- **Hook double-fire** (F3.1): Root cause fix applied. P5 notes the cascade if it recurs, but the fix is in place.
- **Training data pipeline** (waves 4-9, 29-35): 606+ records across agents. Question text enrichment at 500-char median. Deduplication and scoring functional.
- **Write-back injection** (V32.1): End-to-end confirmed. MIPROv2 -> JSON -> .md -> system prompt path works.
- **API key CLI** (F32.2): Code blocker for MIPROv2 execution is resolved.

---

## Cross-Cascade Interaction Analysis

The predict wave reveals three cascades that interact:

```
P6 (drift inversion) --[feeds]--> auto_trigger --[launches]--> improve_agent.py
                                                                       |
P3 (wrong rubric) --[corrupts]--------------------------> optimize_with_claude.py
                                                                       |
P2 (mock corpus) --[poisons]---> held-out eval + training tiers -------+
                                                                       |
                                                               [optimized instructions]
                                                                       |
                                                               karen.md / research-analyst.md
                                                                       |
                                                               [agent behavior degrades]
                                                                       |
P6 (drift inversion) <--[measures degradation as improvement]----------+
```

**The feedback loop is self-reinforcing**: P6 triggers optimization on the best agents. P3 ensures optimization uses the wrong rubric. P2 ensures the eval cannot detect the regression. The result is agents that stop finding real defects, which P6 then scores as "healthy." This loop activates on the next `auto_trigger=true` call with zero additional preconditions.

**Fix ordering matters**: P2 (corpus cleanup) must precede P3 (rubric fix) must precede P6 (metric fix). Fixing P6 alone would stop the auto-trigger cascade but leave the rubric and corpus problems to corrupt the next manual optimization run. Fixing P3 alone would fix karen but leave research-analyst exposed to the mock corpus. All three must be addressed, in order.

---

## Campaign-Wide Verdict Summary (Waves 1-37)

| Category | Count |
|----------|-------|
| Total questions answered | 209+ |
| FIX_APPLIED | ~50 |
| HEALTHY/COMPLIANT/CALIBRATED | ~40 |
| CONFIRMED (predict mode) | 4 |
| WARNING | ~20 |
| FAILURE (subsequently fixed) | ~24 |
| FAILURE (open) | ~7 |
| Other (DIAGNOSIS_COMPLETE, DONE, etc.) | ~15 |

The campaign has moved from discovery (waves 1-2), through a sustained fix cycle (waves 3-32), into forward-looking cascade analysis (waves 33-37). The system is operationally functional but the optimization feedback loop requires targeted repairs before it can be safely engaged.

---

## Recommendation

**STOP**

The core research campaign is complete. All four routing layers work. Hook double-fires are eliminated. Training data pipeline produces quality records. Write-back injection is confirmed end-to-end. The predict wave identified three interacting cascades in the optimization feedback loop (P6 + P3 + P2) that require ordered fixes, but these are maintenance tasks with clear specifications, not research questions requiring further investigation.

**Preconditions before any optimization run:**
1. Clean mock_campaign records from scored_all.jsonl (P2)
2. Clear contaminated DSPy section from karen.md on all machines (P3)
3. Add signature-conditional rubric to optimize_with_claude.py (P3)
4. Replace _score_verdicts() with confidence-weighted mean in drift_detector.py (P6)
5. Add circuit breaker to semantic.py (P1)
6. Restore Ollama or cleanly disable Layer 2 (P1)

**After those 6 items are complete**, the MIPROv2 optimization runs (research-analyst and karen) can safely execute with the API key.

## Next Wave Hypotheses

If further campaign waves are warranted, these are the highest-value questions:

1. After P2/P3/P6 fixes are applied, does `improve_agent.py --dry-run` produce before_score >= 0.50 for research-analyst and a non-degenerate eval for karen?
2. After Ollama is restored or the circuit breaker is deployed, what is the actual Layer 2 hit rate on a mixed dev+campaign session? (R9.2 measured 40-60% without the circuit breaker.)
3. Does the P5 cascade (interrupted-build) actually manifest with F3.1 applied? Needs a live interruption test with an active `.autopilot/` directory.
4. After MIPROv2 runs, does the optimized research-analyst produce measurably different findings on a held-out question set compared to the pre-optimization baseline?
5. Is the P4 slot collision (16.7% rate) producing any observable downstream effect beyond empty request_text in routing_log, or is the damage contained to analytics?
