# Roadmap -- inline-execution-audit

Prioritized remediation items from Wave 1, ordered by impact/effort ratio.

---

## Priority 1: Instruction Layer Fix (High Impact, Low Effort)

| # | Item | Files | Effort | Finding |
|---|------|-------|--------|---------|
| 1.1 | Replace CLAUDE.md line 68 escape hatch with operational definition of "trivial" (single-sentence factual lookups only) | `~/.claude/CLAUDE.md` | 1 text edit | D1.1 |
| 1.2 | Switch prompt router from hookSpecificOutput to additionalContext channel | `masonry/src/hooks/masonry-prompt-router.js` | ~10 lines | D1.3 |
| 1.3 | Rewrite routing hint from annotation format to imperative directive format | `masonry/src/hooks/masonry-prompt-router.js` | Same change as 1.2 | D1.3 |

---

## Priority 2: Intent Coverage Expansion (High Impact, Medium Effort)

| # | Item | Files | Effort | Finding |
|---|------|-------|--------|---------|
| 2.1 | Add maintenance verbs to build rule (fix, update, make, change, set, configure, apply, enable, disable, modify) | `masonry/src/hooks/masonry-prompt-router.js` L75-81 | ~5 lines regex | D5.1 |
| 2.2 | Add spec-writer INTENT_RULE for spec/plan/blueprint/outline vocabulary | `masonry/src/hooks/masonry-prompt-router.js` | ~8 lines new rule | D3.1 |
| 2.3 | Resolve first-match collision priority (changelog, architecture, debug+CSS) | `masonry/src/hooks/masonry-prompt-router.js` | Refactor detection loop | D3.1 |
| 2.4 | Expand research/analyze rule with missing verbs (look into, check if, assess, review, examine, verify) | `masonry/src/hooks/masonry-prompt-router.js` L103+ | ~3 lines regex | D5.1 |

---

## Priority 3: Enforcement Gate Activation (High Impact, Medium Effort, Requires Atomicity)

All 5 items must be deployed simultaneously. Do not deploy 3.3 without 3.1-3.2.

| # | Item | Files | Effort | Finding |
|---|------|-------|--------|---------|
| 3.1 | Implement receipt writer: Mortar writes mortar_consulted:true + mortar_session_id to per-session temp file | Mortar agent instructions + masonry-state.json schema | ~15 lines | D2.2 |
| 3.2 | Implement per-prompt reset: prompt router resets mortar_consulted:false at UserPromptSubmit | `masonry/src/hooks/masonry-prompt-router.js` | ~5 lines | D2.2 |
| 3.3 | Convert advisory gate to hard block for Write/Edit (behind MASONRY_ENFORCE_ROUTING=1 env flag) | `masonry/src/hooks/masonry-approver.js` L293-301 | ~15 lines | D2.1 |
| 3.4 | Add effort:low trivial bypass to gate condition | `masonry/src/hooks/masonry-approver.js` | ~10 lines | V1.1 |
| 3.5 | Migrate receipt store from global singleton to per-session temp file | `masonry/src/hooks/masonry-approver.js` | ~10 lines | D2.2, V1.1 |

---

## Priority 4: Dark Fleet Activation (Medium Impact, High Effort)

| # | Item | Files | Effort | Finding |
|---|------|-------|--------|---------|
| 4.1 | Populate routing_keywords for high-value dark fleet agents (python-specialist, typescript-specialist, database-specialist, devops, docker-specialist, fastapi-specialist) | `masonry/agent_registry.yml` | ~30 entries | D4.2 |
| 4.2 | Expand Mortar dispatch table beyond 10 work types (language-specific, infrastructure, data) | `~/.claude/CLAUDE.md` | Table expansion | D4.2 |
| 4.3 | Prune 31 stub agents or fill them with substantive content | `masonry/agent_registry.yml` + agent .md files | Audit + writes | D4.2 |
| 4.4 | Add file-existence validation to router before returning RoutingDecision | `masonry/src/routing/router.py` | ~10 lines | D4.1 |

---

## Priority 5: Multi-Turn Routing (Medium Impact, Medium Effort)

| # | Item | Files | Effort | Finding |
|---|------|-------|--------|---------|
| 5.1 | Add last_route persistence field to masonry-state.json (written by prompt router, inherited by next turn) | `masonry/src/hooks/masonry-prompt-router.js` + state schema | ~15 lines | D3.2 |
| 5.2 | Add follow-up detection patterns (now, also, same, again, this, that, it) | `masonry/src/hooks/masonry-prompt-router.js` | ~10 lines regex | D3.2 |
| 5.3 | Fix campaign mode routing blackout: suppress hints only for Trowel-assigned questions, not all prompts | `masonry/src/hooks/masonry-prompt-router.js` L183-188 | ~5 lines | D3.2, D5.1 |

---

## Priority 6: Context Optimization (Low Impact, Low Effort)

| # | Item | Files | Effort | Finding |
|---|------|-------|--------|---------|
| 6.1 | Move 6 UI rules files to conditional load group (verify subdirectory exclusion behavior first) | `~/.claude/rules/` -> `~/.claude/rules/ui/` | File move | D1.2 |
| 6.2 | Add conditional load directive to CLAUDE.md for UI rules (load only when UI work detected) | `~/.claude/CLAUDE.md` | Text addition | D1.2 |

---

## Architectural Decisions Required (Tim)

| Decision | Context | Finding |
|----------|---------|---------|
| Bash enforcement scope | Gate Bash same as Write/Edit, or formally accept as ungated bypass? Current: unconditionally exempt. | V1.1, FR1.1 |
| Enforcement rollout strategy | Env flag (MASONRY_ENFORCE_ROUTING=1) for testing, then default-on? | D2.1, V1.1 |
| Dark fleet activation pace | Stage 1: high-value specialists -> Stage 2: campaign agents -> Stage 3: stubs? | D4.2 |

---

## Out of Scope (Platform Constraints)

These require Claude Code platform changes from Anthropic and cannot be addressed within Masonry:

- PreTextGeneration hook event (would enable forced routing before any response)
- Conversation history in hook payloads (would enable multi-turn routing continuity)
- Forced tool invocation from hooks (would enable mandatory Agent tool calls)
