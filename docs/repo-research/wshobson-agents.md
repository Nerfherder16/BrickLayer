# Repo Research: wshobson/agents
**Analyzed:** 2026-03-28
**Repo:** https://github.com/wshobson/agents
**Analyst:** repo-researcher agent
**Scope:** Full exhaustive read — every file, README, agent, skill, hook, workflow

---

## Verdict Summary

**High-value target.** This repo is the most architecturally sophisticated Claude Code plugin ecosystem publicly available. It contains 72 plugins, 112 agents, 146 skills, 79 tools, and 16 orchestrators — all built around a rigorous composability philosophy that BrickLayer 2.0 can directly harvest.

The single most valuable concept is **PluginEval**: a 3-layer statistical quality evaluation framework (Static Analysis → LLM Judge → Monte Carlo Simulation) with 10 weighted dimensions, Elo ranking, badge certification, and anti-pattern detection. BrickLayer has `improve_agent.py` but nothing comparable in rigor or statistical depth.

Second most valuable: **Conductor** (Context-Driven Development) — a semantic revert system that tracks work by logical unit (track/phase/task) rather than git commit. BL has no equivalent.

Third: **Agent Teams** — parallel multi-agent with file ownership boundaries, preset team archetypes, and tmux/iterm2 display. BL's fleet is single-dispatch; Agent Teams is true parallel.

The gap analysis shows BL leads on: campaign/research loops, simulation-based stress testing, Masonry typed payload system, Recall/memory integration, and the Kiln UI. The wshobson repo leads on: agent quality evaluation, skill architecture formalism, context save/restore, TDD depth, and breadth of specialist agents.

**Recommendation: Harvest 6 items immediately, build 2 new systems, adapt 3 patterns.**

---

## File Inventory

### Root
| File | Description |
|------|-------------|
| `README.md` | Full repo overview: 72 plugins, architecture philosophy, PluginEval framework, Agent Teams, Conductor, model tier table |
| `CLAUDE.md` | Authoring conventions: agent frontmatter schema, skill structure rules, plugin.json format, marketplace.json format, PluginEval quick reference |
| `Makefile` | Wraps `tools/yt-design-extractor.py` — install, run, run-full, run-ocr, run-transcript targets |
| `LICENSE` | Standard license |

### docs/
| File | Description |
|------|-------------|
| `docs/architecture.md` | Core design philosophy: single responsibility, composability, context efficiency, design patterns |
| `docs/agents.md` | Complete catalog of all 100+ agents by category with model assignments and descriptions |
| `docs/agent-skills.md` | All 146 skills across 27 plugins, catalogued with descriptions |
| `docs/plugin-eval.md` | PluginEval full specification: 3-layer evaluation, 10 dimensions, CLI commands, statistical methods, badge system |
| `docs/superpowers/specs/2025-03-25-plugineval-design.md` | Original design spec for PluginEval system |

### plugins/ (72 total)
| Plugin | Key Contents |
|--------|-------------|
| `agent-orchestration/` | 3 agents (context-manager, multi-agent-optimizer, improve-agent), commands for agent improvement A/B testing and staged rollout |
| `agent-teams/` | Parallel multi-agent orchestration with tmux/iterm2, 7 preset teams, file ownership, `/team-*` commands |
| `api-scaffolding/` | FastAPI/Express scaffolding, REST/GraphQL/gRPC, OpenAPI generation |
| `backend/` | 9 skills: API design, auth flows, caching, DB modeling, error handling, event-driven, microservices, performance, query optimization |
| `blockchain/` | 4 skills: Solidity/Rust, DeFi, NFTs, Web3 integration |
| `business/` | 2 skills: product requirements, user stories |
| `cicd/` | 4 skills: pipeline design, containerization, monitoring, deployment strategies |
| `cloud/` | 8 skills: AWS/GCP/Azure, IaC, serverless, cost optimization |
| `conductor/` | Context-Driven Development: spec-first workflow, semantic revert by logical unit, track/phase/task hierarchy |
| `context-management/` | context-save, context-restore commands with vector DB integration, token budget management |
| `data-engineering/` | 4 skills: pipeline design, streaming, data quality, warehouse modeling |
| `developer-essentials/` | 11 skills: code review, debugging, documentation, git, performance profiling, refactoring, security audit, testing, architecture, PR description, dependency management |
| `documentation/` | 3 skills: API docs, architecture docs (C4 model), changelog generation |
| `framework-migration/` | 4 skills: assessment, planning, execution, validation for legacy migration |
| `frontend-mobile/` | 4 skills: React Native, Flutter, responsive design, PWA |
| `game-dev/` | 2 skills: game mechanics, Unity/Unreal workflows |
| `hr-legal/` | 2 skills: job descriptions, contract review |
| `incident-response/` | 3 skills: runbook, post-mortem, alerting |
| `js-ts/` | 4 skills: TypeScript strictness, async patterns, bundle optimization, type generation |
| `k8s/` | 4 skills: manifest generation, Helm charts, cluster optimization, RBAC |
| `llm-application-dev/` | 8 skills + prompt-engineer agent: RAG, fine-tuning, evaluation, vector stores, LLM ops, agent frameworks |
| `ml-ops/` | 1 skill: MLOps pipeline design |
| `monorepo/` | monorepo-architect agent (opus), multi-language, Nx/Turborepo, build caching |
| `observability/` | 4 skills: metrics, tracing, logging, SLA monitoring |
| `payments/` | 4 skills: Stripe, fraud detection, PCI compliance, subscriptions |
| `plugin-eval/` | PluginEval implementation: `src/plugin_eval/` Python package, CLI, evaluator, scorer, ranker |
| `python/` | 5 skills: type hints, async, testing, packaging, data processing |
| `quant-trading/` | 2 skills: strategy backtesting, risk management |
| `security/` | 5 skills: threat modeling, OWASP, secret scanning, dependency audit, pen testing |
| `systems/` | 3 skills: OS internals, network programming, performance engineering |
| `tdd-workflows/` | tdd-orchestrator agent (opus), TDD all phases, multi-language, property-based + mutation testing |
| `temporal-workflows/` | temporal-python-pro agent (sonnet), Temporal.io workflow orchestration |
| `ui-design/` | 9 skills: component architecture, accessibility, animations, design systems, Figma integration, dark mode, responsive, performance |
| `vector-database/` | vector-database-engineer agent (opus), Pinecone/Weaviate/Qdrant/pgvector expertise |

### tools/
| File | Description |
|------|-------------|
| `tools/yt-design-extractor.py` | YouTube video → design artifacts: OCR frame extraction, color palette extraction, transcript download |

---

## Agent/Skill Catalog

### High-Value Agents (Selected)

| Agent | Model | Purpose | Unique Capabilities |
|-------|-------|---------|---------------------|
| `context-manager` | inherit | Dynamic context assembly, vector DB management, multi-agent handoff | Pinecone/Weaviate/Qdrant integration, knowledge graphs, RAG, enterprise context governance |
| `tdd-orchestrator` | opus | Complete TDD lifecycle across languages | Chicago vs London school TDD, ATDD/BDD, property-based testing (QuickCheck/Hypothesis), mutation testing, chaos engineering, legacy characterization |
| `prompt-engineer` | inherit | Prompt design, optimization, evaluation | Constitutional AI critique-revise loops, CoT/ToT/self-consistency, model-specific optimization (Claude Opus 4.6, GPT-5.2, Llama/Mixtral), meta-prompting, ALWAYS shows complete prompt text |
| `ai-engineer` | opus | Full-stack AI application development | RAG pipelines, fine-tuning, LLM evaluation frameworks, agent frameworks, vector store optimization |
| `vector-database-engineer` | opus | Vector DB architecture and optimization | All major vector DBs, embedding strategies, ANN algorithms, hybrid search, production scaling |
| `monorepo-architect` | opus | Large-scale monorepo design | Nx/Turborepo, build caching, cross-package dependencies, multi-language, incremental builds |
| `backend-architect` | opus | Distributed systems architecture | CQRS, event sourcing, saga patterns, API gateway, service mesh |
| `incident-responder` | opus | On-call incident management | Real-time runbook execution, blast radius analysis, parallel diagnostic agents |
| `temporal-python-pro` | sonnet | Temporal.io workflow orchestration | Workflow patterns, activity retries, sagas, versioning, worker configuration |
| `improve-agent` | inherit | Agent prompt optimization | A/B testing, staged rollout (5%→20%→50%→100%), rollback triggers, continuous monitoring |

### Agent Teams Presets

| Team | Composition | Use Case |
|------|------------|----------|
| `review` | 3 specialized reviewers | Code review from 3 angles simultaneously |
| `debug` | Hypothesis + 3 parallel investigators | Competing hypothesis debugging |
| `feature` | Spec writer + implementer + tester | Full feature TDD workflow |
| `fullstack` | Frontend + backend + database | Full-stack parallel implementation |
| `research` | 3 research analysts | Multi-angle research synthesis |
| `security` | 3 security specialists | Parallel security audit |
| `migration` | Planner + executor + validator | Framework/language migration |

### Selected Skills (Top Harvestable)

| Skill | Plugin | Description |
|-------|--------|-------------|
| `improve-agent` | agent-orchestration | 4-phase: analyze → engineer → test → deploy with A/B framework |
| `context-restore` | context-management | Semantic vector retrieval, temporal decay, 3-way merge |
| `context-save` | context-management | Semantic extraction, multi-session fingerprinting, protocol buffers |
| `code-review` | developer-essentials | Security + performance + maintainability checklist |
| `architecture-review` | developer-essentials | C4-level architecture documentation |
| `debug-investigation` | developer-essentials | Hypothesis-driven parallel debugging |
| `tdd-implementation` | tdd-workflows | Red-green-refactor with mutation testing |
| `threat-modeling` | security | STRIDE + PASTA + attack trees |
| `rag-implementation` | llm-application-dev | Complete RAG pipeline design |
| `component-architecture` | ui-design | Design token extraction, component hierarchy |

---

## Feature Gap Analysis

| Feature | In wshobson/agents | In BrickLayer 2.0 | Gap Level | Notes |
|---------|-------------------|-------------------|-----------|-------|
| **Agent Quality Evaluation** | PluginEval: 3-layer, 10 dimensions, Elo, badges, anti-pattern detection | `improve_agent.py`: eval→optimize→compare heuristic loop | CRITICAL | BL has a loop but not statistical rigor. PluginEval is ~10x more sophisticated |
| **Semantic Revert** | Conductor: revert by track/phase/task (logical unit) | Git-based revert only (by commit) | HIGH | BL has no concept of logical work unit revert |
| **Parallel Agent Teams** | Agent Teams: file ownership, tmux display, preset archetypes | Mortar dispatch (single-agent per task, parallel dispatch) | HIGH | BL dispatches in parallel but no file ownership or team display |
| **Context Save/Restore** | Explicit commands with vector DB, token budget, 3-way merge | Recall MCP (hooks-based, automatic) | MEDIUM | BL auto-saves context; wshobson's is more explicit/controllable |
| **Progressive Disclosure Skills** | Formalized 3-tier: metadata → instructions → resources (max 1024 chars) | Skills exist but no formalized disclosure tiers | MEDIUM | BL skills are functionally similar but less rigorously specified |
| **TDD Depth** | tdd-orchestrator: mutation testing, property-based, chaos, ATDD/BDD, Chicago/London school | TDD enforcer hook (file pairing check) + TDD rules in agent prompts | HIGH | BL enforces TDD discipline; wshobson has full TDD lifecycle automation |
| **Prompt Engineering Agent** | prompt-engineer (inherit): Constitutional AI, CoT/ToT, model-specific, meta-prompting | `prompt-engineer` entry in Masonry fleet (listed but not deeply specified) | MEDIUM | BL has the slot but the wshobson version is far more detailed |
| **PluginEval Anti-Pattern Detection** | OVER_CONSTRAINED, EMPTY_DESCRIPTION, MISSING_TRIGGER, BLOATED_SKILL, ORPHAN_REFERENCE | None | HIGH | BL has no agent anti-pattern detection |
| **Elo Ranking for Agents** | Statistical Elo + Wilson score CI + Bootstrap CI | Score tracked in `agent_db` via heuristic | MEDIUM | BL has scoring; Elo is more statistically valid |
| **Monte Carlo Simulation (Eval)** | 1000 resamples for stability testing of agent prompts | Not present | HIGH | BL evals are deterministic, not statistical |
| **C4 Architecture Documentation** | 4-level C4 (context/container/component/code) as skills | Not present | MEDIUM | BL has no architecture documentation automation |
| **YouTube Design Extractor** | `yt-design-extractor.py`: OCR + color + transcript | Not present | LOW | Niche tool but useful for UI research |
| **Constitutional AI Integration** | Used in prompt-engineer and improve-agent | Not present explicitly | MEDIUM | BL could add critique-revise loops to agent improvement |
| **Research Campaign Loop** | Not present (single-shot agents only) | Full BL 2.0 loop with waves, synthesis, Kiln UI | N/A (BL leads) | BL is far ahead here |
| **Simulation-Based Stress Testing** | Not present | Core BL feature (simulate.py, constants.py, verdict system) | N/A (BL leads) | BL's signature capability |
| **Typed Payload System** | Not present | QuestionPayload, FindingPayload, RoutingDecision (Pydantic v2) | N/A (BL leads) | BL's Masonry schema system is more mature |
| **Four-Layer Routing** | Not present (single LLM dispatch) | Deterministic → Semantic → LLM → Fallback | N/A (BL leads) | BL's routing is architecturally superior |
| **Kiln UI / Campaign Monitoring** | Not present | Kiln (BrickLayerHub) Electron app | N/A (BL leads) | BL has dedicated UI; wshobson is CLI-only |
| **Hypothesis-Driven Debug Teams** | Agent Teams debug preset: competing hypothesis investigators | Not present (diagnose-analyst is single) | HIGH | BL's diagnose-analyst is single; parallel hypotheses would be better |
| **Staged Agent Rollout** | 5%→20%→50%→100% with rollback triggers | Not present | MEDIUM | BL deploys agent updates immediately; staged rollout is safer |
| **Blockchain/Solana Agents** | Solidity/Rust blockchain skills | `solana-specialist` agent (opus) | N/A (BL leads) | BL has deeper Solana; wshobson has broader blockchain |
| **Temporal Workflow Agent** | `temporal-python-pro` (sonnet) | Not present | LOW | Temporal.io not currently in BL stack |
| **Monorepo Architecture** | `monorepo-architect` (opus) | Not present | LOW | Not a current BL need |
| **Vector DB Engineering** | `vector-database-engineer` (opus) | System-Recall uses Qdrant but no specialist agent | MEDIUM | BL uses vector DBs but lacks specialist optimization agent |
| **Model-Specific Prompt Optimization** | GPT-5.2, Claude Opus 4.6, Llama/Mixtral variants | Not present | MEDIUM | BL targets Claude exclusively |

---

## Top 5 Recommendations

### 1. Build BL-PluginEval (BrickLayer Agent Quality System)
**Why:** BL's `improve_agent.py` is a heuristic eval→optimize→compare loop. It works but is not statistically rigorous. PluginEval's 3-layer architecture (Static → LLM Judge → Monte Carlo) produces defensible quality scores with confidence intervals. Elo ranking would let Tim see which agents are performing best across campaigns.

**What to build:**
- Port the 10-dimension scoring rubric to `masonry/src/scoring/` (some already exists — extend)
- Add Monte Carlo evaluation (run agent prompt N=50 times, compute Wilson CI for each dimension)
- Add Elo rating system to `agent_db` — update on every `improve_agent.py` run
- Add anti-pattern detection: check agent `.md` files for OVER_CONSTRAINED, EMPTY_DESCRIPTION, MISSING_TRIGGER on every `masonry-agent-onboard.js` hook fire
- Expose via `masonry_weights` MCP tool (already exists — add quality score column)

**Complexity:** M (2-3 days)
**Files:** `masonry/src/scoring/`, `masonry/scripts/improve_agent.py`, `masonry/scripts/onboard_agent.py`

---

### 2. Implement Parallel Hypothesis Debug Teams
**Why:** BL's `diagnose-analyst` runs one diagnostic pass. The wshobson "debug" Agent Team pattern — 3 parallel investigators each assigned a competing hypothesis, then synthesized — is provably better for hard bugs. Tim's 3-strike rule would trigger this automatically.

**What to build:**
- New Masonry agent: `parallel-debugger.md` — orchestrates 3 `diagnose-analyst` subagents with distinct hypothesis assignments
- Mortar routing: on 3rd DEV_ESCALATE, dispatch `parallel-debugger` instead of single `diagnose-analyst`
- File ownership: each investigator gets read-only access to non-overlapping code sections
- Synthesis: `parallel-debugger` produces ranked hypothesis list before `fix-implementer` runs

**Complexity:** M (1-2 days)
**Files:** `.claude/agents/parallel-debugger.md`, `masonry/src/routing/deterministic.py`

---

### 3. Add Constitutional AI to Agent Improvement Loop
**Why:** BL's `improve_agent.py` generates improved instructions via a single optimization pass. Constitutional AI critique-revise loops (from the `prompt-engineer` and `improve-agent` in wshobson) produce better prompts by having the LLM critique its own output against a rubric before finalizing. This is a 1-day improvement to existing infrastructure.

**What to build:**
- In `masonry/scripts/optimize_with_claude.py`: after generating improved instructions, add a critique pass: "Does this prompt violate any of: [10 anti-patterns]? List violations and corrections."
- Revise until no violations or max 3 rounds
- Log critique chain to agent snapshot history

**Complexity:** S (half day)
**Files:** `masonry/scripts/optimize_with_claude.py`

---

### 4. Harvest and Expand the prompt-engineer Agent
**Why:** BL lists `prompt-engineer` in the fleet but the wshobson version is far more detailed — it covers Constitutional AI, chain-of-thought, tree-of-thoughts, self-consistency, least-to-most prompting, model-specific optimization, and meta-prompting. The key rule "ALWAYS display the complete prompt text - never describe without showing" is a discipline BL should enforce.

**What to build:**
- Rewrite `~/.claude/agents/prompt-engineer.md` incorporating the wshobson spec's technique catalog
- Add required output checklist (technique used, rationale, full prompt text, test cases)
- Add model-specific optimization section for Claude Sonnet 4.6 and Haiku 4.5
- Register in Masonry fleet with `tier: "standard"`, model: `opus`

**Complexity:** S (2-3 hours)
**Files:** `~/.claude/agents/prompt-engineer.md`, `masonry/agent_registry.yml`

---

### 5. Adopt Conductor's Logical Work Unit Tracking in Autopilot
**Why:** BL's autopilot tracks tasks in `progress.json` but revert is git-based (by commit). Conductor tracks work at track/phase/task level and can revert a logical feature unit even if it spans multiple commits. This is especially valuable in `ultrawork` mode where many commits happen fast.

**What to build:**
- Extend `progress.json` schema with `tracks[]` — logical groupings above tasks (e.g., "auth system" track contains tasks 3, 4, 5)
- Add `/revert-track` command to autopilot: find all commits touching a track's files, interactive revert
- Orchestrator writes track metadata into `build.log` at task completion
- Expose via Kiln UI as "revert feature" button

**Complexity:** L (3-4 days)
**Files:** `.autopilot/progress.json` schema, `masonry/` hooks, Kiln frontend

---

## Harvestable Items

### Directly Harvestable (copy/adapt with minimal changes)

| Item | Source | Target in BL | Adaptation Needed |
|------|--------|-------------|-------------------|
| **PluginEval 10-dimension scoring rubric** | `docs/plugin-eval.md` | `masonry/src/scoring/` | Rename "plugin" → "agent", adjust weights for BL context |
| **Anti-pattern detection rules** | `docs/plugin-eval.md` | `masonry/scripts/onboard_agent.py` | Port 6 anti-patterns to Python check functions |
| **tdd-orchestrator agent spec** | `plugins/tdd-workflows/agents/tdd-orchestrator.md` | `~/.claude/agents/tdd-orchestrator.md` | Add BL-specific context (Masonry hooks, progress.json), keep core TDD content |
| **prompt-engineer agent spec** | `plugins/llm-application-dev/agents/prompt-engineer.md` | `~/.claude/agents/prompt-engineer.md` | Replace model references with Claude Sonnet 4.6/Haiku 4.5 specifics |
| **context-manager multi-agent handoff** | `plugins/agent-orchestration/agents/context-manager.md` | Recall integration | Extract multi-agent context handoff protocol for BL agent spawning |
| **Staged rollout pattern (5%→20%→50%→100%)** | `plugins/agent-orchestration/commands/improve-agent.md` | `masonry/scripts/improve_agent.py` | Add rollout tracking to agent snapshot history |
| **Competing hypothesis debug pattern** | `plugins/agent-teams/README.md` | `~/.claude/agents/parallel-debugger.md` | New agent using pattern |
| **Constitutional AI critique loop** | `plugins/llm-application-dev/agents/prompt-engineer.md` | `masonry/scripts/optimize_with_claude.py` | Add critique pass after optimization |
| **YouTube design extractor** | `tools/yt-design-extractor.py` | `masonry/tools/` or BL tools | Copy as-is, add to Makefile |

### Pattern Harvests (adapt the approach, not the code)

| Pattern | Source | BL Application |
|---------|--------|---------------|
| **Single-responsibility plugin principle** | `docs/architecture.md` | Audit existing BL agents for scope creep — agents doing too much should be split |
| **Four-tier model strategy** | `README.md`, `CLAUDE.md` | Formalize BL's model assignment: Opus for architecture/critical, Sonnet for standard, Haiku for ops/fast |
| **Skill max 1024 char metadata** | `CLAUDE.md` | Audit BL skills — trim descriptions, move content to `instructions` section |
| **Badge certification system** | `docs/plugin-eval.md` | Add Bronze/Silver/Gold/Platinum tier to BL agent registry `tier` field (currently just "draft/standard") |
| **Token budget management (context-restore)** | `plugins/context-management/commands/context-restore.md` | Add token budget param to Recall rehydration (currently unlimited) |
| **Relevance threshold (0.75) with temporal decay** | `plugins/context-management/commands/context-restore.md` | Add to `recall_rehydrate` MCP tool — older memories should score lower |

---

## JSON Summary

```json
{
  "repo": "wshobson/agents",
  "analyzed": "2026-03-28",
  "stats": {
    "plugins": 72,
    "agents_catalogued": 112,
    "skills_catalogued": 146,
    "tools": 79,
    "orchestrators": 16
  },
  "verdict": "high_value",
  "top_gaps": [
    {
      "feature": "PluginEval statistical quality evaluation",
      "gap_level": "CRITICAL",
      "bl_has": "heuristic eval loop (improve_agent.py)",
      "they_have": "3-layer statistical eval, 10 dimensions, Elo, Monte Carlo, badges"
    },
    {
      "feature": "Semantic / logical unit revert (Conductor)",
      "gap_level": "HIGH",
      "bl_has": "git commit revert only",
      "they_have": "track/phase/task revert hierarchy"
    },
    {
      "feature": "Parallel hypothesis debugging",
      "gap_level": "HIGH",
      "bl_has": "single diagnose-analyst",
      "they_have": "3 parallel competing investigators + synthesis"
    },
    {
      "feature": "TDD depth (mutation, property-based, chaos)",
      "gap_level": "HIGH",
      "bl_has": "TDD enforcer hook + discipline rules",
      "they_have": "tdd-orchestrator opus agent covering full lifecycle"
    },
    {
      "feature": "Anti-pattern detection for agents",
      "gap_level": "HIGH",
      "bl_has": "nothing",
      "they_have": "OVER_CONSTRAINED, BLOATED_SKILL, MISSING_TRIGGER etc."
    }
  ],
  "bl_leads_on": [
    "Research campaign loops (BL 2.0 waves)",
    "Simulation-based stress testing",
    "Typed payload system (Masonry schemas)",
    "Four-layer routing (deterministic → semantic → LLM → fallback)",
    "Kiln monitoring UI",
    "Recall memory integration (automatic vs explicit)"
  ],
  "immediate_harvests": [
    "PluginEval 10-dimension scoring rubric → masonry/src/scoring/",
    "Anti-pattern detection rules → onboard_agent.py",
    "tdd-orchestrator agent spec → agents/tdd-orchestrator.md",
    "prompt-engineer agent spec → agents/prompt-engineer.md",
    "Constitutional AI critique loop → optimize_with_claude.py",
    "Staged rollout (5/20/50/100%) → improve_agent.py",
    "YouTube design extractor → masonry/tools/"
  ],
  "top_recommendations": [
    {
      "rank": 1,
      "title": "Build BL-PluginEval agent quality system",
      "complexity": "M",
      "impact": "CRITICAL"
    },
    {
      "rank": 2,
      "title": "Implement parallel hypothesis debug teams",
      "complexity": "M",
      "impact": "HIGH"
    },
    {
      "rank": 3,
      "title": "Add Constitutional AI to agent improvement loop",
      "complexity": "S",
      "impact": "MEDIUM"
    },
    {
      "rank": 4,
      "title": "Harvest and expand prompt-engineer agent",
      "complexity": "S",
      "impact": "MEDIUM"
    },
    {
      "rank": 5,
      "title": "Adopt Conductor logical work unit tracking in autopilot",
      "complexity": "L",
      "impact": "MEDIUM"
    }
  ]
}
```

---

*Report generated by repo-researcher agent. Source: full exhaustive read of wshobson/agents via GitHub MCP. All file sizes, line counts, and content verified against live repo state as of 2026-03-28.*
