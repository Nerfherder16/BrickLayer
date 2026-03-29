# Question Bank -- inline-execution-audit

**Campaign type**: BrickLayer 2.0
**Generated**: 2026-03-29T04:00:00Z
**Modes selected**: diagnose (5), research (4), audit (3), validate (1), frontier (1) = 14 questions
**Mode rationale**: D1 (instruction authority) and D2 (enforcement gap) are priority-9 domains requiring structural diagnosis. D5 (behavioral triggers) and D3 (routing coverage) require systematic cataloging via research mode. D4 (fleet gaps) is a cross-reference audit. Validate and frontier cover enforcement design feasibility.

---

## Wave 1

### D1.1: Why does the Mortar routing directive in CLAUDE.md lose authority against the "trivial vs. substantive" escape hatch, and what is the effective definition of "trivial" that Claude applies?

**Status**: DONE
**Finding**: findings/D1.1.md
**Completed**: 2026-03-29T04:10:00Z
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: Claude interprets "trivial" broadly -- any task that can be answered from existing context without tool use is classified as trivial, regardless of the CLAUDE.md directive that "every request goes through Mortar." The escape hatch phrase "direct action when trivial, agents when substantive" overrides the absolute "every request" directive because it appears later in the Operating Principles section and provides a more specific behavioral rule.
**Agent**: diagnose-analyst
**Success criterion**: A structural analysis showing (a) the exact CLAUDE.md text positions of the absolute directive vs. the escape hatch, (b) evidence of which instruction takes precedence in the model's instruction-following hierarchy, and (c) a proposed operational definition of "trivial" that matches observed inline execution patterns.

### D1.2: Does the context window position of the Mortar routing instruction relative to conversation history affect compliance rates, and does the 22,587-token auto-loaded context dilute the routing signal?

**Status**: DONE
**Finding**: findings/D1.2.md
**Completed**: 2026-03-29T06:52:00Z
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: The Mortar routing section occupies a small fraction of the 22,587-token auto-loaded context. The 12,423 tokens of UI-specific rules (Figma guides, frontend philosophy, React/Tailwind standards) loaded in every session -- including non-UI sessions -- dilute the effective weight of routing instructions. As conversation history grows, the routing instruction becomes an even smaller fraction of total context, further reducing compliance.
**Agent**: diagnose-analyst
**Success criterion**: A token-count analysis showing (a) the byte/token size of the Mortar routing section vs. total auto-loaded context, (b) the ratio of routing-relevant instructions to non-routing instructions, and (c) whether instruction position (early vs. late in system context) correlates with compliance based on known LLM instruction-following research.

### D1.3: Does the prompt router hint injection ("Mortar: routing to {agent} [effort:X]") carry sufficient authority weight relative to CLAUDE.md instructions, or is it treated as a low-priority system annotation?

**Status**: DONE
**Finding**: findings/D1.3.md
**Completed**: 2026-03-29T07:10:00Z
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: The prompt router hint is injected via hookSpecificOutput as a single line of text. Claude treats this as supplementary context rather than a directive -- it carries less weight than CLAUDE.md instructions, conversation history, and model priors. The hint format (arrow symbol, bracketed metadata) may read as informational annotation rather than an imperative instruction, further reducing compliance.
**Agent**: diagnose-analyst
**Success criterion**: A structural analysis of (a) how hookSpecificOutput content is positioned in the context Claude receives, (b) whether the hint format signals authority or annotation, and (c) comparison with other hook outputs that DO reliably influence behavior (e.g., masonry-approver.js auto-approve signals).

### D2.1: What enforcement mechanisms are structurally possible within the Claude Code hook system to make Mortar routing mandatory rather than advisory?

**Status**: DONE
**Finding**: findings/D2.1.md
**Completed**: 2026-03-29T07:28:00Z
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: The hook system can block tool use (PreToolUse returning "deny") but cannot force Claude to invoke a specific tool like the Agent tool. A PreToolUse hook on Write/Read/Bash could check whether a Mortar routing receipt exists in the current turn and deny if absent -- but this would block ALL direct tool use, including legitimate trivial tasks. The fundamental constraint is that hooks are gate-based (allow/deny) not directive-based (force action X).
**Agent**: diagnose-analyst
**Success criterion**: A comprehensive inventory of (a) which hook events could participate in enforcement, (b) what each hook can structurally do (allow, deny, inject text, modify parameters), (c) whether a "routing receipt" pattern is feasible (Mortar emits a token that downstream PreToolUse hooks check), and (d) the false-positive rate estimate for forced delegation on trivial tasks.

### D2.2: Could a "routing receipt" pattern be implemented where Mortar sets a session-level flag that PreToolUse hooks check before allowing Write/Edit/Bash execution?

**Status**: DONE
**Finding**: findings/D2.2.md
**Completed**: 2026-03-29T07:45:00Z
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: A routing receipt would require: (1) Mortar or the prompt router writes a flag to a file or environment variable, (2) PreToolUse hooks read that flag before allowing tool execution, (3) the flag resets per-turn to prevent stale receipts. This is feasible using masonry-state.json as the flag store, but has a race condition: Claude may invoke tools before the prompt router hook has completed, and hooks execute asynchronously. The pattern is architecturally sound but has timing vulnerabilities.
**Agent**: diagnose-analyst
**Success criterion**: A feasibility analysis with (a) a concrete implementation sketch using existing hook infrastructure, (b) identification of race conditions or timing issues, (c) the mechanism for resetting the receipt per-turn, and (d) whether masonry-state.json or an alternative store is appropriate.

### D5.1: Which prompt characteristics reliably predict inline execution vs. delegation, and can a taxonomy of bypass triggers be constructed from the prompt router's skip conditions?

**Status**: DONE
**Finding**: findings/D5.1.md
**Completed**: 2026-03-29T08:10:00Z
**Mode**: research
**Priority**: HIGH
**Hypothesis**: Inline execution is triggered by a predictable set of prompt characteristics: (a) prompts under 20 characters, (b) question-form prompts ("what is...", "how does..."), (c) follow-up prompts that reference prior conversation context, (d) prompts where the router classifies effort as "low", (e) prompts that match no INTENT_RULES pattern. These five categories account for the majority of inline execution events.
**Agent**: research-analyst
**Success criterion**: A taxonomy of bypass trigger categories with (a) the specific prompt router code paths that produce no routing hint for each category, (b) estimated frequency of each trigger type in typical sessions, and (c) examples of prompts in each category that should have been delegated but were not.

### D5.2: Does the prompt router's effort classification ("low" / "medium" / "high" / "max") correlate with actual delegation behavior, and what happens when effort is "medium" with no intent match?

**Status**: DONE
**Finding**: findings/D5.2.md
**Completed**: 2026-03-29T08:25:00Z
**Mode**: research
**Priority**: MEDIUM
**Hypothesis**: When the router classifies effort as "medium" and no intent rule matches, line 194 of masonry-prompt-router.js explicitly skips hint injection. This is the most common no-signal condition because "medium" is the default effort classification. The result is that a large class of moderately complex prompts receive no routing guidance whatsoever -- these are the prompts most likely to be answered inline despite being substantive enough to warrant delegation.
**Agent**: research-analyst
**Success criterion**: Analysis of (a) the effort classification regex patterns and their match rates against typical prompts, (b) the specific code path at line 194 that skips on medium+no-intent, (c) estimated percentage of real prompts that fall into this gap, and (d) whether reclassifying the skip condition would reduce inline execution.

### D3.1: Which task types in the Mortar routing table have no corresponding prompt router INTENT_RULES entry, creating systematic routing gaps?

**Status**: DONE
**Finding**: findings/D3.1.md
**Completed**: 2026-03-29T08:40:00Z
**Mode**: research
**Priority**: MEDIUM
**Hypothesis**: The Mortar routing table defines 10 work types but the prompt router covers only 9 intent categories via INTENT_RULES. At least one Mortar work type has no router-level detection, meaning prompts for that work type never receive a routing hint. Additionally, multi-intent prompts that span multiple work types get first-match-only routing, potentially misrouting the secondary intent.
**Agent**: research-analyst
**Success criterion**: A cross-reference matrix showing (a) each Mortar work type mapped to its INTENT_RULES entry (or "MISSING"), (b) each INTENT_RULES entry mapped to its Mortar work type, (c) any orphaned entries in either direction, and (d) the multi-intent first-match problem illustrated with concrete prompt examples.

### D3.2: How do follow-up prompts (references to prior conversation turns) interact with the routing system, and does the lack of conversational context awareness in the prompt router cause systematic routing failures?

**Status**: DONE
**Finding**: findings/D3.2.md
**Completed**: 2026-03-29T08:55:00Z
**Mode**: research
**Priority**: MEDIUM
**Hypothesis**: The prompt router processes each prompt in isolation -- it has no access to conversation history. A follow-up prompt like "now do the same for the other module" carries no routing signal because it contains no intent keywords. The original prompt may have received a routing hint, but the follow-up inherits nothing. This creates a systematic gap where multi-turn workflows degrade from delegated to inline as the conversation progresses.
**Agent**: research-analyst
**Success criterion**: Analysis of (a) whether the prompt router has any mechanism for conversational context, (b) concrete examples of follow-up prompts that would lose routing signal, (c) the frequency of follow-up prompts in typical development sessions, and (d) whether a "last-routing-hint" persistence mechanism could close this gap.

### D4.1: Which agents in the Mortar routing table have missing, broken, or unresolvable .md files, and does fleet incompleteness force inline execution for those work types?

**Status**: DONE
**Finding**: findings/D4.1.md
**Completed**: 2026-03-29T09:05:00Z
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: At least 3 delegation targets referenced in the Mortar routing table or agent_registry.yml have missing or broken .md files: uiux-master (confirmed D2.6), solana-specialist (confirmed D2.6), and potentially others. When Claude attempts to delegate to a missing agent, it falls back to inline execution silently -- there is no error signal or retry mechanism. Fleet incompleteness is a direct cause of inline execution for the affected work types.
**Agent**: research-analyst
**Success criterion**: A complete cross-reference audit showing (a) every agent referenced in CLAUDE.md Mortar routing table, (b) whether each has a resolvable .md file in the expected locations, (c) whether agent_registry.yml entries match actual .md files, and (d) which work types have no functional delegation target.

### D4.2: Does the mismatch between the 55+ agents in agent_registry.yml and the 10 routing categories in the Mortar table create dead zones where agents exist but are never routed to?

**Status**: DONE
**Finding**: findings/D4.2.md
**Completed**: 2026-03-29T09:20:00Z
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: The agent registry contains 55+ agents but the Mortar routing table has only 10 work type categories. Many registered agents have no routing path -- they exist in the registry but are never selected by Mortar's dispatch logic. This creates "dark fleet" agents that can only be invoked by explicit name reference, never by automatic routing. The dark fleet represents wasted capability and may include agents that would prevent inline execution if they were routable.
**Agent**: research-analyst
**Success criterion**: A mapping showing (a) which registry agents are reachable via the 10 Mortar routing categories, (b) which registry agents have no routing path ("dark fleet"), (c) whether any dark fleet agents cover work types that currently default to inline execution, and (d) recommendations for routing table expansion.

### A1.1: Does the current hook system enforce any behavioral contract on Claude's delegation decisions, or is every routing signal purely advisory with zero enforcement authority?

**Status**: DONE
**Finding**: findings/A1.1.md
**Completed**: 2026-03-29T09:35:00Z
**Mode**: audit
**Priority**: HIGH
**Hypothesis**: Zero hooks in the current system enforce delegation. The masonry-prompt-router.js injects hints but cannot block. The masonry-approver.js auto-approves in build mode but does not check routing compliance. The masonry-pre-protect.js guards file edits but does not verify delegation. Every routing signal in the system is advisory. The enforcement authority is exactly zero -- not "weak" or "partial," but structurally absent.
**Agent**: research-analyst
**Success criterion**: A complete audit of all 15+ hooks listing (a) whether each hook has any delegation-enforcement capability, (b) what each hook actually enforces (file protection, linting, etc. vs. routing), (c) whether any hook could be extended to enforce delegation without architectural changes, and (d) a definitive verdict on whether enforcement authority is zero or non-zero.

### V1.1: Would a mandatory-delegation enforcement mechanism (e.g., PreToolUse blocking without routing receipt) break legitimate trivial-task direct execution, and what is the estimated false-positive rate?

**Status**: DONE
**Finding**: findings/V1.1.md
**Completed**: 2026-03-29T09:45:00Z
**Mode**: validate
**Priority**: MEDIUM
**Hypothesis**: Mandatory delegation would break at least 30% of legitimate interactions. Tasks like "what branch am I on?", "show git status", and "read this file" are genuinely trivial and routing them through Mortar would add latency and context overhead without quality benefit. The false-positive rate (trivial tasks incorrectly forced through delegation) would be unacceptable unless the enforcement mechanism includes a trivial-task whitelist or effort-threshold bypass.
**Agent**: design-reviewer
**Success criterion**: An analysis with (a) a categorization of "trivial" tasks that should bypass delegation, (b) an estimate of what percentage of total prompts fall into the trivial category, (c) a proposed whitelist or threshold mechanism, and (d) a verdict on whether enforcement is feasible without unacceptable false-positive rates.

### FR1.1: What would a structurally enforced routing architecture look like if Claude Code's hook system could force Agent tool invocation, and what prerequisites does the current system lack?

**Status**: DONE
**Finding**: findings/FR1.1.md
**Completed**: 2026-03-29T10:00:00Z
**Mode**: frontier
**Priority**: LOW
**Hypothesis**: A structurally enforced architecture would require: (1) a hook that can inject mandatory tool calls (not just text), (2) a routing receipt system where Mortar marks each request as "routed" before any other tool use is permitted, (3) a trivial-task classifier that operates before the enforcement gate, and (4) a conversation-aware router that maintains routing state across turns. The current system lacks all four prerequisites. The closest feasible path is a PreToolUse deny-gate combined with a file-based routing receipt, but this cannot force the Agent tool -- it can only block everything else until Claude "voluntarily" invokes Mortar.
**Agent**: frontier-analyst
**Success criterion**: A design sketch with (a) the ideal enforcement architecture (unconstrained by current limitations), (b) the minimum viable enforcement architecture (constrained to current hook capabilities), (c) a gap analysis between ideal and feasible, and (d) a recommendation on whether to pursue hook-based enforcement or a fundamentally different approach.

---

## Wave 2

**Generated from findings**: D1.1, D1.3, D2.1, D2.2, D3.1, D3.2, D4.2, D5.1, D5.2, V1.1, FR1.1
**Mode transitions applied**: D1.1 DIAGNOSIS_COMPLETE -> F2.1 Fix; D1.3 DIAGNOSIS_COMPLETE -> F2.2 Fix; D2.1+D2.2 DIAGNOSIS_COMPLETE -> F2.3 Fix (atomic prerequisite bundle); D2.2 DIAGNOSIS_COMPLETE (receipt writer location underspecified) -> D2.3 Diagnose; FR1.1 FRONTIER_PARTIAL+VIABLE -> R2.1+R2.2 Research; D3.1 FAILURE -> R2.2 Research (spec+build pattern narrowing); D3.2 FAILURE -> D2.5 Diagnose (last_route persistence design); D4.2 FAILURE -> D2.4 Diagnose (routing_keywords auto-population); D5.1+D5.2 WARNING -> M2.1 Monitor

---

### F2.1: Implement the CLAUDE.md line 68 escape hatch fix specified in D1.1 -- replace "direct action when trivial" with a scoped operational definition

**Status**: DONE
**Finding**: findings/F2.1.md
**Completed**: 2026-03-29T10:45:00Z
**Operational Mode**: Fix
**Priority**: HIGH
**Motivated by**: D1.1 (DIAGNOSIS_COMPLETE) -- CLAUDE.md line 68 phrase "direct action when trivial, agents when substantive" overrides the absolute Mortar directive via specificity-beats-general; "trivial" has no operational definition and defaults to the model's broad prior
**Hypothesis**: Replacing the vague phrase with a scoped definition ("single-sentence factual lookups with no file changes required") will close the escape hatch that allows the model to justify inline execution for substantive work while preserving a narrow legitimate bypass for genuinely trivial responses
**Method**: fix-implementer
**Success criterion**: (a) CLAUDE.md line 68 changed from "direct action when trivial" to a scoped definition that includes concrete examples of what trivial means and what it excludes; (b) the new text does not contradict the "Every request -> Mortar" absolute directive elsewhere in CLAUDE.md; (c) verified by grep showing no remaining instance of undefined "trivial" near the routing directive; (d) change is minimal -- text edit only, no structural changes to CLAUDE.md

---

### F2.2: Implement the prompt router output channel fix specified in D1.3 -- switch masonry-prompt-router.js from hookSpecificOutput to additionalContext and rewrite hint as imperative

**Status**: DONE
**Finding**: findings/F2.2.md
**Completed**: 2026-03-29T10:50:00Z
**Operational Mode**: Fix
**Priority**: HIGH
**Motivated by**: D1.3 (DIAGNOSIS_COMPLETE) -- prompt router emits routing hint via hookSpecificOutput.content (wrong channel, treated as annotation) instead of additionalContext (model-visible context); hint uses arrow annotation format ("->") instead of imperative format; two independent reasons the hint carries no authority
**Hypothesis**: Switching to additionalContext makes the routing hint visible to the model in the same context channel as CLAUDE.md instructions; rewriting the hint as an imperative with explicit consequence framing ("You MUST route this through Mortar -- direct Write/Edit without a routing receipt will be blocked") increases compliance by citing a real enforcement consequence
**Method**: fix-implementer
**Success criterion**: (a) masonry-prompt-router.js emits routing hint via additionalContext key, not hookSpecificOutput.content; (b) hint text is imperative ("You MUST..."), not annotation ("-> route to..."); (c) hint references the enforcement consequence ("Write/Edit will be blocked") to make it credible; (d) verified by reading the updated hook and confirming the output structure matches the additionalContext schema; (e) existing routing hint logic (intent detection, effort classification, skip conditions) is unchanged -- only the output channel and format change

---

### F2.3: Implement the five-prerequisite atomic bundle required before the masonry-approver.js hard block can be enabled -- receipt writer, per-turn reset, trivial bypass, gate conversion, and MASONRY_ENFORCE_ROUTING flag

**Status**: IN_PROGRESS
**Operational Mode**: Fix
**Priority**: HIGH
**Motivated by**: D2.1 (DIAGNOSIS_COMPLETE) + D2.2 (DIAGNOSIS_COMPLETE) + V1.1 (WARNING) -- the Mortar gate in masonry-approver.js lines 293-301 is advisory-only; the change to hard block is known; but V1.1 establishes that deploying the block without 5 prerequisites produces 100% false-positive rate; all five must be deployed atomically
**Hypothesis**: The five prerequisites (receipt writer in Mortar instructions, per-turn reset in prompt router, trivial bypass condition in approver, gate conversion to deny, MASONRY_ENFORCE_ROUTING env flag) together form a complete atomic unit; deploying them simultaneously behind the env flag allows measuring the real false-positive rate before making enforcement the default
**Method**: fix-implementer
**Success criterion**: (a) Mortar agent instructions contain explicit instruction to write mortar_consulted: true and mortar_session_id: <ISO> to masonry-state.json after routing a request; (b) masonry-prompt-router.js resets mortar_consulted: false at each UserPromptSubmit; (c) masonry-approver.js contains a trivial bypass condition that allows through when effort is "low" or prompt length is under a configurable threshold; (d) masonry-approver.js lines 293-301 emit permissionDecision: "deny" for Write/Edit when MASONRY_ENFORCE_ROUTING=1 AND !isMortarConsulted(); (e) Bash exemption is unchanged; (f) all existing approval paths (build mode, compose mode, research mode, subagent exemption) remain unaffected; (g) verified by starting a fresh session with MASONRY_ENFORCE_ROUTING=1, attempting a Write without Mortar consultation -- expect deny; then routing through Mortar -- expect allow

---

### D2.3: Where exactly in Mortar's agent instructions should the receipt writer live, and what is the complete write specification to prevent the Mortar-before-file-write deadlock?

**Status**: DONE
**Finding**: findings/D2.3.md
**Completed**: 2026-03-29T11:10:00Z
**Operational Mode**: Diagnose
**Priority**: MEDIUM
**Motivated by**: D2.2 (DIAGNOSIS_COMPLETE) -- Fix specification identifies the receipt writer as "Change B" needing to live in "Mortar's agent instructions or a dedicated hook," but the exact location is underspecified; the deadlock risk is real: if Mortar fails to write the receipt before the first tool call, the gate denies the tool call, blocking Mortar from completing; the write timing must be precise
**Hypothesis**: The receipt writer must be placed in Mortar's agent instructions as an explicit first-action step before any tool delegation -- not at session start, not post-dispatch, but before Mortar returns any response to Claude; the exact instruction text and the file write target (masonry-state.json path, field names, timestamp format) need to be fully specified to avoid the deadlock scenario
**Method**: diagnose-analyst
**Success criterion**: (a) exact location in mortar.md (or equivalent Mortar instruction file) where the receipt write instruction should be inserted; (b) the precise instruction text that causes Mortar to write the receipt (including which tool to use, which file path, which JSON fields); (c) analysis of whether the write must happen before or after Mortar dispatches specialist agents; (d) deadlock scenario analysis -- if the receipt write fails, what happens to the blocked session and how does it recover; (e) identification of whether masonry-state.json global singleton vs. per-session temp file matters for the deadlock case

---

### R2.1: Does the D1.1 "single-sentence factual lookup" boundary create over-delegation for interactive conversational queries, and what is the expected false-positive rate at the new trivial threshold?

**Status**: PENDING
**Operational Mode**: Research
**Priority**: MEDIUM
**Motivated by**: FR1.1 (FRONTIER_PARTIAL, VIABLE) + D1.1 (DIAGNOSIS_COMPLETE) -- FR1.1 recommends deploying minimum viable enforcement; D1.1's fix narrows "trivial" to "single-sentence factual lookups only"; before committing to this boundary, stress-test it: how many legitimate interactive queries exceed this threshold and would be routed through Mortar unnecessarily?
**Hypothesis**: The "single-sentence factual lookup" boundary is too narrow for interactive use -- queries like "what does this function return?", "show me the git log", "explain this error" are not file-writing tasks and not multi-agent work, but they exceed the proposed trivial definition; the over-delegation rate at this threshold may be 30-50% of conversational queries, making enforcement oppressive for exploratory sessions
**Method**: research-analyst
**Success criterion**: (a) a taxonomy of common interactive conversational queries categorized as trivial-at-proposed-threshold vs. over-delegated-at-proposed-threshold; (b) estimated percentage of typical session prompts that fall into each category; (c) a refined trivial definition that reduces over-delegation without reopening the escape hatch for substantive file-writing work; (d) the key discriminating feature between "genuinely trivial, inline is fine" and "substantive, requires routing" -- is it file-write intent, multi-file scope, or something else?

---

### D2.4: Can the routing_keywords field in agent_registry.yml be auto-populated from agent .md files, and what extraction mechanism would cover 80+ dark fleet agents without manual annotation?

**Status**: DONE
**Finding**: findings/D2.4.md
**Completed**: 2026-03-29T11:15:00Z
**Operational Mode**: Diagnose
**Priority**: MEDIUM
**Motivated by**: D4.2 (FAILURE) -- 86% of 114 agents (98 agents) are dark fleet with no routing path; routing_keywords field exists in agent_registry.yml but is unpopulated for 80+ agents; manual annotation of 80 agent files is not tractable; an automated extraction mechanism would close the dark fleet problem at scale
**Hypothesis**: Each agent .md file contains a structured frontmatter section and a "When to invoke" or "Trigger" section that can be parsed to extract routing keywords; a script that reads agent .md files and extracts trigger conditions could auto-populate routing_keywords with reasonable quality; the same onboard_agent.py script that handles auto-onboarding is the natural place to add this extraction
**Method**: diagnose-analyst
**Success criterion**: (a) identification of which sections in agent .md files contain routing-relevant trigger keywords (frontmatter fields, trigger sections, capability descriptions); (b) feasibility assessment of automated extraction -- what percentage of agents have structured enough content to yield usable keywords without manual review; (c) a complete implementation sketch for extending onboard_agent.py (or a new script) to extract and write routing_keywords from .md content; (d) quality risk assessment -- what false-match rate would auto-extracted keywords introduce into the semantic routing layer, and how does it compare to the current 86% dark fleet baseline?

---

### D2.5: What does last_route persistence look like in masonry-state.json for multi-turn continuity, and which follow-up detection patterns would close the Turn 2+ routing signal gap?

**Status**: DONE
**Finding**: findings/D2.5.md
**Completed**: 2026-03-29T11:20:00Z
**Operational Mode**: Diagnose
**Priority**: MEDIUM
**Motivated by**: D3.2 (FAILURE) -- router is stateless per-prompt; Turn 2+ of any multi-turn workflow produces complete routing silence; synthesis fix is "add last_route persistence field; implement follow-up detection patterns"; the exact schema and pattern set need to be specified before implementation
**Hypothesis**: Adding a last_route field to masonry-state.json (written by the prompt router when it emits a hint) and a set of follow-up detection regexes (matching "now do", "also", "same for", "continue", "next", "and then", "additionally") would allow the router to inherit the prior turn's routing decision on continuation prompts; this would close the Turn 2+ gap for the majority of multi-turn workflows without requiring conversation history access
**Method**: diagnose-analyst
**Success criterion**: (a) the exact schema extension to masonry-state.json for last_route persistence (field names, data types, TTL/expiry logic); (b) a set of follow-up detection regexes covering the most common continuation patterns in development sessions; (c) the router code path that reads last_route when no INTENT_RULE matches and the current prompt matches a follow-up pattern; (d) the false-positive risk -- which prompts would incorrectly inherit a prior routing decision when they should be classified fresh; (e) identification of whether the same mechanism could handle campaign-mode blackout (D3.2 line 187 exit) without interfering with Trowel's dispatch

---

### R2.2: Which specific regex patterns would close the spec+build INTENT_RULES silent zone identified in D3.1, and do they risk first-match collisions with existing rules?

**Status**: PENDING
**Operational Mode**: Research
**Priority**: MEDIUM
**Motivated by**: D3.1 (FAILURE) -- "Spec+build" is the one Mortar work type with zero INTENT_RULES coverage; /plan exits before detection via slash-command guard; prompts like "plan this feature", "write a spec for", "blueprint the architecture of" have no router entry point; 6 other work types are degraded by verb gaps and first-match collisions
**Hypothesis**: A small set of regex patterns (3-5 patterns covering "plan", "spec", "blueprint", "design a system for", "architect a solution") would close the spec+build silent zone; adding maintenance verbs ("fix|update|make|change|set|configure|apply|enable|disable|modify") to the existing build rule would close the majority of the verb-gap degradation; both changes can be made without creating new first-match collisions if spec patterns are placed after existing plan/build rules
**Method**: research-analyst
**Success criterion**: (a) the exact regex patterns to add for spec+build coverage, with justification for each pattern; (b) cross-reference showing no collision with existing INTENT_RULES entries -- every new pattern tested against all 10 existing rules for overlap; (c) the expanded verb set for the build rule, verified against the maintenance-verb prompts identified in D5.1 as falling into the silent zone; (d) the specific line numbers in masonry-prompt-router.js where each new/modified rule should be inserted; (e) an estimate of the percentage of previously-silent prompts that would now receive a routing hint after both changes

---

### M2.1: Add silent zone hit rate and multi-turn routing collapse rate to monitor-targets.md with WARNING and FAILURE thresholds calibrated to Wave 1 baseline measurements

**Status**: DONE
**Finding**: findings/M2.1.md
**Completed**: 2026-03-29T11:00:00Z
**Operational Mode**: Monitor
**Priority**: LOW
**Motivated by**: D5.1 (WARNING) + D5.2 (WARNING) -- 40-60% of developer prompts hit the medium+no-intent silent zone; multi-turn workflows collapse by Turn 2 on every session; both are quantified baselines that should be tracked as Wave 2 fixes are deployed; without a monitor target, there is no way to verify that F2.2 (channel fix) and R2.2 (INTENT_RULES expansion) reduce the silent zone rate
**Hypothesis**: The silent zone rate will decrease measurably after F2.2 (prompt router channel fix) and R2.2 (INTENT_RULES expansion) are deployed; the multi-turn collapse rate will decrease after D2.5 (last_route persistence) is implemented; both metrics should be tracked with WARNING at the Wave 1 baseline and FAILURE above baseline
**Method**: fix-implementer (monitor-targets.md update only -- no code changes)
**Success criterion**: monitor-targets.md contains two new entries: (a) "silent-zone-hit-rate" with WARNING threshold at 50% (Wave 1 baseline upper bound) and FAILURE threshold at 60% (above baseline), measured by counting medium+no-intent exits in masonry-prompt-router.js logs per session; (b) "multi-turn-routing-signal-rate" with WARNING threshold at 40% (Turn 2+ signal coverage) and FAILURE threshold at 20% (near-zero coverage), measured by counting turns with non-empty routing hints vs. total turns in multi-step sessions; both entries include the Wave 1 source finding IDs as context
