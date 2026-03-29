# BL-Audit Relevant Findings — Research Reference

Source: C:/Users/trg16/Dev/Bricklayer2.0/bl-audit/findings/synthesis.md (Wave 3 synthesis)

## Directly Relevant Findings

### M1.4 — Mortar directive is advisory, not enforced [HIGH SEVERITY — OPEN]

**Status**: Open (not fixed as of Wave 3 synthesis, 2026-03-22)

**Finding**: The Mortar directive in CLAUDE.md is advisory — Claude reads it and may or may not comply. No enforcement mechanism exists to block inline execution when delegation is required. This was found in Wave 2 (Mortar Routing audit, M1.x series).

**Significance for this campaign**: This is the root architectural gap that this campaign investigates. M1.4 confirmed the gap exists but did not explain *why* it manifests, *how frequently*, or *which triggers* cause inline execution vs. delegation.

**Wave 2 note from synthesis**: "Mortar directive is advisory, not enforced — design decision needed." The bl-audit team identified this as a design decision required from Tim. No automated fix was attempted because it requires architectural intent: should enforcement be done via hooks (pre-tool blocking), model instructions (stronger CLAUDE.md language), or structural constraints (no direct output path)?

---

### D5.1 — masonry-build.md uses dead OMC executor [MEDIUM — OPEN]

**Relevance**: A documentation file that references a deleted executor. If Claude reads this file when routing build tasks, it may attempt to use the dead path rather than delegating to the developer agent. Contributes to inline execution for build tasks.

---

### D2.6 — uiux-master and solana-specialist .md files missing [MEDIUM — OPEN]

**Relevance**: If agent .md files are missing, routing to those agents fails silently or forces inline execution. When the agent file doesn't exist, there's no capability specification for Claude to delegate to.

---

### E1.9 — Auto-loaded context is 22,587 tokens [FALSE POSITIVE but informative]

**Finding**: Context load was 45% of threshold. Main inefficiency: 12,423 tokens of UI-specific rules (figma-designer-guide.md, figma-mcp-workflow.md, figma-workflow.md, frontend-design-philosophy.md, react-tailwind-standards.md) loaded in non-UI sessions.

**Relevance**: High context load may reduce effective weight of Mortar routing instructions. In a 22K-token context, the CLAUDE.md Mortar section (which covers routing) is one of many competing instruction sets. The UI rules alone consume more tokens than the Mortar routing section.

---

## Pattern Relevant to This Campaign

### Pattern 6 (Wave 3): Incremental Growth Without Refactoring

"The hook system grew from a few files to 15+ hooks without extracting shared utilities."

**Inference for this campaign**: The same incremental growth pattern may apply to Claude's routing behavior. New agents, new work types, and new instructions were added to CLAUDE.md incrementally without a single authoritative enforcement mechanism. The result is a routing *suggestion* system rather than a routing *enforcement* system.

---

## Wave 2 Mortar Routing Summary (M1.x series)

| ID | Finding | Verdict | Severity |
|----|---------|---------|----------|
| M1.1 | Critical hook bug (output format) | CONFIRMED — Fixed | Critical → Fixed |
| M1.2 | (not referenced in synthesis) | — | — |
| M1.3 | masonry-register.js plain text output | CONFIRMED — Open | High |
| M1.4 | Mortar directive advisory, not enforced | CONFIRMED — Open | High |
| M1.5 | (not referenced) | — | — |
| M1.6 | mortar.md missing git-nerd/infra entries | CONFIRMED — Open | Medium |

The entire M1.x series was about **gaps in the routing layer**. M1.4 is the most structurally significant: it means the routing architecture has no authority.
