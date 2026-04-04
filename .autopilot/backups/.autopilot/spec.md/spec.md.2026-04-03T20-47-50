# Spec: anthropics/skills Integration — 5 Features

## Overview
Adopt 5 patterns from the anthropics/skills repo analysis to improve BrickLayer's agent packaging, routing accuracy, creation workflow, and verification quality. Features build on each other: frontmatter standardization enables progressive disclosure which enables routing optimization.

## Acceptance Criteria
- [ ] All 107 agent .md files have valid YAML frontmatter with: name, description, model, tier, modes, capabilities, tools
- [ ] `onboard_agent.py` validates frontmatter completeness on onboard (warns on missing fields)
- [ ] Router's semantic layer uses frontmatter-only corpus (no body parsing) — already true, just formalize
- [ ] `masonry/scripts/optimize_routing.py` exists and can evaluate routing accuracy per agent
- [ ] Fresh-eyes verification pattern integrated into synthesizer-bl2 as optional step
- [ ] `/forge` skill creates, tests, and onboards a new agent in a guided workflow
- [ ] All existing tests pass, no regressions in routing or onboarding

## Tasks

### Task 1: Backfill YAML frontmatter on 53 remaining agents
**Files**: `.claude/agents/*.md` (53 files without frontmatter), `masonry/scripts/backfill_frontmatter.py`
**Description**: Write a script that reads each agent .md file, detects if YAML frontmatter exists, and if not, generates it by:
1. Using the filename stem as `name`
2. Extracting the first sentence/paragraph as `description`
3. Defaulting `model: sonnet`, `tier: draft`
4. Setting `modes: []`, `capabilities: []`, `tools: []` as empty (to be filled by optimize_routing later)
5. Writing the frontmatter block (`---\n...\n---`) at the top, preserving all existing content below

The script must be idempotent — running twice produces the same result. After running, re-run `onboard_agent.py` to sync registry.

**Test Strategy**: Run the script, then verify: (a) all 107 files start with `---`, (b) `yaml.safe_load` parses every frontmatter block without error, (c) no file content below frontmatter was modified, (d) `onboard_agent.py` runs clean with 0 new warnings.
**Dependencies**: None

### Task 2: Add frontmatter validation to onboard_agent.py
**Files**: `masonry/scripts/onboard_agent.py`, `masonry/tests/test_onboard_agent.py`
**Description**: Add a `validate_frontmatter(meta: dict) -> list[str]` function that checks:
- `name` is non-empty string
- `description` is non-empty and >= 20 chars (too short = useless for semantic routing)
- `model` is one of: opus, sonnet, haiku
- `tier` is one of: production, candidate, draft
- `modes` is a list (can be empty)
- `capabilities` is a list (can be empty)

Return list of warning strings (empty = valid). Call this in `extract_agent_metadata` and print warnings to stderr. Do NOT block onboarding on validation failures — warnings only.

**Test Strategy**: Test with valid frontmatter (0 warnings), missing name (1 warning), short description (1 warning), invalid model (1 warning), missing frontmatter entirely (multiple warnings).
**Dependencies**: None (can run in parallel with Task 1)

### Task 3: Build routing description optimizer
**Files**: `masonry/scripts/optimize_routing.py`
**Description**: Port the skill-creator's eval loop pattern for routing descriptions. The script:
1. Takes an agent name as argument
2. Loads agent's current description + capabilities from registry
3. Generates 20 test queries: 10 "should-route-here" and 10 "should-NOT-route-here"
   - Use Claude (via `claude -p`) to generate test queries based on agent description and capabilities
4. Runs each query through `masonry.src.routing.semantic.route_semantic` (Python import, not MCP)
5. Scores accuracy: correct routes / total queries
6. If accuracy < 80%, use Claude to propose an improved description based on failure cases
7. Re-test with improved description
8. If improved, update the agent .md frontmatter and re-run onboard to sync registry
9. Save results to `masonry/agent_snapshots/{agent}/routing_eval.json`

**Test Strategy**: Run against a known agent (e.g., `research-analyst`). Verify: (a) 20 queries generated, (b) routing accuracy is a number 0-1, (c) results saved to routing_eval.json, (d) if description changed, frontmatter updated and registry synced.
**Dependencies**: Task 1 (all agents need frontmatter for meaningful eval)

### Task 4: Implement fresh-eyes verification pattern
**Files**: `masonry/scripts/fresh_eyes_verify.py`, `.claude/agents/synthesizer-bl2.md`
**Description**: Create a verification script that:
1. Takes a path to synthesis.md as input
2. Reads ONLY the synthesis (no findings, no questions, no project-brief)
3. Generates 5-8 comprehension questions about the synthesis content using Claude
4. Spawns a fresh Claude instance (`claude -p`) with ONLY the synthesis as context
5. Asks each question and captures answers
6. Compares answers against expected answers (from the question generation step)
7. Outputs a verification report: questions, answers, correctness scores, and flagged sections

Also add a section to `synthesizer-bl2.md` noting that after writing synthesis.md, the fresh-eyes verifier can be invoked as an optional quality gate.

**Test Strategy**: Create a mock synthesis.md with known content. Run the verifier. Verify: (a) questions are generated, (b) answers are captured, (c) correctness scores are 0-1, (d) output report is valid JSON or markdown.
**Dependencies**: None (independent of other tasks)

### Task 5: Create /forge agent creation workflow
**Files**: `.claude/skills/forge/SKILL.md`
**Description**: Create a new skill at `.claude/skills/forge/SKILL.md` that guides the creation of a new BrickLayer agent:

**Phase 1 — Interview**: Ask the user:
- Agent name and one-line description
- What modes it operates in (diagnose, research, validate, etc.)
- What capabilities it has
- What model tier (opus/sonnet/haiku)
- Example prompts it should handle (3-5)

**Phase 2 — Draft**: Generate the agent .md file with:
- Complete YAML frontmatter (validated per Task 2's schema)
- Structured instructions following the BrickLayer agent pattern
- DOT process flowchart
- Inline self-review checklist
- Output contract

**Phase 3 — Test Routing**: Run the example prompts through `masonry_route` MCP tool to verify the agent would be correctly routed to. Report accuracy.

**Phase 4 — Onboard**: Save the .md file to `.claude/agents/`, which triggers `masonry-agent-onboard.js` hook automatically.

**Phase 5 — Optimize** (optional): Run `optimize_routing.py` (Task 3) to tune the routing description.

**Test Strategy**: Invoke /forge and create a test agent "test-dummy". Verify: (a) .md file created with valid frontmatter, (b) onboard hook fires and registers in agent_registry.yml, (c) routing test shows > 0% accuracy for the example prompts.
**Dependencies**: Task 1 (frontmatter standard), Task 2 (validation), Task 3 (routing optimizer)

## Dependency Graph
```
Task 1 (frontmatter backfill) ─┬─→ Task 3 (routing optimizer) ─→ Task 5 (/forge skill)
                                │
Task 2 (validation)       ──────┘
Task 4 (fresh-eyes)       ──── independent
```

Tasks 1, 2, 4 can run in parallel. Task 3 needs Task 1. Task 5 needs Tasks 1, 2, 3.

## Out of Scope
- Plugin marketplace integration (future — requires Claude Code plugin system)
- HTML eval viewer for Kiln (future — Kiln enhancement)
- Token/timing capture on subagent completion (future — separate hook change)
- Description "pushiness" tuning (addressed naturally by Task 3's optimizer)
