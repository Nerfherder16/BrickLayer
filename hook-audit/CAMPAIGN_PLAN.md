# Campaign Plan — hook-audit

## Project Summary
Audit of the Masonry + Recall session lifecycle hooks: registration correctness, blocking mechanisms, session state symmetry, cross-hook dependencies, and analytics trigger viability.

## Risk Domains (Ranked by Impact)

### Domain 1: Blocking Mechanism Correctness (CRITICAL)
Three guards use `process.exit(2)`, one uses `{decision:"block"}` stdout + exit 0. If the stdout JSON method is wrong for Stop hooks, masonry-context-monitor never actually blocks. All blocking logic must use the correct mechanism for the current Claude Code version.

### Domain 2: Stop Hook Ordering and Dependencies (HIGH)
masonry-stop-guard depends on the activity log written by masonry-observe (PostToolUse). masonry-session-summary may delete that log. Execution order determines correctness. The chain of 13 Stop hooks has never been fully mapped.

### Domain 3: Session State Symmetry (HIGH)
SessionStart writes a snapshot. Stop hooks write summaries, call Recall, trigger scripts. Whether Stop output is consumed/cleaned correctly by subsequent sessions or accumulates as stale state has not been audited since the hooks were last rewritten.

### Domain 4: masonry-handoff.js Session ID Bug (HIGH)
Settings.json does not pass sessionId to masonry-handoff.js. The guard file is always keyed on 'unknown', breaking multi-session isolation. Impact: unclear — may cause duplicate handoffs to be suppressed, or may corrupt Recall handoff memories.

### Domain 5: Analytics Hook Viability (MEDIUM)
masonry-score-trigger, masonry-ema-collector, masonry-pagerank-trigger all have gate conditions. If the files they check for don't exist (telemetry.jsonl, scored_all.jsonl), they silently no-op every session. Whether these hooks actually fire in practice is unknown.

### Domain 6: Recall Hook Overlap (MEDIUM)
recall-session-summary and masonry-session-summary both write to Recall. They use different domains ("development" vs "autoresearch") for the same projects. Net result: duplicate session summaries per session, domain fragmentation in Recall.

## Research Method
Static analysis of hook source files + settings.json registration. No simulate.py. Questions are answered by reading source code and config, not by running simulations.

## Wave 1 Questions: 18
Focus: Blocking correctness (H1.1), execution order (H1.2, H1.18), known bugs (H1.3), Recall overlap (H1.4), session state (H1.5, H1.10), analytics viability (H1.7, H1.8, H1.9), error handling (H1.6), misc correctness (H1.11, H1.12, H1.13, H1.14, H1.15, H1.16, H1.17)

## Expected Deliverables
- Per-question findings in `findings/`
- Wave synthesis in `findings/synthesis.md`
- Prioritized fix list for Tim to action
