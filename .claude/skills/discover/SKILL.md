---
name: discover
description: >-
  Jobs-to-be-Done discovery + assumption mapping + experiment design.
  3-phase framework to validate a feature idea before building it.
  Output: .discover/{slug}/discovery.md with JTBD canvas, assumption map, experiment backlog.
---

# /discover — JTBD Discovery + Experiment Design

**Invocation**: `/discover <feature or hypothesis>`

## Purpose

Before building, validate. This skill runs a structured discovery process to:
1. Understand WHY someone would use the feature (JTBD)
2. Surface the assumptions that must be true for it to succeed
3. Design the cheapest experiments to test those assumptions

## Output Path

Create `.discover/{slug}/discovery.md` where `{slug}` is a URL-safe version of the
feature or hypothesis text: lowercase, spaces replaced with hyphens, special characters
stripped.

If `.discover/` does not exist, create it.

If a `discovery.md` already exists for the same slug, append a timestamp suffix to the
filename rather than overwriting: `discovery-{YYYYMMDD-HHmmss}.md`.

Print the full path after generation.

## Phase 1 — Jobs-to-be-Done Analysis

Answer each question explicitly in the output:

**Who hires this feature?**
Be specific. Not "developers" but "backend developers working on distributed systems
who deploy twice a week." Name the persona.

**What job are they trying to do?**
Write the functional job in JTBD format:
"When I {situation}, I want to {motivation}, so I can {outcome}."

**What are they firing?**
What solution, workaround, or behavior does this feature replace? What does the user
do today without this feature?

**Functional, emotional, and social jobs:**
- **Functional**: The task they are trying to accomplish
- **Emotional**: How they want to feel (less frustrated, more confident, in control)
- **Social**: How they want to be perceived (competent, organized, efficient)

## Phase 2 — Assumption Mapping

Generate exactly **five** assumptions ordered by: **Importance × Uncertainty**

For each assumption:

```
**Assumption N:** {The thing that must be true for this feature to succeed}
**Importance:** HIGH | MEDIUM | LOW
  (How critical is this to the feature's core value proposition?)
**Uncertainty:** HIGH | MEDIUM | LOW
  (How little do we currently know about whether this is true?)
**Priority Score:** HIGH×HIGH=1, HIGH×MEDIUM=2, HIGH×LOW=3, MEDIUM×HIGH=2,
                   MEDIUM×MEDIUM=4, LOW×HIGH=3, etc. Lower = highest priority.
```

List in ascending priority score order (most critical assumptions first).

## Phase 3 — Experiment Design

For each of the five assumptions, propose the cheapest falsifiable test — a test that
could prove the assumption wrong without building the full feature.

```
**Assumption:** {text from Phase 2}
**Experiment type:** Survey | Prototype | A/B test | Data pull | Interview | Fake door | Analytics
**Design:** {Exact steps to run the experiment}
**Success metric:** {What result confirms the assumption is likely true}
**Failure signal:** {What result would falsify the assumption}
**Estimated effort:** {N hours or N days}
**Estimated time to result:** {N days or N weeks}
```

## discovery.md Structure

```markdown
# Discovery: {feature or hypothesis}

Generated: {ISO-8601 timestamp}

---

## JTBD Canvas

**Persona:** {specific user description}

**Functional job:**
When I {situation}, I want to {motivation}, so I can {outcome}.

**Currently firing:** {what they do today}

**Functional job:** {task}
**Emotional job:** {feeling}
**Social job:** {perception}

---

## Assumption Map

{5 assumptions in priority order, formatted as above}

---

## Experiment Backlog

{5 experiments, one per assumption, formatted as above}

---

## Next Step

Run experiment for Assumption 1 first — it has the highest importance × uncertainty score.
```

## Edge Cases

- `.discover/` does not exist: create it before writing
- Same slug already has a `discovery.md`: append timestamp suffix, do not overwrite
- Feature description is very short (1-3 words): ask a single clarifying question
  before proceeding — "Can you describe the feature in one sentence?"
- No argument provided: print usage and stop
