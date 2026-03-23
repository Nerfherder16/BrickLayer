# Wave 32 Synthesis — Masonry Self-Research

**Wave**: 32
**Date**: 2026-03-23
**Questions answered**: 6
**Net verdicts**: 2 FIX_APPLIED, 3 HEALTHY, 1 DONE (monitoring)

---

## Executive Summary

Wave 32 closed the documentation and tooling gaps that remained after Wave 31's injection-path breakthrough. The two most impactful results: (1) CLAUDE.md now accurately describes the DSPy write-back mechanism — the false "automatic Mortar injection" claim is corrected, and (2) `configure_dspy()` now accepts an explicit `api_key` argument, eliminating the `ANTHROPIC_API_KEY` environment variable requirement and making MIPROv2 runnable via `--api-key sk-ant-...` from any shell. V32.1 independently confirmed the write-back injection path is live and delivering optimized instructions to agents at spawn time. The corpus projection (R32.1) shows +8 to +12 points expected delta for research-analyst — the API call is justified. All code-side blockers are now resolved. The only remaining blocker for MIPROv2 execution is Tim providing an API key.

---

## Findings Summary

| ID | Title | Verdict | Severity | Impact |
|----|-------|---------|----------|--------|
| F32.1 | Correct CLAUDE.md injection description | FIX_APPLIED | High | CLAUDE.md now accurately describes write-back mechanism; mortar.md line 277 clarified as secondary path |
| V32.1 | DSPy write-back injection confirmed active in agent system prompt | HEALTHY | Low | Confirmed: full .md body is system prompt; DSPy block present and non-empty in quantitative-analyst.md |
| F32.2 | configure_dspy() api_key parameter added | FIX_APPLIED | Low | `--api-key` CLI arg + `configure_dspy(api_key=None)` parameter — MIPROv2 now runnable without env var |
| M32.1 | Ollama Backend Monitor Target Added | DONE | Low | `ollama_backend_reachable` monitor entry in monitor-targets.md; current status OFFLINE |
| R32.1 | Expected MIPROv2 Score Improvement for research-analyst | HEALTHY | Info | +8 to +12 pts projected delta; API run justified; 57 records at 500-char median question_text |
| V32.2 | writeback_optimized_instructions() edge-case correctness | HEALTHY | Low | Idempotent replace confirmed; missing .md gracefully skipped; empty instructions protected |

---

## Key Discoveries

### F32.1 — Documentation Corrected

The false claim "Mortar injects optimized prompts on specialist invocation automatically" has been replaced in CLAUDE.md with the accurate description: `run_optimization.py` writes the optimized `signature.instructions` back into agent `.md` files under a `## DSPy Optimized Instructions` delimited section at optimization time; agents receive these instructions in their system prompt on every spawn (code-enforced, no runtime lookup required). The `mortar.md` line 277 directive now has a clarifying parenthetical identifying it as a secondary/backup path, with write-back as primary.

### V32.1 — End-to-End Injection Confirmed

The optimization loop is validated end-to-end:
1. MIPROv2 runs and saves `quantitative-analyst.json` with a `signature.instructions` field
2. `writeback_optimized_instructions()` reads that field and writes it into `quantitative-analyst.md` under the `## DSPy Optimized Instructions` block
3. Claude Code reads the full `.md` body as the agent system prompt (confirmed via official docs + direct file inspection)
4. The spawned `quantitative-analyst` agent therefore receives the optimized instructions on every invocation

This closes the loop from training data → MIPROv2 → JSON → .md write-back → system prompt. V32.1 HEALTHY is the end-to-end validation finding.

### F32.2 — Last Code Blocker Removed

The `ANTHROPIC_API_KEY` environment variable is no longer required. The run command is now:

```bash
cd C:/Users/trg16/Dev/Bricklayer2.0
python masonry/scripts/run_optimization.py research-analyst --api-key sk-ant-... --num-trials 10 --valset-size 25 --signature research
python masonry/scripts/run_optimization.py karen --api-key sk-ant-... --num-trials 10 --valset-size 25 --signature karen
```

11 tests cover the new parameter (8 in `test_optimizer.py`, 3 in `test_run_optimization.py`).

### R32.1 — Run Is Worth the Cost

Corpus analysis of the 57 research-analyst records shows a clear length-quality correlation (Pearson r=0.66 for `question_text` length vs. score). Records at 350+ chars score an estimated 72–78 vs. 60 for short records. The pre-enrichment baseline used ~88-char title-only inputs; the post-F29.1 corpus median is 500 chars. Projected MIPROv2 delta: **+8 to +12 points** above the 68.3% Wave 23 baseline, with 70%+ expected score. This justifies the API cost.

---

## DSPy Pipeline State

**What works:**
- Training data corpus: 606 records, stable (V30.1 HEALTHY)
- MIPROv2 bootstrapping: functional (Wave 23 baseline)
- Signature dispatch: fixed — karen gets KarenSig, others get ResearchAgentSig (F30.5)
- Evidence quality metric gate: content-signal-aware (Wave 25)
- Synthetic negatives: persistent, committed (Wave 29)
- Question_text enrichment: 500-char median for research-analyst (Wave 29)
- PreToolUse:Agent hook: live, CWD fixed (F30.1)
- Injection path: write-back mechanism CONFIRMED (F31.1 + V32.1 HEALTHY)
- `configure_dspy(api_key=...)`: available (F32.2)
- CLAUDE.md: accurate description (F32.1)

**What remains to execute:**
- **MIPROv2 run for research-analyst and karen**: User provides `--api-key sk-ant-...` and runs both optimization commands. This is the only remaining step.

**What is at risk:**
- Ollama backend: OFFLINE (M32.1) — semantic routing degraded, all routing hits LLM layer
- Slot collision under parallel same-type spawns (R30.1 WARNING) — dormant, monitoring only

---

## Open Issues (Priority Order)

1. **HIGH: Execute MIPROv2 optimization runs.** All code blockers resolved (F32.2). Corpus confirmed ready (R32.1: 57 records, 500-char median, +8 to +12 pts projected). Run command:
   ```bash
   python masonry/scripts/run_optimization.py research-analyst --api-key sk-ant-... --num-trials 10 --valset-size 25 --signature research
   python masonry/scripts/run_optimization.py karen --api-key sk-ant-... --num-trials 10 --valset-size 25 --signature karen
   ```
   Expected: `masonry/optimized_prompts/research-analyst.json` + write-back to `research-analyst.md`; karen equivalent.

2. **MEDIUM: Restore Ollama at 192.168.50.62:11434** (M32.1). Semantic routing currently falls through to the LLM layer on every dispatch. Monitor entry is in place.

3. **LOW: Slot collision monitoring** (R30.1). Zero collisions post-activation. Escalate only if parallel same-type spawns begin.

---

## Metric Baseline

- Current best score: 68.3% (Trial 3, Wave 23, quantitative-analyst)
- research-analyst projected score after enriched MIPROv2: **70-80%** (R32.1)
- Corpus state: 606 records (research-analyst: 57, karen: 301 + 5 synthetics)
- Optimization: **READY TO RUN** — all code blockers resolved, api_key CLI arg available
- Injection: **CONFIRMED CODE-ENFORCED** (V32.1 HEALTHY)

---

## Wave 33 Priorities

Wave 33 should execute the optimization runs if an API key is available, validate the results end-to-end, and assess whether any downstream adjustments are needed:

1. **Execute MIPROv2 runs** — user provides API key; both agents optimized and written back.
2. **Validate research-analyst.json output** — confirm `instructions` field non-empty, score meets threshold.
3. **End-to-end agent behavior validation** — spawn the optimized research-analyst on a real question; confirm the DSPy block is active in the response pattern.
4. **Corpus expansion** — with inject confirmed, assess whether adding more training examples would further improve scores, or whether corpus size is adequate.
5. **Restore Ollama** — semantic routing needs the embedding backend.

---

## Recommendation

**CONTINUE**

The DSPy optimization pipeline is fully built and validated. The write-back injection mechanism works (V32.1). Documentation is accurate (F32.1). The CLI is ready (F32.2). Corpus quality is high (R32.1: +8 to +12 pts projected). The only remaining step is Tim providing an API key so MIPROv2 can run. Wave 33 should execute the optimization and close the loop.
