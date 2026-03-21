# Campaign Plan — bl-audit — 2026-03-21

## System Summary

BrickLayer 2.0 is a three-layer AI development platform (BrickLayer / Masonry / Mortar) that orchestrates research campaigns, agent fleets, and code builds via Claude Code. Masonry provides the bridge layer: 22 JS hooks, a four-layer routing engine (deterministic/semantic/LLM/fallback), Pydantic v2 payload schemas, a DSPy optimization pipeline, an MCP server with 14 tools, and a declarative agent registry (45+ agents). This campaign audits the codebase for dead code, unwired items, bugs, config drift, stale references, and structural problems.

## Prior Recall Context

None -- cold start. No prior findings were returned from Recall for this project or domain.

## Domain Risk Ranking

| Domain | Likelihood | Impact | Priority | Rationale |
|--------|-----------|--------|----------|-----------|
| D2 — Unwired Items | 3 | 3 | 9 | 45 agents in registry, 16 in ~/.claude/agents/, 34 in .claude/agents/. 3 hooks on disk NOT in settings.json (masonry-recall-check.js, masonry-statusline.js, masonry-agent-onboard.js). MCP server exposes 14 tools but tools-manifest.md may not match. DSPy generated/ has 46 stubs but optimized_prompts/ is empty. High probability of disconnected wiring. |
| D4 — Config Drift | 3 | 2 | 6 | settings.json hook list is already out of sync with hooks on disk (3 hooks unwired). agent_registry.yml has 45 entries referencing file paths that may not resolve. Registry mixes relative paths (agents/...) with absolute paths (~/.claude/agents/...). Template dir may be stale vs live masonry/. |
| D1 — Dead Code | 2 | 3 | 6 | bl/ package has 30+ modules (scratch.py, crucible.py, healloop.py, claim.py etc.) — unclear which are actively used. bl/runners/ has 16 runners but MCP server only references simulate mode runner via get_runner(). DSPy pipeline has full infrastructure but zero optimized prompts saved — may be entirely unused in practice. |
| D3 — Bugs & Logic | 2 | 3 | 6 | Routing: deterministic layer routes slash commands to targets like "build-workflow" and "campaign-conductor" which are NOT agent names in the registry. Semantic layer uses cosine similarity with threshold 0.60 — may be too aggressive with 45 agents. LLM layer spawns subprocess claude with 20s timeout on Windows — fragile. QuestionPayload.priority is int(1-5) but question schema says HIGH/MEDIUM/LOW — type mismatch. |
| D5 — Stale References | 2 | 2 | 4 | 20+ files still reference DISABLE_OMC/oh-my-claudecode. 15 files reference ports 3100/8100 (retired dashboard). masonry-session-start.js still references OMC. CLAUDE.md still documents DISABLE_OMC workflow. |
| D6 — Structural Problems | 2 | 2 | 4 | Hook duplication: masonry-session-summary.js vs masonry-session-end.js — overlapping stop-time responsibilities. Agent overlap: multiple synthesizer variants (synthesizer.md, synthesizer-bl2.md), multiple hypothesis generators. Template dir has its own agent set — unknown sync state with live agents. |

## Targeting Brief for Question-Designer

### High-priority areas (generate 3-5 questions each)

1. **Hook wiring completeness (D2/D4)** — 3 hooks exist on disk but are not registered in settings.json: masonry-recall-check.js, masonry-statusline.js, masonry-agent-onboard.js. Are they intentionally unwired, orphaned, or broken? The agent-onboard hook is documented in CLAUDE.md as active but is missing from settings.json.

2. **Agent registry integrity (D2/D4)** — 45 registry entries reference file paths using mixed conventions (relative `agents/X.md` vs `~/.claude/agents/X.md` vs `.claude/agents/X.md`). Do all referenced files actually exist? Do all .md files in agent directories have registry entries? Are tier assignments (draft/candidate/trusted) meaningful or all defaulted?

3. **Routing correctness (D3)** — Deterministic layer routes /build to "build-workflow" and /masonry-run to "campaign-conductor" — neither exists in agent_registry.yml. Does the router produce valid targets? Semantic layer threshold at 0.60 with 45 agents may produce false positives. LLM layer subprocess call fragile on Windows.

4. **Dead bl/ modules (D1)** — bl/ contains 30+ modules. Which are imported by anything? scratch.py, crucible.py, healloop.py, claim.py, sweep.py, fixloop.py, followup.py, skill_forge.py, tracer.py — are these all actively called?

5. **DSPy pipeline liveness (D1/D2)** — Generated stubs exist for 46 agents but optimized_prompts/ is empty. Is the optimization pipeline functional? Has it ever been run? Is training_extractor producing usable data?

### Medium-priority areas (generate 1-2 questions each)

1. **Stale OMC/dashboard references (D5)** — 20+ files reference DISABLE_OMC or oh-my-claudecode. masonry-session-start.js still contains OMC logic. How many of these are in active code paths vs docs/history?

2. **MCP server tool coverage (D2)** — Server exposes 14 tools including masonry_run_simulation and masonry_sweep (via bl imports). Do all tool dependencies (bl.runners.get_runner, bl.question_weights, bl.nl_entry, bl.git_hypothesis) actually exist and work?

3. **Hook exit code correctness (D3)** — Invariant: hooks must exit 0 (allow) or 2 (block). Async hooks cannot block regardless of exit code. Do all 22 hooks follow this contract? Are any sync hooks accidentally using exit(1)?

4. **Template staleness (D6)** — template/ directory has its own program.md, constants.py, simulate.py, and agent set. Are these in sync with current masonry/ implementation and agent conventions?

5. **QuestionPayload priority type mismatch (D3)** — Pydantic schema uses int(1-5), question-schema.md uses string HIGH/MEDIUM/LOW. Who converts? Is there a silent validation failure?

### Skip or defer

- **D6 tail risk / black swans**: This is a code audit, not a business model stress test. Black swan scenarios are not applicable to static codebase analysis.
- **Competitive/market analysis (D3 in BL standard)**: Not applicable to an internal tooling audit.
- **Revenue/financial model (D1 in BL standard)**: No financial model exists for this codebase.

## Known Landmines (from prior campaigns)

None -- cold start. No prior BrickLayer campaigns have been run against the BL2.0 codebase itself.

## Recommended Wave Structure

- Wave 1 (12 questions): Focus on D2 (Unwired Items) and D3 (Bugs & Logic) -- highest priority domains with concrete, verifiable targets
- Wave 2 (8 questions): D1 (Dead Code) deep dive + D4 (Config Drift) follow-ups based on Wave 1 findings
- Wave 3 (4-6 questions): D5 (Stale References) cleanup + D6 (Structural) consolidation
- Estimated total questions: 24-26

## BL 2.0 Mode Allocation

For question-designer-bl2 -- translate domain priorities into mode allocations:

| Mode | Suggested question count | Rationale |
|------|--------------------------|-----------|
| diagnose | 6 | D2 unwired items and D3 bugs require root cause analysis with file/line precision |
| audit | 4 | D4 config drift and D2 registry integrity are systematic audit targets |
| research | 2 | D1 dead code investigation requires codebase exploration to trace call graphs |
| validate | 0 | No architectural designs need pre-build review in this audit |
| frontier | 0 | Not warranted for a code health audit |
| benchmark | 0 | No performance baselines needed |
| evolve | 0 | Reserve for Wave 2+ if agent prompt quality issues surface |
| monitor | 0 | Reserve for Wave 2+ |
| predict | 0 | Reserve for Wave 2+ |

Total Wave 1 target: 12 questions

## Constraints to Keep in Mind

These invariants from the project brief and codebase must be stress-tested or validated:

1. **Hook exit codes**: Must be 0 (allow/warn) or 2 (block) -- never 1 or other codes
2. **isResearchProject() detection**: Must use BOTH program.md AND questions.md as sentinels
3. **Async hooks cannot block**: `async: true` hooks exit code is irrelevant to blocking
4. **Session isolation**: Stop guard must never flag files from sibling sessions
5. **Bash auto-approval scope**: Only in research project context, NOT in build/fix mode
6. **AgentRegistryEntry uses extra="ignore"**: Intentional -- allows onboarding fields. But other schemas use extra="forbid" -- any drift here is a bug.
7. **FindingPayload.verdict validation**: Runtime validator against VALID_VERDICTS frozenset (28 values). Any new verdict string will cause a hard ValidationError.
8. **Routing fallback_reason**: Only 5 valid literal values. The router currently always passes "ambiguous" from Layer 4 -- finer-grained reasons (ollama_timeout, llm_timeout) are not propagated from Layers 2-3.

## Instruction Block for Question-Designer-BL2

Read the "High-priority areas" section above before generating questions.md.
Generate questions in priority order -- D2 first, D3 second, D1 third.
For each high-priority area, generate at minimum one DIAGNOSE question and one AUDIT question.
Do not generate questions for "Skip or defer" areas unless directly linked to a high-priority finding.
Use the "BL 2.0 Mode Allocation" table above to set Mode fields -- do not invent mode assignments.
All questions must target specific files, line ranges, or named components -- no vague "is there a problem" questions.
For D2 (Unwired Items), verify both directions: things on disk not in config, AND things in config not on disk.
For D3 (Bugs & Logic), include the exact code path and expected vs actual behavior in the hypothesis.
