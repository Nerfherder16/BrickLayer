# Masonry Self-Research — Wave 29 Synthesis

**Wave**: 29
**Date**: 2026-03-23
**Status**: COMPLETE (5/5 questions DONE)
**Questions**: 5 total — 2 FIX_APPLIED, 1 WARNING, 2 BLOCKED

---

## Executive Summary

- Wave 29 closed both pipeline gaps identified in F28.1: F29.1 wired `_build_qid_to_agent_map()` into `score_findings.py` (median research-analyst `question_text` now 500 chars, up from 88), and F29.2 created a stable `scored_synthetic.jsonl` file that persists karen synthetic negatives across all future scorer reruns. All training data preconditions for MIPROv2 are now fully met.
- MIPROv2 optimization runs for both research-analyst (F29.3) and karen (F29.4) remain BLOCKED — Ollama at `192.168.50.62:11434` is still offline and `ANTHROPIC_API_KEY` is not set in the shell environment. Both commands are written and ready; the only blocker is LLM backend availability.
- V29.1 confirmed that the F28.3 PreToolUse:Agent hook produces populated `request_text` in real production spawns (6 real entries at 500 chars each), but raised a WARNING: zero genuine `pre_spawn` event entries exist in `routing_log.jsonl` from live traffic — all three `pre_spawn` events are smoke-test artifacts. The two-stage mechanism (PreToolUse → pending slot → SubagentStart `start` event) is working correctly, but the success criterion for V29.1 asked for `pre_spawn` entries, which are exclusively written by the manual smoke-test harness.
- `scored_all.jsonl` now contains 604 records (18 agents, 7 with 10+ examples). The training data corpus is in the best state ever: enriched question_text, stable synthetics, correct record attribution.

---

## Findings Table

| ID | Verdict | Severity | Summary |
|----|---------|----------|---------|
| F29.1 | FIX_APPLIED | Medium | _build_qid_to_agent_map() wired into score_findings.py; research-analyst question_text median = 500 chars (was 88); 602 total records, no regressions |
| F29.2 | FIX_APPLIED | Medium | scored_synthetic.jsonl created as stable committed file; 5 karen synthetic negatives survive all reruns; .gitignore negation exception active; idempotency confirmed across 2 reruns |
| F29.3 | BLOCKED | Medium | research-analyst MIPROv2 run blocked: ANTHROPIC_API_KEY not set; Ollama also offline; all data preconditions confirmed met (56 records, median 500-char question_text) |
| V29.1 | WARNING | Medium | F28.3 hook produces non-empty request_text in 6 real production spawns (83% yield); zero genuine pre_spawn events from live traffic — all pre_spawn entries are smoke-test artifacts; one slot-miss observed for spec-writer (CWD-dependent edge case, ~17% miss rate) |
| F29.4 | BLOCKED | Medium | karen MIPROv2 run blocked: same backend issue (Ollama offline, ANTHROPIC_API_KEY not set); all data preconditions confirmed (604 records, 5 karen synthetics, score range 1.0) |

---

## Wave Narrative

### F29.1 — Enrichment Finally Reaches scored_all.jsonl

The F28.1 investigation identified that `score_findings.py` extracted `question_text` from finding file headers (subtitle regex or `**Question**:` field), never touching `questions.md`. F26.1's hypothesis-block enrichment lived exclusively in `training_extractor.py` — a separate code path only triggered when `scored_all.jsonl` is empty. F29.1 bridges this: three targeted changes to `score_findings.py` (guarded import, `qid_map` parameter in `extract_finding_fields()`, one-time `_build_qid_to_agent_map()` call in `run()`) now produce median `input.question_text` of 500 chars for research-analyst records. 49 of 56 research-analyst records reach 500 chars; the 7 below 200 chars correspond to questions without hypothesis blocks in `questions.md` (correct fallback behavior). Total records: 602. All 50 `test_score_findings.py` tests pass with no regressions.

**Impact**: The research-analyst MIPROv2 optimizer will now see rich 500-char question context per training example rather than 88-char file subtitles — a 5.7x improvement in input quality. This was the primary bottleneck holding back training data fidelity since Wave 26.

### F29.2 — Synthetic Negatives Become Permanent Infrastructure

The root cause of the Wave 27/28 synthetic-negatives-lost cycle was `score_ops_agents.py` opening its output file with `"w"` mode, unconditionally overwriting every run. F29.2 makes the synthetics immune to this: a new file `masonry/training_data/scored_synthetic.jsonl` (5 karen negatives, committed to git) is never touched by any scorer script. `score_all_agents.py` merges it as a fifth source after the four dynamically-generated outputs. Deduplication key: `src:synthetic_negative:<commit_hash>:karen:0` — guaranteed unique. `.gitignore` changed from `masonry/training_data/` (directory-level ignore that blocked the negation exception) to `masonry/training_data/*.jsonl` + `!masonry/training_data/scored_synthetic.jsonl`. Two consecutive reruns confirmed idempotency. 26/26 tests pass.

**Impact**: The karen MIPROv2 optimization corpus will always contain negative examples regardless of how many times the scorer pipeline runs. This closes the gradient-signal gap that V28.1 identified as a precondition blocker.

### V29.1 — Hook Architecture Clarified (WARNING)

V29.1 confirmed that the F28.3 two-stage hook mechanism is working in production — 6 real Agent spawns in this session have `request_text` at 500 chars in their `start` events. However, the finding reveals a terminology/architecture mismatch: the `pre_spawn` event type exists only in the smoke-test harness; live hook traffic produces `start` events via SubagentStart (not `pre_spawn` events directly from PreToolUse). The three `pre_spawn` entries in `routing_log.jsonl` all have `session_id: "test-session-001"` — they are artifacts of the F28.3 smoke test, not real session traffic.

One slot-miss was observed: a `spec-writer` spawn at 14:08:32Z wrote a pending slot file but the SubagentStart hook could not consume it within the 10-second TTL due to CWD resolution — leaving `request_text = ""` in the `start` event. This is approximately a 17% miss rate on this session, though with only 6 real post-fix spawns the sample is small.

**Key architectural correction**: `masonry-preagent-tracker.js` does NOT write to `routing_log.jsonl` directly. It writes to `.masonry/pending_agent_prompts/{subagent_type}_latest.json`. The SubagentStart hook (`masonry-subagent-tracker.js`) reads the slot and writes the `start` event to `routing_log.jsonl` with the populated `request_text`. The F28.3 finding's smoke-test evidence section conflated the two-hop output as coming directly from `preagent-tracker.js` — this was corrected by the peer review.

### MIPROv2 Runs — Still Blocked (F29.3, F29.4)

Both optimization commands are written and ready. The exact blocker: LiteLLM's `anthropic/` prefix requires `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` in the shell environment; neither is set. The Claude Code session token is not accessible as an environment variable and LiteLLM has no mechanism to discover it. Ollama remains offline at `192.168.50.62:11434`.

All data preconditions are satisfied — this is purely an external dependency block:
- **Research-analyst**: 56 records, median question_text = 500 chars, no `optimized_prompts/research-analyst.json` yet
- **Karen**: 299+ records, 5 negatives (score=0), score range = 1.0, no `optimized_prompts/karen.json` yet
- Both run commands are ready; see "Recommended Next Actions" below

---

## DSPy Pipeline State After Wave 29

**Functional components:**
- MIPROv2 bootstrapping — functional (Wave 23)
- Ollama backend → `qwen3:14b` — **offline** (192.168.50.62:11434 unreachable)
- `--backend anthropic` code path — wired, not yet executed (requires API key)
- CLI flags (`--num-trials`, `--valset-size`, `--signature`) — functional
- Training data attribution — substantially improved (Wave 24 D24.1)
- question_text enrichment in `score_findings.py` — **fixed and active** (Wave 29 F29.1) — median 500 chars
- Evidence quality metric gate — content-signal-aware (Wave 25 F25.2)
- KarenSig + karen data loader — wired (Wave 25 F25.3)
- `build_karen_metric()` calibration — corrected (Wave 27 F27.1)
- Synthetic negatives persistence — **fixed and committed** (Wave 29 F29.2, `scored_synthetic.jsonl`)
- PreToolUse:Agent hook — live (Wave 28 F28.3); producing populated `request_text` (V29.1 WARNING)

**Known gaps after Wave 29:**
- Ollama at 192.168.50.62 offline — both MIPROv2 runs blocked
- `ANTHROPIC_API_KEY` not set — anthropic backend path unusable
- `optimize_all()` still hardcodes ResearchAgentSig for all agents — open since Wave 25
- V29.1 WARNING: one spec-writer slot-miss observed in 6 total real spawns (~17% miss rate)
- F29.3/F29.4 BLOCKED: no optimized prompts exist yet for any agent
- `masonry/optimized_prompts/` is empty — current best metric still 68.3% (Trial 3, Wave 23)

---

## Open Issues After Wave 29

1. **Run research-analyst MIPROv2** (F29.3 BLOCKED):
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   cd C:/Users/trg16/Dev/Bricklayer2.0
   python masonry/scripts/run_optimization.py research-analyst \
     --backend anthropic --num-trials 10 --valset-size 25 --signature research
   ```

2. **Run karen MIPROv2** (F29.4 BLOCKED):
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   cd C:/Users/trg16/Dev/Bricklayer2.0
   python masonry/scripts/run_optimization.py karen \
     --backend anthropic --num-trials 10 --valset-size 25 --signature karen
   ```

3. **Investigate spec-writer slot-miss (V29.1 WARNING)** — CWD resolution in SubagentStart hook fails to find `.masonry/pending_agent_prompts/` when subagent spawns from a different CWD. Needs dedicated diagnosis.

4. **Fix `optimize_all()` hardcoded ResearchAgentSig** — carry-forward from Wave 25 open issue #6. `optimize_all()` uses ResearchAgentSig for every agent; karen and other agent types need their own signature dispatch.

5. **Post-optimization validation** — After any MIPROv2 run completes, validate: (a) `optimized_prompts/{agent}.json` has non-empty `instructions`; (b) the optimized prompt improves metric score vs. baseline; (c) Mortar injection path correctly picks up the optimized prompt on next spawn.

---

## Recommended Next Actions (Prioritized)

| Priority | Action | Effort | Impact |
|----------|--------|--------|--------|
| 1 | Set `ANTHROPIC_API_KEY`, run research-analyst MIPROv2 (F29.3 unblock) | ~5 min setup + 30-60 min run | First optimized research-analyst prompt — new metric ceiling |
| 2 | Set `ANTHROPIC_API_KEY`, run karen MIPROv2 (F29.4 unblock) | ~5 min setup + 30-60 min run | First optimized karen prompt — ops-domain coverage |
| 3 | Validate optimized prompts post-run | ~30 min | Confirms optimization produced improvement, not regression |
| 4 | Fix spec-writer slot-miss in SubagentStart hook (V29.1 WARNING) | ~30 min | Raises routing signal yield from 83% → ~99% |
| 5 | Fix `optimize_all()` per-agent signature dispatch | ~45 min | Unblocks batch optimization for all agent types |
