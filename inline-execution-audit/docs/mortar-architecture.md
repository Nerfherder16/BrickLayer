# Mortar Architecture — Research Reference

Source: C:/Users/trg16/.claude/CLAUDE.md (Mortar section)

## Core Directive

Every request goes through Mortar. Mortar reads the request, decides the right agents, and dispatches in parallel. All agents report to Mortar.

## Work Type → Agent Mapping

| Work Type | Mortar dispatches to |
|-----------|----------------------|
| Coding task | developer + test-writer + code-reviewer (parallel) |
| Research question | research-analyst + competitive-analyst + others (parallel) |
| Campaign / simulation | Trowel (owns the full BL 2.0 loop) |
| Git hygiene | git-nerd |
| Folder organization / project structure | karen |
| UI / design | uiux-master |
| Architecture decisions | architect or design-reviewer |
| Debugging unknown failure | diagnose-analyst |
| Security review | security agent |
| Spec + build | spec-writer → developer pipeline |

## Core Behavior Rules

- **Every request** → Mortar routes it first
- **Parallel by default** — independent tasks always dispatched simultaneously
- **After any code changes** → git-nerd proactively handles commits and branch hygiene
- **Messy project state** → karen audits and organizes without being asked
- **Campaigns/sims** → Mortar hands to Trowel; Trowel owns that loop end-to-end
- Mortar communicates this architecture to every agent it spawns so they understand their role

## Operating Principles

- Never resume an autopilot build from a prior session — surface the state and ask
- Delegate specialist work to agents — multi-file implementations, debugging, reviews, planning
- Prefer evidence over assumptions — verify outcomes before claiming completion
- Lightest path that preserves quality — direct action when trivial, agents when substantive
- Consult docs (context7) before implementing with unfamiliar SDKs or APIs
- Run independent tasks in parallel — use multiple Agent calls in a single message

## Key Observation: "Trivial vs. Substantive" Threshold

The directive says: "Lightest path that preserves quality — direct action when trivial, agents when substantive."

This creates an intentional bypass for trivial tasks. The research question is: **how is "trivial" defined in practice?** Claude must make a judgment call at every request. This judgment call is the primary locus of inline execution vs. delegation decisions.

## Enforcement Gap (from bl-audit M1.4)

The Mortar directive is ADVISORY. There is no enforcement hook. Claude can always choose to answer inline without being blocked. The hook system (masonry-prompt-router.js) injects routing suggestions but cannot force delegation.

This was identified as HIGH severity in bl-audit Wave 2 and remains an open item.
