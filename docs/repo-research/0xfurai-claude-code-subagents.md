# Repo Research: 0xfurai/claude-code-subagents
**Repo**: https://github.com/0xfurai/claude-code-subagents
**Researched**: 2026-03-28
**Stars**: 797 | **Forks**: 143 | **Contributors**: 3

---

## Verdict Summary

This repo is a flat collection of 138 single-purpose "expert" agent `.md` files covering almost every major programming language, framework, database, DevOps tool, and service in the modern stack. The value is breadth not depth: it's a ready-to-clone library of language/framework specialists that auto-invoke inside Claude Code based on context. BrickLayer beats it in every dimension that matters — orchestration, research loops, hooks, routing, multi-agent coordination, TDD enforcement, optimization pipelines — but this repo fills a genuine gap: BrickLayer has zero language-specific expert agents (python-expert, go-expert, rust-expert, etc.) that can be proactively auto-invoked when working in a specific language. The most actionable harvest is directly importing or adapting the ~15 agents relevant to Tim's stack (Python, Go, Rust, Kotlin, TypeScript/React, Bash, Kafka, Postgres, Redis, Neo4j, Docker, Kubernetes, Terraform, GitHub Actions, OpenTelemetry) and using the `bash-expert` as a template for the highest-quality agent format in the collection.

---

## File Inventory

| File | Description |
|------|-------------|
| `README.md` | Overview, full agent catalog by category, installation instructions, contributing guide |
| `LICENSE` | MIT License |
| `agents/actix-expert.md` | Actix-web (Rust async web framework) specialist |
| `agents/android-expert.md` | Android/Kotlin/Jetpack Compose specialist |
| `agents/angular-expert.md` | Angular/TypeScript/RxJS specialist |
| `agents/angularjs-expert.md` | Legacy AngularJS migration specialist |
| `agents/ansible-expert.md` | Ansible configuration management specialist |
| `agents/aspnet-core-expert.md` | ASP.NET Core / C# web API specialist |
| `agents/astro-expert.md` | Astro static site generation specialist |
| `agents/auth0-expert.md` | Auth0 identity/authentication specialist |
| `agents/ava-expert.md` | AVA concurrent testing specialist |
| `agents/bash-expert.md` | **Standout** — defensive Bash scripting with ShellCheck, shfmt, Bats; most detailed agent in repo |
| `agents/braintree-expert.md` | Braintree/PayPal payment processing specialist |
| `agents/bullmq-expert.md` | BullMQ Redis-based job queue specialist |
| `agents/bun-expert.md` | Bun JavaScript runtime/package manager specialist |
| `agents/c-expert.md` | C systems programming specialist |
| `agents/cassandra-expert.md` | Apache Cassandra distributed DB specialist |
| `agents/celery-expert.md` | Celery distributed task queue (Python) specialist |
| `agents/circleci-expert.md` | CircleCI CI/CD specialist |
| `agents/clojure-expert.md` | Clojure functional programming specialist |
| `agents/cockroachdb-expert.md` | CockroachDB distributed SQL specialist |
| `agents/cpp-expert.md` | Modern C++ STL/templates/RAII specialist |
| `agents/csharp-expert.md` | C#/.NET/LINQ/enterprise patterns specialist |
| `agents/css-expert.md` | CSS layouts/animations/responsive design specialist |
| `agents/cypress-expert.md` | Cypress E2E testing specialist |
| `agents/dart-expert.md` | Dart/Flutter cross-platform specialist |
| `agents/deno-expert.md` | Deno secure JS runtime specialist |
| `agents/django-expert.md` | Django ORM/blueprints/admin specialist |
| `agents/docker-expert.md` | Docker containerization/images/orchestration specialist |
| `agents/dynamodb-expert.md` | AWS DynamoDB NoSQL specialist |
| `agents/elasticsearch-expert.md` | Elasticsearch search/analytics/ELK specialist |
| `agents/electron-expert.md` | Electron cross-platform desktop specialist |
| `agents/elixir-expert.md` | Elixir functional programming/OTP specialist |
| `agents/elk-expert.md` | ELK stack (Elasticsearch/Logstash/Kibana) specialist |
| `agents/erlang-expert.md` | Erlang concurrent/fault-tolerant systems specialist |
| `agents/expo-expert.md` | Expo/React Native managed workflow specialist |
| `agents/express-expert.md` | Express.js middleware/routing specialist |
| `agents/fastapi-expert.md` | FastAPI async/Pydantic/OpenAPI specialist |
| `agents/fastify-expert.md` | Fastify high-performance Node.js specialist |
| `agents/fiber-expert.md` | Fiber Go web framework specialist |
| `agents/flask-expert.md` | Flask blueprints/extensions specialist |
| `agents/flutter-expert.md` | Flutter/Dart cross-platform mobile specialist |
| `agents/flyway-expert.md` | Flyway DB migration/version control specialist |
| `agents/gin-expert.md` | Gin Go web API/middleware specialist |
| `agents/github-actions-expert.md` | GitHub Actions workflows/automation specialist |
| `agents/gitlab-ci-expert.md` | GitLab CI/CD pipelines specialist |
| `agents/go-expert.md` | Go concurrency/interfaces/performance specialist |
| `agents/grafana-expert.md` | Grafana visualization/dashboard specialist |
| `agents/graphql-expert.md` | GraphQL schemas/resolvers/federation specialist |
| `agents/grpc-expert.md` | gRPC high-performance RPC/protobuf specialist |
| `agents/haskell-expert.md` | Haskell functional/monads/type theory specialist |
| `agents/html-expert.md` | HTML semantic/accessibility/web standards specialist |
| `agents/ios-expert.md` | iOS/Swift/UIKit specialist |
| `agents/jasmine-expert.md` | Jasmine BDD testing specialist |
| `agents/java-expert.md` | Java/Spring Boot/JVM optimization specialist |
| `agents/javascript-expert.md` | Modern JavaScript ES6+/async/Node.js specialist |
| `agents/jenkins-expert.md` | Jenkins CI/CD pipelines specialist |
| `agents/jest-expert.md` | Jest JS testing/mocking specialist |
| `agents/jquery-expert.md` | jQuery DOM/legacy browser specialist |
| `agents/jwt-expert.md` | JWT token-based authentication specialist |
| `agents/kafka-expert.md` | **Useful** — Kafka streams/cluster/partitioning specialist with PROACTIVE trigger |
| `agents/keycloak-expert.md` | Keycloak identity/access management specialist |
| `agents/knex-expert.md` | Knex.js query builder/migrations specialist |
| `agents/kotlin-expert.md` | Kotlin/Android/coroutines specialist |
| `agents/kubernetes-expert.md` | Kubernetes container orchestration/scaling specialist |
| `agents/langchain-expert.md` | LangChain LLM pipelines/RAG specialist |
| `agents/laravel-expert.md` | Laravel/Eloquent/Blade specialist |
| `agents/liquibase-expert.md` | Liquibase DB change management specialist |
| `agents/loki-expert.md` | Loki log aggregation specialist |
| `agents/lua-expert.md` | Lua scripting/embedded systems specialist |
| `agents/mariadb-expert.md` | MariaDB specialist |
| `agents/mocha-expert.md` | Mocha JS testing specialist |
| `agents/mongodb-expert.md` | MongoDB NoSQL/aggregation/sharding specialist |
| `agents/mongoose-expert.md` | Mongoose MongoDB ODM specialist |
| `agents/mqtt-expert.md` | MQTT IoT messaging specialist |
| `agents/mssql-expert.md` | MSSQL/T-SQL enterprise specialist |
| `agents/mysql-expert.md` | MySQL/InnoDB/replication specialist |
| `agents/nats-expert.md` | NATS lightweight messaging/pub-sub specialist |
| `agents/neo4j-expert.md` | **Useful** — Neo4j graph DB/Cypher specialist |
| `agents/nestjs-expert.md` | NestJS decorators/modules/enterprise specialist |
| `agents/nextjs-expert.md` | Next.js SSR/SSG/React optimization specialist |
| `agents/nodejs-expert.md` | Node.js runtime/packages/ecosystem specialist |
| `agents/numpy-expert.md` | NumPy numerical computing specialist |
| `agents/oauth-oidc-expert.md` | OAuth 2.0/OpenID Connect specialist |
| `agents/ocaml-expert.md` | OCaml functional/systems programming specialist |
| `agents/openai-api-expert.md` | OpenAI API/GPT integration specialist |
| `agents/openapi-expert.md` | OpenAPI specification/documentation specialist |
| `agents/opensearch-expert.md` | OpenSearch search/analytics specialist |
| `agents/opentelemetry-expert.md` | **Useful** — OpenTelemetry observability/tracing specialist |
| `agents/owasp-top10-expert.md` | OWASP Top 10 web security specialist |
| `agents/pandas-expert.md` | Pandas data manipulation/analysis specialist |
| `agents/perl-expert.md` | Perl text processing/automation specialist |
| `agents/phoenix-expert.md` | Phoenix/Elixir real-time features specialist |
| `agents/php-expert.md` | PHP/Laravel/performance specialist |
| `agents/playwright-expert.md` | Playwright cross-browser testing/automation specialist |
| `agents/postgres-expert.md` | **Useful** — PostgreSQL advanced features/extensions/optimization specialist |
| `agents/prisma-expert.md` | Prisma type-safe DB access/migrations specialist |
| `agents/prometheus-expert.md` | Prometheus metrics/monitoring specialist |
| `agents/pulumi-expert.md` | Pulumi IaC/multi-language specialist |
| `agents/puppeteer-expert.md` | Puppeteer Chrome automation specialist |
| `agents/python-expert.md` | **Useful** — Python advanced features/async/testing specialist |
| `agents/pytorch-expert.md` | PyTorch deep learning specialist |
| `agents/rabbitmq-expert.md` | RabbitMQ AMQP messaging specialist |
| `agents/rails-expert.md` | Ruby on Rails/ActiveRecord/conventions specialist |
| `agents/react-expert.md` | React hooks/state/component architecture specialist |
| `agents/react-native-expert.md` | React Native cross-platform mobile specialist |
| `agents/redis-expert.md` | **Useful** — Redis caching/pub-sub/data structures specialist |
| `agents/remix-expert.md` | Remix routing/data loading/web standards specialist |
| `agents/rest-expert.md` | REST API/HTTP standards specialist |
| `agents/rollup-expert.md` | Rollup ES module bundling specialist |
| `agents/ruby-expert.md` | Ruby/Rails/metaprogramming specialist |
| `agents/rust-expert.md` | **Useful** — Rust ownership/concurrency/safety specialist with PROACTIVE trigger |
| `agents/scala-expert.md` | Scala/Akka/functional programming specialist |
| `agents/scikit-learn-expert.md` | Scikit-learn ML/data science specialist |
| `agents/selenium-expert.md` | Selenium web automation specialist |
| `agents/sequelize-expert.md` | Sequelize Node.js ORM specialist |
| `agents/sidekiq-expert.md` | Sidekiq background jobs/Ruby specialist |
| `agents/sns-expert.md` | AWS SNS messaging/notifications specialist |
| `agents/solidjs-expert.md` | SolidJS fine-grained reactivity specialist |
| `agents/spring-boot-expert.md` | Spring Boot Java microservices specialist |
| `agents/sql-expert.md` | SQL complex queries/optimization/schema design specialist |
| `agents/sqlite-expert.md` | SQLite embedded DB specialist |
| `agents/sqs-expert.md` | AWS SQS message queuing specialist |
| `agents/stripe-expert.md` | Stripe payment processing/webhooks specialist |
| `agents/svelte-expert.md` | Svelte reactive components specialist |
| `agents/swift-expert.md` | Swift iOS/macOS specialist |
| `agents/swiftui-expert.md` | SwiftUI declarative UI/modern iOS specialist |
| `agents/tailwind-expert.md` | Tailwind CSS utility-first specialist |
| `agents/tauri-expert.md` | Tauri Rust-backend/web-frontend desktop specialist |
| `agents/tensorflow-expert.md` | TensorFlow deep learning specialist |
| `agents/terraform-expert.md` | Terraform IaC/cloud provisioning specialist |
| `agents/testcafe-expert.md` | TestCafe E2E testing specialist |
| `agents/trpc-expert.md` | tRPC end-to-end type-safe TypeScript APIs specialist |
| `agents/typeorm-expert.md` | TypeORM TypeScript ORM specialist |
| `agents/typescript-expert.md` | TypeScript type safety/interfaces/advanced features specialist |
| `agents/vector-db-expert.md` | Vector DB indexing/similarity search/embeddings specialist |
| `agents/vitest-expert.md` | Vitest Vite-based testing specialist |
| `agents/vue-expert.md` | Vue.js composition API/state management specialist |
| `agents/webpack-expert.md` | Webpack module bundling/optimization specialist |
| `agents/websocket-expert.md` | WebSocket real-time communication specialist |

---

## Agent/Skill Catalog

All 138 agents follow an identical structure:

```yaml
---
name: {name}-expert
description: {one-line trigger description with optional PROACTIVE marker}
model: claude-sonnet-4-20250514
---

## Focus Areas    (10 bullet list)
## Approach       (10 bullet list)
## Quality Checklist (10 bullet list)
## Output         (10 bullet list)
```

### Structural Patterns Observed

**Uniform model assignment**: All agents use `claude-sonnet-4-20250514`. No haiku for simple tasks, no opus for deep analysis. One-size-fits-all.

**PROACTIVE trigger pattern**: A subset of agents include "Use PROACTIVELY for..." in their description, signaling to Claude Code that it should auto-invoke the agent without being asked. Examples:
- `rust-expert`: "Use PROACTIVELY for Rust optimization and code safety checks"
- `kafka-expert`: "Use PROACTIVELY for Kafka architecture design, troubleshooting, or improving Kafka performance"

**bash-expert is the standout**: Significantly longer (5384 bytes vs ~2000-2500 for others), includes an `## Essential Tools` section, `## Common Pitfalls to Avoid` section, `## Advanced Techniques` section, and `## References & Further Reading`. This is the gold standard format in this repo.

**No frontmatter beyond name/description/model**: No `tools`, `context`, `inputs`, `outputs`, `tier`, or `mode` fields. No typed schemas. No routing logic.

**No inter-agent coordination**: Agents are standalone. No concept of orchestration, delegation chains, or wave-based loops.

**No hooks**: Zero hook files in the repo.

**No MCP config**: Zero MCP server configuration.

**No workflow/pipeline files**: Zero DAG or pipeline definitions.

**No code files**: Pure `.md` agent definitions only.

---

## Feature Gap Analysis

| Feature | In this repo | In BrickLayer 2.0 | Gap Level | Notes |
|---------|-------------|-------------------|-----------|-------|
| Language-specific expert agents (Python, Go, Rust, etc.) | YES — 23 language experts | NO — BL has no dedicated language experts | HIGH | BL's `developer` agent is generic; no Rust/Go/Haskell/Kotlin specialists |
| Framework-specific experts (FastAPI, Next.js, Kafka, etc.) | YES — ~115 framework/service agents | NO — BL has FastAPI in Tim's stack but no specialist | HIGH | Same gap — stack-specific depth is missing |
| PROACTIVE auto-invocation via description trigger | YES — keyword-based in description field | PARTIAL — Mortar routing handles some of this | MED | BL routes via 4-layer routing; this repo uses simpler description matching |
| Dedicated bash/shell expert with ShellCheck+Bats+shfmt | YES — bash-expert.md (standout quality) | NO — git-nerd handles git, no bash-specific agent | MED | BL has no shell scripting specialist |
| Tauri specialist (Rust backend + web frontend) | YES | NO | MED | Relevant given Tim's Electron/Kiln work |
| OpenTelemetry observability specialist | YES | NO | MED | Useful for System-Recall and Sadie instrumentation |
| Agent format: Essential Tools section | YES (bash-expert) | PARTIAL — BL agents list tools in frontmatter | LOW | Format enhancement worth adopting |
| Agent format: Common Pitfalls section | YES (bash-expert) | NO | LOW | Prevents known anti-patterns |
| Agent format: References section | YES (bash-expert) | NO | LOW | Points to authoritative external docs |
| Multi-agent orchestration | NO | YES — Mortar, Trowel, 4-layer routing | N/A | BL is far ahead |
| Research loop / campaigns | NO | YES — BL's core function | N/A | Not in scope for this repo |
| Hooks (lint, TDD, secret scan, stop-guard) | NO | YES — 13 hooks | N/A | BL is far ahead |
| MCP server / typed schemas | NO | YES — Masonry MCP with 15+ tools | N/A | BL is far ahead |
| Agent optimization pipeline | NO | YES — DSPy/EMA improvement loop | N/A | BL is far ahead |
| Adaptive routing (deterministic/semantic/LLM/fallback) | NO | YES | N/A | BL is far ahead |
| Claims board / consensus / PageRank | NO | YES | N/A | BL is far ahead |
| Model selection per task complexity | NO — all sonnet | YES — haiku/sonnet/opus by task | LOW | BL is smarter about cost |
| Agent registry with tier/mode metadata | NO | YES — `masonry/agent_registry.yml` | N/A | BL is far ahead |
| TDD enforcement | NO | YES — masonry-tdd-enforcer hook | N/A | BL is far ahead |
| Kiln desktop monitoring | NO | YES | N/A | BL is far ahead |
| Typed payload contracts | NO | YES — Pydantic v2 schemas | N/A | BL is far ahead |
| Kotlin expert (for JellyStream Android) | YES | NO | MED | JellyStream is active Tim project |
| Vector DB expert (for System-Recall/Qdrant) | YES | NO | MED | System-Recall uses Qdrant |
| Neo4j expert (for System-Recall graph layer) | YES | NO | MED | System-Recall uses Neo4j |
| Redis expert | YES | NO | MED | Tim's stack default |
| Postgres expert | YES | NO | MED | Tim's stack default |
| GitHub Actions expert | YES | NO | LOW | CI/CD automation |
| Terraform expert | YES | NO | LOW | IaC for homelab |
| Docker expert | YES | NO | LOW | BL's devops agent covers some of this |
| LangChain expert | YES | NO | LOW | Less relevant — Tim uses custom agent framework |
| Grafana expert | YES | NO | LOW | Tim monitors with Grafana |
| Prometheus expert | YES | NO | LOW | Related to above |

---

## Top 5 Recommendations

### 1. Import Tim's Stack Experts Directly (Complexity: S)

**What**: Copy ~15 pre-built agents verbatim into `~/.claude/agents/` — the ones matching Tim's exact stack:
- `python-expert`, `typescript-expert`, `javascript-expert`
- `go-expert`, `rust-expert`, `kotlin-expert`
- `bash-expert` (highest priority — most polished)
- `postgres-expert`, `redis-expert`, `neo4j-expert`
- `kafka-expert`, `docker-expert`, `kubernetes-expert`
- `fastapi-expert`, `nextjs-expert`
- `opentelemetry-expert`, `github-actions-expert`

**Why**: Zero implementation cost. These agents auto-invoke when Claude Code detects the relevant language/framework context. The `PROACTIVE` trigger pattern (for rust-expert, kafka-expert) means the agent fires without being asked when it detects optimization opportunities. BL gains 15 experts for the price of a `cp` command.

**Implementation**: `cp agents/python-expert.md agents/rust-expert.md agents/bash-expert.md ... ~/.claude/agents/` then register in `masonry/agent_registry.yml` with `tier: "imported"`.

### 2. Adopt bash-expert Format as BL Agent Gold Standard (Complexity: S)

**What**: Use `bash-expert.md` as the template for all future BL agent definitions. It adds three sections beyond the basic four (Focus Areas / Approach / Quality Checklist / Output):
- `## Essential Tools` — specific tooling the agent relies on with config snippets
- `## Common Pitfalls to Avoid` — explicit anti-patterns with correct alternatives
- `## Advanced Techniques` — named patterns with code examples
- `## References & Further Reading` — authoritative external links

**Why**: Current BL agents are mostly 4-section (Focus/Approach/Quality/Output). The bash-expert 7-section format produces more grounded, less hallucination-prone responses by giving the agent concrete anchors (ShellCheck config flags, specific command patterns, external documentation links). This directly improves developer and test-writer quality.

**Implementation**: Update the `template/.claude/agents/` base template. Apply to developer, test-writer, diagnose-analyst during next optimize cycle.

### 3. Build a `tauri-expert` for Kiln (Complexity: S)

**What**: Create a BL-native `tauri-expert.md` with deeper Kiln/Electron awareness than the generic version in this repo. The generic tauri-expert covers cross-platform desktop basics; a BL version would know Kiln's architecture (Electron currently), BrickLayer IPC patterns, and Masonry daemon communication.

**Why**: Kiln is an active project. The `kiln-engineer` agent exists but is generic. A tauri-expert oriented toward the Kiln migration path (if Tim ever moves from Electron to Tauri for smaller bundle size) would be specifically useful.

**Implementation**: Adapt `tauri-expert.md` + add Kiln-specific context about BL IPC protocol, add to `masonry/agent_registry.yml`.

### 4. Add PROACTIVE Trigger Descriptions to High-Frequency BL Agents (Complexity: S)

**What**: The PROACTIVE pattern from this repo — including "Use PROACTIVELY for X" in the agent description — causes Claude Code to auto-invoke the agent without explicit instruction. Apply this to BL agents that should fire automatically:
- `security` agent: "Use PROACTIVELY when reviewing code with user input, auth flows, or external API calls"
- `refactorer`: "Use PROACTIVELY when a file exceeds 300 lines or has functions over 40 lines"
- `diagnose-analyst`: "Use PROACTIVELY when tests fail 3+ times with the same error"

**Why**: Currently BL agents require explicit routing through Mortar. The PROACTIVE pattern is a lightweight complement that catches cases before Mortar routing kicks in — a first-line auto-trigger that costs nothing to implement.

**Implementation**: Update description fields in `~/.claude/agents/*.md` for 5-8 key agents. One-line change per agent.

### 5. Create `qdrant-expert` and `esphome-expert` for Tim's Unique Stack (Complexity: M)

**What**: This repo covers 138 technologies but misses two critical to Tim's stack: Qdrant (vector DB powering System-Recall) and ESPHome (embedded firmware for Sadie satellite nodes). Model them on the bash-expert 7-section format:
- `qdrant-expert`: Focus on collection management, HNSW index tuning, payload filtering, sparse vector search, Qdrant REST/gRPC API, Docker deployment
- `esphome-expert`: YAML component configuration, custom components in C++, sensor calibration, OTA updates, Home Assistant integration, Sadie satellite node patterns

**Why**: System-Recall and Sadie are two of Tim's top active projects. Neither Qdrant nor ESPHome appears in this 138-agent collection. These would be genuinely novel additions not found anywhere else — built to Tim's specific stack, not generic.

**Implementation**: Write from scratch using bash-expert format. ~3-4 hours total for both. Register in Masonry registry with `tier: "custom"`.

---

## Harvestable Items

The following agents/patterns are worth directly incorporating into BrickLayer:

### Directly Copy (No Modification Needed)
These match Tim's active stack and can be dropped into `~/.claude/agents/` immediately:

| Agent | Why Harvest |
|-------|-------------|
| `bash-expert.md` | Highest quality in repo; ShellCheck/shfmt/Bats expertise; Tim uses Bash automation heavily |
| `python-expert.md` | Tim's primary language; FastAPI, data pipelines, agent frameworks |
| `rust-expert.md` | Tim uses Rust for systems work; PROACTIVE trigger is valuable |
| `go-expert.md` | Tim uses Go for performance-critical work |
| `kotlin-expert.md` | JellyStream Android client is active project |
| `typescript-expert.md` | BL frontend, Kiln, MCP servers all TypeScript |
| `fastapi-expert.md` | System-Recall, ADBP, and Relay all FastAPI |
| `postgres-expert.md` | Tim's stack default DB |
| `redis-expert.md` | Tim's stack (caching, queues) |
| `neo4j-expert.md` | System-Recall graph layer |
| `kafka-expert.md` | ADBP event streaming; PROACTIVE trigger useful |
| `docker-expert.md` | CasaOS homelab is all Docker Compose |
| `opentelemetry-expert.md` | System-Recall and Sadie observability |
| `github-actions-expert.md` | CI/CD for BL and other projects |
| `vector-db-expert.md` | System-Recall Qdrant layer (generic but useful) |

### Adapt (Modify Before Using)
| Agent | What to Adapt |
|-------|---------------|
| `tauri-expert.md` | Add Kiln/Electron awareness; BL IPC protocol context |
| `owasp-top10-expert.md` | BL already has a `security` agent — merge best checklist items into it |
| `langchain-expert.md` | Less relevant (Tim uses custom BL agent framework, not LangChain) — skip unless needed |

### Format Pattern to Adopt
- **bash-expert 7-section format**: Add `## Essential Tools`, `## Common Pitfalls to Avoid`, `## Advanced Techniques`, `## References` to BL's standard agent template
- **PROACTIVE description trigger**: Add "Use PROACTIVELY for..." to high-frequency BL agents (security, refactorer, diagnose-analyst)

### Create From Scratch (Novel Additions)
| Agent | Rationale |
|-------|-----------|
| `qdrant-expert` | System-Recall core; not in this repo or anywhere else |
| `esphome-expert` | Sadie satellite nodes; not in this repo |
| `solana-anchor-expert` | ADBP; BL has `solana-specialist` but a dedicated Anchor expert is missing |

---

## Notes on What This Repo Is NOT

- No hooks of any kind
- No MCP server or tool definitions
- No inter-agent communication or orchestration
- No workflow DAGs or pipeline files
- No routing logic
- No training/optimization pipeline
- No state management
- No campaign or research loop concepts
- No model-per-complexity routing (everything is sonnet)
- No typed contracts or schemas
- No monitoring or registry

This is purely a collection of human-written system prompt documents. The "intelligence" is entirely in the agent content, not in any surrounding infrastructure. BrickLayer's infrastructure is categorically superior; the value here is purely the breadth of language/framework coverage in the agent content itself.
