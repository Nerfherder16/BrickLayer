# Repo Research: GlitterKill/sdl-mcp

**Repo**: https://github.com/GlitterKill/sdl-mcp
**Researched**: 2026-04-16
**Researcher**: repo-researcher agent
**Purpose**: Head-to-head comparison against jCodeMunch to determine redundancy or complementarity

---

## Verdict Summary

SDL-MCP (Symbol Delta Ledger MCP) is a token-efficiency-first code intelligence MCP server with 35+ tools organized around an escalating context ladder, graph slices, change tracking, sandboxed runtime execution, and cross-session development memories. It is substantially broader and more agent-workflow-aware than jCodeMunch. jCodeMunch has a stronger static analysis focus (dead code, coupling metrics, refactoring candidates, diagram rendering) that SDL-MCP does not replicate. Running both together adds real value — the overlap is almost entirely on symbol search and file outline, while the rest is complementary. If you had to pick one, SDL-MCP is the deeper agent tool; jCodeMunch is the better refactoring companion.

---

## File Inventory

Source code files were not enumerated individually (no GitHub API tree traversal was performed). The following is based on the full public documentation, changelog, and tool reference which were read in their entirety.

### Top-Level

| File | Category | Description |
|------|----------|-------------|
| `README.md` | docs | Primary entry point — architecture overview, 30-second how-it-works, quick start |
| `CHANGELOG.md` | docs | 28 releases from v0.1 through v0.10.3 (Apr 2026) |
| `package.json` | config | npm package: `sdl-mcp`, TypeScript, Node.js 24+ |
| `config/sdlmcp.config.example.json` | config | Full annotated config example |

### `docs/`

| File | Category | Description |
|------|----------|-------------|
| `docs/README.md` | docs | Documentation hub / index |
| `docs/getting-started.md` | docs | 5-minute setup, install, serve, client config |
| `docs/mcp-tools-detailed.md` | docs | Complete tool reference — all 35+ tools with schemas and response shapes |
| `docs/mcp-tools-reference.md` | docs | Condensed tool reference table |
| `docs/cli-reference.md` | docs | All 13 CLI commands with options |
| `docs/configuration-reference.md` | docs | Every config field with defaults |
| `docs/agent-workflows.md` | docs | Paste-ready AGENTS.md block, workflow protocols, "do not" list |
| `docs/troubleshooting.md` | docs | Runtime/config debugging guide |
| `docs/feature-deep-dives/iris-gate-ladder.md` | docs | 4-rung escalation system explained with token cost tables |
| `docs/feature-deep-dives/live-indexing.md` | docs | Live editor buffer overlay — real-time draft-aware symbol resolution |
| `docs/feature-deep-dives/runtime-execution.md` | docs | 16-runtime sandboxed execution deep-dive |
| `docs/feature-deep-dives/semantic-embeddings.md` | docs | Embedding provider tiers, ONNX, Jina v2, Nomic |

### Source (TypeScript — structure inferred from changelog and tool reference)

| Module area | Description |
|-------------|-------------|
| Rust native addon (`napi-rs`) | Pass-1 symbol extraction — 12 languages, multi-threaded |
| Tree-sitter fallback | TypeScript/JS symbol extraction when Rust addon unavailable |
| LadybugDB | Custom file-based graph database (`.lbug` format) |
| Indexer | Full + incremental modes, pass-2 call resolution, edge scoring |
| Live index overlay | Draft-aware in-memory symbol overlay, debounced parse queue |
| Slice engine | BFS/beam search, token budget, V1/V2/V3 wire format |
| Iris Gate gating engine | Policy evaluation, break-glass audit, denial guidance |
| Agent context planner | Rung path planning by task type and budget |
| Memory store | Graph-linked `.sdl-memory/*.md` files, content-addressed dedup |
| Runtime executor | 16-runtime sandboxed subprocess, CWD jailing, gzip artifacts |
| Feedback store | Reinforcement-style slice quality tuning |
| MCP server | stdio + streamable HTTP (Hono), flat/gateway/code-mode surfaces |
| CLI | Commander.js, 13 commands including `init`, `serve`, `tool`, `doctor` |

---

## Architecture Overview

```
Your Codebase
     |
     v
Indexer (Rust native or tree-sitter fallback)
  - 12 languages
  - Pass-1: symbol extraction (name, kind, file, range, signature)
  - Pass-2: call resolution with confidence scoring
     |
     v
LadybugDB (file-based graph DB, .lbug format)
  - Symbol nodes with ETags (content-addressed SHA-256)
  - Edge types: call, import, config
  - Cluster/community detection
  - Process (call-chain) tracking
  - Metrics: fan-in, fan-out, 30-day churn, test refs
  - Memory nodes (cross-session knowledge)
     |
     v
Live Index Overlay (in-memory)
  - Editor buffer events via sdl.buffer.push
  - Debounced tree-sitter parse (75ms default)
  - Merged transparently with durable DB on every query
     |
     v
MCP Server (stdio or streamable HTTP)
  - Flat mode: 32 tools + sdl.action.search + sdl.info
  - Code Mode: adds sdl.context, sdl.workflow, sdl.manual (optional exclusive)
  - Gateway mode: 4 namespace surfaces replacing 32 flat tools
  - HTTP extras: /ui/graph, /api/graph/*, /api/symbol/*, /api/repo/*
```

The core design principle is the **Symbol Card** — a compact metadata record (~100 tokens) containing everything an agent needs to understand a symbol without reading its source code. The **Iris Gate Ladder** enforces escalation from cards through skeleton IR, hot-path excerpts, and finally gated raw code windows.

---

## Complete Tool Catalog

### Category 0: Diagnostics
| Tool | What it does |
|------|-------------|
| `sdl.info` | Unified runtime report: version, config path, logging, LadybugDB status, Rust addon status |

### Category 1: Repository Management
| Tool | What it does |
|------|-------------|
| `sdl.repo.register` | Register or update a repo: path, languages, ignore globs |
| `sdl.repo.status` | Health score, file/symbol counts, watcher state, prefetch stats, live index status, optional memory surfacing |
| `sdl.repo.overview` | Token-bounded codebase overview: stats / directories / full (hotspots, clusters, processes) |
| `sdl.index.refresh` | Full or incremental re-indexing with MCP progress notifications |

### Category 2: Live Editor Buffer
| Tool | What it does |
|------|-------------|
| `sdl.buffer.push` | Push editor buffer event (open/change/save/close/checkpoint) with content, version, dirty flag, cursor, selections |
| `sdl.buffer.checkpoint` | Force-flush pending draft buffers to durable DB |
| `sdl.buffer.status` | Buffer queue depth, dirty count, checkpoint state |

### Category 3: Symbol Search and Retrieval
| Tool | What it does |
|------|-------------|
| `sdl.symbol.search` | Text search with optional hybrid retrieval (FTS + vector + RRF). Triggers predictive prefetch of top-5 cards. |
| `sdl.symbol.getCard` | Single symbol card: identity, signature, 1-2 line summary, invariants, side effects, deps, metrics, cluster, processes, ETags |
| `sdl.symbol.getCards` | Batch fetch up to 100 cards by ID or natural ref; per-symbol ETags; partial-success metadata |

### Category 4: Graph Slices
| Tool | What it does |
|------|-------------|
| `sdl.slice.build` | BFS/beam subgraph from entry symbols or task text. Token budget, V1/V2/V3 wire format, ETag caching, auto-discovery mode |
| `sdl.slice.refresh` | Incremental delta from a known slice handle — avoids rebuild |
| `sdl.slice.spillover.get` | Paginated overflow symbols beyond budget |

### Category 5: Code Access — Iris Gate Ladder
| Tool | Rung | What it does |
|------|------|-------------|
| `sdl.code.getSkeleton` | 2 | Signatures + control flow, bodies elided (~200-400 tokens) |
| `sdl.code.getHotPath` | 3 | Lines matching specified identifiers + context lines (~400-800 tokens) |
| `sdl.code.needWindow` | 4 | Full raw source — policy gated, requires justification + identifier hints + line/token limits. Returns denial guidance on reject. |

### Category 6: File Access
| Tool | What it does |
|------|-------------|
| `sdl.file.read` | Read non-source files (configs, YAML, SQL, docs). Modes: line range, regex search, JSON path extraction. Blocked for indexed source extensions. |

### Category 7: Delta and Change Tracking
| Tool | What it does |
|------|-------------|
| `sdl.delta.get` | Semantic diff between two ledger versions: changed symbols with signature/invariant/side-effect diffs, blast radius with distance ranking, fan-in trend amplifiers |

### Category 8: Policy Management
| Tool | What it does |
|------|-------------|
| `sdl.policy.get` | Read current code-access gating policy |
| `sdl.policy.set` | Patch policy: maxWindowLines, maxWindowTokens, requireIdentifiers, allowBreakGlass |

### Category 9: PR and Risk Analysis
| Tool | What it does |
|------|-------------|
| `sdl.pr.risk.analyze` | Composite risk score (0-100), categorized findings with severity, impacted symbols, evidence, recommended test targets |

### Category 10: Context Summary
| Tool | What it does |
|------|-------------|
| `sdl.context.summary` | Token-bounded context briefing (key symbols, dep graph, risk areas, files touched). Formats: markdown/json/clipboard. For export to non-MCP environments. |

### Category 11: Agent Context and Feedback
| Tool | What it does |
|------|-------------|
| `sdl.agent.context` | Task-shaped context engine: plans rung path by task type (debug/review/implement/explain), executes each rung, collects evidence. Precise and broad modes. |
| `sdl.agent.feedback` | Record useful/missing symbols after a task — reinforcement-style slice quality tuning |
| `sdl.agent.feedback.query` | Query stored feedback, aggregated stats on most-useful and most-missing symbols |

### Category 12: Runtime Execution
| Tool | What it does |
|------|-------------|
| `sdl.runtime.execute` | Sandboxed subprocess: 16 runtimes (node, typescript, python, shell, go, rust, java, kotlin, c, cpp, csharp, ruby, php, perl, r, elixir). CWD jailed, scrubbed env, concurrency limited, gzip artifact persistence. Output modes: minimal/summary/intent. |
| `sdl.runtime.queryOutput` | On-demand keyword search of stored artifact from a previous execute |

### Category 13: Development Memories
| Tool | What it does |
|------|-------------|
| `sdl.memory.store` | Store decision/bugfix/task_context with symbol and file links, confidence score, tags. Backed by `.sdl-memory/*.md` for Git sharing. |
| `sdl.memory.query` | Full-text search memories by type, tags, symbols, staleness |
| `sdl.memory.remove` | Soft-delete memory, optionally remove backing file |
| `sdl.memory.surface` | Auto-surface memories relevant to a set of symbols, ranked by confidence x recency x overlap |

### Category 14: Usage Statistics
| Tool | What it does |
|------|-------------|
| `sdl.usage.stats` | Cumulative token savings vs raw file reads, per-tool breakdowns, compression ratios |

### Category 15: Code Mode Tools
| Tool | What it does |
|------|-------------|
| `sdl.action.search` | Keyword search the SDL action catalog with optional schema and examples |
| `sdl.manual` | Compact filtered API reference before diving into workflows |
| `sdl.context` | Task-shaped context inside Code Mode (mirrors sdl.agent.context) |
| `sdl.workflow` | Multi-step operation pipeline: up to 50 actions, $N result piping, dataPick/dataMap/dataFilter/dataSort/dataTemplate transforms, cross-step ETag caching |

---

## Head-to-Head Feature Gap Analysis

### SDL-MCP capabilities that jCodeMunch lacks

| Capability | SDL-MCP Tool | jCodeMunch | Gap Level | Notes |
|------------|-------------|------------|-----------|-------|
| **Iris Gate Ladder — graduated context escalation** | `getSkeleton` → `getHotPath` → `needWindow` | `get_symbol_source` (no gating) | HIGH | SDL-MCP enforces card-first, then skeleton (elided bodies), then identifier-targeted excerpts, then policy-gated raw window with justification. jCodeMunch gives you the full symbol source directly. No budget enforcement, no denial guidance, no graduated escalation. |
| **Hot-path excerpts (identifier-targeted line extraction)** | `sdl.code.getHotPath` | None | HIGH | Returns only lines matching specific identifiers + N context lines. ~400-800 tokens vs 1000-4000 for full source. No equivalent in jCodeMunch. |
| **Policy-gated raw code access with audit** | `sdl.code.needWindow` | None | HIGH | Requires justification, expected line count, identifier hints. Policy engine approves/denies with `whyDenied` and `nextBestAction`. Break-glass with audit trail. jCodeMunch has no code access gating at all. |
| **Graph slice with token budget** | `sdl.slice.build` | `get_context_bundle`, `get_ranked_context` | HIGH | BFS/beam subgraph from entry symbols or task text with explicit token/card budgets. V1/V2/V3 wire format compression (deduplicated file paths, grouped edge encoding). ETag caching per symbol. `slice.refresh` for incremental deltas. Spillover pagination. jCodeMunch bundles context but has no incremental delta or wire compression. |
| **Live editor buffer overlay** | `sdl.buffer.push/checkpoint/status` | None | HIGH | Draft-aware symbol resolution from unsaved editor content. Push keystroke-level buffer events, parse in background, all subsequent search/card/slice calls reflect unsaved code. jCodeMunch has no live indexing. |
| **Semantic delta between ledger versions** | `sdl.delta.get` | None (only `get_blast_radius` on current state) | HIGH | Compares two indexed versions, returns per-symbol signature/invariant/side-effect diffs, blast radius ranked by graph distance + fan-in, fan-in trend amplifiers. jCodeMunch blast radius is single-point; SDL-MCP tracks change over time. |
| **PR risk scoring with test recommendations** | `sdl.pr.risk.analyze` | None | HIGH | Composite 0-100 risk score, categorized findings (severity: low/med/high), evidence for each finding, recommended test targets. |
| **Sandboxed runtime execution** | `sdl.runtime.execute` + `sdl.runtime.queryOutput` | None | HIGH | 16-runtime subprocess execution gated by policy, CWD jailed, scrubbed env, gzip artifact persistence, on-demand output search. Completely outside jCodeMunch scope. |
| **Cross-session development memories** | `sdl.memory.*` | None | HIGH | Typed memories (decision/bugfix/task_context) linked to symbols and files, auto-surfaced in slice builds, backed by `.sdl-memory/*.md` for Git sharing, staleness detection when linked symbols change. |
| **Agent feedback loop / slice quality tuning** | `sdl.agent.feedback` + `sdl.agent.feedback.query` | None | MEDIUM | Records which symbols were useful or missing after each task. Aggregated stats feed slice ranking improvement. No equivalent in jCodeMunch. |
| **Workflow chaining — multi-step round-trip** | `sdl.workflow` | None | MEDIUM | Up to 50 actions in one call with `$N` result references, internal data transforms (dataPick, dataMap, dataFilter, dataSort, dataTemplate), cross-step ETag caching, budget tracking. |
| **Task-shaped context engine** | `sdl.agent.context` / `sdl.context` | `get_ranked_context`, `get_context_bundle` | MEDIUM | Plans a rung path based on task type (debug/review/implement/explain) and available budget. Executes rungs in sequence, collects evidence, returns synthesized answer. Precise mode strips envelope for token efficiency. jCodeMunch's context tools don't differentiate by task type or gate on token budget. |
| **ETag-based conditional requests everywhere** | On `getCard`, `getCards`, `slice.build`, `slice.refresh` | None | MEDIUM | Content-addressed caching: if a symbol hasn't changed, server returns `notModified` with zero data transfer. Eliminates redundant retransmission across a session. |
| **Hybrid FTS + vector retrieval with RRF** | `sdl.symbol.search` with `semantic: true` | Embedding-based `search_symbols` | MEDIUM | Reciprocal Rank Fusion combining full-text search candidates with vector search candidates. Falls back gracefully to legacy. jCodeMunch uses embeddings but not RRF fusion. |
| **Codebase overview with cluster/process summaries** | `sdl.repo.overview` with `level: "full"` | `get_project_intel` (partial overlap) | MEDIUM | Returns community detection clusters, call-chain processes, per-directory breakdowns with top exports, hotspots (fan-in, churn, file size, edge count), token compression metrics. |
| **PR-ready context export** | `sdl.context.summary` with `format: "clipboard"` | None | LOW | Generate token-bounded markdown/JSON/clipboard summaries for non-MCP surfaces (Slack, Jira, PRs). |
| **Token usage tracking** | `sdl.usage.stats` | None | LOW | Cumulative savings vs raw file reads, per-tool breakdowns, compression ratios. |
| **Predictive prefetch** | Auto-triggered on `symbol.search` | None | LOW | Top-5 search results have their cards pre-fetched in background anticipating follow-up `getCard` calls. |
| **HTTP transport with Graph UI** | `sdl-mcp serve --http` | stdio only | LOW | Multi-agent shared server, interactive graph visualization at `/ui/graph`, REST endpoints for graph neighborhood and symbol lookup. |
| **Policy management** | `sdl.policy.get/set` | None | LOW | Runtime-configurable code access policy without server restart. |

---

### jCodeMunch capabilities that SDL-MCP lacks

| Capability | jCodeMunch Tool | SDL-MCP | Gap Level | Notes |
|------------|----------------|---------|-----------|-------|
| **Dead code detection** | `find_dead_code` | None | HIGH | SDL-MCP tracks fan-in (who calls a symbol) and can surface zero-fan-in symbols, but has no dedicated dead code tool. |
| **Refactoring candidate extraction** | `get_extraction_candidates` | None | MEDIUM | Suggests functions/blocks that should be extracted based on complexity and duplication patterns. No SDL-MCP equivalent. |
| **Coupling metrics** | `get_coupling_metrics` | None | MEDIUM | Afferent/efferent coupling, instability scores. SDL-MCP has fan-in/fan-out per symbol but no module-level coupling analysis. |
| **Safe refactoring plans** | `plan_refactoring` | None | MEDIUM | Generates an ordered, safe refactoring plan for a specific change. SDL-MCP has `sdl.delta.get` for post-change analysis but no pre-change planning. |
| **Diagram rendering** | `render_diagram` | None | MEDIUM | Generate dependency, class, or call-hierarchy diagrams from code. SDL-MCP has `/ui/graph` HTTP endpoint but no MCP tool that outputs a diagram. |
| **High-level project intelligence** | `get_project_intel` | `sdl.repo.overview` (partial) | LOW | jCodeMunch provides a single high-level summary including architecture patterns, tech stack, key components. SDL-MCP's overview is more metrics-heavy than narrative. |
| **Hotspots tool (dedicated)** | `get_hotspots` | `sdl.repo.overview` (embedded) | LOW | SDL-MCP includes hotspot data (fan-in, churn, file size, edges) within `repo.overview`, but it's not a standalone tool. |
| **Impact preview before a change** | `get_impact_preview` | `sdl.delta.get` (post-change) | LOW | jCodeMunch can preview impact before code is written. SDL-MCP computes it after indexing a new version. |
| **Turn planning suggestion** | `plan_turn` | `sdl.agent.context` rung planning (internal) | LOW | jCodeMunch exposes optimal tool sequence suggestion as a user-callable tool. SDL-MCP's planner is internal to `sdl.agent.context`. |

---

## Direct Overlap (Where Both Do the Same Thing)

| Capability | SDL-MCP | jCodeMunch | Notes |
|------------|---------|------------|-------|
| Symbol search by name | `sdl.symbol.search` | `search_symbols` | Both support name-based lookup and filtering by kind |
| Symbol source / implementation | `sdl.symbol.getCard` + `sdl.code.needWindow` | `get_symbol_source` | jCodeMunch gives raw source immediately. SDL-MCP gives metadata first, raw source only with justification. |
| File structure / outline | `sdl.code.getSkeleton` | `get_file_outline` | SDL-MCP elides bodies (more aggressive compression); jCodeMunch provides outline without gating |
| Dependency graph | `sdl.slice.build` edges + `sdl.repo.overview` | `get_dependency_graph` | SDL-MCP bakes deps into symbol cards; jCodeMunch has a dedicated module-level dependency graph tool |
| Blast radius | `sdl.delta.get` blast radius | `get_blast_radius` | SDL-MCP ties blast radius to version diffs; jCodeMunch is single-point |
| Call hierarchy | Symbol card `deps.calls` + `sdl.slice.build` | `get_call_hierarchy` | jCodeMunch has dedicated bidirectional call hierarchy; SDL-MCP exposes calls through cards and slices |
| Find references | Symbol card `metrics.fanIn` + slice edges | `find_references` | jCodeMunch is more direct; SDL-MCP requires traversing slice edges |
| Text search | `sdl.file.read` search mode | `search_text` | SDL-MCP restricts to non-indexed files; jCodeMunch searches all code |
| Repository health | `sdl.repo.status` healthScore + healthComponents | `get_repo_health` | Both provide a composite health score; SDL-MCP's is more granular (5 components) |
| Directory tree | `sdl.repo.overview` directories | `get_file_tree` | SDL-MCP overview includes per-directory symbol counts; jCodeMunch is a pure tree |
| Indexing | `sdl.index.refresh` | `index_repo`, `index_folder`, `index_file` | jCodeMunch supports granular partial indexing; SDL-MCP is full or incremental |

---

## Top 5 Recommendations for BrickLayer

### 1. Iris Gate Ladder Pattern — Enforce Graduated Context Escalation [HIGH PRIORITY]

SDL-MCP's central innovation: forbid agents from jumping straight to raw source. The ladder forces card-first (metadata, ~100 tokens), then skeleton (structure, ~300 tokens), then hot-path (targeted lines, ~600 tokens), then gated raw window (full source, ~2000 tokens, requires justification). BrickLayer agents currently call `get_symbol_source` immediately — they burn 10-20x tokens on context gathering that could be answered by metadata alone.

Implementation sketch: Add a CLAUDE.md rule and masonry hook that intercepts `get_symbol_source` calls and routes through a ladder check — try `get_file_outline` first, only escalate to `get_symbol_source` if outline is insufficient. Teach agents the escalation vocabulary. Long-term: build a ladder-aware jCodeMunch wrapper agent.

### 2. Slice-Based Context with ETag Caching [HIGH PRIORITY]

SDL-MCP's `sdl.slice.build` builds a BFS subgraph from entry symbols within an explicit token budget, then `sdl.slice.refresh` returns only the delta since the last call. BrickLayer agents rebuild context from scratch on every turn. The ETag pattern means unchanged symbols cost zero tokens on refresh.

Implementation sketch: Create a `context-slicer` agent wrapper that maintains a slice handle per session, calls refresh instead of rebuild, and enforces `maxCards: 30, maxEstimatedTokens: 4000` as default budget. This aligns with BrickLayer's EMA training pipeline — token usage reduction is measurable.

### 3. Cross-Session Development Memories Linked to Symbols [HIGH PRIORITY]

SDL-MCP memories are typed (decision/bugfix/task_context), linked to specific symbol IDs and file paths, auto-surfaced when those symbols appear in slices, and backed by `.sdl-memory/*.md` for Git sharing. BrickLayer uses Recall (Qdrant + Neo4j) for memory, but it lacks symbol-level linking — memories are not automatically surfaced when a specific function appears in a slice.

Implementation sketch: Extend Recall's schema to support `symbolId` and `fileRelPath` links. Add a `sdl.memory.surface`-equivalent that queries for memories when a set of symbol IDs enters a BrickLayer session. The `.sdl-memory/*.md` Git-sharing pattern is directly adoptable as a lightweight fallback.

### 4. Agent Feedback Loop for Slice Quality [MEDIUM PRIORITY]

SDL-MCP's `sdl.agent.feedback` records which symbols were actually useful vs missing after a task completes. This feeds the slice ranker over time. BrickLayer has EMA training on telemetry but doesn't track symbol-level utility feedback. Knowing that "when debugging auth middleware, these 5 symbols are always relevant and these 3 are always missing" would improve routing quality.

Implementation sketch: Add a PostToolUse hook on BrickLayer's masonry-observe.js that extracts symbol references from agent completions and records a simple utility log (was this symbol referenced in the fix? was it in the original context?). Feed this into the EMA pipeline.

### 5. Hot-Path Excerpt Tool (Identifier-Targeted Line Extraction) [MEDIUM PRIORITY]

SDL-MCP's `sdl.code.getHotPath` returns only the lines containing specific identifiers plus N context lines. This is the single most token-efficient way to answer "where is X used in Y function" — 400-800 tokens vs 1000-4000 for full source. jCodeMunch has `find_references` which locates symbols globally, but not a within-symbol targeted line extractor.

Implementation sketch: Build a `get_hot_path` wrapper tool (or jCodeMunch extension request) that takes `(symbolId, identifiersToFind[], contextLines)` and returns a grep-style excerpt. This is implementable with jCodeMunch's `get_symbol_source` + a local regex extractor as a stopgap.

---

## Novel Patterns to Note for Future Work

**Iris Gate policy engine with break-glass audit**: Denying raw code access with `whyDenied` + `nextBestAction` forces agents to justify escalation. The audit trail is a novel governance pattern worth considering for BrickLayer's overseer/agent-auditor integration.

**V2/V3 wire format compression**: Deduplicating file paths and grouping edge encodings in slice responses. For BrickLayer's masonry MCP server, response compression on large context payloads could meaningfully reduce token spend.

**Predictive prefetch**: On `symbol.search`, SDL-MCP pre-fetches cards for the top-5 results in the background. BrickLayer could apply a similar anticipatory pattern — when a routing decision is made, pre-warm the context for the most likely next symbols.

**`outputMode: minimal` + on-demand artifact query**: Execute → get a handle → only pay token cost for excerpts you actually query. This two-phase pattern for runtime output would benefit BrickLayer's diagnose-analyst / fix-implementer loop where test output is often large and mostly irrelevant.

**Confidence-aware rung path planning**: SDL-MCP's planner adjusts the rung path based on confidence tiers — high confidence means fewer rungs, low confidence triggers broader escalation. BrickLayer's Mortar routing could apply a similar confidence gate: high-confidence routes get fewer verification steps, low-confidence routes get full consensus.

---

## Final Comparison Verdict

| Dimension | SDL-MCP | jCodeMunch | Winner |
|-----------|---------|------------|--------|
| Symbol search and retrieval | Hybrid FTS+vector+RRF, batch cards, ETags | Name-based search, direct source | SDL-MCP |
| File/symbol structure | Skeleton IR (elided bodies), policy gated | Outline, direct source, no gating | Depends on use: SDL-MCP for agents, jCodeMunch for humans |
| Token efficiency | Core design principle — ladder, budgets, ETags, compression | Not a primary concern | SDL-MCP |
| Dead code / coupling | Minimal (fan-in only) | Dedicated tools | jCodeMunch |
| Refactoring support | No planning tools | Extraction candidates, safe refactoring plans | jCodeMunch |
| Diagram generation | HTTP graph UI only | `render_diagram` MCP tool | jCodeMunch |
| Change tracking | Semantic versioned diffs, blast radius over time | Single-point blast radius | SDL-MCP |
| Runtime execution | 16-runtime sandboxed subprocess | None | SDL-MCP |
| Memory / persistence | Cross-session memories linked to symbols | None | SDL-MCP |
| Agent workflow tooling | Workflow chaining, task-shaped context, feedback loop | `plan_turn`, `plan_refactoring` | Draw |
| Setup complexity | npm install, init, serve | Per-project indexing | Comparable |
| Breadth | 35+ tools across 15 categories | ~21 tools | SDL-MCP |

**Running both is additive, not redundant.** The overlapping 30% (symbol search, file outline, dependency graph, blast radius, call hierarchy) can be handled by either — default to jCodeMunch there since it's already integrated. The non-overlapping 70% is genuinely distinct: SDL-MCP owns token efficiency, context budgets, live indexing, delta tracking, runtime execution, and memories; jCodeMunch owns dead code, coupling, refactoring plans, and diagrams.

**The highest-value SDL-MCP concept to adopt without switching tools is the Iris Gate Ladder pattern**: enforce card/outline-first in agent CLAUDE.md instructions, only escalate to full source when outline is provably insufficient. That alone captures 60% of SDL-MCP's token-efficiency value with zero infrastructure change.
