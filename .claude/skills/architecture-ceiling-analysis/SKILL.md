---
name: architecture-ceiling-analysis
description: Map the enforcement ceiling of a hook/plugin system — distinguish fundamental platform limits from incidental code gaps that can be fixed
---

# /architecture-ceiling-analysis — Architecture Ceiling Mapping

Maps the ceiling of what a hook or plugin system can structurally enforce versus what is blocked by platform constraints. Distinguishes fundamental limits (outside your control) from incidental gaps (missing code, fixable). Distilled from FR1.1 (architecture ceiling analysis) in the inline-execution-audit campaign.

## Steps

### 1. Identify the enforcement goals

List what behavior enforcement is trying to achieve:
- What should ALWAYS happen before X?
- What should NEVER happen without Y?
- What should be BLOCKED if Z condition is not met?

### 2. Map available hook events

Read the platform documentation (or infer from existing hooks) to list:
- What events can hooks intercept? (PreToolUse, PostToolUse, UserPromptSubmit, Stop, etc.)
- What can each hook event DO? (allow, deny, inject context, modify parameters, block)
- What can each hook event NOT do? (force tool invocation, intercept text generation, modify response)

Build a capability table:

```
Hook Event          | Can Allow/Deny | Can Inject Context | Can Force Action
--------------------|----------------|--------------------|-----------------
PreToolUse          | YES            | YES (additionalContext) | NO (can't force Agent invocation)
PostToolUse         | YES (advisory) | YES (stderr log)   | NO
UserPromptSubmit    | YES (exit)     | YES (additionalContext) | NO
Stop                | YES (block)    | NO                 | NO
PreTextGeneration   | N/A (doesn't exist) | N/A          | N/A
```

### 3. Classify each enforcement goal

For each enforcement goal, classify against the capability table:

| Goal | Hook Required | Hook Available? | Verdict |
|------|-------------|----------------|---------|
| Force Mortar before any response | PreTextGeneration hook | NOT AVAILABLE | **FUNDAMENTAL GAP** |
| Block Write/Edit without routing receipt | PreToolUse deny | AVAILABLE | VIABLE |
| Force Agent tool invocation | No hook can do this | NOT AVAILABLE | **FUNDAMENTAL GAP** |
| Enforce Bash exemption list | PreToolUse Bash check | AVAILABLE | VIABLE |
| Multi-turn routing continuity | Conversation-aware hook | NOT AVAILABLE | **FUNDAMENTAL GAP** |
| Per-turn receipt reset | UserPromptSubmit reset | AVAILABLE | VIABLE |

**Fundamental Gap**: The platform does not provide the hook event needed. Cannot be solved within the current architecture.
**Viable**: The hook event exists and has the necessary capability. May require code to be written.

### 4. Separate fundamental from incidental

**Fundamental gaps** (platform limits):
- These require a platform upgrade (e.g., Anthropic adding a TextGeneration hook)
- Cannot be solved by writing code
- Note them as permanent constraints in your architecture

**Incidental gaps** (missing code):
- The hook event exists but the code hasn't been written
- Estimate: lines of code, files to modify
- These are your build backlog

Example from inline-execution-audit FR1.1:
```
FUNDAMENTAL GAPS (outside Tim's control):
  1. No PreTextGeneration hook — inline text responses permanently ungated
  2. No TextGeneration intercept — cannot force Agent tool invocation
  3. Hook payload is single-prompt — no multi-turn state in hook context

INCIDENTAL GAPS (~80 lines of code):
  1. Receipt writer missing from Mortar instructions (~15 lines)
  2. Per-turn receipt reset missing from prompt router (~5 lines)
  3. Gate advisory-only (safety pin) in masonry-approver.js (~10 lines)
  4. Trivial bypass condition missing (~10 lines)
  5. MASONRY_ENFORCE_ROUTING flag not wired (~5 lines)
  6. Receipt isolation: global singleton vs. per-session path (~35 lines)
```

### 5. Define minimum viable enforcement

Given the fundamental limits, what is the strongest enforcement posture achievable within the architecture?

The minimum viable architecture is usually:
- The highest-impact Viable enforcement goal
- With all prerequisites identified
- Deployed behind a feature flag
- With a clear bypass path for legitimate exemptions

State the minimum viable architecture explicitly:

```
Minimum Viable Enforcement:
  Gate: [hook event] deny for [tool set] when [condition]
  Writer: [what writes the compliance state]
  Reset: [what resets per turn]
  Bypass: [legitimate exemptions: Bash, build mode, subagent context, etc.]
  Flag: [env var] to enable/disable

What this covers: [X%] of routing compliance surface
What this cannot cover: inline text responses (fundamental gap)
```

### 6. Report architecture ceiling

```
ARCHITECTURE CEILING ANALYSIS — [project]

Enforcement Goal: [goal]

Ceiling Summary:
  Fundamental Gaps:  N — cannot solve without platform upgrade
  Incidental Gaps:   N — solvable with code (~N lines)
  Viable Paths:      N — ready to implement

Fundamental Gaps (permanent constraints):
  1. [gap]: requires [platform capability not available]
  2. ...

Minimum Viable Architecture:
  [description]
  Covers: X% of enforcement surface
  Cannot cover: [fundamental gap list]

Build Backlog (incidental gaps, priority order):
  1. [gap]: ~N lines — [file to modify]
  2. ...
  Total effort: ~N lines across N files

Recommendation: [build the minimum viable architecture, note the ceiling clearly]
```

## Notes

- The distinction between fundamental and incidental gaps is critical for scoping: don't spend engineering effort on fundamental limits, focus on incidental gaps
- "The ceiling is X" is a complete finding — knowing the limit is as valuable as knowing what's buildable
- Feature flags (MASONRY_ENFORCE_ROUTING=1) are the right pattern for enforcement that has a non-zero false-positive risk — measure real FP rate before making it the default
- The "completed feature with safety pin still in" pattern is common — find it with /hook-enforcement-audit
