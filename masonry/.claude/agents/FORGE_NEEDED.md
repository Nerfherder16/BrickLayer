# FORGE_NEEDED — 2026-03-24T20:30:00Z

## Gaps Found

### CRITICAL_MISSING: fix-implementer
**Priority**: CRITICAL
**Reason**: 5 open fix-mode questions (P1, P4, P5 tasks A-B, P6/F12.1) require targeted implementation. No fix-implementer agent exists in the fleet to execute these fixes. Synthesis.md explicitly calls out F12.1 (confidence-weighted drift scoring) as "a maintenance task, not a research question."
**Suggested description**: Targeted fix agent for precision implementation of remediation items (F12.1 drift metric, hook behavior guards, circuit breakers, collision prevention). Reads fix requirements, writes minimal code changes, validates via test runs.
**Suggested mode coverage**: fix

### CRITICAL_MISSING: python-backend-engineer
**Priority**: CRITICAL
**Reason**: F12.1 (confidence-based drift metric) is blocked without specialized implementation. drift_detector.py requires adding confidence parameter threading through _score_verdicts(), detect_drift(), and run_drift_check(). This requires understanding DSPy scoring patterns, agent_db.json data structure, and confidence calibration logic. Current diagnose-analyst and design-reviewer are not equipped for drift-detection domain work.
**Suggested description**: Python backend specialist for optimization/drift-detection work. Understands DSPy metrics, confidence-weighted scoring, training data infrastructure, and MIPROv2 pipeline patterns. Capable of reading agent_db.json, modifying scoring logic, and validating against held-out eval sets.
**Suggested mode coverage**: fix, diagnose

### HIGH_MISSING: hook-specialist
**Priority**: HIGH
**Reason**: P4 (pre-agent tracker collision fix) and V-mid.2 (build-guard/stop-guard behavior risks) both require Node.js hook modifications. Current fleet has no agent capable of understanding hook framework, session state coordination, cross-session visibility, or file-based synchronization patterns. masonry-preagent-tracker.js, masonry-build-guard.js, and masonry-stop-guard.js all require expert-level hook engineering.
**Suggested description**: Node.js hook specialist for masonry integration layer fixes. Understands hook lifecycle, atomic file operations, session boundaries, cross-session communication, and hookSpecificOutput delivery semantics. Capable of debugging hook double-fire cascades and implementing collision prevention.
**Suggested mode coverage**: fix

### HIGH_MISSING: routing-specialist
**Priority**: HIGH
**Reason**: P1 (Ollama offline cascade) has two components: (1) add circuit breaker to semantic.py with module-level state management, (2) add SEMANTIC_ROUTING_ENABLED to constants.py and wire to router.py decision logic. This requires understanding the four-layer routing pipeline, timeout behavior, fallback semantics, and environment configuration patterns. No current agent covers routing domain.
**Suggested description**: Routing layer specialist for masonry four-layer router (deterministic, semantic, LLM, fallback). Understands Ollama integration, circuit breaker patterns, timeout tuning, layer selection logic, and environment variable wiring. Capable of implementing resilience improvements and configurable routing disable paths.
**Suggested mode coverage**: fix, diagnose

### MEDIUM_MISSING: synthesizer-bl2
**Priority**: MEDIUM
**Reason**: Wave 38 synthesis exists but was generated without a dedicated synthesis agent in the fleet. Synthesis.md calls out 5 cross-cascade hypothesis questions for Wave 39, but no agent is registered to produce next-wave synthesis when questions complete. Masonry baseline requires synthesizer for end-of-wave aggregation.
**Suggested description**: Synthesis agent for masonry campaign. Reads all findings in findings/, extracts cross-cascade patterns, aggregates verdict statistics, identifies feedback loops, and writes synthesis reports. Reports next-wave hypotheses for hypothesis-generator to expand question bank.
**Suggested mode coverage**: research

### STALE_TOOL_DECLARATION: mortar
**Priority**: MEDIUM
**Reason**: mortar.md defines `input_schema: QuestionPayload` and `output_schema: FindingPayload` in frontmatter but has no `tools:` field. Agent has MCP tool dependencies for routing (masonry_route) and session state (masonry_status, masonry_questions). Should declare these explicitly.
**Suggested description**: Add YAML frontmatter field `tools: [masonry_route, masonry_status, masonry_questions, masonry_recall]` to mortar.md to match its internal dependencies.
**Suggested mode coverage**: agent

---

## Summary

**Fleet Status**: Incomplete for maintenance/fix cycle. 5 specialist agents CRITICAL or HIGH priority missing. Masonry campaign cannot resolve open items (P1, P4, P5, P6/F12.1, V-mid.2) without: (1) fix-implementer to orchestrate targeted changes, (2) python-backend-engineer for drift-detection work, (3) hook-specialist for Node.js hook engineering, (4) routing-specialist for circuit breaker implementation.

**Synthesis coverage**: Existing synthesis (Wave 38) is healthy but no agent registered for ongoing synthesis aggregation. Hypothesis-generator will need synthesis input for Wave 39 question bank expansion.

**Timeline**: F12.1 is the critical blocker for MIPROv2 optimization to execute safely. P1 (circuit breaker) is non-blocking for optimization but impacts routing quality/cost continuously. P4 and V-mid.2 address data integrity and session robustness. All four fix items should be prioritized before next optimization wave.

