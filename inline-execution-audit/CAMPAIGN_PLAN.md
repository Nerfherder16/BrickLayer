# Campaign Plan -- inline-execution-audit -- 2026-03-29

## System Summary

BrickLayer 2.0 uses a three-layer architecture (Claude Code / Masonry / BrickLayer) where every request is supposed to route through Mortar, which dispatches to specialist agents in parallel. The routing is signaled by a UserPromptSubmit hook (masonry-prompt-router.js) and directed by CLAUDE.md instructions, but enforcement is purely advisory -- Claude can always answer inline without any blocking mechanism. This campaign investigates the structural and behavioral causes of inline execution bypass, why the prompt router signal gets ignored, and what enforcement mechanisms could close the gap.

## Prior Campaign Context

The bl-audit campaign (Waves 1-3, 56 questions, 36 confirmed findings) identified M1.4 as the key open item: "Mortar directive is advisory, not enforced -- design decision needed" (HIGH severity). Additional relevant findings:
- **D2.6**: uiux-master and solana-specialist .md files are missing -- routing to these agents fails silently
- **D5.1**: masonry-build.md references dead OMC executor -- misdirects build task routing
- **E1.9**: Auto-loaded context is 22,587 tokens (45% of threshold), with 12,423 tokens of UI-specific rules loaded in all sessions, potentially diluting routing instruction weight
- **M1.6**: mortar.md missing git-nerd and infra routing entries -- routing table gaps
- **Pattern 6**: Incremental growth without refactoring -- applies directly to the routing instruction set

## Domain Risk Ranking

Domains adapted from the standard BrickLayer D1-D6 framework to fit this behavioral/structural research campaign:

| Domain | Description | Likelihood | Impact | Priority | Rationale |
|--------|-------------|-----------|--------|----------|-----------|
| D1 | Instruction authority -- CLAUDE.md weight vs. competing context | 3 | 3 | **9** | CLAUDE.md routing directive competes with 22K tokens of auto-loaded context, conversation history, and model priors. The "trivial vs. substantive" escape hatch gives Claude permanent permission to bypass. This is the root cause domain. |
| D2 | Enforcement gap -- can advisory become mandatory? | 3 | 3 | **9** | bl-audit M1.4 confirmed the gap exists. No hook blocks inline execution. The prompt router injects text but cannot force tool use. The entire routing architecture has zero enforcement authority. Tied for highest priority because it is the architectural fix domain. |
| D5 | Behavioral triggers -- prompt characteristics that trigger inline execution | 3 | 2 | **6** | Empirically observable: short questions, follow-ups, and "explain" prompts reliably trigger inline execution. The prompt router explicitly skips prompts < 20 chars and question-style prompts (classifies effort as "low"). Understanding trigger taxonomy is essential for any enforcement design. |
| D3 | Routing coverage -- task types with poor/missing routing signal | 2 | 3 | **6** | The prompt router covers 10 intent categories but has documented gaps: simple questions/lookups (no hint), multi-intent prompts (first-match only), follow-up prompts (no context awareness), and slash commands (explicitly skipped). Missing coverage = guaranteed inline execution. |
| D4 | Agent fleet gaps -- missing or non-functional delegation targets | 2 | 2 | **4** | D2.6 confirmed uiux-master and solana-specialist .md files are missing. D5.1 confirmed masonry-build.md references a dead executor. When the delegation target does not exist or is broken, inline execution is the only option. Fleet gap count is bounded; prior audit mapped most of it. |
| D6 | Systemic drift -- routing quality vs. session length / context size | 2 | 2 | **4** | E1.9 found 22K tokens of base context. As sessions grow, the Mortar routing instruction becomes a smaller fraction of total context. The masonry-context-monitor.js warns at 150K tokens but does not act on routing degradation. Plausible but hardest to measure without controlled experiments. |

## Targeting Brief for Question-Designer

### High-priority areas (generate 3-5 questions each)

1. **D1: Instruction authority hierarchy** -- Why does the Mortar routing directive lose to other context signals? Investigate: (a) the "trivial vs. substantive" escape hatch language, (b) context window position of routing instructions vs. conversation history, (c) whether stronger directive language (MUST/NEVER vs. advisory) changes compliance rates, (d) whether the prompt router hint injection position matters relative to system prompt.

2. **D2: Enforcement mechanism design** -- What enforcement mechanisms are structurally possible within the Claude Code hook system? Investigate: (a) whether a PreToolUse hook could block Write/Read/Bash if Mortar has not been invoked, (b) whether a SubagentStart requirement could be injected, (c) whether a "routing receipt" pattern (Mortar emits a token that downstream tools check) is feasible, (d) whether enforcement breaks legitimate trivial-task direct execution, (e) what the false-positive rate of forced delegation would be for genuinely trivial requests.

### Medium-priority areas (generate 1-2 questions each)

3. **D5: Behavioral trigger taxonomy** -- Catalog which prompt characteristics predict inline execution vs. delegation. Investigate: (a) prompt length thresholds, (b) question-form vs. imperative-form prompts, (c) presence/absence of routing keywords, (d) whether the `[effort:low]` classification from the prompt router correlates with inline execution.

4. **D3: Routing signal gaps** -- Map the prompt types that fall through all routing rules. Investigate: (a) multi-intent prompts where first-match misroutes, (b) follow-up prompts that inherit no routing signal from prior turns, (c) ambiguous prompts where intent detection returns null AND effort is "medium" (the explicit skip condition on line 194 of masonry-prompt-router.js).

5. **D4: Agent fleet completeness** -- Verify which delegation targets are missing or broken. Cross-reference the Mortar routing table (10 work types) against agent_registry.yml entries and confirm each target agent has a resolvable .md file. Extends D2.6 from bl-audit.

### Skip or defer

- **D6: Systemic drift** -- Important but unmeasurable in a pure research campaign without controlled session-length experiments. Defer to a future campaign that can run instrumented sessions of varying length. Note as a hypothesis for Wave 2 if Wave 1 findings suggest context dilution is a primary factor.

## Known Landmines (from prior campaigns)

- **M1.4** (bl-audit Wave 2, HIGH): Mortar directive advisory not enforced -- the central finding this campaign extends. Do not re-confirm; instead investigate root causes and solutions.
- **D2.6** (bl-audit Wave 1, MEDIUM): uiux-master and solana-specialist .md files missing -- verified gap, do not re-discover; use as evidence for D4 fleet gap analysis.
- **D5.1** (bl-audit Wave 1, MEDIUM): masonry-build.md dead OMC executor -- verified, use as evidence for D3 routing coverage analysis.
- **M1.6** (bl-audit Wave 2, MEDIUM): mortar.md missing git-nerd and infra routing entries -- verified, use as evidence for D3 and D4.
- **E1.9** (bl-audit Wave 3, FALSE_POSITIVE but informative): Auto-loaded context is 22,587 tokens -- not a defect, but use the 12,423-token UI-rules dilution as evidence for D1 instruction authority analysis.

## Recommended Wave Structure

- **Wave 1 (10-12 questions)**: Focus on D1 (instruction authority) and D2 (enforcement gap) -- the two priority-9 domains. Include 2-3 D5 (behavioral trigger) questions as supporting evidence for the D1/D2 analysis.
- **Wave 2 (6-8 questions)**: D3 (routing coverage gaps), D4 (fleet completeness), and D5 follow-ups based on Wave 1 findings. Include 1-2 D6 (systemic drift) questions if Wave 1 suggests context dilution is a factor.
- **Estimated total questions**: 16-20 across 2 waves

## BL 2.0 Mode Allocation

| Mode | Suggested question count | Rationale |
|------|--------------------------|-----------|
| diagnose | 5-6 | D1 and D2 are root-cause domains requiring structural diagnosis of why routing fails |
| research | 5-6 | D3 and D5 require systematic cataloging of routing gaps and behavioral triggers |
| audit | 3-4 | D4 fleet completeness is a cross-reference audit; D2 enforcement feasibility is a constraint audit |
| validate | 1-2 | Only for proposed enforcement mechanisms -- validate that a design would work without breaking trivial tasks |
| frontier | 1-2 | Blue-sky: could a completely different enforcement model (e.g., routing receipts, mandatory Agent tool) work? |
| benchmark / evolve / monitor / predict | 0 for Wave 1 | Reserve for Wave 2 if controlled experiments become feasible |

Total Wave 1 target: 10-12 questions

## Constraints to Keep in Mind

1. **The "trivial" escape hatch**: CLAUDE.md says "Lightest path that preserves quality -- direct action when trivial, agents when substantive." This is the intentional bypass. Any enforcement must account for it.
2. **Prompt router skip conditions**: Empty, slash commands, < 20 chars, inside BL research loop, active campaign mode, no intent match AND effort == "medium". These are explicit no-signal conditions.
3. **First-match routing**: The INTENT_RULES array uses first-match logic. Multi-intent prompts get single routing hints.
4. **No hook can force Agent tool use**: Hooks can block tools (PreToolUse returns "deny") but cannot force Claude to invoke a specific tool. Enforcement must work within this constraint.
5. **22,587 tokens of auto-loaded context**: The routing instruction is a small fraction of total context. Any instruction-weight solution must account for signal dilution.
6. **55+ agents in registry, 10 routing categories**: The fleet is large but the routing table has only 10 buckets. Coverage gaps exist between the fine-grained fleet and the coarse routing table.

## Instruction Block for Question-Designer-BL2

Read the "High-priority areas" section above before generating questions.md.
Generate questions in priority order -- D1 first, D2 second, then D5/D3/D4.
For each high-priority area, generate at minimum one DIAGNOSIS question and one structural analysis question.
Do not generate questions for "Skip or defer" areas (D6) unless directly linked to a high-priority finding.
Use the "BL 2.0 Mode Allocation" table above to set Mode fields -- do not invent mode assignments.
This is a pure research campaign with no simulate.py -- all questions must be answerable through code reading, structural analysis, and behavioral reasoning. Do not generate simulation or parameter-sweep questions.
