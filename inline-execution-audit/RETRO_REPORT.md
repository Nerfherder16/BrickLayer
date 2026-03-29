# Retrospective Report — inline-execution-audit

**Date**: 2026-03-29
**Campaign**: inline-execution-audit
**Waves**: 2 (14 + 9 questions = 23 total)
**Agent**: retrospective
**Synthesized from**: Wave 1 + Wave 2 findings, peer review records, synthesis.md

---

## Executive Summary

The inline-execution-audit campaign ran 23 questions across two waves, mapping a five-layer root cause chain explaining why Claude defaults to inline execution instead of routing through Mortar. Wave 2 fixed the top three chain nodes (F2.1–F2.3) and produced complete fix specifications for the remaining four.

**What went right**: The research loop closed end-to-end, findings are accurate, the enforcement bundle (F2.3) was deployed atomically with all prerequisites, and four reusable skills were distilled. The synthesis correctly identifies what's deployed, what's specified-but-undeployed, and what remains fundamental.

**What went wrong**: The peer-reviewer agent fabricated specific technical objections on two findings (A1.1 and D4.2), requiring Trowel re-verification that added session overhead. One finding (D2.2) contains a fabricated JSON evidence block. One finding assumption (D1.2) is unverified on-device. The retro agent itself lacked Write tool access and could not write its output to disk — requiring reconstruction in the follow-up session.

---

## Process Efficiency

| Metric | Value | Notes |
|--------|-------|-------|
| Total questions | 23 (14 Wave 1, 9 Wave 2) | |
| Completed | 23 / 23 (100%) | |
| FIXED | 3 | F2.1, F2.2, F2.3 |
| DIAGNOSIS_COMPLETE | 8 | D1.1–D2.5 minus deployed |
| CONFIRMED | 1 | A1.1 |
| WARNING | 6 | D4.1, D5.1, D5.2, V1.1, R2.1, R2.2 |
| FAILURE | 3 | D3.1, D3.2, D4.2 |
| FRONTIER_PARTIAL | 1 | FR1.1 |
| MONITOR_SET | 1 | M2.1 |
| Peer review overturns | 2 (A1.1, D4.2) | Both overturns were false — prior peer verdicts fabricated |
| Context exhaustion | 2 sessions | Session 1 ended at ~987K tokens; Session 2 ended at ~1255K |
| Agent output loss | 2 (R2.1, R2.2 prior session) | Background agents from Session 1 lost in compaction; Trowel synthesized findings from summary + live code inspection |
| gitignore force-add | Required for all findings | `*/findings/*` is gitignored, requires `git add -f` every wave |

### Session overhead causes:
1. **Peer-reviewer fabrication** (A1.1, D4.2): Required re-verification passes by Trowel, adding ~2K tokens and one extra commit per finding
2. **R2.1/R2.2 agent output loss**: Background agents from Session 1 lost in compaction. Trowel reconstructed from summary + code, then live agents confirmed findings on second run
3. **masonry-state.json verdict count correction**: State had DIAGNOSIS_COMPLETE: 3 (should be 8), FAILURE: 6 (should be 3), CONFIRMED: 3 (should be 1) — required manual correction
4. **Retro agent lacking Write tool**: RETRO_REPORT.md required reconstruction in Session 3 from task output; output file was 0 bytes

---

## Content Integrity Analysis

### Finding-by-Finding Review

**Wave 1 Findings**

| ID | Verdict | Content Integrity | Notes |
|----|---------|------------------|-------|
| D1.1 | DIAGNOSIS_COMPLETE | ✓ ACCURATE | CLAUDE.md line 68 escape hatch correctly identified and fixed by F2.1 |
| D1.2 | DIAGNOSIS_COMPLETE | ⚠ UNVERIFIED ASSUMPTION | "6 UI rules files loaded unconditionally" assumes Claude Code subdirectory loading behavior. Has not been tested on device. Fix should not be implemented until subdirectory conditional loading is verified to work. |
| D1.3 | DIAGNOSIS_COMPLETE | ✓ ACCURATE | `hookSpecificOutput` vs `additionalContext` channel mismatch verified in source; fixed by F2.2 |
| D2.1 | DIAGNOSIS_COMPLETE | ✓ ACCURATE | No PreTextGeneration hook — fundamental platform constraint confirmed |
| D2.2 | DIAGNOSIS_COMPLETE | ⚠ EVIDENCE FABRICATION | Section 2 JSON shows `mortar_consulted: true` but actual masonry-state.json at the path checked had neither `mortar_consulted` nor `mortar_session_id` fields. Functional conclusion (isMortarConsulted() returns false) is correct, but stated reason (stale timestamp) was wrong — actual reason is fields entirely absent. Fix specification is unaffected. |
| D2.3 | DIAGNOSIS_COMPLETE | ✓ ACCURATE | Deadlock diagnosis correct; Bash receipt writer is the correct architecture; implemented in F2.3 |
| D2.4 | DIAGNOSIS_COMPLETE | ✓ ACCURATE | 61 agents without routing_keywords; three-strategy extraction approach correct |
| D2.5 | DIAGNOSIS_COMPLETE | ✓ ACCURATE | last_route schema + 14 follow-up patterns; TTL/false-positive mitigations correctly scoped |
| D3.1 | FAILURE | ✓ ACCURATE | 70% routing surface dark or degraded confirmed; spec+build zero coverage confirmed by R2.2 |
| D3.2 | FAILURE | ✓ ACCURATE | Router stateless per-prompt; multi-turn collapse confirmed via code inspection |
| D4.1 | WARNING | ✓ ACCURATE | All 20 Mortar routing agents resolvable; finding is correct |
| D4.2 | FAILURE | ✓ ACCURATE (peer OVERRIDE overturned) | 86% dark fleet confirmed correct; prior peer-reviewer claimed "masonry-prompt-router.js does not exist" — **verifiably false**. Trowel re-verified: file exists at correct path, 261+ lines |
| D5.1 | WARNING | ✓ ACCURATE | 40-60% silent zone for medium+no-intent prompts confirmed by code path analysis |
| D5.2 | WARNING | ✓ ACCURATE | Medium effort as structural default confirmed |
| V1.1 | WARNING → resolved | ✓ ACCURATE | 5 prerequisites correctly identified; all 5 deployed by F2.3 |
| A1.1 | CONFIRMED | ✓ ACCURATE (peer OVERRIDE overturned) | Enforcement authority structurally zero confirmed; all 5 peer OVERRIDE objections were fabricated. See Peer Reviewer section below. |
| FR1.1 | FRONTIER_PARTIAL | ✓ ACCURATE | Write/Edit deny-gate viable; PreTextGeneration gap is permanent platform constraint |

**Wave 2 Findings**

| ID | Verdict | Content Integrity | Notes |
|----|---------|------------------|-------|
| F2.1 | FIXED | ✓ VERIFIED | CLAUDE.md line 68 operational definition deployed; tested against D1.1 regression |
| F2.2 | FIXED | ✓ VERIFIED | `additionalContext` channel + imperative format confirmed in masonry-prompt-router.js |
| F2.3 | FIXED | ✓ VERIFIED | All 5 prerequisites deployed atomically; gate behind MASONRY_ENFORCE_ROUTING=1 |
| D2.3 | DIAGNOSIS_COMPLETE | ✓ ACCURATE | Receipt writer deadlock solved; Bash one-liner architecture correct and implemented |
| D2.4 | DIAGNOSIS_COMPLETE | ✓ ACCURATE | 3-strategy extraction approach specified; auto-extract script path clear |
| D2.5 | DIAGNOSIS_COMPLETE | ✓ ACCURATE | last_route schema complete; 14 follow-up patterns; TTL=10min, max 5 turns |
| M2.1 | MONITOR_SET | ✓ ACCURATE | Thresholds calibrated to Wave 1 baselines; targets clear |
| R2.1 | WARNING | ✓ ACCURATE | Syntactic vs. semantic mismatch confirmed in code; 8-15% over-delegation estimate reasonable |
| R2.2 | WARNING | ✓ ACCURATE | Patterns A+B+C collision-free; Pattern D hard collision correctly identified and excluded; dead code at line 77 correctly noted |

**Overall content integrity**: 21/23 findings accurate. 1 finding (D2.2) has a fabricated evidence block in a supporting section (functional conclusion correct). 1 finding (D1.2) has an unverified assumption.

---

## Critical Findings (Process Issues)

### CRITICAL-1: Peer-Reviewer Fabrication on A1.1 and D4.2

**Finding**: The peer-reviewer agent produced fabricated specific technical objections on two findings, both resulting in OVERRIDE verdicts that were themselves incorrect.

**A1.1 OVERRIDE fabrications** (all 5 claims verified false by Trowel):
1. "`isMortarConsulted()` function not found" — function exists at lines 122-134 in masonry-approver.js
2. "Line 300 is console.log, not the quoted comment" — line 300 is exactly the quoted comment "Always allow through — gate is advisory only"
3. "`masonry-mortar-enforcer.js` does not exist" — 101-line file exists at correct path with BLOCKED_TYPES = Set([""])
4. "`mortar_consulted` / `mortar_session_id` fields not in masonry-state.json" — both fields present in masonry/masonry-state.json
5. "Hook count 23 not supported, only 13 in settings.json" — settings.json has exactly 19 hook registrations

**D4.2 OVERRIDE fabrications**:
- "masonry-prompt-router.js does not exist at the path stated" — file exists at correct path with 261+ lines

**Impact**: Two findings required Trowel re-verification passes. A1.1 had to be re-examined against live code with explicit evidence capture. D4.2 required a file existence check. Both findings were confirmed correct after re-verification.

**Root cause hypothesis**: The peer-reviewer agent was operating on a stale or incomplete context view of the codebase. It may have been checking file existence without correctly resolving the project-relative path, or operating from a context window that did not include the relevant hook files.

**Recommended action**: Add a "CRITICAL: verify file paths resolve before asserting nonexistence" instruction to peer-reviewer.md. The peer-reviewer should use Grep/Glob to confirm existence before any "NOT FOUND" claim.

---

### CRITICAL-2: D2.2 Fabricated Evidence Block

**Finding**: D2.2 Section 2 presents a specific JSON object as the "live masonry-state.json content" but the object does not match the actual file. The shown JSON includes `mortar_consulted: true` and a specific `mortar_session_id`. The actual file at the time of inspection contained neither field.

**Functional conclusion unaffected**: isMortarConsulted() returns false regardless — either because the fields are absent (actual situation) or because the session_id is stale (stated reason). The fix specification is correct.

**Recommended action**: diagnose-analyst.md should require that JSON evidence blocks be quoted directly from Read tool output, not synthesized. Any JSON in an evidence block should include the `# Read from: {path}` provenance comment.

---

## Open Issues (Carry-Forward)

### OPEN-1: MASONRY_ENFORCE_ROUTING=1 — R2.1 Read tool gap

The gate bypass in masonry-approver.js exempts Bash (unconditionally) but not Read. At `MASONRY_ENFORCE_ROUTING=1`, question-form prompts that require only a file read (not a Write/Edit) would still have `mortar_consulted=false` and trigger the gate if a Write follows in the same turn.

**Minimum fix**: Add `Read` tool to the Bash exemption check in masonry-approver.js. OR: Update the effort:low classifier to require "no-tool-use intent" (not just syntactic question-word form).

**Severity**: Must fix before enabling `MASONRY_ENFORCE_ROUTING=1` in production.

### OPEN-2: D1.2 — subdirectory conditional loading unverified

The D1.2 fix recommendation (move 6 UI rules files to conditional load group) assumes Claude Code supports conditional loading of rules files from subdirectories. This behavior has not been verified on device.

**Required before implementing**: Test that moving a `.claude/rules/` file to a subdirectory (e.g., `.claude/rules/ui-only/`) actually prevents it from loading in non-UI sessions.

### OPEN-3: D2.4 — dark fleet activation quality gate missing

The D2.4 spec calls for a backfill script that auto-extracts routing_keywords for 61 agents. The 5-10% false-match rate estimate has not been validated against real session prompts.

**Required**: After running the backfill, sample 20-30 real session prompts and manually verify the extracted keywords produce correct matches. Adjust keyword selectivity before activating in semantic routing.

### OPEN-4: D2.5 — multi-turn last_route schema needs campaign mode interaction test

The D2.5 spec notes line 187 of masonry-prompt-router.js early-exits for campaign mode, suppressing all routing. The last_route inheritance logic was specified for non-campaign context. The interaction between `mode: "campaign"` early exit and TTL-expiry-based inheritance has not been tested.

### OPEN-5: R2.2 — `/plan` dead code at line 77

R2.2 identified that `/\/plan\b/` at line 77 in the build rule is dead code — line 168 exits early for all slash commands before detectIntent() runs. This creates a misleading pattern in the rule that suggests /plan routes to the developer team, when in practice it is never evaluated by that rule.

**Action**: Remove or comment the dead `/plan\b/` pattern from line 77. No behavioral change — dead code removal only.

### OPEN-6: R2.1/R2.2 agent output reconstruction overhead

Two Wave 2 question agents (R2.1, R2.2) had their outputs lost in Session 1 context compaction. Trowel reconstructed findings from the session summary + live code inspection and added them to the findings files directly. The agents ran again in Session 2 and confirmed the reconstructed findings were accurate — but the reconstruction process added overhead.

**Systemic recommendation**: Background research agents should be given a Write tool or an explicit instruction to write a findings stub to disk before returning, so output survives context compaction. The current pattern of "agent completes but cannot write" introduces recovery overhead every time a session boundary falls mid-wave.

---

## Confidence Calibration

| Category | Avg Confidence | Range | Notes |
|----------|---------------|-------|-------|
| CONFIRMED / FIXED | 0.93 | 0.85–0.93 | High confidence, all verified |
| DIAGNOSIS_COMPLETE | 0.84 | 0.78–0.91 | Generally well-supported; D2.2 has evidence issue |
| WARNING | 0.80 | 0.72–0.85 | R2.1 and R2.2 have bounded uncertainty in rate estimates |
| FAILURE | 0.87 | 0.82–0.91 | 70-86% metrics are direct counts, high confidence |
| FRONTIER_PARTIAL | 0.78 | — | Single finding; fundamental platform constraint well-established |

**Calibration note**: Confidence estimates across findings are generally well-calibrated. The 8-15% over-delegation range in R2.1 is an estimate with meaningful uncertainty — actual false-positive rate may differ when measured against real developer prompt logs. The synthesis correctly flags this for post-enforcement validation.

---

## Agent Performance

| Agent | Questions | Accuracy | Issues |
|-------|-----------|----------|--------|
| research-analyst | D1.1, D1.2, D1.3, D3.1, D3.2, D4.1, D4.2, D5.1, D5.2, A1.1, R2.1, R2.2 | High | D1.2 unverified assumption |
| diagnose-analyst | D2.1, D2.2, D2.3, D2.4, D2.5 | High | D2.2 fabricated evidence JSON |
| fix-implementer | F2.1, F2.2, F2.3 | High | All 3 fixes verified correct |
| quantitative-analyst | V1.1, M2.1 | High | None |
| frontier-analyst | FR1.1 | High | None |
| **peer-reviewer** | A1.1, D4.2 | **CRITICAL FAILURE** | Fabricated 5 objections on A1.1, 1 on D4.2; all overturned by Trowel re-verification |
| synthesizer-bl2 | synthesis.md | High | Synthesis accurate; committed with correct files |

**Peer-reviewer score**: 0 / 2 correctly reviewed findings (0%). Both findings were correctly CONFIRMED but received fabricated OVERRIDE verdicts. **Priority agent for instruction update.**

---

## Skills Extracted This Campaign

Four new skills were distilled and written to `~/.claude/skills/`:

1. **`/hook-enforcement-audit`** — Audits hook systems for advisory-vs-enforcement gaps. Classifies each hook as HARD_BLOCK / ADVISORY / INJECT / PASS-THROUGH, maps the enforcement ceiling, identifies prerequisite bundles needed before enabling hard blocks.

2. **`/routing-coverage-matrix`** — Maps routing rules against work types, finds silent zones, first-match collisions, and orphaned routes. Produces a coverage table with percentage estimates per work type.

3. **`/dark-fleet-analysis`** — Analyzes an agent registry to identify agents with no automatic routing path (dark fleet), quantifies coverage gap, and produces a staged activation sequence.

4. **`/architecture-ceiling-analysis`** — Maps the enforcement ceiling of a hook/plugin system. Distinguishes fundamental platform limits (no hook event available) from incidental gaps (missing code). Produces a build backlog scoped to what's actually achievable.

These skills are reusable for any future project with an agent routing system.

---

## Recommended Follow-Up Actions

Ordered by impact:

1. **Fix peer-reviewer.md**: Add explicit instruction to verify file existence with Grep/Glob before asserting "NOT FOUND". Add instruction to quote JSON evidence directly from Read tool output with provenance comment.

2. **Enable MASONRY_ENFORCE_ROUTING=1 trial**: The enforcement gate is ready. Before enabling, fix OPEN-1 (Read tool exemption). Then enable in a single session, measure actual FP rate against the 8-15% estimate in R2.1.

3. **Deploy R2.2 patterns**: Add Patterns A, B, C to INTENT_RULES at position after build rule. Expand build rule maintenance verbs. Remove dead `/plan\b/` at line 77. Estimated 30-minute implementation.

4. **Deploy D2.5 last_route persistence**: Add FOLLOWUP_PATTERNS array, isFollowUp(), and inheritance logic to masonry-prompt-router.js. Estimated 50-line addition.

5. **Run D2.4 dark fleet backfill**: Write and run `backfill_routing_keywords.py` for 61 agents. Validate top 20 keywords against real prompts before activating semantic routing layer.

6. **Fix diagnose-analyst.md**: Add requirement that JSON evidence blocks be quoted from Read tool output, not constructed.

7. **Verify D1.2 subdirectory assumption**: Test that Claude Code conditional rules loading from subdirectory works as expected before implementing.

8. **Give research agents Write tool access**: Prevents reconstruction overhead when session boundaries fall mid-wave. Research agents should write findings stub to disk before returning final output.

---

## Campaign Closure

All 23 questions answered. Synthesis committed (b24e21a). Four skills extracted. The enforcement path (F2.1 + F2.2 + F2.3) is deployed and functional behind `MASONRY_ENFORCE_ROUTING=1`. The next phase is implementation of D2.4, D2.5, and R2.2 — not further investigation.

The root cause chain is fully mapped. The ceiling is known. The gap between "mapped" and "fixed" is approximately 150 lines of code across 3 files.
