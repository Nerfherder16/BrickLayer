---
name: parse-prd
description: >-
  Parse a Product Requirements Document into .autopilot/spec.md.
  Extracts: goal, user stories → success criteria, features → tasks.
  Assigns SPARC mode annotations. Adds complexity estimates (1-10).
---

# /parse-prd — PRD to Spec Converter

**Invocation**: `/parse-prd <file-path>` or `/parse-prd` (paste PRD text after invoking)

## Purpose

Convert a Product Requirements Document (PRD) into a buildable `.autopilot/spec.md`
that `/build` can execute. Extracts structure, converts requirements to tasks, annotates
with SPARC modes, and adds complexity estimates.

## Input Handling

- **With file path**: Read the file at the provided path. If the path does not exist,
  report the error and stop — do not create an empty spec.
- **Without file path**: Wait for the user to paste PRD text and signal EOF (or submit
  the message) before processing.
- **Existing spec.md**: If `.autopilot/spec.md` already exists, warn the user and ask
  whether to overwrite or append as additional tasks. Do not overwrite silently.

## Extraction Rules

### Goal

Extract from the PRD's "Overview", "Objective", "Problem Statement", or "Summary"
section. Write as 1-2 sentences. If no such section exists, infer the goal from the
document title and first paragraph.

### Success Criteria

Source: "Acceptance Criteria", "Definition of Done", "User Stories", or "Goals" sections.

- Convert each user story to one measurable success criterion
- Format: `- [ ] {measurable outcome}`
- Must be verifiable — not "users can easily X" but "users can complete X in under N steps"
- If the PRD uses "As a user / I want / So that" format, extract the "so that" clause as
  the criterion

### Tasks

Source: "Features", "Requirements", "Scope", "Deliverables" sections.

- One task per distinct deliverable or feature
- Break compound features into sub-tasks when they touch different files or layers
  (e.g., "User authentication" splits into API endpoint task + frontend form task)
- Order tasks by dependency: data models first, then services, then API, then UI
- If the PRD has no identifiable user stories or feature list, generate one task per
  top-level PRD section as a fallback

### SPARC Mode Annotations

Assign based on feature type — append `[mode:X]` after the task description:

| Feature type | Mode |
|---|---|
| UI components, React, TypeScript frontend, CSS, HTML | `[mode:typescript]` |
| API endpoints, Python services, business logic | `[mode:python]` |
| Database schema, migrations, queries | `[mode:database]` |
| Docker, deployment, CI/CD, infrastructure | `[mode:devops]` |
| Security review, auth, authorization, input validation | `[mode:security]` |
| Complex multi-class interaction, algorithm design | `[mode:tdd]` |
| Architecture decision, subsystem design | `[mode:architect]` |

### Complexity Estimates

Add a comment after each task description:

```
<!-- complexity: N/10 -->
```

Scale:
- 1-2: Trivial (config change, add a field, rename something) — under 1 hour
- 3-4: Simple (new endpoint with tests, new UI component) — half a day
- 5-6: Medium (new feature touching 2-3 layers) — 1 day
- 7-8: Hard (new subsystem, external service integration) — 2-3 days
- 9-10: Very hard (major architecture change, multiple subsystems) — multi-day

Estimate based on: number of files likely touched, presence of new data models,
external service dependencies, and test complexity.

### Out of Scope

Include anything the PRD explicitly excludes, plus anything a developer might
assume is included but the PRD is silent on.

## Output Format

Write to `.autopilot/spec.md`:

```markdown
# Spec: {project or feature name from PRD}

## Goal
{1-2 sentence goal extracted from PRD}

## Success Criteria
- [ ] {measurable criterion from user story 1}
- [ ] {measurable criterion from user story 2}

## Tasks

- [ ] **Task 1** [mode:database] — Create {model} schema and migration <!-- complexity: 3/10 -->
  **Files:** `{migration file}`, `{model file}`
  **What to build:** {description}

- [ ] **Task 2** [mode:python] — Implement {service} business logic <!-- complexity: 5/10 -->
  **Files:** `{service file}`
  **What to build:** {description}

- [ ] **Task 3** [mode:typescript] — Build {component} UI <!-- complexity: 4/10 -->
  **Files:** `{component file}`
  **What to build:** {description}

## Notes
{Constraints, tech choices, or assumptions from the PRD}

## Out of Scope
{Explicit exclusions from PRD + implied exclusions}
```

## Completion Summary

After writing the spec, print:

```
Parsed {N} requirements into {M} tasks.
Estimated complexity: low | medium | high
  (low = all tasks ≤5, medium = mix, high = any task ≥8)
Spec written to: .autopilot/spec.md
```

## Edge Cases

- File path does not exist: report error and stop
- No identifiable feature list: generate one task per top-level PRD section
- `.autopilot/spec.md` already exists: warn and ask to overwrite or append
- PRD pasted via stdin (no path): wait for full text before processing
- PRD has no user stories: use top-level requirement statements as success criteria
- Compound feature spans multiple layers: split into separate tasks per layer
