# Repo Research: VoltAgent/awesome-claude-code-subagents

**Repo**: https://github.com/VoltAgent/awesome-claude-code-subagents
**Researched**: 2026-03-28
**Researcher**: repo-researcher agent
**Purpose**: Identify capability gaps and patterns for BrickLayer 2.0

---

## Verdict Summary

This is the most complete publicly available catalog of Claude Code subagents — 127+ agents across 10 categories, packaged into a Claude plugin marketplace system with versioned bundles and CI enforcement. It beats BrickLayer in agent breadth (coverage of niche domains: chaos engineering, RL, accessibility testing, legacy modernization, scientific literature) and in distribution infrastructure (the plugin system is a significant gap BrickLayer lacks entirely). BrickLayer beats it across the board on runtime infrastructure: hooks, MCP server, routing engine, DSPy optimization, Recall integration, Kiln monitoring, EMA telemetry, and the full SPARC research loop — this repo has zero runtime, it is a pure agent content catalog with no orchestration capabilities.

---

## File Inventory

### Root
- `README.md` — 29KB master index; install instructions, smart model routing table, tool philosophy, all 127 agents with descriptions, subagent-catalog slash commands, contributing guide
- `CLAUDE.md` — Standard subagent file format spec; tool assignment by agent role; canonical template
- `CONTRIBUTING.md` — Version bump requirements; PR workflow; quality standards (grammar, tools, descriptions)
- `.claude/settings.local.json` — Repo-level Claude Code permissions (Bash for:*, python3:*, git status:*, grep patterns)

### `.claude-plugin/`
- `marketplace.json` — 10 plugin entries with name, source, description, version, category, keywords

### `.github/workflows/`
- `enforce-plugin-version-bump.yml` — CI workflow: blocks PRs that modify .md agent files without bumping plugin.json + marketplace.json

### `tools/subagent-catalog/`
- `search.md` — `/subagent-catalog:search` slash command skill (fuzzy search across catalog)
- `fetch.md` — `/subagent-catalog:fetch` slash command skill (install a named agent)
- `list.md` — `/subagent-catalog:list` slash command skill (browse by category)
- `invalidate.md` — `/subagent-catalog:invalidate` slash command skill (clear local cache)
- `config.sh` — Shared shell config: GitHub API base URL, cache paths

### `categories/01-code-development/` (12 agents)
- `full-stack-developer.md` — Full-stack React/Node/Python developer (sonnet)
- `api-developer.md` — REST/GraphQL/gRPC API developer (sonnet)
- `typescript-developer.md` — TypeScript-specific specialist (sonnet)
- `python-developer.md` — Python-specific specialist (sonnet)
- `rust-developer.md` — Rust systems specialist (sonnet)
- `go-developer.md` — Go specialist (sonnet)
- `mobile-developer.md` — iOS/Android/React Native (sonnet)
- `game-developer.md` — Unity/Unreal/Godot specialist (sonnet)
- `embedded-developer.md` — Firmware/C/RTOS/MQTT (sonnet)
- `blockchain-developer.md` — Smart contracts/Solidity/Web3 (sonnet)
- `database-developer.md` — SQL/NoSQL/schema design (sonnet)
- `algorithm-specialist.md` — Data structures, complexity analysis, competitive programming (sonnet)

### `categories/02-language-framework/` (14 agents)
- `react-specialist.md` — React 18+/hooks/performance (sonnet)
- `vue-specialist.md` — Vue 3/Composition API/Pinia (sonnet)
- `angular-specialist.md` — Angular 17+/signals/RxJS (sonnet)
- `nextjs-specialist.md` — Next.js 14+/App Router/RSC (sonnet)
- `elixir-developer.md` — Elixir/Phoenix/OTP/GenServer (sonnet)
- `swift-developer.md` — Swift/SwiftUI/UIKit/Combine (sonnet)
- `kotlin-developer.md` — Kotlin/Coroutines/Compose/Android (sonnet)
- `rails-developer.md` — Ruby on Rails/ActiveRecord/Hotwire (sonnet)
- `django-developer.md` — Django/DRF/Celery/channels (sonnet)
- `laravel-developer.md` — Laravel/Eloquent/Livewire/Inertia (sonnet)
- `spring-developer.md` — Spring Boot/WebFlux/Hibernate (sonnet)
- `dotnet-developer.md` — .NET 8+/C#/ASP.NET Core (sonnet)
- `powershell-developer.md` — PowerShell 7+/modules/DSC/CIM (sonnet)
- `wordpress-developer.md` — WordPress/WooCommerce/Gutenberg (sonnet)

### `categories/03-infrastructure-devops/` (14 agents)
- `devops-engineer.md` — CI/CD/deployment pipelines (sonnet)
- `kubernetes-operator.md` — K8s orchestration/Helm/operators (sonnet)
- `terraform-architect.md` — IaC with Terraform/state management (sonnet)
- `terragrunt-expert.md` — Terragrunt/DRY Terraform/environments (sonnet)
- `ansible-automator.md` — Configuration management/playbooks (sonnet)
- `aws-architect.md` — AWS services/Well-Architected Framework (sonnet)
- `gcp-specialist.md` — GCP services/BigQuery/GKE (sonnet)
- `azure-engineer.md` — Azure services/AKS/DevOps pipelines (sonnet)
- `docker-specialist.md` — Container builds/multi-stage/compose (sonnet)
- `sre-engineer.md` — SLOs/SLAs/error budgets/runbooks (sonnet)
- `network-engineer.md` — Networking/routing/security groups (sonnet)
- `database-admin.md` — DBA tasks/tuning/HA/backup (sonnet)
- `linux-admin.md` — Linux administration/scripting/hardening (sonnet)
- `monitoring-engineer.md` — Observability/Prometheus/Grafana/alerting (sonnet)

### `categories/04-quality-security/` (12 agents)
- `qa-engineer.md` — Test strategy/automated testing (sonnet)
- `test-automation.md` — Cypress/Playwright/Selenium frameworks (sonnet)
- `security-auditor.md` — OWASP/CVEs/threat modeling (sonnet)
- `penetration-tester.md` — Ethical hacking/reconnaissance/exploitation (sonnet)
- `compliance-auditor.md` — SOC2/HIPAA/GDPR/PCI-DSS compliance (sonnet)
- `performance-engineer.md` — Load testing/benchmarking/profiling (sonnet)
- `chaos-engineer.md` — Chaos experiments/blast radius/game days (sonnet)
- `accessibility-tester.md` — WCAG 2.1/3.0/screen reader testing (haiku)
- `api-tester.md` — REST/GraphQL/contract testing/fuzzing (sonnet)
- `mobile-tester.md` — Mobile-specific test automation/appium (sonnet)
- `security-scanner.md` — SAST/DAST/dependency scanning (sonnet)
- `code-quality-reviewer.md` — Code review/tech debt/complexity analysis (sonnet)

### `categories/05-data-ai/` (12 agents)
- `data-engineer.md` — ETL/pipelines/dbt/Spark/Airflow (sonnet)
- `ml-engineer.md` — ML training/deployment/MLOps (sonnet)
- `data-scientist.md` — Statistical analysis/visualization/reporting (sonnet)
- `ai-agent-builder.md` — LangChain/LlamaIndex/agent frameworks (sonnet)
- `llm-optimizer.md` — Prompt engineering/fine-tuning/evals (sonnet)
- `computer-vision-engineer.md` — YOLO/OpenCV/segmentation/diffusion (sonnet)
- `nlp-engineer.md` — NLP tasks/transformers/sentiment/NER (sonnet)
- `reinforcement-learning-engineer.md` — PPO/SAC/TD3/DQN/Gymnasium/RLlib/Isaac Gym (sonnet)
- `vector-db-specialist.md` — Qdrant/Pinecone/Weaviate/pgvector (sonnet)
- `streaming-engineer.md` — Kafka/Pulsar/Flink/real-time pipelines (sonnet)
- `analytics-engineer.md` — dbt/Snowflake/dimensional modeling (sonnet)
- `feature-store-engineer.md` — Feast/Tecton/feature pipelines (sonnet)

### `categories/06-developer-experience/` (9 agents)
- `dx-optimizer.md` — Build time optimization/monorepo tooling/HMR (sonnet)
- `documentation-writer.md` — Technical writing/API docs/OpenAPI (sonnet)
- `code-reviewer.md` — Pull request review/standards enforcement (sonnet)
- `refactoring-specialist.md` — Structural refactoring/pattern migration (sonnet)
- `dependency-manager.md` — Dependency updates/audits/lockfiles (sonnet)
- `mcp-developer.md` — MCP server development/JSON-RPC 2.0 (sonnet)
- `monorepo-architect.md` — Turborepo/Nx/Bazel/workspace tooling (sonnet)
- `legacy-modernizer.md` — Strangler fig/branch by abstraction/migration (sonnet)
- `performance-profiler.md` — Application profiling/flamegraphs/optimization (sonnet)

### `categories/07-domain-specific/` (14 agents)
- `fintech-developer.md` — Payment processing/PCI-DSS/KYC/AML (sonnet)
- `healthtech-developer.md` — HL7 FHIR/HIPAA/EHR integration (sonnet)
- `iot-developer.md` — MQTT/CoAP/ESP32/edge computing (sonnet)
- `ar-vr-developer.md` — WebXR/three.js/Unity XR/spatial UI (sonnet)
- `robotics-developer.md` — ROS2/SLAM/motion planning/sensor fusion (sonnet)
- `scientific-computing.md` — NumPy/SciPy/simulation/HPC (sonnet)
- `geospatial-developer.md` — GIS/PostGIS/Mapbox/satellite imagery (sonnet)
- `audio-developer.md` — DSP/Web Audio API/synthesis/DAW (sonnet)
- `compiler-developer.md` — Language design/LLVM/bytecode/IR (sonnet)
- `graphics-programmer.md` — WebGPU/WGSL/shaders/rendering (sonnet)
- `quantum-developer.md` — Qiskit/Cirq/quantum algorithms (sonnet)
- `bioinformatics-developer.md` — Biopython/BWA/genomics pipelines (sonnet)
- `crypto-developer.md` — Zero-knowledge proofs/STARK/SNARK/Noir (sonnet)
- `edge-computing.md` — Cloudflare Workers/Deno Deploy/edge-native (sonnet)

### `categories/08-business-product/` (10 agents)
- `product-manager.md` — PRDs/roadmaps/prioritization/OKRs (sonnet)
- `scrum-master.md` — Sprint planning/retrospectives/agile ceremonies (sonnet)
- `technical-writer.md` — Technical documentation/style guides (sonnet)
- `ux-researcher.md` — User research/journey mapping/usability testing (sonnet)
- `growth-hacker.md` — A/B testing/funnel optimization/virality (sonnet)
- `seo-specialist.md` — SEO/content strategy/keyword research (sonnet)
- `sales-engineer.md` — Technical sales/demos/POC development (sonnet)
- `customer-success.md` — Onboarding flows/health scoring/playbooks (sonnet)
- `marketing-engineer.md` — Marketing automation/attribution/analytics (sonnet)
- `technical-recruiter.md` — Technical hiring/screening/take-home design (sonnet)

### `categories/09-meta-orchestration/` (10 agents)
- `multi-agent-coordinator.md` — Multi-agent patterns: master-worker/peer/hierarchical/pub-sub/scatter-gather/consensus, DAG execution, saga patterns, checkpoint/restart (opus)
- `workflow-orchestrator.md` — State machines, saga patterns, 2-phase commit, compensation, ACID, human-in-loop workflows, SLA tracking (opus)
- `context-manager.md` — Shared state for distributed agents: vector embeddings, graph relationships, full-text search, hierarchical org (sonnet)
- `agent-installer.md` — In-session agent browser and installer: GitHub API + Bash/WebFetch, installs to ~/.claude/agents/ (haiku)
- `error-coordinator.md` — Distributed error detection <30s, recovery >90%, MTTR <5min, circuit breakers, bulkhead isolation, post-mortem automation (sonnet)
- `performance-monitor.md` — Metric latency <1s, SLO management, error budgets, distributed tracing, burn rate alerts, ML-based anomaly detection (haiku)
- `resource-optimizer.md` — Cost optimization/autoscaling/resource allocation (sonnet)
- `security-coordinator.md` — Centralized security policy enforcement across agents (sonnet)
- `observability-engineer.md` — Distributed tracing/metrics/logs unified pipeline (sonnet)
- `prompt-optimizer.md` — Automated prompt optimization/eval/tuning loops (sonnet)

### `categories/10-research-analysis/` (10 agents)
- `scientific-literature-researcher.md` — Uses `mcp__bgpt__search_papers` (external BGPT MCP at https://bgpt.pro/mcp/sse); returns 25+ structured fields per paper (sonnet)
- `market-researcher.md` — Market analysis/competitive intelligence/trend forecasting (sonnet)
- `data-analyst.md` — Statistical analysis/SQL/visualization/reporting (sonnet)
- `financial-analyst.md` — DCF/valuations/financial modeling/risk (sonnet)
- `competitive-intelligence.md` — CI frameworks/win-loss/landscape mapping (sonnet)
- `trend-forecaster.md` — Trend analysis/signal detection/forecasting models (sonnet)
- `user-behavior-analyst.md` — Cohort analysis/funnel analysis/retention (sonnet)
- `risk-analyst.md` — Risk frameworks/Monte Carlo/sensitivity analysis (sonnet)
- `survey-researcher.md` — Survey design/statistical sampling/analysis (sonnet)
- `patent-analyst.md` — Patent search/freedom-to-operate/IP strategy (sonnet)

---

## Architecture Overview

The repo has zero runtime architecture — it is a pure content catalog with a distribution layer on top.

**Content layer**: 127+ agent `.md` files, each with YAML frontmatter (`name`, `description`, `model`, `tools`) and a markdown system prompt body following a consistent pattern: role definition → communication protocol (structured JSON for inter-agent state) → progress tracking (structured JSON for real-time metrics) → task execution methodology → output requirements.

**Distribution layer**: Claude Code plugin marketplace system. Ten category bundles (`.claude-plugin/plugin.json` per category + master `.claude-plugin/marketplace.json`). Installed via `claude plugin marketplace add voltagent-core-dev` or `claude plugin install path`. CI workflow enforces that any `.md` file change bumps the corresponding plugin version, preventing stale installs.

**Tooling layer**: `tools/subagent-catalog/` provides four slash commands (`/subagent-catalog:search`, `:fetch`, `:list`, `:invalidate`) backed by shell scripts and GitHub API calls for in-session catalog browsing without leaving Claude Code.

**Agent-installer meta-agent**: `categories/09-meta-orchestration/agent-installer.md` is an in-session haiku-model agent that can browse the catalog and install agents at runtime, enabling self-expanding agent fleet capabilities.

The key design decision: all agents embed a **Communication Protocol** section with a JSON context-query format, enabling structured inter-agent state passing. All agents embed a **progress tracking JSON** block showing live metrics. This gives every agent in the catalog a consistent integration contract for use in orchestrated multi-agent workflows.

---

## Agent Catalog

### Meta-Orchestration (Selected Deep Reads)

**multi-agent-coordinator** (opus)
- Coordination patterns: master-worker, peer-to-peer, hierarchical, pub-sub, scatter-gather, consensus
- DAG execution, saga patterns, checkpoint/restart, deadlock prevention
- Targets: <5% coordination overhead, 100+ agent scalability, 100% deadlock prevention
- Unique: consensus-based decision making across agents; scatter-gather with aggregation

**workflow-orchestrator** (opus)
- State machines, saga pattern with compensation logic, two-phase commit, ACID
- Human task workflows with approval gates, SLA tracking with escalation
- Target: 99.9% reliability, <30s recovery
- Unique: compensation logic for failed distributed transactions; human-in-loop SLA tracking

**context-manager** (sonnet)
- Shared state context store for distributed agents
- Vector embeddings + graph relationships + full-text search + hierarchical organization
- Target: <100ms retrieval, 99.9% availability, 89% cache hit rate
- Unique: hybrid retrieval (vector + graph + full-text); context partitioning by agent role

**agent-installer** (haiku)
- In-session agent browser and installer
- GitHub API + WebFetch/Bash(curl) to list categories and agent files
- Installs to `~/.claude/agents/` (global) or `.claude/agents/` (local)
- Unique: self-expanding fleet; interactive browsing without leaving Claude Code

**error-coordinator** (sonnet)
- Distributed error detection <30s, recovery >90%, MTTR <5min
- Circuit breakers, bulkhead isolation, cascade prevention
- Post-mortem automation, chaos engineering integration
- Learning integration: 15% monthly improvement in error pattern recognition
- Unique: cross-agent error correlation; automated post-mortem generation; continuous learning loop

**performance-monitor** (haiku)
- Metric latency <1s, 90-day retention, alert accuracy >95%, resource overhead <2%
- SLO management, error budgets, distributed tracing, burn rate alerts
- ML-based anomaly detection
- Unique: burn rate calculation for SLO error budgets; haiku model (low overhead for monitoring)

### Quality/Security (Selected Deep Reads)

**chaos-engineer** (sonnet)
- Hypothesis-driven experiments with blast radius control
- Types: infrastructure chaos, application chaos, data chaos, security chaos
- Automated rollback <30s; game day planning; CI/CD integration
- Unique: BrickLayer has no chaos engineering capability; hypothesis-driven experiment format

**accessibility-tester** (haiku)
- WCAG 2.1/3.0 compliance; screen reader testing (NVDA/JAWS/VoiceOver/Narrator)
- ARIA implementation, keyboard navigation, mobile accessibility
- Automated score improvement tracking (67→98 example)
- Unique: BrickLayer's masonry-design-token-enforcer warns on hex colors but has no WCAG testing

### Developer Experience (Selected Deep Reads)

**dx-optimizer** (sonnet)
- Build time <30s target; HMR <100ms; test run <2min
- Monorepo tooling (Nx, Turborepo); developer satisfaction metrics 4.6/5
- Automated workflow metric tracking
- Unique: quantitative DX improvement with specific targets; developer satisfaction scoring

**mcp-developer** (sonnet)
- MCP server development: JSON-RPC 2.0 compliance, TypeScript SDK (Zod), Python SDK (Pydantic)
- Protocol compliance testing >90% coverage
- Integration patterns: database adapters, API wrappers, file system, auth providers
- Unique: BrickLayer has Masonry as an MCP server but no dedicated agent for building new MCP servers

**legacy-modernizer** (sonnet)
- Strangler fig pattern, branch by abstraction, parallel run, event interception
- Zero production disruption; characterization tests for legacy behavior capture
- Schema evolution, cloud migration patterns
- Unique: structured migration framework with explicit zero-disruption constraint

### Data/AI (Selected Deep Read)

**reinforcement-learning-engineer** (sonnet)
- PPO, SAC, TD3, DQN, A2C/A3C, Dreamer/MuZero, CQL/IQL (offline RL)
- Frameworks: Gymnasium/Farama, Stable-Baselines3, RLlib/Ray, CleanRL, TorchRL, JAX (PureJaxRL), Unity ML-Agents, Isaac Gym
- Sim-to-real with domain randomization
- Unique: BrickLayer has no RL specialist; offline RL with conservative Q-learning is niche

### Research/Analysis (Selected Deep Read)

**scientific-literature-researcher** (sonnet)
- Uses `mcp__bgpt__search_papers` — external BGPT MCP at `https://bgpt.pro/mcp/sse`
- Returns 25+ structured fields per paper: methods, results, conclusions, sample sizes, limitations, quality scores, citation counts
- Full-text search across scientific paper corpus
- Unique: BrickLayer has no academic paper search; this is a high-value research capability gap

---

## Feature Gap Analysis

| Feature | In VoltAgent/awesome | In BrickLayer 2.0 | Gap Level | Notes |
|---------|---------------------|-------------------|-----------|-------|
| Claude plugin marketplace system | Yes — 10 bundles, versioned, CI enforced | No — individual .md files only | HIGH | Enables `claude plugin marketplace add voltagent-core-dev` distribution; BrickLayer has 50+ agents with no packaging/versioning system |
| Scientific paper search (BGPT MCP) | Yes — mcp__bgpt__search_papers, 25+ fields | No | HIGH | External MCP at bgpt.pro/mcp/sse; returns structured paper metadata; directly relevant to BrickLayer's research campaigns |
| Chaos engineering agent | Yes — hypothesis-driven, blast radius control, game days | No | HIGH | CI/CD integration for continuous chaos; structured experiment format; would improve BrickLayer's simulation capabilities |
| DX optimizer agent | Yes — build time, HMR, test suite targets, satisfaction metrics | Partial (developer, devops agents exist) | HIGH | BrickLayer developer agent has no DX-specific focus or quantitative targets; dx-optimizer has explicit build time / HMR thresholds |
| MCP server developer agent | Yes — JSON-RPC 2.0, TypeScript/Python SDKs, protocol testing | No dedicated agent | MEDIUM | BrickLayer has masonry-engineer for Masonry changes but no general MCP server development specialist |
| Agent self-installation (agent-installer) | Yes — haiku agent, GitHub API, in-session install | Partial (masonry-agent-onboard.js hook) | MEDIUM | BrickLayer auto-onboards discovered agents; VoltAgent allows in-session browsing + install of agents by name |
| Saga pattern / compensation logic | Yes — workflow-orchestrator with 2-phase commit, compensation | Partial (consensus-builder, claims board) | MEDIUM | BrickLayer has consensus and claims escalation; no explicit saga/compensation for failed multi-step operations |
| Subagent catalog slash commands | Yes — /subagent-catalog:search, :fetch, :list, :invalidate | No | MEDIUM | In-session catalog browsing without leaving Claude Code; useful for Tim's fleet management |
| Error coordinator (distributed error correlation) | Yes — cross-agent circuit breakers, bulkhead, post-mortem | Partial (masonry-tool-failure.js 3-strike) | MEDIUM | BrickLayer has 3-strike escalation; no cross-agent error correlation or automated post-mortem |
| SLO / error budget tracking | Yes — performance-monitor with burn rate alerts | No | MEDIUM | BrickLayer tracks EMA scores per agent but no formal SLO/error budget management |
| Legacy modernization patterns | Yes — strangler fig, branch by abstraction, parallel run | No | MEDIUM | BrickLayer has no migration-specific agent; useful for ADBP / any legacy system work |
| Accessibility testing (WCAG) | Yes — accessibility-tester (haiku) | Partial (design-token-enforcer warns on hex) | MEDIUM | BrickLayer has no WCAG compliance testing; masonry-design-token-enforcer only checks tokens |
| Reinforcement learning specialist | Yes — full RL stack (PPO/SAC/DQN/RLlib/Isaac Gym) | No | MEDIUM | Niche but relevant if BrickLayer adds adaptive agent training via RL |
| Plugin version enforcement CI | Yes — enforce-plugin-version-bump.yml | No plugin system exists | MEDIUM | Prerequisite pattern for any future plugin marketplace |
| Communication Protocol standard | Yes — all 127 agents embed structured JSON context-query section | Partial (payload schemas in masonry/src/schemas/) | MEDIUM | VoltAgent agents have this in the agent body; BrickLayer has typed schemas but agents don't embed a standard inter-agent communication section |
| Elixir/Phoenix specialist | Yes — elixir-developer.md | No | LOW | BrickLayer has no Elixir work |
| Swift/SwiftUI specialist | Yes | No | LOW | BrickLayer has Kotlin (JellyStream); no iOS work |
| Rails/Django/Laravel/Spring specialists | Yes | Partial (python-developer exists in fleet) | LOW | Project-specific |
| PowerShell developer | Yes | No | LOW | Tim uses Python/Bash preference; Windows-specific tooling |
| WordPress developer | Yes | No | LOW | Not in Tim's stack |
| Compliance auditor (SOC2/HIPAA/GDPR) | Yes | No dedicated agent | LOW | BrickLayer has security agent (OWASP); compliance auditing is broader |
| Penetration tester | Yes | Partial (security agent covers OWASP) | LOW | Ethical hacking scope extends beyond BrickLayer's security agent |
| Game developer | Yes | No | LOW | Not relevant to current projects |
| Business/product agents (10 agents) | Yes — PM, scrum master, growth hacker, etc. | Partial (karen for docs/roadmaps) | LOW | Business context agents; not core to BrickLayer's dev/research mission |
| Terragrunt expert | Yes | Partial (devops agent) | LOW | Tim uses Docker Compose/CasaOS; Terragrunt not in stack |
| Geospatial/robotics/quantum/bioinformatics | Yes | No | LOW | Highly domain-specific; not relevant to current projects |
| Full runtime infrastructure (hooks) | No | Yes — 14 hooks (PreToolUse, PostToolUse, Stop, SessionStart) | BrickLayer advantage | VoltAgent has zero hooks |
| MCP server (Masonry) | No | Yes — masonry_status, masonry_route, masonry_fleet, etc. | BrickLayer advantage | VoltAgent has no MCP server |
| DSPy prompt optimization | No | Yes — eval→optimize→compare loop | BrickLayer advantage | VoltAgent has prompt-optimizer agent but no automated eval pipeline |
| Campaign research loop | No | Yes — full SPARC loop via Trowel | BrickLayer advantage | VoltAgent is a pure agent catalog with no orchestration |
| EMA telemetry + HNSW reasoning bank | No | Yes — telemetry.jsonl → α=0.3 EMA, local HNSW | BrickLayer advantage | No equivalent in VoltAgent |
| PageRank confidence scoring | No | Yes — graph/PageRank damping=0.85 | BrickLayer advantage | No equivalent in VoltAgent |
| Recall integration (memory) | No | Yes — Qdrant + Neo4j + Ollama | BrickLayer advantage | VoltAgent agents have no persistent memory |
| Kiln monitoring UI | No | Yes — BrickLayerHub Electron app | BrickLayer advantage | No equivalent in VoltAgent |
| Adaptive topology selector | No | Yes — parallel/pipeline/mesh/hierarchical | BrickLayer advantage | VoltAgent coordinator mentions patterns but has no automated selector |
| Claims board / async escalation | No | Yes — .autopilot/claims.json + HUD | BrickLayer advantage | No equivalent in VoltAgent |

---

## Top 5 Recommendations

### 1. Build a BrickLayer Plugin Marketplace System [16h, HIGH PRIORITY]

**What to build**: Package BrickLayer's 50+ agents into versioned category bundles installable via `claude plugin marketplace add bricklayer-core-dev`. Mirror the VoltAgent structure: a `marketplace.json` at repo root, per-category `.claude-plugin/plugin.json` files, a CI workflow that blocks PRs that modify agent `.md` files without bumping the corresponding plugin version.

**Why it matters**: BrickLayer agents have no packaging, versioning, or distribution infrastructure. When Tim wants to start a fresh project with the BrickLayer fleet, there is no clean install path. The VoltAgent approach shows that 10 plugin bundles covering logical categories (core dev, infrastructure, QA, data/AI, meta-orchestration, research) is the right granularity. Version enforcement via CI prevents the silent drift problem where an agent changes but downstream installs don't update.

**Implementation sketch**:
1. Create `plugins/` directory with category groupings matching BrickLayer's agent tiers
2. Write `.claude-plugin/plugin.json` per category (name, version, agent paths)
3. Write root `marketplace.json` aggregating all bundles
4. Add `.github/workflows/enforce-plugin-version-bump.yml` — detect .md changes in git diff, check plugin.json version was bumped, block merge if not
5. Add `/bricklayer-install` slash command backed by shell script
6. Update karen agent to track plugin versions in CHANGELOG

### 2. Integrate BGPT MCP for Academic Paper Search in Research Campaigns [4h, HIGH PRIORITY]

**What to build**: Add `mcp__bgpt__search_papers` to BrickLayer's MCP server list and create a `bgpt-researcher` agent (or extend `research-analyst`) to invoke the BGPT MCP at `https://bgpt.pro/mcp/sse`. The tool returns 25+ structured fields per paper including methods, results, sample sizes, limitations, and quality scores.

**Why it matters**: BrickLayer's research campaigns (Trowel loop, research-analyst, competitive-analyst) currently have no access to academic literature. For quantitative research questions — especially in ADBP (token economics, behavioral finance), System-Recall (memory architectures, vector search), and any ML work — peer-reviewed literature is high-signal evidence. VoltAgent's `scientific-literature-researcher` demonstrates the pattern: the BGPT MCP is a drop-in external tool requiring only a settings.json entry.

**Implementation sketch**:
1. Add BGPT MCP to `~/.claude/settings.json` under `mcpServers`: `{ "bgpt": { "type": "sse", "url": "https://bgpt.pro/mcp/sse" } }`
2. Extend `research-analyst.md` with a `Literature Search` phase that calls `mcp__bgpt__search_papers` for empirical evidence
3. Add `bgpt-researcher` as an optional specialist for pure academic literature review tasks
4. Update Trowel to include a literature search wave when `mode: "academic"` is set
5. Test on a SPARC campaign question to validate structured paper output

### 3. Add Chaos Engineer Agent for Simulation Fault Injection [8h, HIGH PRIORITY]

**What to build**: A `chaos-engineer` agent for BrickLayer that applies hypothesis-driven fault injection experiments to `simulate.py` runs. It should generate hypotheses ("if latency increases 3x, what breaks?"), define blast radius constraints, inject failures systematically, and roll back automatically on safety violations.

**Why it matters**: BrickLayer's autoresearch loop runs simulations to find failure boundaries, but agents currently modify SCENARIO PARAMETERS manually. A chaos agent would systematically generate edge-case parameter combinations, run them, collect failure modes, and generate post-mortems — automating the most time-intensive part of the research loop. VoltAgent's chaos-engineer shows the pattern: hypothesis-driven experiments with explicit blast radius control and automated rollback in <30s.

**Implementation sketch**:
1. Create `.claude/agents/chaos-engineer.md` with hypothesis generation (using findings/ context), experiment execution (modify simulate.py parameters, run, capture output), blast radius guard (define max parameter deviation), automated rollback on error
2. Add `masonry_run_simulation` invocation pattern where chaos-engineer generates 10 hypotheses, runs them in parallel, returns a fault map
3. Hook into the Trowel campaign loop as an optional `mode: "chaos"` wave
4. Add post-mortem template to findings/ format

### 4. Build a DX Optimizer Agent with Quantitative Build Targets [6h, HIGH PRIORITY]

**What to build**: A `dx-optimizer` agent for BrickLayer with explicit quantitative targets: build time <30s, HMR <100ms, test suite <2min, and a developer satisfaction metric. This agent analyzes build configs, identifies bottlenecks, implements caching, and measures improvement deltas.

**Why it matters**: BrickLayer's developer and devops agents handle code and infrastructure but have no DX-specific focus. Tim's projects (Kiln electron app, System-Recall FastAPI, Sadie voice assistant, ADBP frontend) all have build pipelines that degrade over time. A dx-optimizer with concrete targets would prevent the "builds just get slower" drift and surface optimization opportunities proactively. VoltAgent's dx-optimizer shows the pattern: monorepo tooling (Nx/Turborepo), Vite optimization, test parallelization, with tracking toward specific millisecond targets.

**Implementation sketch**:
1. Create `.claude/agents/dx-optimizer.md` with build measurement phase (time npm run build, time pytest, time vite dev), analysis phase (identify bottlenecks: cold vs. warm, tree-shaking, test isolation), optimization phase (implement caching, code splitting, parallel test runners), and verification phase (remeasure against targets)
2. Define BrickLayer-specific DX baselines: Kiln (Electron), System-Recall (FastAPI + pytest), ADBP (Next.js or React + Anchor)
3. Add to masonry_fleet as a tier-2 specialist invoked by Mortar on any build-configuration task

### 5. Standardize Agent Communication Protocol Across the BrickLayer Fleet [4h, MEDIUM PRIORITY]

**What to build**: Add a `## Communication Protocol` section and `## Progress Tracking` JSON block to every BrickLayer agent `.md` file, establishing a standard inter-agent context-passing contract. This matches the pattern embedded in all 127 VoltAgent agents.

**Why it matters**: BrickLayer agents communicate via Masonry typed payload schemas (QuestionPayload, FindingPayload) but the agent `.md` files themselves don't embed a standard inter-agent communication section. When Mortar spawns agents in parallel, each agent starts cold without a standard for receiving context from the orchestrator. The VoltAgent pattern demonstrates that embedding a structured JSON context-query block in the agent's system prompt enables consistent, debuggable inter-agent state passing.

**Implementation sketch**:
1. Design the BrickLayer agent Communication Protocol: `{ "from_agent": "...", "campaign_id": "...", "question_id": "...", "context": {...}, "query": "..." }` — aligning with existing QuestionPayload and FindingPayload schemas
2. Write a template section (3-4 lines) to add to every agent `.md` file
3. Use masonry-agent-onboard.js hook to detect new agents missing the section and auto-add it
4. Run `improve_agent.py` eval loop to verify that adding the section improves or maintains scoring

---

## Novel Patterns to Incorporate (Future)

**Saga pattern with compensation logic**: The `workflow-orchestrator` agent implements two-phase commit and compensation transactions for failed multi-step operations. BrickLayer's claims board handles escalation but has no automated rollback path when a multi-agent workflow partially fails. Worth tracking for the Trowel campaign loop when wave tasks partially complete.

**Context manager as shared state service**: The `context-manager` agent maintains hybrid retrieval (vector + graph + full-text) for distributed agent state. BrickLayer has Recall (Qdrant + Neo4j + Ollama) for memory but agents don't actively update a shared context mid-campaign. A lightweight context-manager pattern sitting in front of Recall could improve mid-campaign state sharing between parallel agents.

**Burn rate alerts for agent SLOs**: The `performance-monitor` uses error budget burn rate calculations (alerting when SLO error budget is depleting faster than allowed). BrickLayer's EMA system tracks per-agent scores but doesn't frame them as SLOs with error budgets. Mapping each agent's EMA score to an SLO (e.g., "research-analyst must score ≥0.75 in 95% of runs") and tracking burn rate would give Kiln a more formal quality management view.

**ML-based anomaly detection for tool failures**: The `performance-monitor` uses ML models to detect anomalous metric patterns. BrickLayer's masonry-tool-failure.js uses a simple 3-strike counter. Training a lightweight anomaly model on telemetry.jsonl (tool failure patterns, timing, agent combos) could catch cascade failures before the 3-strike threshold triggers.

**Characterization tests for legacy code**: The `legacy-modernizer` generates characterization tests that capture existing behavior before refactoring, preventing regressions. BrickLayer's TDD enforcer requires tests alongside new code but has no pattern for capturing legacy behavior first. This is directly applicable to Kiln and older Masonry scripts.

**In-session agent cross-installation**: The `agent-installer` agent can install agents from the VoltAgent catalog into BrickLayer's `~/.claude/agents/` directory at runtime. This means Tim could in-session say "install chaos-engineer from VoltAgent" and have it available immediately. BrickLayer's masonry-agent-onboard.js would then auto-register it. The two systems compose naturally.

**Parallel game day planning**: The chaos engineer's game day planning pattern — scheduled chaos days with explicit hypothesis queues, safety controls, and observers — maps well to BrickLayer research campaigns. Running a "game day" as a dedicated campaign wave (mode: "chaos") would formalize what is currently ad-hoc parameter stress testing.

**Patent search integration**: The `patent-analyst` agent uses WebFetch/WebSearch for patent landscape analysis. For ADBP (Solana discount-credit platform), understanding the IP landscape around employee benefit token systems could be valuable. Extending `research-analyst` with a patent search phase is low-effort and potentially high-value.
