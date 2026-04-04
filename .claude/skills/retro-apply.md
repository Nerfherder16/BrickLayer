---
name: retro-apply
description: Convert retro-actions.md CODE/OUTPUT/DEPENDENCY fix items into a buildable .autopilot/spec.md, then hand off to /build — skips WORKFLOW and CONFIG items automatically
user-invocable: true
---

# /retro-apply — Apply Retrospective Actions

Reads `retro-actions.md` from the current project, converts `CODE` and `OUTPUT` fix items into a buildable `.autopilot/spec.md`, then waits for your approval before running `/build`.

## What It Does

1. Reads `retro-actions.md` in the current directory (must exist — run after `/masonry-run` wave-end)
2. Filters to actionable items: `Fix type: CODE`, `OUTPUT`, or `DEPENDENCY`
3. Skips `WORKFLOW` items (environment recommendations, not buildable)
4. Skips `CONFIG` items (project-local calibration, not a build task)
5. Invokes spec-writer to produce `.autopilot/spec.md` from the filtered items
6. Presents spec to you for approval
7. On approval: invokes `/build`

## Invocation

```
/retro-apply
```

No arguments. Must be run from the campaign project directory containing `retro-actions.md`.

## How to Invoke

Spawn the spec-writer agent with the retro-apply context:

```
Use the spec-writer agent defined in ~/.claude/agents/spec-writer.md.

Request: Convert retro-actions.md into a build spec.

Read retro-actions.md in the current directory. Extract all items where Fix type is CODE,
OUTPUT, or DEPENDENCY. Ignore WORKFLOW and CONFIG items.

For each extracted item, create a task in .autopilot/spec.md:
- Task description: the item's Proposed fix field
- File targets: derived from the item's surface symptom + proposed fix
- Test strategy: "Verify the friction described in the item no longer occurs in a fresh campaign run"
- Mark items with Universality=UNIVERSAL as higher priority than PROJECT items

After writing the spec, present it and ask for approval before proceeding.
On approval, run /build.

Project directory: [current working directory]
```

## When to Use

After any BrickLayer wave that produced a `retro-actions.md` file with CRITICAL or HIGH items.
The retrospective agent writes `retro-actions.md`; `/retro-apply` converts it into executable build tasks.

## What Gets Built vs Skipped

| Fix type | Action |
|----------|--------|
| `CODE` | Spec task → `/build` |
| `OUTPUT` | Spec task → `/build` |
| `DEPENDENCY` | Spec task → `/build` (adds to requirements.txt) |
| `WORKFLOW` | Skipped — surfaced to user as a recommendation only |
| `CONFIG` | Skipped — project-local, not a framework change |

## Output

- `.autopilot/spec.md` — ready for `/build`
- User sees: spec summary, task count, WORKFLOW items listed separately as recommendations
