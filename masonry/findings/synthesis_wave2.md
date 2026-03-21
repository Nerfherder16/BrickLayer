# Synthesis — Masonry Self-Research Wave 2

**Campaign type**: BrickLayer 2.0
**Wave**: 2
**Questions**: 9 (F: 2, D: 3, R: 2, V: 1, M: 1 — all DONE)
**Date**: 2026-03-21

---

## Executive Summary

Wave 2 completed 9 questions with 6 FAILURE verdicts, 1 HEALTHY, 1 COMPLETE (monitor), and 1 DIAGNOSIS_COMPLETE pair. The dominant themes are: (1) the double-fire hook problem is broader than Wave 1 found — it affects every event type, not just PostToolUse; (2) Layer 3 (LLM routing) is empirically confirmed dead on this machine, with all three measured runs exceeding the 8-second timeout; (3) the V1.5 fix specification had two uncovered attack vectors (relative-path bypass for directory patterns, and complete Bash tool bypass); (4) the DSPy drift detector has correctness defects for new agents and non-standard verdicts; and (5) Stop hooks run in parallel, refuting D1.5's sequential short-circuit hypothesis.

---

## Verdicts Table — Wave 2

| ID | Question (short) | Verdict | Severity |
|----|-----------------|---------|----------|
| F2.1 | Minimum safe fix for double-fire: global settings.json is strict superset | DIAGNOSIS_COMPLETE | High |
| F2.2 | V1.5 path blocklist: relative-path bypass + Bash vector unblocked | FAILURE | Medium |
| D2.1 | Stop hook execution: parallel, not sequential short-circuit | HEALTHY (refutes D1.5) | — |
| D2.2 | masonry-subagent-tracker: guaranteed race via D1.1 double-fire | FAILURE | Medium |
| D2.3 | DSPy drift detector: baseline=0.0 false negative + UNCALIBRATED misclassification | FAILURE | Low |
| R2.1 | Semantic threshold 0.70 at model's training-data cutoff, not discriminative | FAILURE | High |
| R2.2 | `claude --print` median 10.3s on this machine; 8s timeout confirmed dead | FAILURE | High |
| V2.1 | Bash tool vector completely bypasses V1.5 fix specification | FAILURE | High |
| M2.1 | `_embedding_cache_size` monitor entry created | COMPLETE | — |

---

## Cross-Wave Synthesis

### The Double-Fire Problem Is Systemic (F2.1 + D2.2)

Wave 1 (D1.1) found that observe and guard double-fire on PostToolUse. Wave 2 (F2.1) found this is the entire plugin configuration, not just two hooks. All 10 hook registrations in the plugin `hooks/hooks.json` are exact duplicates of registrations in `~/.claude/settings.json`:

- SessionStart: masonry-session-start fires twice per session
- UserPromptSubmit: masonry-register fires twice per prompt
- PreToolUse ExitPlanMode: masonry-context-safety fires twice per plan exit
- PostToolUse Write/Edit: observe + guard each fire twice
- PostToolUseFailure: masonry-tool-failure fires twice
- SubagentStart: masonry-subagent-tracker fires twice (D2.2 race)
- Stop: stop-guard + build-guard + ui-compose-guard each fire twice

The minimum safe fix (F2.1) is to empty the plugin's `hooks` object — the global settings.json provides a strict superset including masonry-approver, masonry-lint-check, masonry-design-token-enforcer, masonry-context-monitor, masonry-tdd-enforcer, and masonry-session-summary. No coverage is lost.

**F2.1 is the highest-priority single change in the codebase** — it resolves D1.1, D1.2 (race amplified by double-fire), D1.4, D2.2 (SubagentStart race), and eliminates duplicate Stop output, all at once.

### Layer 3 Is Dead on This Machine (R2.2 + D1.6)

Two independent confirmed failures make Layer 3 (LLM routing) non-functional:

1. **R2.2** (empirical): All three measured `claude --print` invocations exceeded the 8-second timeout (10.0s, 10.3s, 14.0s). Layer 3 times out and falls to Layer 4 on every call.

2. **D1.6** (code analysis): `shlex.quote + shell=True` on Windows cmd.exe produces POSIX single-quote escaping that cmd.exe ignores. Prompts containing apostrophes, `&`, `|`, `>`, `<` are malformed.

The fix for D1.6 (switch to list-form subprocess) reduces latency by ~300ms (cmd.exe startup elimination) but does not fix the fundamental latency issue. The fix for R1.3/R2.2 is to increase `_LLM_TIMEOUT` to 20 seconds on Windows.

**Priority**: D1.6 first (correctness fix), then update `_LLM_TIMEOUT` to 20s on Windows.

### V1.5 Fix Spec Required Three Iterations to Complete (V1.5 → F2.2 → V2.1)

The original V1.5 finding specified a 6-pattern path blocklist. Wave 2 analysis found two additional weaknesses:
- **F2.2**: Directory patterns 5 and 6 (`/[/\\]src[/\\]/`, `/[/\\]docs[/\\]/`) miss relative paths starting with `src/` or `docs/` (no leading separator). Fix: `(?:^|[/\\])` prefix.
- **V2.1**: Bash tool calls pass `file_path = ''`, bypassing the entire blocklist. The V1.5 specification never addressed Bash. Fix: exclude Bash from auto-approval entirely, or scan command string.

The complete, implementation-ready fix:
```javascript
const toolName = (parsed.tool_name || '').toLowerCase();
const filePath = toolInput.file_path || toolInput.path || '';

// Protect Tier 1/2 files from Write/Edit auto-approval
if (approve && isTier1Tier2(filePath)) process.exit(0);

// Never auto-approve Bash during build — command content not reliably analyzable
if (approve && toolName === 'bash') process.exit(0);
```

With `TIER1_TIER2_PATTERNS` updated to use `(?:^|[/\\])` prefixes on the directory patterns.

### Semantic Routing Threshold Needs Structural Fix (R2.1)

The threshold 0.70 was set equal to the model's training-data positive-pair selection cutoff (confirmed from the official Qwen3 paper). For the Masonry registry with 3+ tight semantic clusters (research: 4 agents; audit/review: 5 agents; code/implementation: 4 agents), multiple agents simultaneously score above threshold for domain-consistent queries.

The structural fix is a margin check, not just a threshold adjustment:
```python
sims = sorted(sims, key=lambda x: x[1], reverse=True)
if sims[0][1] >= _DEFAULT_THRESHOLD:
    if len(sims) == 1 or (sims[0][1] - sims[1][1]) >= _MARGIN_THRESHOLD:
        return RoutingDecision(target_agent=sims[0][0].name, ...)
    # margin too thin → fall through to Layer 3
return None
```

Recommended: `_MARGIN_THRESHOLD = 0.05`, pending live calibration data.

### D1.5 Hypothesis Refuted (D2.1)

Wave 1 found D1.5 as FAILURE (stop-guard masking build-guard). Wave 2 (D2.1) confirmed via Claude Code documentation that Stop hooks run in parallel, not sequentially. Exit code 2 from any hook blocks the stop, but ALL hooks run simultaneously and all stderr outputs are collected. D1.5's hypothesis was wrong — the behavior is correct. No fix needed.

D1.5 should be considered HEALTHY per D2.1.

### DSPy Pipeline Correctness (D2.3)

Two defects confirmed:
1. **baseline_score == 0.0 false negative**: New agents with all-FAILURE verdicts report `alert_level = "ok"` — they are never flagged for re-optimization through the drift pathway. This affects every newly onboarded agent until it accumulates a non-zero baseline.
2. **UNCALIBRATED scored as 0.0**: Research-analyst's data-gap findings would penalize it in drift scoring if findings ever gain inline agent attribution.

Both are low-severity defects (current impact limited by finding format lacking agent attribution) but the verdict taxonomy gap is structurally important to address before Wave 3 findings accumulate.

---

## Cumulative Priority Fix Order (Waves 1 + 2)

### P0 — Critical, fix before next session

| ID | Fix | Lines changed |
|----|-----|--------------|
| **F2.1** | Empty `hooks/hooks.json` `hooks` object | ~90 lines removed |
| **D1.6** | Replace `shlex.quote + shell=True` with list-form subprocess in `llm_router.py` | ~8 lines |
| **V1.5 + F2.2 + V2.1** | Complete masonry-approver path blocklist: correct patterns 5+6, add Bash exclusion | ~25 lines added |

### P1 — High value, fix in next maintenance window

| ID | Fix | Lines changed |
|----|-----|--------------|
| **R1.3/R2.2** | `_LLM_TIMEOUT = 20` on Windows (after D1.6) | 2 lines |
| **D1.2** | Atomic rename-based strike counter write in masonry-guard.js | 5 lines |
| **D1.3** | Add logging + CWD fallback in `_load_registry` | 4 lines |
| **R1.5** | Circuit breaker for Ollama semantic layer (fast-fail after 2 consecutive timeouts) | ~30 lines |
| **V1.4** | Registry membership check for `target_agent` in llm_router.py | 5 lines |
| **R2.1** | Add margin check to semantic router (`best - second >= 0.05`) | 8 lines |

### P2 — Polish, address when convenient

| ID | Fix | Lines changed |
|----|-----|--------------|
| **D2.3** | Add UNCALIBRATED to `_PARTIAL_VERDICTS`, DIAGNOSIS_COMPLETE to `_OK_VERDICTS`; fix baseline=0.0 branch | 6 lines |
| **R1.4** | Add 8 missing slash commands to `_SLASH_COMMANDS` | 8 lines |
| **V1.2** | `re.IGNORECASE` + `.lower()` for `_MODE_FIELD_RE` | 2 lines |
| **R1.6** | Add `fallback_reason` field to `RoutingDecision` | 5 lines |
| **D2.2** | File locking or append-only format for `agents.json` | ~20 lines |

### P3 — Track, defer until Wave 3 calibration data available

| ID | Action |
|----|--------|
| **R1.1/R2.1** | Run 20-query calibration script against live Ollama to determine discriminative threshold |
| **D1.7** | Add file locking to `onboard_agent.py` registry append (hook inactive) |
| **V1.3/M2.1** | Monitor `_embedding_cache_size`; add 200-entry size limit if exceeded |

---

## Wave 3 Recommendations

If Wave 3 runs, highest-value questions:

1. **After F2.1 fix applied**: Verify double-fire elimination — trace hook invocation count with a controlled Write tool call
2. **After D1.6 fix applied**: Re-measure Layer 3 latency with list-form subprocess to confirm cmd.exe overhead was the marginal contributor
3. **After masonry-approver fix applied**: Test edge cases: `../` traversal, Windows backslash paths, multi-file Bash commands
4. **R2.1 live calibration**: Run the 20-query benchmark against the actual Ollama/qwen3-embedding:0.6b endpoint with sample Masonry user prompts
5. **DSPy training data integrity**: After Wave 1+2 findings accumulate, verify that `build_dataset()` correctly categorizes the 18+9=27 findings and produces valid training examples for each of the targeted agents
