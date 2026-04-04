# Wave 1 Synthesis -- inline-execution-audit

**Date**: 2026-03-29
**Questions**: 14 total -- 6 success (5 DIAGNOSIS_COMPLETE + 1 CONFIRMED), 4 partial (WARNING), 3 failed (FAILURE), 1 frontier (FRONTIER_PARTIAL)

---

## Executive Summary

1. **Claude defaults to inline execution because a vague escape hatch ("direct action when trivial") at CLAUDE.md line 68 overrides the absolute Mortar directive via specificity-beats-general, with no operational definition of "trivial."** The model's trained prior treats most text-answer tasks as trivial, swallowing the routing directive (D1.1).

2. **The routing signal is structurally drowned.** The Mortar routing section is 4.8% of 23K-token auto-context; UI-specific rules alone are 12.9x the routing signal volume, loaded unconditionally in every session including non-UI work (D1.2).

3. **Enforcement authority is exactly zero.** 0 of 23 active hooks check routing compliance. The Mortar gate in masonry-approver.js is advisory-only by deliberate design -- the enforcement infrastructure is fully built but the safety pin was never pulled (A1.1, D2.1).

4. **40-60% of developer prompts receive no routing signal at all.** The prompt router's medium+no-intent gate silently drops prompts with maintenance verbs (fix, update, set, make, change), and multi-turn workflows collapse to inline by Turn 2 because the router is stateless per-prompt (D5.1, D5.2, D3.2).

5. **86% of the agent fleet is dark.** 98 of 114 registered agents have no automatic routing path through Mortar. The "every request goes through Mortar" design goal is structurally contradicted by a fleet where only 16 agents are auto-routable (D4.2).

---

## Root Cause Chain

The inline execution default is not a single defect but a compounding chain of five structural failures:

```
D1.1  CLAUDE.md escape hatch ("trivial" undefined, specificity beats absolute)
  |
  +-- D1.2  Context dilution amplifies the escape hatch (routing = 4.8% of context)
  |
  +-- D1.3  Prompt router hint in wrong channel (hookSpecificOutput vs additionalContext)
        |     + annotation format ("->") vs imperative ("You MUST")
        |
        +-- D5.1/D5.2  40-60% of prompts hit silent zone (medium+no-intent gate)
              |
              +-- D3.1  70% of routing surface dark or collision-prone (verb gaps, first-match)
              |
              +-- D3.2  Multi-turn collapse: full signal Turn 1, silence Turn 2+
                    |
                    +-- A1.1  Zero enforcement at any layer (advisory-only gate)
                          |
                          +-- D2.1/D2.2  Receipt pattern exists but writer absent + gate softened
```

**The chain reads:** The escape hatch (D1.1) provides the model-level justification for inline execution. Context dilution (D1.2) lowers the activation threshold for the escape hatch. The prompt router's wrong channel and annotation format (D1.3) mean routing hints that do fire carry no authority. The silent zone (D5.1/D5.2) means 40-60% of prompts never even generate a hint. Coverage gaps (D3.1) and stateless routing (D3.2) mean the hints that do fire are often wrong or absent on follow-up turns. Zero enforcement (A1.1) means none of this is caught -- even correctly-routed hints are advisory suggestions Claude can ignore. The receipt pattern (D2.1/D2.2) that could enforce routing is architecturally present but deliberately softened.

**Result:** Every layer of the routing system -- instruction, context weight, hint injection, intent detection, multi-turn continuity, enforcement -- independently fails to prevent inline execution. The layers compound rather than compensate.

---

## Enforcement Gap Analysis (A1.1 + D2.1 + D2.2 + V1.1)

The enforcement system is best described as **a completed feature with the safety pin still in**.

**What exists:**
- `isMortarConsulted()` function -- fully implemented, reads `mortar_consulted` + `mortar_session_id` from masonry-state.json with 4-hour freshness window
- Gate condition in masonry-approver.js lines 293-301 -- fires correctly on every non-exempt Write/Edit
- Receipt schema fields -- defined in the state file schema
- 7 hooks with genuine hard-blocking capability (file protection, TDD, git hygiene, build continuity)

**What is missing:**
- The block decision: gate outputs `process.stderr.write()` (invisible to model) then allows through. Line 300 comment: "Always allow through -- gate is advisory only."
- Receipt writer: nothing in the hook chain writes `mortar_consulted: true`. The field does not exist in the live state file. `isMortarConsulted()` returns false on every call.
- Per-session isolation: masonry-state.json is a global singleton. Concurrent sessions share and corrupt receipt state.

**Why it cannot be deployed today (V1.1):**
Enabling the hard block without prerequisites produces 100% false-positive rate -- every Write/Edit blocked in every session. Five coordinated prerequisites are required:

| # | Prerequisite | Status | Effort |
|---|-------------|--------|--------|
| 1 | Receipt writer (Mortar writes token after routing) | MISSING | ~15 lines |
| 2 | Per-prompt reset (prompt router resets receipt each turn) | MISSING | ~5 lines |
| 3 | Trivial bypass (effort:low skips the hard block) | MISSING | ~10 lines |
| 4 | Bash scope decision (gate Bash or accept as ungated bypass) | UNRESOLVED | Architectural |
| 5 | CLAUDE.md line 68 fix (operational definition of "trivial") | MISSING | Text change |

**The fundamental constraint:** Claude Code's hook system is gate-based (PreToolUse can allow/deny tool calls) not directive-based (no hook can intercept text generation or force Agent tool invocation). No `PreTextGeneration` hook event exists. Inline text responses are permanently ungated.

---

## Coverage Gap Analysis (D3.1 + D3.2 + D4.2 + D5.1 + D5.2)

### Intent Detection Gaps

The prompt router's INTENT_RULES cover 10 patterns against 10 Mortar work types. Cross-reference reveals:

- **1 work type with ZERO coverage:** "Spec + build" (spec-writer pipeline) -- no INTENT_RULE for `spec`, `plan`, `blueprint`; `/plan` exits before detection via slash-command guard
- **6 work types DEGRADED:** verb gaps (build rule missing `fix`/`update`/`make`/`change`/`set`), first-match collisions (changelog->git-nerd, architecture->architect over research-analyst, debug->diagnose over uiux-master)
- **1 orphaned INTENT_RULE:** refactoring routes to `refactorer` which has no Mortar dispatch row
- **70% of the routing surface (7/10 work types) is dark or collision-prone**

### Silent Zone

The medium+no-intent gate (lines 194-195) silently drops 40-60% of developer prompts. "Medium" effort is defined entirely by exclusion -- zero regex patterns, zero keyword matches. Any prompt >= 50 chars that avoids all trigger vocabulary returns "medium" by structural default.

### Multi-Turn Collapse

The router reads only `input.prompt` and `input.cwd`. Zero conversation history. Zero follow-up detection. Zero routing persistence. A 3-turn workflow produces: full signal (Turn 1) -> complete silence (Turn 2) -> effort-only noise (Turn 3). Campaign mode causes total router blackout (line 187 exit on `mode` set).

### Dark Fleet

114 registered agents. 16 auto-routable (14%). 98 dark (86%). 31 placeholder stubs. The `routing_keywords` field exists in agent_registry.yml specifically for semantic routing but is unpopulated for 80+ agents.

---

## Architecture Ceiling (FR1.1)

| Architecture Target | Feasibility | Gap Type |
|----|----|----|
| Force Agent tool invocation before any response | BLOCKED | No PreTextGeneration hook in Claude Code |
| Intercept inline text responses | BLOCKED | No TextGeneration hook event |
| Multi-turn routing continuity | BLOCKED | Hook payload is single-prompt only |
| Write/Edit deny-gate with routing receipt | VIABLE | 6 incidental code changes (~80 lines) |
| Per-session receipt isolation | VIABLE | Path change + schema update |
| Trivial-task deterministic classifier | VIABLE | ~50 lines |
| Full-fleet routing manifest | VIABLE | Registry population work |
| Campaign-mode routing (remove line 187 exit) | VIABLE | One condition removal |

**3 fundamental gaps** (hook system limits, outside Tim's control). **6 incidental gaps** (missing code, ~80 lines total). **1 architectural decision** (Bash exemption).

The minimum viable architecture is a Write/Edit deny-gate backed by a routing receipt. This enforces file-write compliance but cannot enforce text-generation compliance. The text-generation gap is permanent given the current hook model.

---

## Critical Findings (must act)

1. **D1.1** [DIAGNOSIS_COMPLETE] -- CLAUDE.md line 68 escape hatch overrides absolute Mortar directive; "trivial" undefined
   Fix: Replace vague "direct action when trivial" with scoped definition: "single-sentence factual lookups only"

2. **A1.1** [CONFIRMED] -- Zero routing enforcement across 23 hooks; advisory gate has safety pin in
   Fix: Convert masonry-approver.js lines 293-301 from stderr advisory to hard block (after prerequisites)

3. **D3.1** [FAILURE] -- 70% routing surface dark or degraded; "Spec+build" has zero coverage; 3 first-match collisions
   Fix: Add spec-writer INTENT_RULE; expand build rule verb set; implement multi-intent detection

4. **D4.2** [FAILURE] -- 86% of 114 agents are dark fleet with no routing path
   Fix: Populate `routing_keywords` for 80+ agents; expand Mortar dispatch table beyond 10 categories

5. **D3.2** [FAILURE] -- Router stateless per-prompt; multi-turn workflows collapse by Turn 2
   Fix: Add `last_route` persistence field; implement follow-up detection patterns

---

## Significant Findings (important but not blocking)

1. **D1.2** [DIAGNOSIS_COMPLETE] -- Routing signal is 4.8% of 23K context; UI rules 12.9x volume; context dilution amplifies escape hatch
   Fix: Move 6 UI rules files to conditional load group (verify Claude Code subdirectory behavior first)

2. **D1.3** [DIAGNOSIS_COMPLETE] -- Prompt router uses wrong output channel (hookSpecificOutput vs additionalContext) and annotation format
   Fix: Switch to `additionalContext` channel; rewrite hint in imperative format

3. **D5.1** [WARNING] -- Build rule missing maintenance verbs; 30-45% of prompts in silent zone
   Fix: Add `fix|update|make|change|set|configure|apply|enable|disable|modify` to build rule verb set

4. **D5.2** [WARNING] -- "Medium" effort is structural default with zero regex; 40-60% hit silent zone
   Fix: Fix must be at INTENT_RULES coverage layer, not effort classification

5. **V1.1** [WARNING] -- Enforcement feasible but 5 prerequisites required; 100% false-positive without receipt writer
   Fix: Deploy prerequisites atomically; use MASONRY_ENFORCE_ROUTING=1 env flag for rollout

6. **D2.2** [DIAGNOSIS_COMPLETE] -- Receipt pattern architecturally present but writer absent and gate softened
   Fix: Add receipt writer to Mortar agent + per-prompt reset in prompt router

---

## Healthy / Verified

- **D4.1** [WARNING, structurally healthy]: All 20 Mortar routing table agents have resolvable .md files (0 missing). bl-audit D2.6 finding is stale -- uiux-master and solana-specialist now present. WARNING only on lack of file-existence validation in the router.

- **FR1.1** [FRONTIER_PARTIAL]: The minimum viable enforcement architecture (Write/Edit deny-gate + routing receipt) is confirmed buildable within existing hook capabilities. ~80 lines of code across 3 files. The text-generation enforcement gap is a permanent platform constraint, not a Masonry deficiency.

---

## Recommendation

**STOP**

All 14 questions are answered. The root cause chain is fully mapped from instruction ambiguity through enforcement absence. The campaign has produced a complete structural diagnosis with specific fix specifications for every identified gap. The next phase is implementation, not further investigation. The five-prerequisite deployment sequence (V1.1) provides the exact build order. No additional research questions are needed in this domain.

---

## Next Wave Hypotheses (for future campaigns)

1. **Behavioral validation after D1.1 fix**: Does narrowing the "trivial" definition to "single-sentence factual lookups" measurably increase Mortar consultation rate? What is the over-delegation rate?

2. **Receipt writer integration test**: After implementing the 5 prerequisites, what is the real false-positive rate of the Write/Edit hard block behind MASONRY_ENFORCE_ROUTING=1?

3. **Dark fleet activation impact**: After populating routing_keywords for 80+ agents, what percentage of previously-inline prompts now route to specialists? Does quality improve?

4. **Multi-turn routing persistence**: After implementing `last_route` persistence and follow-up detection, does the Turn 2+ routing signal gap close from 40-60% to < 10%?

5. **Context dilution reduction**: After moving 6 UI rules to conditional load, does routing compliance measurably improve in non-UI sessions?

---

## Cross-Domain Conflicts

1. **Enforcement vs. usability (V1.1)**: Hard-blocking Write/Edit without a receipt will break legitimate trivial-task workflows. The Bash exemption creates an asymmetric bypass. The trivial-bypass classifier must be deployed simultaneously with the hard block.

2. **Dark fleet vs. routing noise (D4.2)**: Activating 98 dark-fleet agents without quality-gating their routing_keywords could flood Mortar's semantic layer with false matches. Activation should be staged: high-value specialists first (python-specialist, typescript-specialist, database-specialist, devops), then campaign agents, then stubs last.

3. **Campaign mode blackout (D3.2/D5.1)**: The line 187 early exit suppresses all routing during active campaigns. Removing it would cause routing hints to fire during BL research loops, potentially interfering with Trowel's dispatch. The fix should be conditional: suppress routing hints only for questions already assigned to agents by Trowel.
