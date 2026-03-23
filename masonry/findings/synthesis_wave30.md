# Wave 30 Synthesis — Masonry Self-Research

**Wave**: 30
**Date**: 2026-03-23
**Questions answered**: 6
**Net verdicts**: 2 FIX_APPLIED, 1 HEALTHY, 1 BLOCKED, 2 WARNING
**Peer Review Override**: V30.5 FAILURE → WARNING (mortar.md line 277 LLM-honor injection directive confirmed)

---

## Executive Summary

Wave 30's dominant theme was closing infrastructure gaps from Waves 28-29 while auditing the end-to-end viability of the DSPy optimization pipeline. Two fixes landed (CWD slot handoff, signature dispatch table), the training corpus was re-verified as stable and complete, and the MIPROv2 backend blocker persists unchanged. The most important discovery is V30.5 FAILURE: **the optimized prompt injection path does not exist in code** — even if MIPROv2 runs succeed and produce optimized JSON files, no code reads those files when spawning specialist agents. CLAUDE.md's claim that "Mortar injects optimized prompts on specialist invocation automatically" is false. This means the entire optimization pipeline, from training data enrichment (Waves 24-29) through MIPROv2 execution, terminates at a dead end until an injection mechanism is built.

---

## Findings Summary

| ID | Title | Verdict | Severity | Impact |
|----|-------|---------|----------|--------|
| F30.1 | Fix CWD mismatch in preagent/subagent slot handoff | FIX_APPLIED | Medium | Both hooks now use `os.homedir()` for slot path — eliminates spec-writer slot misses from V29.1 |
| V30.1 | F29.1 + F29.2 corpus complete and stable for both MIPROv2 runs | HEALTHY | Info | 606 records, deterministic across reruns, all 5 pre-MIPROv2 readiness criteria met |
| F30.2 | Both MIPROv2 runs still blocked: no LLM backend available | BLOCKED | Medium | Ollama offline, ANTHROPIC_API_KEY not set — unchanged from Wave 29 |
| R30.1 | One-slot-per-type collision risk in masonry-preagent-tracker.js | WARNING | Low-Medium | 0% post-activation collision rate; theoretical risk confirmed by code but unrealized in practice |
| V30.5 | Optimized prompt injection path: LLM-honor only, no code enforcement | WARNING (override from FAILURE) | High | mortar.md line 277 has LLM-honor directive; code-enforced path (hooks/runner/router) is absent |
| F30.5 | Fix optimize_all() signature dispatch | FIX_APPLIED | High | Dispatch table routes karen to KarenSig, others to ResearchAgentSig; 6 tests guard regression |

---

## Key Discoveries

### V30.5 WARNING — Injection Is LLM-Honor Only, Not Code-Enforced (Peer Review Override)

V30.5 originally returned FAILURE; a peer review OVERRIDE corrected it to WARNING after finding that `mortar.md` line 277 contains: "If `masonry/optimized_prompts/{agent_name}.json` exists, read it and inject the optimized instructions into the specialist invocation."

The final picture:

1. MIPROv2 optimization correctly produces JSON files with an `instructions` field (`quantitative-analyst.json` confirmed).
2. `mortar.md` line 277 instructs Mortar to read and inject the optimized prompt when spawning a specialist. This is an **LLM-honor-based** injection path — Mortar as an LLM orchestrator follows this directive when it acts as the dispatcher.
3. **No code-enforced injection exists** — no hook, routing layer, MCP server, or runner reads `optimized_prompts/*.json`. If Mortar is bypassed (direct agent spawn, non-Mortar dispatch), the optimized prompts are not applied.
4. The `AgentRegistryEntry.optimized_prompt` schema field remains a placeholder — never populated or read by code.

The original finding missed mortar.md line 277. The CLAUDE.md claim of "automatic" injection is partially accurate (Mortar follows the directive) but overstated (not code-enforced, not guaranteed under all dispatch paths).

### F30.1 + F30.5 — Two Infrastructure Fixes Land

**F30.1** resolved the V29.1 spec-writer slot-miss by moving both hooks to `os.homedir()` as the base path for pending agent prompt slots. The CWD divergence (preagent hook resolving through `masonry/` subdirectory vs. subagent hook using bare CWD) is eliminated. This should raise prompt capture yield from the 83% observed in V29.1 toward near-100%.

**F30.5** replaced the hardcoded `ResearchAgentSig` in `optimize_all()` with a dispatch table (`_AGENT_SIGNATURES`) that correctly routes karen to `KarenSig` and all other agents to `ResearchAgentSig` as default. This was a carry-forward open issue since Wave 25. Six unit tests guard the dispatch logic.

### R30.1 — Slot Collision Risk Is Real But Dormant

Code inspection confirms the one-slot-per-type overwrite strategy will produce mislabeled training data when two agents of the same type spawn within the 10-second TTL window. However, routing log analysis shows 0% post-F28.3 collision rate (14 starts, no concurrent same-type spawns within the window). The risk is limited to DSPy training signal quality — functional agent behavior is unaffected. Recommended action: monitor; escalate to queue-based slots only if the campaign loop begins dispatching same-type agents in parallel.

---

## DSPy Pipeline State

**What works:**
- Training data corpus: 606 records, stable, enriched (V30.1 HEALTHY)
- MIPROv2 bootstrapping: functional (Wave 23 baseline)
- Signature dispatch: fixed — karen gets KarenSig, others get ResearchAgentSig (F30.5)
- Evidence quality metric gate: content-signal-aware (Wave 25)
- Synthetic negatives: persistent, committed to git (Wave 29)
- Question_text enrichment: 500-char median for research-analyst (Wave 29)
- PreToolUse:Agent hook: live, CWD fixed (F30.1)

**What is broken:**
- **Injection path: LLM-honor only** (V30.5 WARNING) — mortar.md line 277 has a directive to read and inject optimized prompts. Code-enforced injection (via hooks or runner) is absent. Direct spawns bypassing Mortar will not apply optimization.
- **MIPROv2 execution: BLOCKED** (F30.2) — neither Ollama nor Anthropic API available. Ready to run the instant a backend is restored.

**What is at risk:**
- Slot collision under parallel same-type spawns (R30.1 WARNING) — dormant, monitoring only

---

## Open Issues (Priority Order)

1. **V30.5 — HIGH: Harden the injection path from LLM-honor to code-enforced.** `mortar.md` line 277 already provides an LLM-honor injection directive. However, this only works when Mortar is the dispatcher — direct spawns bypass it. Implementation: a PreToolUse or SubagentStart hook that reads `optimized_prompts/{agent_name}.json` and prepends the `instructions` field makes injection unconditional regardless of dispatch path. Also: update CLAUDE.md to accurately describe the injection as "LLM-honor-based via Mortar" rather than "automatic".

2. **F30.2 — HIGH: Unblock MIPROv2 execution.** Set `ANTHROPIC_API_KEY` or restore Ollama at `192.168.50.62:11434`. All data preconditions are met. Run commands are ready:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   cd C:/Users/trg16/Dev/Bricklayer2.0
   python masonry/scripts/run_optimization.py research-analyst --backend anthropic --num-trials 10 --valset-size 25 --signature research
   python masonry/scripts/run_optimization.py karen --backend anthropic --num-trials 10 --valset-size 25 --signature karen
   ```

3. **R30.1 — MEDIUM: Monitor slot collision rate.** No action needed now. If the campaign loop begins dispatching same-type agents in parallel, implement queue-based slots (option b from R30.1 finding). Current collision rate: 0% post-activation.

---

## Metric Baseline

- Current best score: 68.3% (Trial 3, Wave 23, quantitative-analyst)
- Corpus state: 606 records (research-analyst: 57, karen: 301 + 5 synthetics)
- Optimization: F30.2 BLOCKED — both backends unavailable
- Injection: V30.5 WARNING — LLM-honor via mortar.md line 277; code-enforced path absent

---

## Wave 31 Priorities

Wave 31 must address the pipeline's terminal gap before anything else. The correct sequencing:

1. **Harden the injection path** (V30.5 partial resolution). LLM-honor injection exists via mortar.md line 277. A hook-based approach (reading `optimized_prompts/{agent}.json` at SubagentStart) would make injection code-enforced and unconditional, covering direct spawns that bypass Mortar. This is the recommended next step.

2. **Update CLAUDE.md** to accurately describe injection as "LLM-honor-based via Mortar (mortar.md line 277)" rather than "automatic". Code-enforced injection would allow stronger language once implemented.

3. **Unblock and execute MIPROv2 runs** (F30.2 resolution). Only after the injection path exists does running MIPROv2 produce value. Set the API key, run both agents, validate output.

4. **End-to-end validation**: After injection is built and MIPROv2 runs, verify that a spawned agent actually receives the optimized prompt text. This closes the loop from training data through optimization through injection through agent behavior.

The V30.5 finding fundamentally reorders priorities: building the injection path must come before running optimization, not after. All prior waves assumed the injection was already implemented — it was not.

---

## Recommendation

**CONTINUE**

The self-research campaign has identified the single most important gap in the DSPy pipeline: the injection path. Waves 23-29 built everything upstream (training data, scorers, signatures, metrics, synthetic negatives, enrichment). Wave 30 discovered that the downstream consumer — the code that would actually use optimized prompts at runtime — was never built. Wave 31 should implement the injection mechanism, correct documentation, and then (and only then) execute MIPROv2 runs. The campaign is now positioned to close the full optimization loop for the first time.
