---
name: spec-mine
description: >-
  Inverse spec-writer — mines existing code into a .autopilot/spec.md describing what
  the code DOES. Analyzes public API, data models, business logic, test coverage gaps.
  Useful for legacy code, onboarding, or refactor preparation.
---

# /spec-mine — Mine Code Into a Spec

**Invocation**: `/spec-mine <path or module>`

## Purpose

The inverse of `/plan`. Instead of writing a spec for what to build, this reads existing
code and writes a spec describing what was already built. Useful for:
- Onboarding new contributors to a codebase
- Writing tests for legacy code with no spec
- Preparing for a refactor (know what you have before changing it)
- Documenting undocumented code

The output describes the current implementation, not a desired future state. Task
descriptions are written in past tense to signal this distinction.

## Path Resolution

- If the argument points to a **single file**: analyze only that file
- If the argument points to a **directory**: analyze all non-test, non-config files within it
  (skip `test_*`, `*_test.*`, `*.test.*`, `*.spec.*`, `tsconfig.json`, `*.config.*`, `*.lock`)
- If the path does **not exist**: report the error and stop immediately

## What to Extract

For the target path or module, analyze:

**1. Public API Surface**
- All exported functions, classes, endpoints, CLI commands and their signatures
- What each public function does (behavioral, not implementation detail)
- Input types, output types, observable side effects

**2. Data Models**
- Database models, Pydantic schemas, TypeScript interfaces, Zod schemas
- Relationships between models
- Validation rules, constraints, and invariants visible in the code

**3. Business Logic Flows**
- The main "happy path" for each feature or module entry point
- Error handling paths (what gets caught, what propagates)
- Integration points with other modules or external services

**4. Test Coverage Gaps**
- What behaviors have existing tests
- What behaviors have NO tests — these become tasks annotated `[mode:tdd]`
- Edge cases visible in the code but not exercised by any test

**5. Undocumented Behaviors**
- Side effects not obvious from the function signature
- Assumptions baked into the code (magic numbers, implicit ordering, globals)
- Known limitations or TODO/FIXME comments

## Output

If `.autopilot/spec.md` already exists, warn the user and ask for confirmation before
overwriting. Do not overwrite silently.

Write to `.autopilot/spec.md` using the standard spec format:

```markdown
# Spec: {module name} — Existing Behavior

## Goal
Document the existing behavior of {module} for onboarding, testing, and refactor preparation.

## What This Code Does
{1-2 paragraph description of the module's purpose, written in present tense}

## Success Criteria
- [ ] All exported functions documented with behavioral descriptions
- [ ] All data models documented with their constraints
- [ ] Coverage gaps identified as explicit tasks

## Tasks (Reverse-Engineered)

- [ ] **Task 1** [mode:tdd] — Write tests for {function} (currently untested)
  **Files:** {test file to create}
  **What to build:** Tests covering: {list of behaviors discovered in the code}

- [ ] **Task 2** — Documents behavior of {function}
  **Files:** {source file analyzed}
  **Behaviors:** {description in past tense}

## Notes
{Any undocumented behaviors, assumptions, or TODOs found in the code}

## Out of Scope
{Any paths or behaviors explicitly excluded from this analysis}
```

Generated spec tasks have **no** `[depends:N]` annotations — dependency order is inferred
from the code structure, not prescribed.

After writing the spec, print a summary:

```
spec-mine complete:
  Files analyzed: N
  Exported functions found: N
  Data models found: N
  Test coverage gaps: N (these are [mode:tdd] tasks in the spec)
  Spec written to: .autopilot/spec.md
```

## Edge Cases

- Single file target: scope analysis to that file only; do not crawl its imports
- Directory target: skip test files, config files, lock files, and static assets
- Path does not exist: report error and stop — do not create an empty spec
- `.autopilot/spec.md` already exists: warn and ask for confirmation before overwriting
- No public exports found: note this in the spec Goal section and list internal functions
  as the API surface with a warning that the module may be private
- Tasks have no `[depends:N]` annotations (order is described, not prescribed)
