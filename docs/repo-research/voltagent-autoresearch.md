# Repo Research: VoltAgent/awesome-claude-code-subagents + uditgoenka/autoresearch

**Repos**: https://github.com/VoltAgent/awesome-claude-code-subagents · https://github.com/uditgoenka/autoresearch
**Researched**: 2026-03-28
**Researcher**: repo-researcher agent
**Purpose**: Identify capability gaps and patterns for BrickLayer 2.0

---

## Verdict Summary

Two complementary repos — one is a catalogue of 127+ Claude Code subagents covering domains BrickLayer hasn't touched (game dev, IoT, Fintech, chaos engineering, RL, MLOps, NLP, penetration testing, embedded systems, etc.) and the other is a mature autonomous iteration skill with sub-commands BrickLayer lacks (`:debug`, `:fix`, `:ship`, `:scenario`, `:predict`, `:learn`). BrickLayer beats both on research-campaign depth (typed payloads, EMA training, HNSW recall, consensus voting, graph/PageRank scoring) but is outclassed on breadth of specialist agents and on the meta-skill of applying autoresearch principles to non-research domains like shipping, bug hunting, and codebase documentation. The highest-value lift for BrickLayer is the `/autoresearch:debug` + `/autoresearch:fix` chained loop and the multi-persona swarm prediction pattern, both of which directly address Tim's stated top priority of Ruflo-level dev execution.

---

## File Inventory

### VoltAgent/awesome-claude-code-subagents

```
README.md                                  — Full agent catalogue (127+ agents across 10 categories)
CLAUDE.md                                  — Template, tool philosophy, contributing guide
CONTRIBUTING.md                            — PR guidelines, agent format spec
install-agents.sh                          — Interactive installer (browse, select, install/uninstall)
.claude/settings.local.json               — Local MCP settings (not substantive)
categories/01-core-development/            — 10 agents: api-designer, backend-developer, electron-pro, etc.
categories/02-language-specialists/        — 28 agents: Swift, Vue, Angular, Elixir, Expo, Flutter, Kotlin, etc.
categories/03-infrastructure/              — 16 agents: Azure, Kubernetes, Terraform, Terragrunt, SRE, etc.
categories/04-quality-security/            — 14 agents: chaos-engineer, penetration-tester, accessibility-tester, etc.
categories/05-data-ai/                     — 13 agents: LLM architect, MLOps, NLP, RL engineer, data-scientist, etc.
categories/06-developer-experience/        — 13 agents: MCP developer, legacy-modernizer, dx-optimizer, etc.
categories/07-specialized-domains/         — 12 agents: embedded-systems, IoT, game-developer, fintech, payment-integration, etc.
categories/08-business-product/            — 11 agents: product-manager, scrum-master, legal-advisor, sales-engineer, etc.
categories/09-meta-orchestration/          — 9 agents: context-manager, workflow-orchestrator, task-distributor, etc.
categories/10-research-analysis/           — 7 agents: scientific-literature-researcher (BGPT MCP), trend-analyst, etc.
tools/subagent-catalog/                    — Claude Code skill for searching/fetching from this catalogue
```

### uditgoenka/autoresearch

```
README.md                                  — Full command reference + loop description
COMPARISON.md                             — Karpathy's original autoresearch vs this implementation
CONTRIBUTING.md                           — Contribution guidelines
claude-plugin/commands/autoresearch.md    — Main /autoresearch command registration
claude-plugin/commands/autoresearch/      — 8 subcommand registrations (ship, plan, security, debug, fix, scenario, predict, learn)
claude-plugin/skills/autoresearch/SKILL.md — Master skill file (30KB): interactive setup gate, all subcommand protocols
claude-plugin/skills/autoresearch/references/autonomous-loop-protocol.md — Full 8-phase loop protocol (28KB)
claude-plugin/skills/autoresearch/references/core-principles.md         — 7 Karpathy principles with ML examples
claude-plugin/skills/autoresearch/references/debug-workflow.md           — Scientific bug-hunt loop (21KB)
claude-plugin/skills/autoresearch/references/fix-workflow.md             — Error-crusher loop (26KB)
claude-plugin/skills/autoresearch/references/learn-workflow.md           — Doc engine protocol (22KB)
claude-plugin/skills/autoresearch/references/plan-workflow.md            — Setup wizard protocol (9KB)
claude-plugin/skills/autoresearch/references/predict-workflow.md         — Multi-persona swarm (30KB)
claude-plugin/skills/autoresearch/references/results-logging.md          — TSV tracking format
claude-plugin/skills/autoresearch/references/scenario-workflow.md        — Scenario explorer (18KB)
claude-plugin/skills/autoresearch/references/security-workflow.md        — STRIDE+OWASP audit (36KB)
claude-plugin/skills/autoresearch/references/ship-workflow.md            — Universal ship workflow (14KB)
guide/                                    — 10 guides + scenario walkthroughs
scripts/                                  — (not read; not relevant — installer helpers)
```

---

## Architecture Overview

### VoltAgent Architecture

This is a pure catalogue — no runtime, no orchestration layer, no shared infrastructure. Each agent is a self-contained markdown file with YAML frontmatter (`name`, `description`, `tools`, `model`). Agents are designed to be loaded into Claude Code's `~/.claude/agents/` or `.claude/agents/` directories.

The notable structural pattern is the Communication Protocol section inside each agent: agents declare JSON query payloads they send to a shared `context-manager` agent for coordinated state. This is a lightweight "inter-agent blackboard" pattern — not enforced at the platform level, but baked into agent prompts. The `context-manager` agent is the implicit hub: all agents query it before acting.

Model routing is explicit: `model: opus` for architecture/security/financial, `model: sonnet` for everyday coding, `model: haiku` for docs/search. Tool permissions are role-typed (read-only agents get no Write; research agents get WebFetch/WebSearch).

### Autoresearch Architecture

A single SKILL.md file loads all subcommands via a skill reference. The architecture is a state machine over a TSV results log (not JSON, not a database — just a flat file). Git is the explicit memory layer: every experiment is committed with `experiment:` prefix before verification; rollbacks use `git revert` (not `git reset --hard`) so failed attempts remain in history for pattern learning.

The interactive setup gate is the most sophisticated prompt-engineering pattern: `AskUserQuestion` is mandatory and BLOCKING before any loop starts. All required config (Goal, Scope, Metric, Direction, Verify, Guard) is collected in batched calls (max 4 questions per call) with smart codebase-scan defaults. The loop itself is deterministic: Read context → One change → Commit → Verify → Guard check → Keep/Revert → Log → Repeat.

The multi-persona prediction pattern (`:predict`) uses file-based knowledge graphs: .md files ARE the knowledge structure. Zero external dependencies (no vector DB, no graph DB). Each persona runs independently in the same Claude context, cross-examines findings, and a Devil's Advocate is mandatory to prevent groupthink.

---

## VoltAgent/awesome-claude-code-subagents

### Full Agent Inventory

#### Category 01 — Core Development
- **api-designer** — REST and GraphQL API architect; schema design, versioning, documentation
- **backend-developer** — Server-side expert for scalable APIs; auth, caching, async patterns
- **electron-pro** — Desktop application development; IPC, auto-update, packaging, cross-platform
- **frontend-developer** — React/Vue/Angular UI development; component architecture, state management
- **fullstack-developer** — End-to-end feature development; coordinates front and back
- **graphql-architect** — GraphQL schema design, federation, subscriptions, DataLoader
- **microservices-architect** — Distributed systems; service mesh, event-driven, circuit breakers
- **mobile-developer** — Cross-platform mobile (React Native, Flutter, native iOS/Android)
- **ui-designer** — Visual design and interaction; design systems, accessibility, animation
- **websocket-engineer** — Real-time communication; Socket.IO, WebRTC, pub-sub, scaling

#### Category 02 — Language Specialists
- **typescript-pro** — Advanced TypeScript; generics, decorators, conditional types
- **sql-pro** — Query optimization, schema design, indexing strategies
- **swift-expert** — iOS/macOS; SwiftUI, Combine, async/await, App Store
- **vue-expert** — Vue 3 Composition API, Pinia, Nuxt, testing
- **angular-architect** — Angular 15+ enterprise patterns, RxJS, NgRx
- **cpp-pro** — C++ performance; RAII, templates, SIMD, memory management
- **csharp-developer** — .NET ecosystem; LINQ, async, DI, EF Core
- **django-developer** — Django 4+; ORM, DRF, channels, Celery
- **dotnet-core-expert** — .NET 8 cross-platform; minimal APIs, Blazor, gRPC
- **dotnet-framework-4.8-expert** — Legacy .NET Framework; WCF, WebForms, COM interop
- **elixir-expert** — Elixir/OTP; GenServer, Phoenix LiveView, fault-tolerant supervision trees
- **expo-react-native-expert** — Expo SDK, EAS Build, OTA updates, native modules
- **fastapi-developer** — FastAPI async patterns, Pydantic v2, dependency injection
- **flutter-expert** — Flutter 3+; BLoC, Riverpod, platform channels
- **golang-pro** — Go concurrency; goroutines, channels, context propagation, interfaces
- **java-architect** — Enterprise Java; Spring, Hibernate, JPA, microservices
- **javascript-pro** — Modern JS; ESM, async/await, proxy/reflect, toolchain
- **powershell-5.1-expert** — Windows PowerShell 5.1 and .NET Framework automation
- **powershell-7-expert** — Cross-platform PowerShell 7+ modern .NET automation
- **kotlin-specialist** — Modern JVM; coroutines, Flow, Ktor, multiplatform
- **laravel-specialist** — Laravel 10+; Eloquent, queues, Livewire, Sail
- **nextjs-developer** — Next.js 14+; App Router, RSC, ISR, edge runtime
- **php-pro** — PHP 8+; modern OOP, Composer, testing, security
- **python-pro** — Python ecosystem; type hints, dataclasses, asyncio, packaging
- **rails-expert** — Rails 8.1; Hotwire, Turbo, Active Record, Action Cable
- **react-specialist** — React 18+; concurrent features, Server Components, hooks
- **rust-engineer** — Systems programming; ownership, traits, async, unsafe, FFI
- **spring-boot-engineer** — Spring Boot 3+; reactive, Security, Data, OpenAPI
- **symfony-specialist** — Symfony 6-8; Doctrine ORM, Messenger, API Platform

#### Category 03 — Infrastructure
- **azure-infra-engineer** — Azure infrastructure, Az PowerShell automation, ARM/Bicep
- **cloud-architect** — AWS/GCP/Azure multi-cloud; IaC, cost optimization, FinOps
- **database-administrator** — DBA work; backup, replication, failover, migration
- **docker-expert** — Containerization; multi-stage builds, compose, secrets, optimization
- **deployment-engineer** — Deployment automation; blue-green, canary, rollback strategies
- **devops-engineer** — CI/CD pipelines; GitHub Actions, Jenkins, artifact management
- **devops-incident-responder** — DevOps-specific incident handling; runbooks, on-call
- **incident-responder** — System incident response; runbooks, postmortem, RCA
- **kubernetes-specialist** — K8s; Helm, operators, RBAC, HPA, multi-cluster
- **network-engineer** — Networking; BGP, SD-WAN, firewall, load balancing, DNS
- **platform-engineer** — IDP design; golden paths, self-service, developer portals
- **security-engineer** — Infrastructure security; WAF, SIEM, zero-trust, hardening
- **sre-engineer** — SRE; SLOs, error budgets, toil reduction, runbooks
- **terraform-engineer** — Terraform IaC; modules, state management, drift detection
- **terragrunt-expert** — Terragrunt DRY IaC; root configs, dependency management
- **windows-infra-admin** — Active Directory, DNS, DHCP, GPO, PowerShell DSC

#### Category 04 — Quality and Security
- **accessibility-tester** — WCAG 2.1 compliance; screen readers, keyboard nav, ARIA, axe
- **ad-security-reviewer** — Active Directory security; GPO auditing, privilege escalation paths
- **architect-reviewer** — Architecture review; ADRs, trade-off analysis, pattern validation
- **chaos-engineer** — Controlled failure injection; GameDay planning, blast radius, MTTR
- **code-reviewer** — Code quality review; patterns, security, maintainability
- **compliance-auditor** — Regulatory compliance; GDPR, SOC2, ISO27001, HIPAA, PCI
- **debugger** — Advanced debugging; stack traces, memory dumps, profiling
- **error-detective** — Error pattern analysis; root cause, correlation, resolution
- **penetration-tester** — Ethical hacking; OWASP Top 10, network pen test, social engineering
- **performance-engineer** — Perf optimization; profiling, caching, query tuning, benchmarks
- **powershell-security-hardening** — PowerShell security; execution policy, Just Enough Admin
- **qa-expert** — Test automation; Selenium, Playwright, Jest, test strategy
- **security-auditor** — Security vulnerability assessment; CVE scanning, threat modeling
- **test-automator** — Test automation frameworks; CI integration, test pyramids

#### Category 05 — Data and AI
- **ai-engineer** — AI system design; RAG, fine-tuning, evaluation, inference optimization
- **data-analyst** — Data analysis; pandas, SQL, visualization, statistical inference
- **data-engineer** — Data pipelines; Spark, Airflow, dbt, Kafka, data lakes
- **data-scientist** — ML/statistics; feature engineering, model selection, A/B testing
- **database-optimizer** — Query tuning, indexing, EXPLAIN plans, partitioning
- **llm-architect** — LLM system design; prompt engineering, context management, RAG patterns
- **machine-learning-engineer** — ML systems; training infrastructure, model serving, MLflow
- **ml-engineer** — Applied ML; scikit-learn, PyTorch, experiment tracking, deployment
- **mlops-engineer** — MLOps; model registry, drift detection, automated retraining, monitoring
- **nlp-engineer** — NLP; transformers, tokenization, text classification, entity extraction
- **postgres-pro** — PostgreSQL expert; partitioning, JSONB, pg_stat, vacuum, replication
- **prompt-engineer** — Prompt optimization; chain-of-thought, few-shot, structured outputs
- **reinforcement-learning-engineer** — RL; reward shaping, policy gradients, DQN, multi-agent RL

#### Category 06 — Developer Experience
- **build-engineer** — Build systems; Webpack, Vite, Bazel, Gradle, caching, parallelism
- **cli-developer** — CLI tools; argument parsing, UX, testing, distribution
- **dependency-manager** — Package management; auditing, update strategies, vulnerability scanning
- **documentation-engineer** — Technical docs; API docs, tutorials, doctest, readability
- **dx-optimizer** — Developer experience; onboarding, tooling, feedback loops, ergonomics
- **git-workflow-manager** — Git workflows; branching strategies, hooks, rebasing, CI
- **legacy-modernizer** — Legacy modernization; strangler fig, incremental migration, risk mitigation
- **mcp-developer** — Model Context Protocol server development; tool definitions, resource schemas
- **powershell-ui-architect** — WinForms, WPF, Metro, TUI for PowerShell
- **powershell-module-architect** — PowerShell module structure; publishing, pester testing
- **refactoring-specialist** — Code refactoring; extract method, design patterns, SOLID
- **slack-expert** — Slack platform; bolt SDK, workflows, Block Kit, event API
- **tooling-engineer** — Developer tooling; linters, formatters, code generators, templates

#### Category 07 — Specialized Domains
- **api-documenter** — API documentation; OpenAPI, Swagger, Postman, documentation sites
- **blockchain-developer** — Web3; smart contracts, DeFi, NFTs, wallet integration, auditing
- **embedded-systems** — Embedded/RTOS; C, C++, bare metal, HAL, MISRA, firmware
- **fintech-engineer** — Financial systems; regulatory compliance, payment processing, risk models
- **game-developer** — Game development; Unity, Unreal, game loops, physics, multiplayer
- **iot-engineer** — IoT systems; MQTT, edge computing, firmware OTA, protocols
- **m365-admin** — Microsoft 365 administration; Exchange, Teams, SharePoint, Power Platform
- **mobile-app-developer** — Mobile apps; native and cross-platform, app store optimization
- **payment-integration** — Payment systems; Stripe, PayPal, PCI compliance, fraud detection
- **quant-analyst** — Quantitative finance; pricing models, risk metrics, backtesting, VaR
- **risk-manager** — Risk assessment; ERM frameworks, risk matrices, control evaluation
- **seo-specialist** — SEO; Core Web Vitals, schema markup, crawlability, content strategy

#### Category 08 — Business and Product
- **business-analyst** — Requirements; user stories, process mapping, gap analysis
- **content-marketer** — Content strategy; SEO content, brand voice, editorial calendar
- **customer-success-manager** — Customer success; onboarding, health scoring, churn prevention
- **legal-advisor** — Legal/compliance; contracts, IP, privacy law, regulatory guidance
- **product-manager** — Product strategy; roadmapping, prioritization, PRDs, OKRs
- **project-manager** — Project management; Gantt, risk tracking, stakeholder communication
- **sales-engineer** — Technical sales; demos, POCs, RFP responses, objection handling
- **scrum-master** — Agile; sprint planning, retrospectives, impediment removal, velocity
- **technical-writer** — Technical documentation; style guides, API references, tutorials
- **ux-researcher** — User research; usability studies, interviews, persona development
- **wordpress-master** — WordPress; custom themes, plugins, WooCommerce, performance

#### Category 09 — Meta and Orchestration
- **agent-installer** — Self-service agent discovery and installation from this GitHub catalogue
- **agent-organizer** — Multi-agent workflow coordinator; task decomposition, result aggregation
- **context-manager** — Shared state hub for multi-agent systems; hierarchical context storage
- **error-coordinator** — Centralized error handling; error aggregation, recovery coordination
- **it-ops-orchestrator** — IT operations workflows; provisioning, patching, compliance automation
- **knowledge-synthesizer** — Cross-agent knowledge aggregation; synthesis, deduplication
- **multi-agent-coordinator** — Advanced multi-agent orchestration; dependency DAGs, parallel dispatch
- **performance-monitor** — Agent performance tracking; latency, throughput, cost optimization
- **task-distributor** — Task allocation and load balancing across agents
- **workflow-orchestrator** — Complex workflow automation; state machines, conditional branching

#### Category 10 — Research and Analysis
- **research-analyst** — Comprehensive research; source evaluation, synthesis, evidence grading
- **search-specialist** — Advanced information retrieval; multi-source search, result ranking
- **trend-analyst** — Emerging trends; signal detection, forecasting, tech radar
- **competitive-analyst** — Competitive intelligence; market positioning, feature comparison
- **market-researcher** — Market analysis; TAM/SAM/SOM, consumer insights, surveys
- **data-researcher** — Data discovery; dataset curation, quality assessment, provenance
- **scientific-literature-researcher** — PubMed/arXiv search via BGPT MCP; evidence synthesis, PICO framework

---

## Gap Analysis — VoltAgent Agents NOT in BrickLayer

Agents excluded: all that map to existing BrickLayer agents (developer, code-reviewer, security, devops, architect, research-analyst, competitive-analyst, synthesizer, etc.)

### Confirmed Gaps

| Agent | Gap Level | Reason |
|-------|-----------|--------|
| chaos-engineer | HIGH | BrickLayer has no controlled failure injection, GameDay planning, or resilience testing capability |
| penetration-tester | HIGH | BrickLayer's security agent is OWASP-focused code review; pen-tester does active exploitation, network testing, social engineering |
| performance-engineer | HIGH | No dedicated profiling, benchmarking, load testing, or perf regression detection agent in BrickLayer |
| mlops-engineer | HIGH | BrickLayer has ML research but no model registry, drift detection, or automated retraining agent |
| llm-architect | HIGH | No agent focused on RAG system design, context management patterns, LLM evaluation frameworks |
| reinforcement-learning-engineer | MEDIUM | RL is a distinct discipline from general ML; policy gradients, reward shaping, multi-agent RL |
| nlp-engineer | MEDIUM | Distinct from general data-scientist; NLP pipeline specifics (tokenization, NER, embeddings) |
| embedded-systems | MEDIUM | Tim has ESPHome/IoT work (Sadie satellite nodes); no firmware/RTOS specialist exists |
| iot-engineer | MEDIUM | MQTT, edge computing, firmware OTA; complements Tim's ESPHome work |
| chaos-engineer | HIGH | (see above) |
| fintech-engineer | MEDIUM | ADBP project (Solana discount credits) needs payment systems, regulatory, risk overlap |
| payment-integration | MEDIUM | Stripe/PayPal/PCI compliance; distinct from Solana/blockchain work |
| game-developer | LOW | No active game projects |
| accessibility-tester | MEDIUM | BrickLayer builds UIs (Kiln, dashboards) with no a11y validation agent |
| incident-responder | MEDIUM | Distinct from devops; post-incident runbooks, RCA, escalation playbooks |
| sre-engineer | MEDIUM | SLOs, error budgets, toil reduction — no dedicated SRE agent in BrickLayer |
| legacy-modernizer | MEDIUM | Strangler fig patterns, incremental migration strategies |
| mcp-developer | HIGH | BrickLayer builds and uses MCP servers heavily; no dedicated MCP server development agent |
| dx-optimizer | LOW | Developer experience tooling improvements |
| knowledge-synthesizer | MEDIUM | Cross-agent synthesis distinct from BrickLayer's synthesizer (campaign-specific) |
| context-manager | LOW | BrickLayer uses Recall (Qdrant+Neo4j) for this; context-manager is file-based shared state |
| scientific-literature-researcher | HIGH | PubMed/arXiv BGPT MCP integration for evidence-based research; BrickLayer has no academic literature search capability |
| trend-analyst | MEDIUM | Forward-looking signal detection and tech forecasting; frontier-analyst is tangential |
| market-researcher | LOW | BrickLayer's competitive-analyst partially covers this |
| risk-manager | MEDIUM | Enterprise risk frameworks (ERM, risk matrices); distinct from BrickLayer's simulation/stress-testing |
| legal-advisor | MEDIUM | Contract review, IP, privacy law; relevant to ADBP/Relay projects |
| scrum-master | LOW | Agile ceremony facilitation |
| product-manager | LOW | PRDs, roadmapping; partially covered by spec-writer + karen |
| data-engineer | MEDIUM | Pipeline architecture (Spark, Airflow, dbt, Kafka); BrickLayer has quantitative-analyst but not ETL/pipeline specialist |
| database-optimizer | MEDIUM | EXPLAIN plans, vacuum, partitioning; BrickLayer's database-specialist is broad |
| elixir-expert | LOW | No active Elixir projects |
| golang-pro | LOW | Occasional Go use but not primary |
| websocket-engineer | LOW | Real-time comms; covered partially by backend-developer |
| microservices-architect | LOW | Partially covered by architect |

### Top 10 to Harvest

**1. mcp-developer [HIGH, immediate need]**
BrickLayer builds its own MCP server (Masonry), extends it regularly, and Tim's workflow is deeply MCP-native. A dedicated agent that knows MCP tool definitions, resource schemas, transport layers, and testing patterns would directly accelerate Masonry development. BrickLayer currently has no agent for this. The VoltAgent mcp-developer focuses on server development, schema design, and tool implementation — exactly what Masonry engineering needs.

**2. chaos-engineer [HIGH, test coverage gap]**
BrickLayer can build systems but has no agent for resilience testing. Chaos engineering is distinct from security auditing — it's about failure injection, blast radius control, GameDay exercises, and MTTR improvement. BrickLayer campaigns stress-test business models mathematically; this agent stress-tests deployed systems physically. Given Tim runs a homelab with multiple services (Recall, Sadie, JellyStream), a chaos agent would immediately useful.

**3. penetration-tester [HIGH, security depth]**
BrickLayer's security agent does static OWASP code review. The penetration-tester does active exploitation: reconnaissance, network scanning, privilege escalation, lateral movement, API fuzzing, and social engineering scenario planning. These are categorically different. For ADBP (Solana platform handling money), active pen testing is needed alongside code review.

**4. performance-engineer [HIGH, missing discipline]**
No BrickLayer agent focuses on profiling, load testing, benchmark regression detection, or perf optimization. This matters for the Kiln Electron app, Masonry MCP server response times, and Recall query latency. The VoltAgent performance-engineer covers CPU/memory profiling, query tuning, caching strategies, and benchmark interpretation.

**5. llm-architect [HIGH, meta relevance]**
BrickLayer is itself an LLM system. An llm-architect agent that understands RAG design patterns, context window management, embedding strategies, evaluation frameworks, and LLM-specific failure modes would help design better campaigns, better recall integration, and better agent fleet architecture. This is a meta-improvement agent.

**6. scientific-literature-researcher [HIGH, research quality]**
BrickLayer's research loop uses web search and competitive analysis but has no academic literature integration. The scientific-literature-researcher uses the BGPT MCP to query PubMed and arXiv, applies PICO evidence frameworks, and synthesizes peer-reviewed findings. For regulatory-researcher questions and quantitative-analyst work that benefits from academic backing, this fills a genuine gap.

**7. mlops-engineer [HIGH, EMA training pipeline]**
BrickLayer already has an EMA training pipeline (telemetry.jsonl, collector.py, ema_history.json). An mlops-engineer agent would own this: model registry, drift detection, automated retraining triggers, training data quality monitoring. Currently this pipeline runs without dedicated oversight; the agent would close that gap.

**8. accessibility-tester [MEDIUM, UI work]**
BrickLayer builds UIs — Kiln desktop app, future dashboards. No accessibility testing exists. The VoltAgent accessibility-tester does WCAG 2.1 compliance checks, screen reader testing, keyboard navigation, ARIA attribute validation, and color contrast analysis. Every UI BrickLayer ships should have a11y review.

**9. embedded-systems / iot-engineer [MEDIUM, Sadie project]**
Tim's Sadie project uses ESPHome satellite nodes — firmware engineering. BrickLayer has no embedded/firmware specialist. These two agents cover complementary concerns: embedded-systems handles RTOS, HAL, bare metal, MISRA; iot-engineer handles MQTT, firmware OTA, edge compute. Together they'd cover the full Sadie stack.

**10. data-engineer [MEDIUM, pipeline work]**
BrickLayer's quantitative-analyst handles simulation math. Data-engineer handles the plumbing: ETL pipelines, Kafka consumers, dbt models, Airflow DAGs, data quality checks. Given Recall (Qdrant + Neo4j) is a core BrickLayer dependency with its own data ingestion pipeline, a data-engineer agent would improve that infrastructure.

---

## uditgoenka/autoresearch

### Loop Implementation Details

The SKILL.md implements 9 commands that all share the same core loop but with different objectives:

**Core loop (all commands):**
1. Read current state + git log + results TSV
2. Pick ONE change based on goal + history of what worked/failed
3. Make the change
4. `git commit` BEFORE verification (so the state is always committed)
5. Run verify command (mechanical metric only — no subjective assessment)
6. If Guard is set, run guard command (regression prevention)
7. Decision matrix:
   - IMPROVED + guard passes → Keep, log "keep"
   - IMPROVED + guard fails → Revert, rework optimization (max 2 attempts), then log "discard (guard failed)"
   - SAME/WORSE → `git revert`, log "discard"
   - CRASHED → Fix inline (max 3 tries), else log "crash" and advance
8. Log result to TSV with: iteration, commit hash, metric value, delta, status, description
9. Repeat. Unbounded: never stop. Bounded: stop at N and print summary.

**Critical differentiators from a naive loop:**
- `git revert` (not `git reset --hard`) — failed experiments REMAIN in git history for pattern learning
- Agent MUST read `git log --oneline -20` and `git diff HEAD~1` at the start of each iteration — history is memory
- Guard is separate from verify — metric improvement + regression prevention are distinct checks
- Commit BEFORE verify — the state is always atomic and recoverable
- "Simplicity wins" rule — equal metric + less code = KEEP over equal metric + more code

**The 9 subcommands and their distinguishing loop objectives:**

| Command | Loop Objective | Metric | Stops When |
|---------|---------------|--------|------------|
| `/autoresearch` | Improve any user-defined metric | User-specified shell command output | User interrupts or N iterations |
| `/autoresearch:plan` | No loop — wizard only | N/A | Config validated and confirmed |
| `/autoresearch:debug` | Find all bugs via scientific method | Bugs found + hypothesis confirmed | All reachable bugs documented |
| `/autoresearch:fix` | Drive error count to zero | Error count (lower is better) | Error count = 0 |
| `/autoresearch:security` | STRIDE+OWASP coverage | `(owasp_tested/10)*50 + (stride_tested/6)*30 + min(findings,20)` | User interrupts or N iterations |
| `/autoresearch:ship` | Drive checklist pass rate to 100% | `(checklist_passing/total)*80 + dry_run*15 + no_blockers*5` | Score = 100 or user decides |
| `/autoresearch:scenario` | Cover all 12 dimensions of a scenario | `scenarios*10 + edge_cases*15 + (dimensions/12)*30 + actors*5` | All dimensions explored |
| `/autoresearch:predict` | Confirm/deny hypotheses across personas | `findings_confirmed*15 + probable*8 + minority*3 + ...` | All personas complete |
| `/autoresearch:learn` | Documentation health score | `validation%*0.5 + coverage%*0.3 + size_compliance%*0.2` | Validation passes or 3 retries |

**Interactive setup gate — a notable prompt engineering pattern:**
Every command begins with a BLOCKING `AskUserQuestion` check. If ANY required config is missing, the agent MUST collect it in batched calls (max 4 questions per call) before executing. This is enforced in the SKILL.md with explicit "YOU MUST NOT start any loop without completing interactive setup" language. Context is scanned first to provide smart defaults.

**Results tracking format (TSV):**
```
iteration  commit   metric  delta   status    description
0          a1b2c3d  85.2    0.0     baseline  initial state
1          b2c3d4e  87.1    +1.9    keep      add tests for auth edge cases
2          -        86.5    -0.6    discard   refactor test helpers (broke 2 tests)
```
Every 10 iterations, Claude prints a progress summary. Bounded loops print baseline → current best at end.

### What's Different from BrickLayer's Research Loop

BrickLayer's campaign loop is a different shape entirely. This table maps the key differences:

| Dimension | BrickLayer Research Loop | Autoresearch Loop |
|-----------|--------------------------|-------------------|
| **Objective** | Discover failure boundaries in a simulation | Improve a measurable metric in any artifact |
| **Unit of work** | Question (answered once per wave) | Iteration (one atomic change, keep or discard) |
| **State format** | questions.md (PENDING/ANSWERED), findings/*.md | results.tsv (iteration log), git history |
| **Memory** | Qdrant + Neo4j (Recall), HNSW reasoning bank | Git log (same session, no external deps) |
| **Scoring** | EMA (α=0.3), PageRank confidence, consensus vote | Mechanical metric delta (binary: better or worse) |
| **Rollback** | N/A (findings are read-only conclusions) | Automatic: `git revert` on every failure |
| **Stopping** | Question bank exhausted + hypothesis-generator | User interrupts OR N iterations OR goal achieved |
| **Verification** | Simulation run (simulate.py verdict) | Any shell command that outputs a number |
| **Scope** | Research/business model stress-testing | Code, content, ML models, docs, security — anything |
| **Human escalation** | claims.json (async) | AskUserQuestion at setup; Guard failures |
| **Multi-agent** | Fleet dispatched per question | Single agent loop (predict subcommand does multi-persona) |

**Key things autoresearch does that BrickLayer does NOT:**

1. **Automatic rollback on failure.** BrickLayer findings are write-once conclusions; there is no concept of "this iteration made things worse, revert it." Autoresearch uses git revert as a first-class mechanism.

2. **Guard/Verify separation.** BrickLayer has a single verification path (simulate.py verdict). Autoresearch separates "did the metric improve" (verify) from "did I break anything else" (guard). This prevents metric-chasing that regresses other quality dimensions.

3. **Commit-before-verify discipline.** BrickLayer doesn't enforce this. Autoresearch commits every experiment before running verification — ensures every state is recoverable regardless of what verification does.

4. **Git-as-memory protocol.** Autoresearch explicitly requires reading `git log --oneline -20` and `git diff HEAD~1` at the start of each iteration. BrickLayer doesn't have this — agents don't systematically use git history as a learning signal within a session.

5. **Domain-agnostic metric.** BrickLayer's "metric" is always a simulation verdict (HEALTHY/CRITICAL/FAILING). Autoresearch accepts ANY shell command that outputs a number — test coverage %, bundle size, benchmark ms, OWASP coverage score. This is far more flexible.

6. **`:debug` scientific method loop.** BrickLayer's research loop generates hypotheses about business model failures. Autoresearch's debug loop applies the scientific method to bugs: symptom → recon → hypothesis → test → classify (confirmed/disproven/inconclusive) → log → repeat. The 7 investigation techniques (binary search, differential debugging, minimal reproduction, trace execution, pattern search, working backwards, rubber duck) are codified in the debug-workflow.md.

7. **`:predict` multi-persona swarm.** BrickLayer has consensus-builder (weighted majority vote across agents on a question). Autoresearch's predict does something different: simulate N expert personas (Architect, Security Analyst, Performance Engineer, Reliability Engineer, Devil's Advocate) who independently analyze code, cross-examine each other's findings, and reach consensus — all within one Claude context, no external dependencies. Anti-herd mechanism: Devil's Advocate is mandatory, groupthink detected via flip rate and entropy.

8. **`:ship` as a workflow.** BrickLayer has git-nerd for commits and karen for organization but no concept of a "shipping workflow" — 8 phases (Identify, Inventory, Checklist, Prepare, Dry-run, Ship, Verify, Log) applied to code PRs, deployments, content, marketing emails, research papers. This is a distinct product artifact lifecycle.

9. **`:learn` documentation engine.** BrickLayer has karen for docs organization but no agent that scouts a codebase, generates initial documentation, validates it against the actual code, and iteratively fixes validation failures. The learn-workflow does this with a validation-fix loop capped at 3 retries before escalating.

10. **`:scenario` as 12-dimension exploration.** BrickLayer's hypothesis-generator creates new research questions based on prior findings. Autoresearch's scenario command systematically explores a single scenario across 12 dimensions: happy path, errors, edge cases, abuse, scale, concurrency, temporal, data variation, permissions, integrations, recovery, state transitions. This exhausts the scenario space rather than the question space.

### Novel Patterns to Adopt

**1. Guard/Verify separation** — BrickLayer's `/build` should distinguish between "did the task metric improve" and "did existing tests still pass." Currently both are bundled. Separating them prevents the fix-implementer from improving a metric by breaking adjacent behavior.

**2. Commit-before-verify discipline** — Add to the `/build` worker agent protocol: always commit work before running the test suite. This ensures every state is recoverable and the git log reflects the actual experiment sequence.

**3. Git-as-memory for agent iterations** — In any multi-iteration agent loop (hypothesis-generator, fix-implementer), require the agent to read `git log --oneline -20` before picking the next action. This uses the actual experiment history as a learning signal rather than relying on context window alone.

**4. Mandatory Devil's Advocate in consensus** — BrickLayer's consensus-builder uses weighted majority vote. Adding a mandatory Devil's Advocate role (always argues the opposite of the emerging consensus) would reduce false confidence on ambiguous findings. The anti-herd mechanism (detect groupthink via flip rate) is worth implementing in the consensus protocol.

**5. TSV results tracking** — BrickLayer uses findings/*.md for question results. For iterative optimization campaigns (EMA training, agent improvement loops), a TSV log with: iteration, metric, delta, status, description would make the optimization trajectory inspectable without reading individual finding files.

**6. Interactive setup gate** — The `AskUserQuestion` batching pattern (collect all required config in 2 batched calls with smart defaults from codebase scan) is cleaner than BrickLayer's current approach of letting agents infer configuration from CLAUDE.md. Worth adopting for `/plan`, `/masonry-init`, and any campaign setup wizard.

**7. Bounded iteration mode** — BrickLayer's research loop is unbounded by design. Adding `Iterations: N` support to Trowel would let Tim run campaigns with explicit stopping criteria without needing to manually interrupt — useful for scheduled overnight runs with a defined budget.

### Priority: HIGH

Autoresearch is a mature implementation of principles BrickLayer already follows (autonomous iteration, git discipline, mechanical verification) but applied to a wider set of domains with better-specified sub-workflows. The `:debug`, `:fix`, and `:predict` patterns directly address Tim's top priority (dev execution), and the `:ship` and `:learn` patterns fill gaps in BrickLayer's build → release lifecycle. This is not a conceptual extension but a practical pattern library to harvest.

---

## Feature Gap Analysis

| Feature | In Repos | In BrickLayer 2.0 | Gap Level | Notes |
|---------|---------|-------------------|-----------|-------|
| Automatic git rollback on iteration failure | autoresearch | No (findings are write-once) | HIGH | Critical for dev iteration loops |
| Guard/Verify separation | autoresearch | No (single verify path) | HIGH | Prevents metric-chasing regressions |
| Commit-before-verify protocol | autoresearch | No | HIGH | Ensures atomic recoverable states |
| Git-as-memory (read git log each iteration) | autoresearch | No | HIGH | Uses experiment history as learning signal |
| `/autoresearch:debug` — scientific bug hunt | autoresearch | Partial (diagnose-analyst does one pass) | HIGH | 7 investigation techniques, iterative loop |
| `/autoresearch:fix` — error-count-to-zero loop | autoresearch | Partial (fix-implementer does one cycle) | HIGH | Stops only when error count = 0 |
| `/autoresearch:predict` — multi-persona swarm | autoresearch | Partial (consensus-builder, multi-agent) | HIGH | Personas debate each other; anti-herd mechanism |
| Mandatory Devil's Advocate in consensus | autoresearch | No | HIGH | Prevents groupthink in majority vote |
| `/autoresearch:ship` — 8-phase shipping workflow | autoresearch | Partial (git-nerd + karen) | MEDIUM | End-to-end artifact lifecycle not formalized |
| `/autoresearch:learn` — codebase doc engine | autoresearch | Partial (karen docs org) | MEDIUM | Validation-fix loop for docs not implemented |
| `/autoresearch:scenario` — 12-dimension exploration | autoresearch | No | MEDIUM | Different from hypothesis-generator |
| TSV iteration log | autoresearch | No (findings/*.md) | MEDIUM | Machine-readable optimization trajectory |
| Bounded iteration mode (Iterations: N) | autoresearch | No | MEDIUM | Explicit stopping criteria for loops |
| Batched interactive setup (AskUserQuestion) | autoresearch | No | MEDIUM | Smart config collection before loop start |
| Domain-agnostic mechanical metric | autoresearch | No (always simulate.py) | MEDIUM | Any shell command → metric number |
| chaos-engineer agent | VoltAgent | No | HIGH | Controlled failure injection, GameDay, MTTR |
| penetration-tester agent | VoltAgent | No (code review only) | HIGH | Active exploitation, network, social engineering |
| performance-engineer agent | VoltAgent | No | HIGH | Profiling, load testing, benchmark regression |
| mcp-developer agent | VoltAgent | No | HIGH | Masonry development needs this |
| llm-architect agent | VoltAgent | No | HIGH | RAG design, context patterns, eval frameworks |
| scientific-literature-researcher | VoltAgent | No | HIGH | PubMed/arXiv via BGPT MCP |
| mlops-engineer agent | VoltAgent | No | HIGH | Drift detection, retraining, model registry |
| embedded-systems / iot-engineer | VoltAgent | No | MEDIUM | ESPHome/Sadie project relevance |
| accessibility-tester agent | VoltAgent | No | MEDIUM | Kiln/dashboard UI coverage |
| sre-engineer agent | VoltAgent | No | MEDIUM | SLOs, error budgets, toil reduction |
| incident-responder agent | VoltAgent | No | MEDIUM | Postmortem, RCA, runbooks |
| data-engineer agent | VoltAgent | No | MEDIUM | ETL/pipeline for Recall infrastructure |
| reinforcement-learning-engineer | VoltAgent | No | MEDIUM | RL distinct from general ML |
| nlp-engineer agent | VoltAgent | No | MEDIUM | NLP pipeline specifics |
| risk-manager agent | VoltAgent | No | MEDIUM | ERM frameworks beyond simulation |
| fintech-engineer agent | VoltAgent | No | MEDIUM | ADBP project regulatory/payment context |
| legal-advisor agent | VoltAgent | No | MEDIUM | ADBP/Relay compliance needs |
| agent-installer (self-service catalogue) | VoltAgent | masonry-onboard.js | LOW | BrickLayer has auto-onboarding |
| context-manager agent | VoltAgent | Recall (Qdrant+Neo4j) | LOW | BrickLayer's Recall is stronger |
| trend-analyst agent | VoltAgent | frontier-analyst partial | MEDIUM | Forward-looking signal detection |

---

## Top 5 Recommendations

### 1. Add `/autoresearch:debug` + `/autoresearch:fix` Chain as Masonry Skills [16h, PRIORITY 1]

**What to build:** Two new Masonry skills: `/debug` and `/fix`, modeled directly on autoresearch's debug-workflow.md and fix-workflow.md. The debug skill uses scientific method — hypothesis → experiment → classify (confirmed/disproven/inconclusive) → log → repeat — across the 7 investigation techniques. The fix skill drives error count to zero one fix at a time, committing before verifying, reverting on regression. Chain them with `--from-debug` to hand off confirmed hypotheses.

**Why it matters:** Tim's top priority is Ruflo-level dev execution. BrickLayer's current diagnose-analyst + fix-implementer does one pass — investigate once, fix once. The autoresearch pattern does N passes until errors = 0, with rollback on each bad fix. This changes the agent from a one-shot tool to a loop that doesn't stop until the build is green. The TSV log gives Tim full visibility into what the agent tried overnight.

**Implementation sketch:**
- Add `masonry/skills/debug/` and `masonry/skills/fix/` directories following the autoresearch skill pattern
- Implement commit-before-verify discipline in both skills
- Add Guard parameter (always run existing tests as regression check)
- Write results to `debug/{timestamp}/debug-results.tsv` and `fix/{timestamp}/fix-results.tsv`
- Wire into Trowel as two new campaign modes, or expose as standalone Masonry commands

### 2. Add `mcp-developer` Agent to BrickLayer Fleet [8h, PRIORITY 2]

**What to build:** A specialist agent focused exclusively on MCP server development — tool definitions, resource schemas, transport implementation (stdio/SSE/HTTP), schema validation, and MCP testing patterns. Source the VoltAgent mcp-developer.md as a starting point, then add Masonry-specific context (Masonry's existing schema patterns in `masonry/src/schemas/`, the tool naming conventions, the health check patterns).

**Why it matters:** BrickLayer builds and maintains Masonry (its own MCP server) and uses MCP servers daily (recall, github, context7, figma, proxmox). Every Masonry feature addition is MCP work. Currently developer or devops handles this without MCP-native expertise baked in. A dedicated agent would produce better tool definitions, catch schema violations earlier, and generate proper MCP test harnesses.

**Implementation sketch:**
- Adapt VoltAgent's mcp-developer.md for BrickLayer's context
- Add Masonry-specific MCP patterns: QuestionPayload/FindingPayload schema conventions, tool naming (masonry_*), health check endpoints
- Register in agent_registry.yml with tier: "active", modes: ["mcp", "build"]
- Trigger from Mortar when request matches "MCP server", "tool definition", "masonry schema", "new MCP tool"

### 3. Implement Mandatory Devil's Advocate + Anti-Herd in Consensus Builder [6h, PRIORITY 3]

**What to build:** Extend the existing consensus-builder agent to always include a Devil's Advocate synthetic vote that argues the opposite of the emerging consensus. Add groupthink detection: if all N agents agree with >90% confidence, treat the consensus as suspect and require the Devil's Advocate to explicitly counter. Track a "flip rate" metric — if no agent ever dissents, escalate to human review.

**Why it matters:** BrickLayer's consensus uses weighted majority vote with conservative BLOCKED on ties. This is good for tie-breaking but doesn't protect against correlated failures (all agents trained similarly, all reach the same wrong conclusion confidently). The autoresearch predict workflow's anti-herd mechanism addresses this directly. False consensus on a campaign finding is worse than a tie — it surfaces as a confident wrong answer rather than an appropriate BLOCKED.

**Implementation sketch:**
- Add `devil_advocate_vote` computation in consensus-builder: flip the majority verdict and generate a 1-3 sentence counter-argument
- Add `groupthink_score = 1 - entropy(vote_distribution)` — log when > 0.85
- If groupthink_score > 0.85 AND all verdicts agree, set consensus confidence -= 0.2 and add `[ANTI-HERD WARNING]` to output
- Add to claims.json escalation triggers: `"consensus_groupthink"` type

### 4. Add `chaos-engineer` and `penetration-tester` Agents [12h, PRIORITY 4]

**What to build:** Two new agents sourced and adapted from VoltAgent. The chaos-engineer adds controlled failure injection capability — Steady state definition, blast radius scoping, GameDay scenario planning, and MTTR tracking. The penetration-tester extends BrickLayer's existing security agent with active exploitation: network scanning, privilege escalation paths, API fuzzing, and vulnerability exploitation (read-only, never actually attacking production systems — generating attack scenarios and code evidence).

**Why it matters:** BrickLayer's security agent is a static code reviewer (OWASP Top 10). Two security disciplines are missing: (1) infrastructure resilience testing — verifying that BrickLayer's own services (Masonry, Kiln, Recall) degrade gracefully under failure; (2) active security testing that goes beyond code to network and infrastructure surfaces. ADBP handles real money and needs pen-test-grade security review, not just code review.

**Implementation sketch:**
- Adapt VoltAgent's chaos-engineer.md with BrickLayer project awareness (Masonry MCP server, Kiln Electron, Recall API)
- chaos-engineer trigger: "resilience test", "GameDay", "failure injection", "MTTR", "blast radius"
- Adapt VoltAgent's penetration-tester.md with explicit read-only mode (produces attack scenarios and evidence, never executes exploits)
- penetration-tester trigger: "pen test", "active security", "exploit", "privilege escalation", "attack surface"
- Both agents write structured reports to `security/{date}/` following autoresearch's output pattern

### 5. Add `scientific-literature-researcher` + `mlops-engineer` Agents [10h, PRIORITY 5]

**What to build:** Two agents that close the academic research and ML operations gaps. The scientific-literature-researcher uses the BGPT MCP server (if available) or falls back to Exa/web search to query PubMed and arXiv, applies PICO evidence grading, and integrates literature findings into campaign research. The mlops-engineer owns BrickLayer's EMA training pipeline — telemetry collection, model drift detection, retraining triggers, and quality monitoring of the agent optimization loop.

**Why it matters:** BrickLayer's quantitative-analyst and regulatory-researcher currently cite no peer-reviewed sources. Academic literature backing would elevate research quality and is often decisive for regulatory questions (FDA, SEC, healthcare). Separately, the EMA pipeline runs without dedicated oversight — an mlops-engineer agent would detect when agent performance has drifted (e.g., after a model update) and trigger targeted retraining rather than waiting for Tim to notice degraded campaign quality.

**Implementation sketch:**
- scientific-literature-researcher: check for BGPT MCP in settings.json; if absent, use Exa with scholarly domain filters; output in PICO format (Population, Intervention, Comparison, Outcome); trigger from regulatory-researcher and quantitative-analyst when evidence quality < threshold
- mlops-engineer: reads telemetry.jsonl and ema_history.json; computes drift score against baseline; if drift > 15% triggers `masonry/scripts/improve_agent.py` for drifted agents; writes `masonry/mlops/health-report.md` on each run; trigger: "model drift", "agent quality", "EMA pipeline", "retrain"

---

## Novel Patterns to Incorporate (Future)

**Composite scoring metrics.** Autoresearch uses composite scores for complex objectives (e.g., security audit score = OWASP coverage * 50 + STRIDE coverage * 30 + findings * capped at 20). BrickLayer uses binary verdicts (HEALTHY/CRITICAL) and EMA confidence scores separately. A composite campaign score that combines multiple signal types would give Mortar richer routing data.

**Output directory convention.** Autoresearch creates dated output dirs (`security/YYMMDD-HHMM-slug/`, `ship/YYMMDD-HHMM-slug/`) for each run. BrickLayer's findings go into flat `findings/` directories. Adopting timestamped output dirs per campaign wave would enable better tracing and parallel campaign runs without collision.

**`:ship` 8-phase pattern as release workflow.** The Identify → Inventory → Checklist → Prepare → Dry-run → Ship → Verify → Log sequence is a clean generalization of any release artifact lifecycle. BrickLayer's `/build` ends at "tests pass, committed." Extending it to include dry-run → deploy → post-deploy health check would close the loop that currently requires Tim to manually verify deployments.

**Agent self-star pattern.** Autoresearch asks users to star the repo after first completion via `gh api -X PUT /user/starred/...`. Tongue-in-cheek, but the underlying pattern (agent tracks whether a post-completion action has been done via a marker file) is useful for BrickLayer's changelog and synthesis flows — track whether synthesis.md has been generated this session without re-reading the full campaign state.

**Scale-aware scouting.** The `:learn` workflow adjusts parallelism for codebases with 5K+ files. BrickLayer's campaign initialization doesn't do this — large projects with many docs files overwhelm the question-designer's context. Adding a file-count check at campaign init that adjusts chunk sizes would prevent context overflow on large codebases.

**BGPT MCP for academic literature.** The scientific-literature-researcher uses a third-party MCP (github.com/connerlambden/bgpt-mcp) for structured PubMed/arXiv queries. This is worth evaluating for BrickLayer's research campaigns — especially regulatory research where peer-reviewed citations carry weight that web search results don't.
