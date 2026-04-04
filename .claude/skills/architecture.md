---
name: architecture
description: SPARC Phase 3 -- generate architecture.md from spec + pseudocode before /build
user-invocable: true
---

# /architecture -- Pre-Build Architecture Document

Invoke the architecture-writer agent to produce `.autopilot/architecture.md`.

Act as the architecture-writer agent defined in `~/.claude/agents/architecture-writer.md`. Read `.autopilot/spec.md` and `.autopilot/pseudocode.md` (if present). Explore the codebase. Write `.autopilot/architecture.md` following the format in the agent instructions.

The output document defines component boundaries, interface contracts, data flows, dependencies, out-of-scope items, and rollback plan for the current spec. Developer agents receive this context during `/build` to avoid architectural drift.

Run this after `/pseudocode` and before `/build` when the build has multiple interacting components or non-trivial data flows.
