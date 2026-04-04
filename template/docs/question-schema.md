# BrickLayer 2.0 — Canonical Question Schema

This document is the authoritative reference for question format in `questions.md`.
All agents that read or write questions must conform to this schema.

**Referenced by**: `question-designer-bl2.md`, `mortar.md`, `hypothesis-generator.md`, `hypothesis-generator-bl2.md`

---

## Field Reference

Every question block is a markdown section with these fields:

```markdown
### {ID}: {question text}

**Status**: PENDING
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: what we expect to find — a falsifiable prediction
**Agent**: diagnose-analyst
**Success criterion**: what a definitive answer looks like
```

### Field: ID

Format: `{PREFIX}{wave}.{number}` — e.g. `D1.1`, `FR2.3`, `R1.4`

Prefix maps to Mode:

| Prefix | Mode |
|--------|------|
| `D` | diagnose |
| `F` | fix |
| `R` | research |
| `A` | audit |
| `V` | validate |
| `B` | benchmark |
| `E` | evolve |
| `M` | monitor |
| `P` | predict |
| `FR` | frontier |

### Field: Status

Valid values (exact case):

| Value | Meaning |
|-------|---------|
| `PENDING` | Not yet processed |
| `IN_PROGRESS` | Currently being worked (set by campaign loop) |
| `DONE` | Finding written, question closed |
| `INCONCLUSIVE` | Processed but no definitive finding |
| `BLOCKED` | Invalid mode or other structural issue — needs human |
| `PENDING_HUMAN` | Hit MAX_OVERRIDES — escalated to human |

### Field: Mode

Valid values (all lowercase):

| Mode | Routes to | Notes |
|------|-----------|-------|
| `diagnose` | diagnose-analyst | Root cause analysis |
| `fix` | fix-implementer | Requires DIAGNOSIS_COMPLETE finding |
| `research` | research-analyst, regulatory-researcher, or competitive-analyst | Use **Agent**: to disambiguate |
| `audit` | compliance-auditor | Requires audit-checklist.md |
| `validate` | design-reviewer | Pre-build design review |
| `benchmark` | benchmark-engineer | Performance baseline measurement |
| `evolve` | evolve-optimizer | Requires benchmarks.json baseline |
| `monitor` | health-monitor | Requires monitor-targets.md |
| `predict` | cascade-analyst | Failure cascade analysis |
| `frontier` | frontier-analyst | Exploration epistemology, not falsification |
| `simulate` | quantitative-analyst | BL 1.x compatibility — economic simulation |
| `agent` | {**Agent**: field} | Direct routing — use **Agent**: to name the target |

**Mortar rejects any Mode not in this list.** Questions with unrecognized modes are marked BLOCKED at startup.

### Field: Priority

Valid values: `HIGH`, `MEDIUM`, `LOW`

Mortar processes questions in order: HIGH first, then MEDIUM, then LOW. Within a tier, order is by position in the file.

### Field: Hypothesis

A falsifiable prediction — what the agent expects to find and why.
- Good: "The decay function clamps to 0.05 because constants.py line 12 defines MIN_IMPORTANCE = 0.05"
- Bad: "There might be an issue with the decay function"

For Frontier mode: describe what capability you're exploring, not a prediction to falsify.

### Field: Agent

The specialist agent that will run this question. Must be a filename (without .md) of an agent in `.claude/agents/`.

| Mode | Default agent | Alternate |
|------|---------------|-----------|
| `diagnose` | `diagnose-analyst` | — |
| `fix` | `fix-implementer` | — |
| `research` | `research-analyst` | `regulatory-researcher`, `competitive-analyst` |
| `audit` | `compliance-auditor` | — |
| `validate` | `design-reviewer` | — |
| `benchmark` | `benchmark-engineer` | — |
| `evolve` | `evolve-optimizer` | — |
| `monitor` | `health-monitor` | — |
| `predict` | `cascade-analyst` | — |
| `frontier` | `frontier-analyst` | — |
| `simulate` | `quantitative-analyst` | — |

### Field: Success criterion

What a definitive answer looks like — the bar that makes a finding DONE rather than INCONCLUSIVE.
- Good: "The test suite passes and `python simulate.py` returns verdict: HEALTHY"
- Bad: "We understand the issue"

---

## Optional Fields

These fields are added by Mortar after processing:

```markdown
**Finding**: findings/D1.1.md
**Completed**: 2026-03-17T14:32:00Z
**Override count**: 0
```

---

## Example — Complete Question Block

```markdown
### D1.1: Does the memory decay function correctly clamp importance scores to a minimum of 0.05?

**Status**: PENDING
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: The clamp is implemented in bl/memory.py but the test at line 45 uses the wrong comparison operator, allowing scores below 0.05.
**Agent**: diagnose-analyst
**Success criterion**: Test suite passes with a case that confirms scores never fall below 0.05 after decay.
```

---

## Common Mistakes

| Mistake | Effect | Fix |
|---------|--------|-----|
| `**Mode**: Diagnose` (CamelCase) | Mortar marks BLOCKED | Use lowercase: `diagnose` |
| `**Operational Mode**: diagnose` (wrong field name) | Mortar ignores it — routes to default | Use `**Mode**:` |
| `**Method**: diagnose-analyst` (wrong field name) | Mortar ignores agent override | Use `**Agent**:` |
| Mode not in valid list | Mortar marks BLOCKED at startup | Check mode table above |
| Missing `**Mode**:` field entirely | Mortar marks BLOCKED | Add Mode field |
