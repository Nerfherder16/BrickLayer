# Project Brief — inline-execution-audit

**Date**: 2026-03-29
**Campaign type**: Pure research (no simulate.py)
**Investigator**: Trowel (BL 2.0 campaign conductor)

---

## What This Project Investigates

Claude Code is configured via CLAUDE.md to route every request through Mortar, which dispatches work to specialist agents in parallel. The architecture explicitly states:

> "Every request goes through Mortar. Never do complex work solo when Mortar can dispatch a team."

Despite this instruction, Claude frequently defaults to **inline execution** — answering research questions directly, writing code in the main context, doing multi-step analysis without spawning agents. This campaign investigates **why** that happens, how reliably the delegation happens, and what structural or behavioral changes would close the gap.

---

## Key Invariants (System Design Truths)

1. **Mortar is the stated entry point for ALL work** — CLAUDE.md is explicit and comprehensive.
2. **The prompt router (masonry-prompt-router.js) pre-signals intent** — it injects routing hints before Claude processes the prompt.
3. **The agent fleet is extensive** — 55+ agents registered in agent_registry.yml, covering nearly every work type.
4. **bl-audit finding M1.4** identified "Mortar directive is advisory, not enforced — design decision needed" as a HIGH-severity open item.
5. **No enforcement mechanism exists** — there is no hook that blocks Claude from answering inline; only guidance text in CLAUDE.md.

---

## Known Failure Modes (from Prior Campaign bl-audit)

| ID | Finding | Severity |
|----|---------|----------|
| M1.4 | Mortar directive is advisory, not enforced | High |
| D5.1 | masonry-build.md uses dead OMC executor | Medium |
| D2.6 | uiux-master and solana-specialist .md files missing | Medium |

---

## Research Questions This Campaign Must Answer

The core gap: when given a prompt that CLAUDE.md says should route to an agent, Claude sometimes answers inline. We need to understand:

1. **Which prompt types trigger inline execution** vs. reliable delegation?
2. **What is the failure rate** of the Mortar routing directive across different task types?
3. **Why does the prompt router signal get ignored** — is it a context load issue, instruction conflict, or architectural gap?
4. **What enforcement mechanisms are possible** — hooks, penalties, auto-routing?
5. **Is the gap universal or session-specific** — does it depend on context size, model, session state?
6. **What does bl-audit M1.4 tell us** — was the advisory-not-enforced nature an intentional design choice or an oversight?

---

## Scope

**In scope:**
- Claude Code behavior when CLAUDE.md routing instructions are present
- The masonry-prompt-router.js hook and its signal injection mechanism
- The agent_registry.yml and agent fleet coverage
- Behavioral analysis from the bl-audit synthesis (Waves 1-3)
- Structural analysis of why instruction-following fails for routing

**Out of scope:**
- Simulation (no simulate.py — this is pure behavioral/structural research)
- Benchmarking latency or throughput
- Changes to CLAUDE.md or hook code (research only, no implementation)

---

## Source Authority

| Tier | Source | Authority |
|------|--------|-----------|
| Tier 1 | CLAUDE.md (Mortar section), bl-audit synthesis | Human-authored ground truth |
| Tier 2 | masonry-prompt-router.js, agent_registry.yml | Implementation truth |
| Tier 3 | findings/, questions.md | Research output |

---

## Success Criteria

This campaign succeeds if it produces:
1. A clear taxonomy of when inline execution occurs vs. delegation
2. Root cause analysis for the most common inline-execution failure patterns
3. Specific, actionable recommendations for enforcement (hook-level or architecture-level)
4. A verdict on whether M1.4 is fixable with current architecture or requires a design change
