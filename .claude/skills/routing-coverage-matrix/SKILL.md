---
name: routing-coverage-matrix
description: Map routing rules against work types to find silent zones, first-match collisions, and orphaned routes
---

# /routing-coverage-matrix — Routing Coverage Analysis

Produces a cross-reference matrix showing which work types have routing coverage, which have silent zones, and where first-match collisions cause misrouting. Distilled from D3.1 (INTENT_RULES coverage gap) and D5.1/D5.2 (silent zone analysis) in the inline-execution-audit campaign.

## Steps

### 1. Locate routing configuration

Find the router file (typically `masonry/src/hooks/masonry-prompt-router.js` or equivalent):
- Read the INTENT_RULES array (or equivalent routing table)
- Extract each rule: patterns[], route, note

Find the routing target table (typically in CLAUDE.md or mortar.md):
- Extract each work type → agent mapping

### 2. Build the cross-reference matrix

For each **work type** in the routing target table:
- Find the INTENT_RULES entry that would match it
- If found: note the patterns and first-match position
- If missing: **SILENT ZONE** — mark as uncovered

For each **INTENT_RULES entry**:
- Find the corresponding work type
- If no work type matches: **ORPHANED RULE** — exists in router but has no dispatch target

Output the matrix:

```
Routing Coverage Matrix — [project]

Work Type             | INTENT_RULE Entry       | Coverage  | Notes
----------------------|-------------------------|-----------|-------
Coding task           | build rule (L74)        | DEGRADED  | missing: fix|update|set verbs
Research question     | research rule (L103)    | OK        |
Campaign/simulation   | campaign rule (L33)     | OK        |
Spec + build          | (none)                  | SILENT    | /plan slash handled, natural language not
Git hygiene           | git rule (L82)          | OK        |
UI/design             | ui rule (L58)           | DEGRADED  | too broad — catches non-UI mentions of "css"
Architecture          | arch rule (L51)         | COLLISION | first-match steals from research-analyst
Debugging             | debug rule (L67)        | OK        |
Security review       | security rule (L44)     | OK        |
Documentation         | docs rule (L96)         | OK        |
Refactoring           | refactor rule (L89)     | ORPHANED  | routes to refactorer, not in Mortar dispatch
```

### 3. Test for first-match collisions

For each pair of rules where the patterns could overlap, construct test prompts that should hit Rule B but hit Rule A first:

Test prompt: "architect a database schema for the new feature"
- Expected: architect + design-reviewer (L51)
- Actual: architect + design-reviewer (L51) ← OK in this case
- But: "investigate the architecture of this service" → research rule (L103) or architecture rule (L51)?
  - Pattern test: `\b(architect|architecture)\b` fires at L51 BEFORE `\b(investigate)\b` at L103
  - **COLLISION**: investigation of architectural topics routes to architect, not research-analyst

For each collision, note: which work type is swallowed, what the correct route should be.

### 4. Analyze the silent zone

The silent zone is prompts that match **no INTENT_RULE** and also have **medium** effort (default fallback).

Run effort classification against a sample prompt set:
- Short prompts (< 50 chars): `effort = low` — hint emitted as `[effort:low]` only
- Question-form prompts (`what|where|how|why...`): `effort = low`
- Standard dev prompts without trigger words: `effort = medium` → **silent exit**

Identify the most common prompt patterns that hit the silent zone:
- Maintenance verbs: "fix the", "update the", "change", "set", "configure"
- Continuation prompts: "now do", "also", "same for", "continue", "next"
- Follow-up after context: "what about", "and then", "additionally"

Estimate the silent zone rate: what % of typical session prompts hit no rule AND get medium effort?

### 5. Report and recommend

```
ROUTING COVERAGE SUMMARY

Silent Zones:    N work types  ← no routing coverage at all
Degraded:        N work types  ← coverage present but verb gaps or broad patterns
Collisions:      N             ← first-match steals traffic from correct route
Orphaned Rules:  N             ← router rule has no dispatch target

Silent Zone Prompts: ~X% of typical session prompts receive no routing signal

Recommended Fixes (in priority order):
1. [SILENT ZONE] Add INTENT_RULE for [work type]: [proposed regex]
2. [DEGRADED] Expand [rule] verb set: add [verbs]
3. [COLLISION] Reorder [rule A] after [rule B] at position N
4. [ORPHANED] Either add [agent] to Mortar dispatch or remove the orphaned rule
```

## Notes

- This skill is read-only — only analyzes, never modifies routing files
- Test any proposed regex against all existing rules before adding to verify no new collisions
- Place more specific rules BEFORE more general ones in the array
- The "medium effort is default fallback with zero regex" pattern is a common silent zone cause
