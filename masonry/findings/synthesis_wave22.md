# Wave 22 Synthesis -- Masonry Self-Research

**Wave**: 22
**Status**: PARTIAL (4/5 questions answered, R22.2 deferred by user)
**Date**: 2026-03-21
**Questions**: 5 total -- 1 FIX_APPLIED (success), 1 DIAGNOSIS_COMPLETE (success), 1 WARNING (partial), 1 PENDING (deferred)

## Questions Answered

| ID | Verdict | Summary |
|----|---------|---------|
| F22.1 | FIX_APPLIED | Ollama backend wired into optimizer.py: `configure_dspy(backend="ollama", model="qwen3:14b")` works across all three entry points (optimizer.py, run_optimization.py CLI, mcp_server/server.py) |
| R22.1 | WARNING | Smoke test PASSED -- qwen3:14b produces valid structured output via DSPy ChainOfThought (all 5 fields populated). But `configure_dspy(backend="ollama")` defaults to model="claude-sonnet-4-6", which Ollama rejects. Caller must pass model explicitly. |
| D22.1 | DIAGNOSIS_COMPLETE | confidence_calibration band [0.5, 0.95] in score_findings.py:178 creates a 30-point cliff for confidence > 0.95. 77 findings affected, 40 training records suppressed (14.4% of training volume). Fix: widen to [0.5, 1.0]. |
| R22.2 | PENDING | Full MIPROv2 trial deferred -- user pause requested. Blocked on configure_dspy default model fix. |

## Campaign Milestone: DSPy + Ollama Pipeline End-to-End FUNCTIONAL

The smoke test (R22.1) confirms the DSPy optimization pipeline can produce structured output through the local Ollama server using qwen3:14b. This resolves the primary uncertainty from Wave 21 (R21.1). The pipeline path is:

```
build_dataset() -> dspy.ChainOfThought(ResearchAgentSig) -> ollama_chat/qwen3:14b -> structured output
```

All five defined output fields (verdict, severity, confidence, evidence, mitigation) were populated in a single-prediction run. The evidence field was 380 chars and the mitigation field 392 chars -- both above quality thresholds.

## Critical Findings (must act)

1. **R22.1** [WARNING] -- `configure_dspy(backend="ollama")` defaults to model="claude-sonnet-4-6"
   Fix: Change the default model parameter to "qwen3:14b" when backend="ollama", or require the model parameter when backend != "anthropic". This is a 1-line fix in optimizer.py line 38. Without this fix, every Ollama-backend call that omits the `model` argument will fail with a 404.

## Significant Findings (important but not blocking)

1. **D22.1** [DIAGNOSIS_COMPLETE] -- confidence_calibration cliff at 0.95 suppresses 14.4% of training volume
   The [0.5, 0.95] band in `_score_confidence_calibration()` at score_findings.py:178 gives only 10/40 points to any finding with confidence > 0.95. This is a cliff, not a gradient -- 0.95 scores 40/40 while 0.96 scores 10/40. The existing severity-match logic already handles overconfidence for low-stakes findings. Fix spec is complete: widen to [0.5, 1.0] on line 178. Secondary fix in optimizer.py:60 changes the center-bias formula from `1 - |conf - 0.75|` to a flat [0.7, 1.0] acceptance band.

## Healthy / Verified

- **F22.1**: Ollama backend fully wired into optimizer.py, run_optimization.py CLI (`--backend ollama`), and mcp_server/server.py. All three entry points verified with signature inspection.
- **DSPy + Ollama connectivity**: Ollama server at 192.168.50.62:11434 confirmed reachable with qwen3:14b available.
- **Training data**: 136 scored training examples across 6 agents via build_dataset(), including 42 for research-analyst.

## Training Data Health (End of Wave 22)

| Metric | Wave 21 | Wave 22 | Change |
|--------|---------|---------|--------|
| Total training records (scored_all) | 435 | 435 | Stable |
| Training-ready (score >= 60) | 278 | 278 | Stable (318 after D22.1 fix) |
| Suppressed by confidence cliff | 40 | 40 | Fix spec ready |
| Vigil verdict | HEALTHY | HEALTHY | Stable |
| Vigil thorns | 0 | 0 | Stable |
| DSPy Ollama smoke test | Unverified | PASSED | Resolved |

## Open Issues (Carried Forward)

1. **R22.1 default model** -- `configure_dspy(backend="ollama")` must not default to "claude-sonnet-4-6". 1-line fix in optimizer.py:38.

2. **D22.1 confidence band** -- score_findings.py:178 needs `[0.5, 1.0]` to stop suppressing 40 training records. Fix spec complete with verification commands.

3. **R22.2 full MIPROv2 trial** -- Deferred by user pause. Unblocked once R22.1 default model is fixed. quantitative-analyst has 125 training records ready.

## Recommendation

**CONTINUE**

Two targeted fixes remain before the DSPy pipeline is production-ready: (1) the configure_dspy default model (trivial, 1 line) and (2) the confidence_calibration band (1 line, fix spec complete). After those, R22.2 (full MIPROv2 trial) is the validation gate for the entire optimization pipeline. These are implementation tasks with complete specifications -- Wave 23 should execute all three.

## Next Wave Hypotheses

1. Fix configure_dspy() default model to "qwen3:14b" when backend="ollama" (F-class, from R22.1)
2. Apply confidence_calibration band fix [0.5, 1.0] in score_findings.py:178 (F-class, from D22.1)
3. Run R22.2: full MIPROv2 optimization for quantitative-analyst via Ollama -- measure pre/post score delta
4. After MIPROv2 trial: does the optimized prompt produce measurably different verdicts on held-out questions vs. the unoptimized baseline?
5. Does source-tagging masonry vs. ADBP training records improve or degrade DSPy optimization quality? (carried from Wave 21)
