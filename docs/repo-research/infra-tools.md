# Repo Research: Infrastructure Tools Bundle

**Repos analyzed**:
1. https://github.com/promptfoo/promptfoo (18.7K stars)
2. https://github.com/Pimzino/spec-workflow-mcp (4.1K stars)
3. https://github.com/tirth8205/code-review-graph (3.7K stars)
4. https://github.com/thedotmack/claude-mem (40K stars — AGPL-3.0)
5. https://github.com/eyaltoledano/claude-task-master (26K stars)

**Researched**: 2026-03-28
**Researcher**: repo-researcher agent
**Purpose**: Identify capability gaps and integration opportunities for BrickLayer 2.0 infrastructure

---

## Summary

Five high-star tools targeting the same Claude Code + agent workflow space BrickLayer occupies. Two are directly complementary (code-review-graph, claude-task-master). Two overlap significantly with existing BL systems (claude-mem, spec-workflow-mcp) but expose specific gaps. One (promptfoo) already has a full report at `promptfoo-promptfoo.md` — only the delta is covered here.

---

## 1. promptfoo/promptfoo

See full analysis: `C:/Users/trg16/Dev/Bricklayer2.0/docs/repo-research/promptfoo-promptfoo.md`

**Core mechanism**: YAML-driven eval harness that executes prompt variants against multiple providers, scores outputs with 50+ assertion types, and generates HTML/CLI reports. Red-team mode generates adversarial probes using 40+ plugins (OWASP LLM Top 10, MITRE ATLAS, RAG poisoning, memory poisoning, MCP security) and 25+ attack strategies (jailbreak, crescendo, prompt-injection, tree-search). Trace-based red-teaming feeds OpenTelemetry spans back to attack strategies to craft more effective subsequent attacks based on observed guardrail decisions and tool-call sequences. Risk scoring follows CVSS principles: impact base (1-4) + exploitability (ASR-scaled) + human factor + complexity penalty.

**Gap vs BrickLayer**:
- BL's `eval_agent.py` scores a single agent prompt against a held-out JSONL with 3 heuristic metrics. Promptfoo evaluates hundreds of test cases across provider grids with 50 assertion types.
- BL has zero red-teaming capability. Promptfoo has 40+ red-team plugins covering privilege escalation, RAG poisoning, memory poisoning, MCP-specific attacks, and RBAC violations.
- BL has no trace-based attack feedback loop. Promptfoo's OpenTelemetry integration creates an adversarial feedback cycle where attack strategies adapt based on observed internal agent behavior.
- BL's `masonry-security-review` skill is OWASP Top 10 code review. Promptfoo tests live agent behavior under adversarial inputs — a different and complementary attack surface.

**Integration path**: Use promptfoo as the eval harness for BL's DSPy optimization loop — replace `eval_agent.py` with a `promptfoo eval` subprocess call. Add a `/masonry-redteam` skill that generates a `promptfoo.yaml` config targeting the Masonry MCP server and runs it. The existing `masonry-security-review` catches code vulnerabilities; promptfoo catches behavioral vulnerabilities at runtime.

**Priority**: HIGH — BL's eval system is a thin wrapper around `claude -p`. Promptfoo is the industry standard. The red-team gap is a genuine capability hole; BL has no way to test agent behavior under adversarial conditions before deploying agents to campaigns.

---

## 2. Pimzino/spec-workflow-mcp

**Core mechanism**: MCP server exposing 12 tools that enforce a sequential 3-phase spec creation workflow: Requirements → Design → Tasks. Each phase gate-locked by an approval step visible in a real-time web dashboard (port 5000) or VSCode sidebar extension. File store is `.spec-workflow/specs/{name}/{requirements,design,tasks}.md`. Steering documents (product, tech, structure) provide project-level context injected into all spec contexts. Task status tracked as `pending/in-progress/completed` with visual progress bars in the dashboard. Approval workflow: AI creates doc → requests approval → dashboard shows pending → human approves/rejects with feedback → AI revises if rejected.

**Tools (12 total)**:
- `spec-workflow-guide`, `steering-guide` — documentation retrieval
- `create-spec-doc` (with `revision: bool`) — creates/updates requirements, design, or tasks docs
- `spec-list`, `spec-status`, `get-spec-context` — list and query
- `create-steering-doc` — project-level steering (product/tech/structure)
- `get-template-context`, `get-steering-context` — inject context
- `manage-tasks` (update/complete/list/progress actions) — task lifecycle
- `request-approval`, `get-approval-status`, `delete-approval` — approval lifecycle

**Gap vs BrickLayer**:
- BL's `/plan` → `spec.md` workflow is single-document, single-phase. Spec-workflow-mcp enforces three separate documents with explicit gate approval between each.
- BL has no concept of "steering documents" — persistent project-level context (tech stack decisions, product vision, structural conventions) that auto-injects into every spec creation. BL's equivalent is `project-brief.md` but it's not actively injected into agent contexts via MCP tools.
- BL's approval mechanism is claims.json + Kiln (async human escalation). Spec-workflow adds a synchronous web dashboard with revision tracking and feedback threading per document.
- BL tracks task status in `progress.json`. Spec-workflow tracks it at the individual task level within markdown with visual dashboard display.
- BL has no "related specs" or "spec dependencies" concept — spec-workflow's `get-spec-context` returns related specs and dependency specs automatically.

**Integration path**: The steering document concept is the most extractable pattern. Add a `masonry_steering` MCP tool that reads `.autopilot/steering/` files (product.md, tech.md, structure.md) and injects them into plan/build agent prompts. The approval gate between requirements and design phases could replace the current single-step `/plan` → human-approve → `/build` flow with a finer-grained 3-checkpoint model. The dashboard is redundant with Kiln.

**Priority**: MEDIUM — The core steering document injection pattern is genuinely useful and can be built in a few hours. The 3-phase gate enforcement is architecturally compatible with BL's existing state machine but doesn't provide sufficient new value over the current `/plan → approve → /build` flow to justify a full rewrite. The web dashboard is explicitly not wanted (Kiln-only policy).

---

## 3. tirth8205/code-review-graph

**Core mechanism**: Python package that parses a codebase with Tree-sitter into an SQLite graph of nodes (functions, classes, imports) and edges (calls, inheritance, test coverage). On every file edit or git commit, a hook fires that re-parses only changed files using SHA-256 hashes to detect changes, re-indexes in under 2 seconds for 2,900-file projects. Exposes 22 MCP tools and 5 MCP prompt templates. Core value proposition: blast-radius analysis — for any changed file, compute the exact set of callers, dependents, and test files affected, then generate a "minimal review context" covering only those files. Benchmarked at 8.2x average token reduction (up to 16.4x on Go repos) vs reading entire source files. Impact accuracy: 100% recall, 0.54 F1 (conservative — over-predicts but never misses affected files).

**Key tools**:
- `get_impact_radius_tool` — blast radius for changed files
- `get_review_context_tool` — token-optimized review context with structural summary
- `query_graph_tool` — callers, callees, tests, imports, inheritance queries
- `detect_changes_tool` — risk-scored change impact with function-level precision
- `list_flows_tool` / `get_flow_tool` / `get_affected_flows_tool` — execution flow tracing
- `list_communities_tool` / `get_community_tool` / `get_architecture_overview_tool` — community detection (Leiden algorithm)
- `refactor_tool` / `apply_refactor_tool` — rename preview, dead code detection
- `generate_wiki_tool` / `get_wiki_page_tool` — auto-generated wiki from community structure
- `cross_repo_search_tool` — search across registered multi-repo registry
- `semantic_search_nodes_tool` — vector embedding search via sentence-transformers, Gemini, or MiniMax
- `find_large_functions_tool` — find functions exceeding a line-count threshold

**18 languages**: Python, TypeScript/TSX, JavaScript, Vue, Go, Rust, Java, Scala, C#, Ruby, Kotlin, Swift, PHP, Solidity, C/C++, Dart, R, Perl

**Gap vs BrickLayer**:
- BL's code-reviewer agent reads files and writes review comments. It has no structural awareness of which files matter for a given change — it reads whatever the developer points it at.
- BL has no blast-radius analysis. BL's `masonry-lint-check.js` fires on every write but only runs linters on the changed file, with no awareness of dependents.
- BL's HNSW reasoning bank stores agent findings. Code-review-graph stores structural code relationships — a completely different data shape that enables precise "what breaks if I touch X" reasoning.
- BL has no community detection or architecture overview generation. The wiki generation from communities is a novel artifact BL can't produce.
- BL's `diagnose-analyst` works from error messages. Code-review-graph's `detect_changes_tool` produces risk-scored function-level impact analysis before errors occur, enabling proactive risk flagging during `/build`.

**Integration path**:
1. Install `code-review-graph` as an MCP server in BL's `.mcp.json`. Costs nothing — it auto-registers with Claude Code.
2. Inject `get_review_context_tool` output into the `code-reviewer` agent's context when reviewing a PR or post-build verification. This replaces "read all changed files" with "read only blast-radius files."
3. Add a `masonry-blast-radius.js` PostToolUse hook that calls `get_impact_radius_tool` after Write/Edit operations and logs high-impact changes to Kiln.
4. Wire `detect_changes_tool` into the `/verify` skill to get risk-scored impact analysis before the verify agent reads any files.

**Priority**: HIGH — The token reduction is real and measurable (8.2x average, 100% recall). BL's agent fleet routinely burns context on full-repo reads during review and verify phases. The MCP server installs in one command and immediately makes every existing BL agent smarter about what to read. This is additive infra with no rearchitecting required.

---

## 4. thedotmack/claude-mem

**Core mechanism**: Claude Code plugin (installed via `/plugin` commands, not npm) that runs 5 lifecycle hooks and a persistent worker service (Bun HTTP server on port 37777). Hooks capture all tool use observations (PostToolUse), session starts (SessionStart), user prompts (UserPromptSubmit), and session ends (Stop/SessionEnd). Observations are compressed with AI into semantic summaries and stored in SQLite with FTS5 full-text search. A Chroma vector database provides hybrid semantic + keyword search. Three MCP tools implement a layered retrieval pattern: `search` (compact index, ~50-100 tokens/result) → `timeline` (chronological context around an observation) → `get_observations` (full detail, ~500-1,000 tokens/result, always batch IDs). A web viewer UI at port 37777 shows a real-time memory stream. `<private>` tags in messages exclude content from storage. "Endless Mode" (beta) uses a biomimetic memory architecture for extended sessions.

**Gap vs BrickLayer**:
- BL uses System-Recall (Qdrant + Neo4j + Ollama at 100.70.195.84:8200) for memory. Claude-mem uses local SQLite + Chroma — a different deployment model (fully local vs. self-hosted service).
- BL's recall integration uses `recall_search`, `recall_search_full`, `recall_timeline` MCP tools — functionally identical to claude-mem's 3-tool layered retrieval pattern. BL already has this.
- BL's masonry-observe.js (PostToolUse) and session-start hook both fire for memory retrieve/observe — functionally identical to claude-mem's 5-hook lifecycle.
- Claude-mem's `<private>` tag pattern for excluding sensitive content from storage is a concrete gap. BL has no equivalent privacy gate on what gets stored to Recall.
- Claude-mem's web viewer UI provides a real-time observation stream with citation links per observation. Kiln doesn't currently show Recall memory streams.
- Claude-mem's 3-layer retrieval (search index → timeline → full detail) is a token efficiency pattern explicitly designed to avoid fetching full observations until they're filtered. BL's recall hooks fetch full content immediately. This pattern is worth extracting regardless of storage backend.

**Integration path**: Do not replace System-Recall with claude-mem — Recall's Neo4j graph and Qdrant vector search are significantly more capable. Extract two patterns: (1) add a `<private>` / `<no-recall>` tag parser to masonry-observe.js that strips tagged content before sending to Recall; (2) update masonry-session-start.js to use the 3-layer search pattern (compact index first, then fetch full observations only for IDs that pass a relevance threshold).

**Priority**: MEDIUM — BL already has memory infrastructure that exceeds claude-mem's capabilities. The `<private>` tag and 3-layer retrieval patterns are worth a few hours to implement in the existing hooks. The web viewer is redundant with Kiln.

---

## 5. eyaltoledano/claude-task-master

**Core mechanism**: JSON-driven task management system with an MCP server exposing 36 tools (configurable down to 7 "core" tools via `TASK_MASTER_TOOLS` env var). Tasks stored in `.taskmaster/tasks/tasks.json` using a tagged context system — tasks are namespaced by tag (e.g., `master`, `feature-branch`) enabling isolated parallel task lists per branch or context. Key differentiators vs. a flat task list:

- **PRD parsing**: `parse-prd` reads a natural-language PRD and generates a full task tree with IDs, priorities, dependencies, details, and test strategies.
- **Complexity analysis**: `analyze` scores each task 1-10 on complexity, recommends subtask count, and generates AI expansion prompts. `complexity-report` displays tasks ranked by complexity score.
- **Smart expansion**: `expand-task` breaks a task into subtasks using the complexity analysis recommendations. Expansion uses a research model (Perplexity) for fresh information.
- **Dependency graph**: `validate-dependencies` checks for circular deps and invalid references. `fix-dependencies` auto-repairs them. `next-task` returns the highest-priority task whose all dependencies are satisfied.
- **Scope management**: `scope-up` and `scope-down` adjust task granularity (collapse subtasks back to parent or expand parent to subtasks).
- **Multi-model routing**: configures separate main model, research model (Perplexity for web-fresh info), and fallback model. Claude Code CLI ("claude-code/sonnet") supported as a no-API-key model option.
- **Tag isolation**: tasks in different tags have independent ID sequences and are completely isolated — enables parallel branch development without task number conflicts.
- **Research tool**: `research` tool sends a query to the research model with current codebase context injected, returning fresh information relevant to the project.

**Tools breakdown**: `get_tasks`, `next_task`, `get_task`, `set_task_status`, `update_subtask`, `parse_prd`, `expand_task` (core 7) + `initialize_project`, `analyze_project_complexity`, `expand_all`, `add_subtask`, `remove_task`, `generate`, `add_task`, `complexity_report` (standard 15) + dependency management, tag management, research, scope tools, models config (full 36).

**Gap vs BrickLayer**:
- BL's `/plan` creates `spec.md` — a single flat document. Taskmaster creates a structured JSON task graph with explicit dependency edges, priority levels, complexity scores, and test strategies per task.
- BL has no complexity analysis. The `analyze` tool assigns 1-10 complexity scores and recommends subtask counts — this directly maps to BL's need to decide when to spawn sub-agents vs. handle inline.
- BL's `/build` processes tasks sequentially or in parallel via `progress.json`. Taskmaster's `next-task` tool surfaces the highest-priority dependency-unblocked task — a smarter scheduling algorithm than BL's fixed sequential approach.
- BL has no PRD parsing. Taskmaster's `parse-prd` ingests natural language product requirements and generates an entire task tree with test strategies. BL requires manual question.md authoring.
- BL has no `research` tool integrated into the task management layer. Taskmaster's research model (Perplexity) provides web-fresh information with project context injected — BL's research is campaign-level, not task-level.
- BL's tag/context system (`progress.json` is a single file) doesn't support parallel branch task isolation. Taskmaster's tagged task lists allow simultaneous task lists for multiple branches.
- BL's `next-task` equivalent is implicit in `progress.json` ordering. Taskmaster's `next_task` is an explicit MCP tool that evaluates priorities, dependency satisfaction, and task IDs — surfacing the optimal next action.

**Integration path**:
1. Add `complexity_score` and `recommended_subtask_count` fields to BL's `progress.json` schema — populated by a complexity analysis pass at `/plan` time.
2. Implement a `masonry_next_task` MCP tool that reads `progress.json`, evaluates dependency satisfaction, and returns the optimal next task with priority weighting.
3. Add a `/parse-prd` skill that reads a PRD file and generates `questions.md` (campaign) or `spec.md` (build) using Taskmaster-style structured parsing.
4. Implement tag-isolated task contexts in `progress.json` to support concurrent multi-branch builds without state collision (relevant for `/masonry-team` multi-instance builds).

**Priority**: HIGH — BL's task management (`progress.json` + sequential build loop) is the weakest part of the `/build` system. Taskmaster's dependency graph, complexity scoring, and priority-aware `next_task` scheduling would directly improve build reliability and agent allocation decisions. The PRD parsing is the highest-value single feature — it closes the gap between "Tim has an idea" and "BL has a question bank/task list."

---

## Cross-Cutting Patterns

Three patterns appear across multiple repos and are worth noting:

**1. Token-efficient layered retrieval** (claude-mem, code-review-graph): Both implement a compact index → selective fetch pattern. Claude-mem does it for memory observations; code-review-graph does it for code context. BL should apply this pattern to masonry-session-start.js (Recall retrieval) and to the code-reviewer agent (blast-radius first, full file read second).

**2. Selective tool loading** (claude-task-master): The `TASK_MASTER_TOOLS` env var enabling core/standard/all/custom tool subsets reduces context window overhead from 36 tools × ~600 tokens = ~21K tokens to 7 tools × ~600 tokens = ~4K tokens. BL's Masonry MCP server exposes all tools always. A `MASONRY_TOOLS` env var with similar tiering would reduce context overhead for focused sessions.

**3. Steering documents as persistent project-level context** (spec-workflow-mcp): Project-level decisions (tech stack, conventions, product vision) captured in separate documents and auto-injected into every spec/task context. BL's `project-brief.md` plays this role but isn't actively retrieved via MCP tools during agent execution.

---

## Priority Summary

| Repo | Priority | What to build |
|------|----------|---------------|
| code-review-graph | HIGH | Install as MCP server now; add masonry-blast-radius.js hook; wire into code-reviewer and /verify |
| claude-task-master | HIGH | Add complexity scoring to /plan; implement masonry_next_task tool; add /parse-prd skill |
| promptfoo | HIGH | Already documented — integrate as eval harness, add /masonry-redteam skill |
| spec-workflow-mcp | MEDIUM | Extract steering document injection pattern into .autopilot/steering/ + masonry MCP tool |
| claude-mem | MEDIUM | Extract `<private>` tag parser for masonry-observe.js; apply 3-layer retrieval to session-start |
