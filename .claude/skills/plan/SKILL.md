---
name: plan
description: >-
  Interactive planning mode for the Autopilot system. Invokes the spec-writer
  agent to explore the codebase and write .autopilot/spec.md. Supports SPARC
  mode annotations, dependency graph, and phase_end markers for /build.
---

# /plan — Write an Autopilot Spec

When invoked, act as the **spec-writer** agent as defined in
`~/.claude/agents/spec-writer.md` (or `.claude/agents/spec-writer.md` in the
project if it exists there).

## What spec-writer does

1. **Reads the task description** — either from the user's prompt following `/plan`,
   or asks "What do you want to build?" if invoked with no arguments.

2. **Explores the codebase deeply** — reads relevant files, checks existing
   patterns, queries Recall for prior context, reviews any existing
   `.autopilot/spec.md`.

3. **Writes `.autopilot/spec.md`** — a precise, buildable specification with:
   - Goal and success criteria
   - Task list (numbered, ordered by dependency, with mode and depends annotations)
   - Files to create/modify per task
   - Test requirements per task
   - Design system constraints (if UI work)
   - Out of scope items

4. **Presents the spec to the user** — shows a full summary of the spec (all tasks, success criteria), then always close with:

   ```
   Spec written to .autopilot/spec.md — N tasks.

   What would you like to do?
     1. Build now — run /build immediately in this session
     2. Compact + build — compact context first, then auto-start build in the fresh session
     3. Not yet — I'll make changes or come back later
   ```

   **Option 2 (compact + build):** When the user picks option 2 (or says "compact first", "compact then build", "2"):
   - Write `.autopilot/mode` = `"build"` (signals auto-resume to session-start)
   - Write `.autopilot/progress.json` with all tasks in `"PENDING"` status (so session-start detects the pending build)
   - Write `.autopilot/build.log` with one entry: `[timestamp] COMPACT_HANDOFF: Spec approved. Compact and resume with /build.`
   - Tell the user:
     ```
     Build queued. Run /compact now — when you start the next session, the build will resume automatically.
     If auto-resume doesn't trigger, run /build to start manually.
     ```

   **If context is high (>750K tokens in this session):** proactively suggest option 2:
   ```
   ⚠ Context is high — option 2 (compact + build) is recommended to avoid degradation.
   ```

5. **Iterates on feedback** — if the user requests changes, update `spec.md`
   and re-present. Do NOT start building until the user explicitly runs `/build`
   or says "go", "build it", "approved", "looks good", etc.

## Rules

- NEVER start implementing code during `/plan` — exploration and spec writing only
- NEVER mark the spec as approved yourself — wait for the user
- If `.autopilot/spec.md` already exists, read it first and ask: "There's an
  existing spec — continue from it, or start fresh?"
- **Do NOT write `.autopilot/mode`** during planning — "plan" mode is not read by
  any hook or downstream system. The only modes that matter are `build`/`fix`
  (set by `/build`). Writing `mode = "plan"` triggers the session-lock and blocks
  every plan run after a recent session.
- Before writing `.autopilot/spec.md`, ensure the directory exists:
  ```bash
  mkdir -p .autopilot
  ```
- The spec must be concrete enough that a developer agent with no other context
  could implement it correctly

## Spec format

```markdown
# Spec: {feature name}

## Goal
{1-2 sentence description of what this builds and why}

## Success Criteria
- [ ] {measurable outcome 1}
- [ ] {measurable outcome 2}

## Tasks
- [ ] **Task 1** — {description}
  **Files:** {list of files to create or modify}
  **What to build:** {description}
  **Tests required:** {what tests prove this works}

- [ ] **Task 2** [mode:python] [depends:1] — {description}
  **Files:** ...
  **What to build:** ...
  **Tests required:** ...

- [ ] **Task 3** [mode:typescript] [depends:1] — {description} [phase_end:frontend]
  ...

## Out of Scope
- {things explicitly NOT included in this spec}

## Notes
- {architectural constraints, existing patterns to follow, gotchas}
```

## Task Annotations

Use these annotations on individual tasks. `/build` reads them to route correctly:

### `[mode:X]` — SPARC mode override
Tells `/build` which specialist agent to use for implementation.

| Annotation | Agent dispatched |
|------------|-----------------|
| `[mode:python]` | `python-specialist` — FastAPI, asyncio, SQLAlchemy |
| `[mode:typescript]` | `typescript-specialist` — React 19, Tailwind v4, Vitest |
| `[mode:database]` | `database-specialist` — PostgreSQL, Qdrant, Neo4j, Redis |
| `[mode:tdd]` | `tdd-london-swarm` — London-school parallel TDD |
| `[mode:tdd-deep]` | `tdd-orchestrator` — mutation testing + property-based + chaos |
| `[mode:security]` | `security` — OWASP audit, read-only |
| `[mode:devops]` | `devops` — Docker, CI/CD, infra |
| `[mode:architect]` | `architect` — design only, no code |
| `[mode:review-only]` | `peer-reviewer` — review only, no modifications |

If no annotation: `/build` uses the default `developer` agent.

### `[depends:N]` — Dependency ordering
Task will not start until task N is DONE. Use for tasks that depend on shared files
or interfaces established by earlier tasks.

```
- [ ] **Task 3** [mode:typescript] [depends:1] [depends:2] — build dashboard
```

### `[phase_end:name]` — Phase checkpoint commit
When `/build` completes this task, it creates a git tag `phase/{name}`. Use to
mark logical phases within a large build (e.g., `[phase_end:backend]`).

## Strategy Guidance

Suggest a strategy when presenting the spec if the nature of the work warrants it:

| Strategy | When to suggest |
|----------|-----------------|
| `conservative` | Security-sensitive work, production migrations, auth changes |
| `balanced` | Default — most feature work |
| `aggressive` | Prototyping, exploratory builds, non-critical tooling |

Mention strategy in the spec Notes section:
```
## Notes
- Suggested strategy: /build --strategy conservative (touches auth + payments)
```

## SPARC Context Docs

For larger specs (≥5 tasks), note in the spec that `/build` will run Phase 0:
- `pseudocode-writer` generates `.autopilot/pseudocode.md` before task 1
- `architecture-writer` generates `.autopilot/architecture.md` before task 1

Both docs are injected into every worker agent prompt. If you have architectural
constraints the writers should know, capture them in spec Notes.
