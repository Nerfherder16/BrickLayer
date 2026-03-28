# /teach-bricklayer — Context Gathering Protocol

One-time project setup skill. Asks 8 targeted questions, then writes `.bricklayer.md` — a persistent context file read by all agents at session start.

## Trigger

`/teach-bricklayer`

Run once per new project.

## The 8 Questions

1. **Project name and purpose** (1-2 sentences)
2. **Tech stack** (languages, frameworks, databases, infrastructure)
3. **Current state** (prototype / MVP / production / legacy)
4. **The most important invariant** — what must NEVER break?
5. **The hardest problem** — what keeps you up at night?
6. **How you want agents to communicate** (terse/detailed, proactive/reactive)
7. **What NOT to do** — common mistakes to avoid in this codebase
8. **Key external dependencies** — APIs, services, teams to reference

## Output: .bricklayer.md

```markdown
# BrickLayer Project Context

## Project
{name and purpose}

## Stack
{tech stack}

## Current State
{prototype/MVP/production/legacy}

## Critical Invariants
{from Q4 — highest priority for all agents}

## Hard Problems
{from Q5 — agents apply extra caution here}

## Communication Style
{terse/detailed/proactive/reactive}

## Don'ts
{patterns to avoid}

## External Dependencies
{APIs, services, people}

## Agent Instructions
Read this file at session start before doing anything else.
Prioritize Critical Invariants above all other concerns.
Apply the Communication Style in all responses.
```

## Session Start Integration

Once `.bricklayer.md` exists, `masonry-session-start.js` reads it automatically and injects content into every agent spawn as system context.

## Updating

Re-run `/teach-bricklayer` when context changes significantly, or edit `.bricklayer.md` directly.

## Notes
- Interactive: asks one question at a time
- Non-destructive: if `.bricklayer.md` exists, shows current content and asks "update or keep?"
- Recommended: run after `/plan` on any new project
