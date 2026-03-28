# Repo Research: Skills Libraries Cross-Reference

**Repos analyzed**: 5 public skills library repos
**Researched**: 2026-03-28
**Researcher**: repo-researcher agent
**Purpose**: Identify skill gaps and novel patterns for BrickLayer 2.0 from the top community skills libraries

---

## Verdict Summary

These five repos collectively represent the community consensus on what Claude Code skills should cover. The dominant pattern is framework/language specialists (Python Pro, Go Pro, Rust, etc.) and DevOps/infra tools — territory where BrickLayer's agent fleet operates at a higher abstraction level (campaign loop, consensus, SPARC phases) rather than framework-specific depth. The most actionable gaps are: (1) context engineering primitives that BrickLayer lacks as explicit skills — context degradation detection, context compression strategy, and LLM-as-judge evaluation; (2) operational engineering skills BrickLayer's agents don't cover — incident commander, observability/SLO designer, chaos engineer, dependency auditor, git worktree manager; and (3) business/product skills entirely absent from BrickLayer's domain — regulatory compliance, product discovery, C-level advisory, marketing automation. BrickLayer beats all five repos on campaign orchestration, multi-agent routing, SPARC phases, and self-improving agent loops (EMA/DSPy); none of the five repos have anything comparable to Trowel, Mortar's four-layer routing, or the consensus builder.

---

## Repo 1: sickn33/antigravity-awesome-skills

**URL**: https://github.com/sickn33/antigravity-awesome-skills
**Stars**: 27K+
**Claim**: 1,329+ agentic skills across Claude Code, Cursor, Codex CLI, Gemini CLI

### Category breakdown

The repo is a massive aggregator. Key category families visible from the CATALOG.md and directory structure:

- **Core Development**: Language specialists (Python, TypeScript, JavaScript, Go, Rust, C++, Swift, Kotlin, Java, C#, PHP, Ruby), framework specialists (FastAPI, Django, NestJS, Rails, Laravel, .NET Core, Spring Boot)
- **Frontend**: React, Next.js, Vue, Angular, React Native, Flutter, Svelte, SolidJS
- **Infrastructure**: Kubernetes, Terraform, Helm, Docker, cloud architects (AWS, GCP, Azure)
- **Data/ML**: Pandas, Spark, MLflow, RAG, fine-tuning, embeddings, vector databases
- **Security**: Penetration testing, OWASP audits, secrets management, supply chain
- **Operations**: SRE, incident commander, observability, chaos engineering, runbook generation
- **Productivity workflows**: Code documenter, spec miner, feature forge, debugging wizard, legacy modernizer
- **Product/Business**: Product manager, agile coach, growth hacker, SEO auditor
- **Meta-skills**: Skill auditor (scan installed skills for injection/exfiltration risks before running)
- **CLI installer**: `npx antigravity-skill install <slug>` — installable from terminal

Structure: Each skill is a directory with `SKILL.md` (frontmatter with `triggers`, `when_to_use`, `author`), optional `examples/`, optional `tests/`. The frontmatter trigger system is notable — skills declare their own activation keywords.

### Novel skills not in BrickLayer

- **skill-security-auditor** — scans any skill file for prompt injection, command injection, data exfiltration patterns, and supply chain risks before installation. Returns PASS/WARN/FAIL. BrickLayer has no equivalent — any skill installed is trusted blindly.
- **incident-commander** — full incident response playbook: severity classifier (P0-P4), automatic runbook lookup, PIR (post-incident review) generator, on-call escalation decision tree
- **observability-designer** — designs SLOs, error budgets, alert thresholds, and dashboard layouts from codebase analysis. Different from BrickLayer's devops agent which is general-purpose.
- **chaos-engineer** — fault injection planner for microservices, including blast radius analysis and hypothesis-driven chaos experiments
- **codebase-onboarding** — auto-generates onboarding documentation by scanning codebase structure, entry points, dependency graph, and key patterns. Distinct from BrickLayer's spec-writer which writes specs for new features, not comprehension docs for new engineers.
- **git-worktree-manager** — parallel development in multiple git worktrees with port isolation per worktree and environment variable sync
- **monorepo-navigator** — Turborepo/Nx/pnpm workspace understanding, impact analysis (which packages are affected by a change), build graph visualization
- **dependency-auditor** — multi-language scanner (npm, pip, cargo, go.mod) with license compliance and CVE detection, generates upgrade plan
- **performance-profiler** — Node/Python/Go profiling integration, bundle analysis, load test scenario generator
- **legacy-modernizer** — structured approach to modernizing legacy code: identify patterns, create migration plan, incremental refactor with test coverage preservation
- **embedded-systems** — firmware, RTOS, IoT sensor protocols; entirely absent from BrickLayer
- **game-developer** — game engine architecture, ECS patterns, physics integration, shader basics
- **the-fool** — five structured reasoning modes to challenge and stress-test any technical or product decision (devil's advocate, first principles, inversion, pre-mortem, Socratic method)

### Top 5 to harvest

1. **skill-security-auditor** — BrickLayer has no mechanism to vet skills/agents being added. A security gate that scans new agent `.md` files for injection patterns before auto-onboarding would be valuable. Could integrate with `masonry-agent-onboard.js` hook.
2. **incident-commander** — BrickLayer's devops agent handles deployment but has no incident response playbook. A dedicated incident response skill with severity classification, escalation trees, and PIR templates fills a real gap.
3. **observability-designer** — SLO design and alert engineering are genuinely specialized. BrickLayer's devops agent is general; a focused observability skill would produce better artifacts.
4. **codebase-onboarding** — Auto-generating onboarding docs is a standalone skill that could integrate with BrickLayer's `/plan` flow (generate "what is this codebase" doc as step 0).
5. **the-fool** — The five structured challenge modes are immediately useful for BrickLayer's hypothesis-generator and design-reviewer agents as incorporated techniques, even without making it a standalone skill.

**Priority**: MEDIUM (Antigravity is a broad aggregator; most of its value comes from skill volume, not novel patterns. The specific skills above are genuinely useful but most of the 1329 skills are framework specialists BrickLayer intentionally delegates to language-appropriate agents.)

---

## Repo 2: muratcankoylan/Agent-Skills-for-Context-Engineering

**URL**: https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering
**Stars**: 14.3K
**Claim**: 13 skills covering context engineering theory and practice

### Category breakdown

13 skills in four tiers:

**Foundational (3)**:
- `context-fundamentals` — anatomy of a context window, attention mechanics, U-shaped attention curves, lost-in-middle phenomenon
- `context-degradation` — detecting four failure patterns: lost-in-middle, context poisoning, distraction injection, context clash
- `context-compression` — compaction strategies: summarization, selective retention, chunked offloading

**Architectural (5)**:
- `multi-agent-patterns` — orchestrator/peer-to-peer/hierarchical patterns with formal definitions of when each degrades
- `memory-systems` — short-term (in-context), episodic (file-based), semantic (vector), graph (entity relationships) — with Python implementation stubs
- `tool-design` — tool schemas that reduce context cost: narrow tool descriptions, low-cardinality output, single-purpose tools
- `filesystem-context` — using the filesystem as dynamic context: scratchpads, plan files, tool output offloading
- `hosted-agents` — background agent infrastructure (sandboxed VMs, Modal integration, pre-built images, warm pools, self-spawning agents for parallelism, Cloudflare Durable Objects for per-session state, multi-client interfaces)

**Operational (3)**:
- `context-optimization` — compaction triggers at 70% utilization, KV-cache exploitation, masking strategies
- `evaluation` — basic agent eval frameworks
- `advanced-evaluation` — LLM-as-a-Judge: direct scoring with rubrics, pairwise comparison with position bias mitigation, rubric generation from examples, bias mitigation strategies

**Cognitive Architecture (1)**:
- `bdi-mental-states` — BDI (Belief-Desire-Intention) cognitive architecture: transform RDF/external context into formal mental state representations, deliberative reasoning, explainability

**Methodology (1)**:
- `project-development` — LLM project lifecycle from ideation to deployment

### Novel skills not in BrickLayer

- **context-degradation detection** — BrickLayer's `masonry-context-monitor.js` hook warns on token count >150K but does not detect the four semantic degradation patterns (lost-in-middle, poisoning, distraction, clash). This skill formalizes when context is semantically degraded, not just large.
- **context-compression strategy** — BrickLayer has no formal compaction skill. When context gets large, the agent currently just continues. This skill defines compaction triggers, what to summarize vs retain, and how to offload to files.
- **LLM-as-Judge (advanced-evaluation)** — BrickLayer's EMA scoring loop uses heuristic metrics (verdict match, evidence quality, confidence calibration). The LLM-as-Judge techniques here — pairwise comparison, rubric generation, position bias mitigation — would improve the quality of agent output scoring in the DSPy optimization loop.
- **BDI mental states** — Transforming external RDF context into formal belief/desire/intention representations for deliberative reasoning. Novel cognitive architecture pattern not present anywhere in BrickLayer.
- **hosted-agents skill** — Infrastructure patterns for background agents: Modal sandboxes, pre-built warm images, self-spawning parallelism, Cloudflare Durable Objects per-session state. BrickLayer's parallel dispatch happens within Claude Code sessions; this describes infrastructure for fully hosted persistent agents.
- **tool-design as explicit skill** — The principle that tool schema design (narrow descriptions, low cardinality output, single-purpose) reduces context cost is not documented anywhere in BrickLayer's agent authoring guidance.
- **filesystem-context as explicit skill** — BrickLayer uses filesystems extensively but the formal pattern of using files as a dynamic context store (scratchpad, plan persistence, tool output offloading) is not documented as a reusable pattern.

### Top 5 to harvest

1. **context-degradation detection** — Extend `masonry-context-monitor.js` beyond token count. Add detection for lost-in-middle symptoms (agent ignoring early instructions), context poisoning (bad data overriding good), and distraction injection. HIGH value for long-running campaigns.
2. **LLM-as-Judge evaluation** — The DSPy optimization loop in BrickLayer uses heuristic scoring. Adding LLM-as-Judge with pairwise comparison and position bias mitigation would dramatically improve prompt optimization quality. Integrate into `masonry/scripts/eval_agent.py`.
3. **context-compression skill** — Make compaction an explicit skill that agents can invoke when they detect degradation. Define: trigger threshold (70% utilization), what to summarize (old tool outputs, completed subtasks), what to preserve (original goal, key decisions, live state).
4. **hosted-agents patterns** — The Modal/warm-pool/self-spawning patterns describe infrastructure BrickLayer will need as it scales to truly parallel background agents. Document as a reference architecture for `masonry-team` mode.
5. **tool-design principles** — Add to BrickLayer's agent authoring standard: tool schemas should be narrow, outputs should be low cardinality, tools should be single-purpose. Reduces context cost per tool call in multi-turn campaigns.

**Priority**: HIGH (context engineering is the discipline BrickLayer operates in but has not formalized. The degradation detection and LLM-as-judge techniques directly improve the quality of BrickLayer's existing infrastructure.)

---

## Repo 3: forrestchang/andrej-karpathy-skills

**URL**: https://github.com/forrestchang/andrej-karpathy-skills
**Stars**: 7.5K
**Claim**: Karpathy-inspired behavioral guidelines for Claude Code

### Category breakdown

This is a single skill (`karpathy-guidelines`) with four behavioral principles encoded as a `CLAUDE.md` injection:

1. **Think Before Coding** — Surface assumptions, present interpretations, push back, stop when confused
2. **Simplicity First** — Minimum code, no speculative features, no abstractions for single-use cases
3. **Surgical Changes** — Touch only what the task requires, don't "improve" adjacent code, clean up only your own orphans
4. **Goal-Driven Execution** — Transform imperative instructions into verifiable success criteria with looping

The repo's unique value is the encoding mechanism: these principles are installed as a Claude Code plugin (`CLAUDE.md`) that applies globally, not as a per-task skill. The format is a behavioral constraint layer rather than domain expertise.

### Novel skills not in BrickLayer

- **Surgical changes constraint** — BrickLayer's agents (developer, fix-implementer) do not have an explicit constraint against modifying adjacent code. This is a frequent source of unexpected diff noise in autopilot builds. The "Surgical Changes" principle would improve build predictability.
- **Assumption surfacing as a pre-flight check** — The "Think Before Coding" principle formalizes what BrickLayer's spec-writer partially does, but it doesn't apply to all agents. Making all agents surface their assumptions before acting (not just during planning) would reduce silent mistakes.
- **Goal-Driven Execution framing** — The explicit transformation of "make it work" into testable success criteria with a verification loop is what BrickLayer's TDD enforcer partially implements, but it's not framed as a universal agent behavioral standard.
- **Simplicity gate** — No BrickLayer agent has an explicit check: "would a senior engineer say this is overcomplicated?" The four-question Simplicity First checklist is a concrete heuristic BrickLayer agents could apply.

### Top 5 to harvest

1. **Surgical changes constraint** — Add to developer and fix-implementer agent definitions: only change lines that directly trace to the task. Do not improve, reformat, or refactor adjacent code. Mention any unrelated issues but do not fix them. This is a HIGH signal improvement for autopilot build quality.
2. **Assumption surfacing** — Add to all BrickLayer agents: before executing, state the three most critical assumptions you are making. If any assumption is uncertain, ask rather than guess.
3. **Simplicity gate** — Add to code-reviewer agent: apply a simplicity check ("could this be 50 lines instead of 200?") as a distinct review dimension separate from correctness.
4. **Goal-Driven framing** — The spec-writer already does this, but developer and test-writer agents should restate the success criteria at the top of each task before writing code.
5. **The tradeoff note** — The repo correctly notes these guidelines bias toward caution over speed and should use judgment for trivial tasks. BrickLayer's agent dispatch could use task complexity estimation to decide how much pre-flight checking to apply.

**Priority**: MEDIUM (These are behavioral improvements to existing agent definitions, not new capabilities. High value-to-effort ratio because they're just prompt additions, but they don't fill any architectural gap.)

---

## Repo 4: Jeffallan/claude-skills

**URL**: https://github.com/Jeffallan/claude-skills
**Stars**: 7.3K
**Claim**: 66 specialized skills for full-stack developers

### Category breakdown

66 skills organized into 10 categories:

**Language Specialists (12)**: Python Pro, TypeScript Pro, JavaScript Pro, Go Pro, Rust Engineer, SQL Pro, C++ Pro, Swift Expert, Kotlin Specialist, C# Developer, PHP Pro, Java Architect

**Backend Frameworks (7)**: NestJS Expert, Django Expert, FastAPI Expert, Spring Boot Engineer, Laravel Specialist, Rails Expert, .NET Core Expert

**Frontend & Mobile (7)**: React Expert, Next.js Developer, Vue Expert (TS), Vue Expert (JS), Angular Architect, React Native Expert, Flutter Expert

**Infrastructure & Cloud (5)**: Kubernetes Specialist, Terraform Engineer, Postgres Pro, Cloud Architect, Database Optimizer

**API & Architecture (7)**: GraphQL Architect, API Designer, WebSocket Engineer, Microservices Architect, MCP Developer, Architecture Designer, Feature Forge

**Quality & Testing (4)**: Test Master, Playwright Expert, Code Reviewer, Code Documenter

**DevOps & Operations (5)**: DevOps Engineer, Monitoring Expert, SRE Engineer, Chaos Engineer, CLI Developer

**Security (2)**: Secure Code Guardian, Security Reviewer

**Data & Machine Learning (6)**: Pandas Pro, Spark Engineer, ML Pipeline, Prompt Engineer, RAG Architect, Fine-Tuning Expert

**Platform Specialists (4)**: Salesforce Developer, Shopify Expert, WordPress Pro, Atlassian MCP

**Specialized (3)**: Legacy Modernizer, Embedded Systems, Game Developer

**Workflow (3)**: Debugging Wizard, Fullstack Guardian, The Fool

Notable: Each skill ships with a formal `Skill Workflows` section that chains skills together in decision trees (e.g., "New Feature Development: Feature Forge → Architecture Designer → Fullstack Guardian + Framework Skills → Test Master → Code Reviewer → Security Reviewer → DevOps Engineer → Monitoring Expert"). This multi-skill chaining documentation is more explicit than BrickLayer's routing documentation.

Also notable: the `spec-miner` skill — reverse-engineers specifications from existing codebases. Distinct from BrickLayer's spec-writer which writes specs for new work.

### Novel skills not in BrickLayer

- **spec-miner** — reads an existing codebase and reconstructs its implicit specification: what are the contracts, what are the assumptions, what patterns are being enforced. BrickLayer's spec-writer goes the other direction (requirements → spec). This skill is the inverse.
- **code-documenter** — dedicated skill for adding inline documentation, JSDoc/docstrings, and API docs. BrickLayer's code-reviewer and developer agents do this incidentally but not as a primary output.
- **fine-tuning-expert** — LoRA, QLoRA, PEFT, model optimization. BrickLayer has no ML training skills.
- **MCP developer skill** — formal skill for building MCP servers from OpenAPI specs, with schema validation and manifest generation. BrickLayer builds MCP servers (Masonry) but has no skill for helping users build their own.
- **atlassian-mcp** — Jira/Confluence integration via MCP, JQL queries, CQL queries. Not in BrickLayer.
- **graphql-architect** — GraphQL schema design, resolvers, federation. Not in BrickLayer's typescript-specialist.
- **SRE engineer** — SLOs, error budgets, on-call runbooks, toil reduction. BrickLayer's devops agent is CI/CD focused; SRE practice is separate.
- **The Fool (structured challenge modes)** — 5 reasoning modes: devil's advocate, first principles, inversion, pre-mortem, Socratic. Same as antigravity. High value for design-reviewer agent.
- **Skill decision trees and chaining documentation** — The explicit chaining of skills into workflow sequences (Feature Development → Bug Fix → Legacy Migration → Cloud-Native Development) is a documentation pattern BrickLayer lacks for its agent dispatch chains.

### Top 5 to harvest

1. **spec-miner pattern** — Add a `/spec-mine` skill that dispatches a subagent to reverse-engineer the implicit specification of an existing codebase. Useful for onboarding to legacy systems before running `/plan`. Maps to BrickLayer's agent architecture easily.
2. **SRE skill** — Dedicated skill covering SLO definition, error budget calculation, on-call runbook authoring, and toil quantification. BrickLayer's devops agent doesn't cover this depth.
3. **The Fool challenge modes** — Integrate the five structured challenge modes (devil's advocate, inversion, pre-mortem, first principles, Socratic) into BrickLayer's design-reviewer and hypothesis-generator agents.
4. **MCP developer skill** — A `/mcp-build` skill that takes an OpenAPI spec and scaffolds an MCP server (TypeScript or Python) with manifest.json, tool definitions, and basic tests.
5. **Skill decision tree documentation** — Document BrickLayer's agent dispatch chains as explicit workflow sequences in CLAUDE.md or Mortar's routing documentation. The "when to use which agent" decision tree format from this repo is immediately adoptable.

**Priority**: MEDIUM (Most skills are framework specialists BrickLayer delegates to language-capable agents. The spec-miner, SRE, and MCP developer skills are genuine gaps. The decision tree documentation pattern is low effort with high usability impact.)

---

## Repo 5: alirezarezvani/claude-skills

**URL**: https://github.com/alirezarezvani/claude-skills
**Stars**: 6.9K
**Claim**: 205 production-ready skills across 9 domains for 11 AI coding tools

### Category breakdown

205 skills in 9 domains, plus agents, personas, and commands:

**Engineering — Core (26)**: Architecture, frontend, backend, fullstack, QA, DevOps, SecOps, AI/ML, data, Playwright Pro (12 subskills with Cypress/Selenium migration, TestRail, BrowserStack), Self-Improving Agent (5 skills: auto-memory curation, pattern promotion, skill extraction, memory health), Google Workspace CLI, accessibility audit

**Engineering — POWERFUL (30)**: agent-designer, agent-workflow-designer, rag-architect, database-designer, database-schema-designer, migration-architect, skill-security-auditor, ci-cd-pipeline-builder, mcp-server-builder, pr-review-expert, api-design-reviewer, api-test-suite-builder, dependency-auditor, release-manager, observability-designer, performance-profiler, monorepo-navigator, changelog-generator, codebase-onboarding, runbook-generator, git-worktree-manager, env-secrets-manager, incident-commander, tech-debt-tracker, interview-system-designer

**Product (14)**: product-manager, agile-po, strategist, ux-researcher, ui-design, landing-page-generator, saas-scaffolder, analytics-setup, experiment-designer, discovery-coach, roadmap-communicator, code-to-prd, user-story-writer, rice-prioritizer

**Marketing (43)**: 7 pods — Content (8), SEO (5), CRO (6), Channels (6), Growth (4), Intelligence (4), Sales (2) + orchestration router. 32 Python tools.

**Project Management (6)**: senior-pm, scrum-master, jira-expert, confluence-expert, atlassian-admin, sprint-planner

**Regulatory & Quality Management (12)**: ISO 13485, MDR 2017/745, FDA 21 CFR Part 820, ISO 27001, GDPR, CAPA, risk-management, document-controller, audit-trail-manager, validation-protocol-writer, complaint-management, supplier-quality

**C-Level Advisory (28)**: Full C-suite (CEO, CTO, CFO, COO, CMO, CPO, CHRO, CLO, CSO, CDO), board-meeting-prep, due-diligence, culture-coach, strategic-planning, investor-relations, M&A-advisor, competitive-intelligence, organizational-design

**Business & Growth (4)**: customer-success, sales-engineer, revenue-ops, contracts-proposals

**Finance (2)**: financial-analyst (DCF, budgeting, forecasting), saas-metrics-coach (ARR, MRR, churn, LTV, CAC)

**Personas (3)**: startup-cto, growth-marketer, solo-founder — pre-configured identities with curated skill loadouts

**Orchestration protocol**: A documented lightweight protocol for coordinating personas and skills across domain boundaries without a framework. Four patterns: Solo Sprint (single persona across project phases), Domain Deep-Dive (one persona + stacked skills), Multi-Agent Handoff (personas review each other), Skill Chain (sequential skills, no persona).

**Commands (19)**: a11y-audit, changelog, code-to-prd, competitive-matrix, financial-health, focused-fix, google-workspace, okr, persona, pipeline, plugin-audit, prd, project-health, retro, rice, saas-health, seo-auditor, sprint-health, sprint-plan, tdd, tech-debt, user-story

**Self-Improving Agent subskill cluster**: Auto-memory curation, pattern promotion from episodic to semantic memory, skill extraction from successful sessions, memory health monitoring. This is the closest analog to BrickLayer's EMA training pipeline found in any of the five repos — though BrickLayer's is more sophisticated (weighted EMA, HNSW reasoning bank, PageRank confidence scoring).

### Novel skills not in BrickLayer

**Product domain (entirely absent from BrickLayer)**:
- **product-manager** — PRD writing, prioritization frameworks (RICE, ICE, Kano), roadmap planning
- **ux-researcher** — user interview synthesis, persona generation, Jobs-to-be-Done framework
- **experiment-designer** — A/B test design, statistical significance, minimum detectable effect calculation
- **landing-page-generator** — generates TSX + Tailwind landing pages from a JSON config
- **saas-scaffolder** — generates SaaS boilerplate with auth, billing, multi-tenancy patterns
- **discovery-coach** — shapes ambiguous ideas into testable hypotheses
- **rice-prioritizer** — RICE scoring CLI tool (stdlib Python, zero pip installs)

**Regulatory domain (entirely absent from BrickLayer)**:
- **mdr-745-specialist** — EU Medical Device Regulation compliance (Annex II, III technical docs)
- **iso-13485-specialist** — ISO 13485 quality management system for medical devices
- **fda-qsr-specialist** — FDA 21 CFR Part 820 quality system regulation
- **gdpr-specialist** — GDPR data protection impact assessments, Article 30 records
- **iso-27001-specialist** — Information security management system documentation
- **capa-specialist** — Corrective and Preventive Action tracking and root cause analysis

**C-Level Advisory (entirely absent from BrickLayer)**:
- **cto-advisor** — technology strategy, build-vs-buy decisions, tech debt quantification (comes with Python tech_debt_analyzer.py CLI)
- **cfo-advisor** — financial modeling, unit economics, SaaS metrics (MRR, ARR, NDR, CAC payback)
- **cmo-advisor** — marketing strategy, go-to-market planning, positioning
- **investor-relations** — pitch deck review, due diligence data room, cap table modeling
- **board-meeting-prep** — board deck structure, metrics selection, narrative framing

**Marketing (entirely absent from BrickLayer)**:
- **seo-auditor** — technical SEO audit with Python crawler, Core Web Vitals analysis, structured data validation
- **content-production** — brand voice analysis, content calendar generation, repurposing workflows
- **cro-specialist** — conversion rate optimization, landing page analysis, A/B test design
- **growth-analyst** — funnel analysis, cohort retention, growth accounting (new/expansion/churn/resurrection)
- **email-sequence-writer** — drip campaign design, behavioral trigger logic

**Engineering skills absent from BrickLayer**:
- **self-improving-agent** — auto-curates memory from session history: extracts successful patterns, promotes episodic memory to semantic, manages memory health scores. Closest community analog to BrickLayer's EMA loop.
- **pr-review-expert** — blast radius analysis (what could break), security scan, coverage delta. BrickLayer's code-reviewer is general; this is PR-specific with impact analysis.
- **api-test-suite-builder** — scans all API routes and auto-generates a complete test suite (parametrized, edge cases, auth variations)
- **release-manager** — semantic version bumping from conventional commits, release notes generation, readiness checklist
- **interview-system-designer** — designs engineering interview loops, question banks, calibration rubrics

**Cross-cutting patterns absent from BrickLayer**:
- **Persona system** — pre-configured agent identities (startup-cto, growth-marketer, solo-founder) with skill loadouts and communication styles. BrickLayer has agents but no persona concept (a cross-domain identity that switches which skills to emphasize).
- **Multi-tool conversion** — single conversion script (`convert.sh --tool all`) that outputs skill formats for Cursor, Aider, Windsurf, Kilo Code, OpenCode, Augment. BrickLayer skills are Claude Code only.
- **Skill security gate** — same as antigravity; scans skills for malicious patterns before installation.
- **Orchestration protocol** — four named patterns for multi-agent coordination across domains without a framework. Solo Sprint, Domain Deep-Dive, Multi-Agent Handoff, Skill Chain.

### Top 5 to harvest

1. **Product domain skills** — `/discover` skill that combines ux-researcher + discovery-coach + experiment-designer to take a vague idea through validated hypothesis. BrickLayer's research capabilities focus on business model stress-testing, not product discovery. A `/discover` skill would make BrickLayer useful for early-stage product work.
2. **release-manager skill** — A `/release` skill: reads recent commits (conventional commit format), bumps semver, generates structured release notes, runs a release readiness checklist (tests passing, migrations documented, rollback plan). Maps cleanly to BrickLayer's git-nerd + karen.
3. **Persona concept** — Define 2-3 BrickLayer personas (e.g., "Startup CTO", "Research Analyst", "Platform Engineer") that configure which Mortar routing priorities and agent defaults to emphasize. Lightweight — just a CLAUDE.md injection pattern.
4. **saas-health / financial-health commands** — Quick diagnostic commands that compute SaaS metrics (MRR, churn, CAC payback, LTV:CAC) from input data. Could be a BrickLayer `/health` skill that wraps the Python tools.
5. **C-level advisory agents** — A `cto-advisor` agent that applies to BrickLayer's own development: when designing new BrickLayer capabilities, consult a CTO advisor persona to assess build-vs-buy, technical debt implications, and scaling constraints. Meta-level application of these skills to BrickLayer itself.

**Priority**: HIGH for product/business domains; MEDIUM for the engineering skills (most are covered by BrickLayer's existing fleet at a higher abstraction). The regulatory compliance domain is HIGH if BrickLayer ever targets regulated industries.

---

## Cross-Repo Analysis

### What ALL five repos lack that BrickLayer has

These capabilities appear in none of the five repos:

- **Campaign orchestration loop** — Trowel's research campaign (questions.md → findings/ → synthesis.md) has no equivalent. These repos are task-focused, not campaign-focused.
- **Four-layer routing** — Mortar's deterministic → semantic → LLM → fallback routing handles 60%+ of work with zero LLM calls. No repo has routing intelligence.
- **Consensus builder** — Weighted majority vote with BLOCKED-on-tie conservative default. None of these repos model multi-agent consensus.
- **EMA training pipeline** — The telemetry.jsonl → collector.py → ema_history.json loop with α=0.3 EMA scoring is unique to BrickLayer.
- **HNSW reasoning bank** — Local vector similarity with hnswlib + PageRank confidence scoring. No equivalent.
- **SPARC phases** — The /plan → /pseudocode → /architecture → /build → /verify → /fix state machine with mode files and progress.json is unique.
- **Hook-driven enforcement** — All 14 hooks (lint, TDD, design tokens, stop guard, context monitor, etc.) enforced at the tool level. These repos have no enforcement infrastructure.
- **Claims board** — Async human escalation via .autopilot/claims.json. Unique.
- **Agent registry with drift detection** — agent_registry.yml + masonry_drift_check. Unique.

### Patterns that appear in multiple repos (community consensus)

- **Skill frontmatter with trigger keywords** — All repos use `triggers:` metadata in SKILL.md. BrickLayer uses a different activation model (slash commands + Mortar routing). The trigger keyword pattern is simpler but less powerful.
- **Progressive disclosure** — Load skill names/descriptions first, full content on activation. BrickLayer's masonry-session-start.js does something similar but for campaign state, not skill content.
- **Skill templates with Gotchas sections** — muratcankoylan standardized "Gotchas" sections (5-9 per skill) documenting failure modes. BrickLayer agent files don't have standardized failure mode documentation.
- **Multi-tool format conversion** — Both antigravity and alirezarezvani support converting skills to Cursor, Aider, Windsurf, etc. BrickLayer is Claude Code only by design, but the pattern is useful for portability.
- **Skills-as-plugins marketplace** — All repos register via `/plugin marketplace add`. BrickLayer uses a different installation model (manual copy to ~/.claude/agents/). The marketplace model is more discoverable.

---

## Feature Gap Analysis

| Feature | In Skills Libraries | In BrickLayer 2.0 | Gap Level | Notes |
|---------|--------------------|--------------------|-----------|-------|
| Context degradation detection (semantic) | muratcankoylan | Hook checks token count only | HIGH | Lost-in-middle, poisoning, clash patterns not detected |
| LLM-as-Judge evaluation | muratcankoylan | Heuristic EMA scoring only | HIGH | Pairwise comparison + bias mitigation missing |
| Context compression skill | muratcankoylan | No formal compaction | HIGH | No trigger threshold, no compaction strategy |
| Product discovery skills | alirezarezvani | Not present | HIGH | UX research, experiment design, JTBD framework |
| Persona concept | alirezarezvani | Not present | MEDIUM | Cross-domain identities with skill loadouts |
| Release manager skill | alirezarezvani | git-nerd handles commits | MEDIUM | Semver bumping, release notes, readiness checklist |
| Spec-miner (reverse-engineer spec) | Jeffallan | spec-writer is forward only | MEDIUM | Inverse of spec-writer; useful for legacy codebase work |
| Incident commander | sickn33, alirezarezvani | devops agent is general | MEDIUM | Severity classification, PIR, escalation decision tree |
| Observability / SLO designer | sickn33, alirezarezvani | devops agent is general | MEDIUM | SLO definitions, error budgets, alert design |
| Skill security auditor | sickn33, alirezarezvani | Not present | MEDIUM | Scan new agent files for injection before onboarding |
| Surgical changes constraint | forrestchang | Not in developer agent | MEDIUM | Explicit prohibition on modifying adjacent code |
| Assumption surfacing pre-flight | forrestchang | Only in spec-writer | MEDIUM | All agents should surface assumptions before acting |
| BDI cognitive architecture | muratcankoylan | Not present | LOW | Formal belief/desire/intention mental model |
| Regulatory compliance (ISO, MDR, FDA) | alirezarezvani | Not present | LOW (unless targeted) | Medical device / regulated industry skills |
| C-level advisory agents | alirezarezvani | Not present | LOW | CEO/CFO/CMO personas; not BrickLayer's core domain |
| Marketing automation skills | alirezarezvani | Not present | LOW | SEO, CRO, content production; not BrickLayer's domain |
| Embedded systems / game dev | Jeffallan, sickn33 | Not present | LOW | Niche; BrickLayer's fleet handles general code |
| Fine-tuning / LoRA skills | Jeffallan | Not present | LOW | ML training pipeline outside BrickLayer's scope |
| MCP developer skill | Jeffallan, alirezarezvani | Not present | MEDIUM | Scaffold MCP servers from OpenAPI specs |
| Gotchas sections in agent files | muratcankoylan | Not standardized | MEDIUM | Failure mode documentation per agent |
| Multi-tool format conversion | alirezarezvani, sickn33 | Claude Code only | LOW | Portability nice-to-have |
| Chaos engineer | Jeffallan, sickn33 | Not present | LOW | Fault injection for microservices resilience |
| Codebase onboarding generator | sickn33, alirezarezvani | Not present | MEDIUM | Auto-generate onboarding docs from codebase scan |
| Campaign orchestration | None | BrickLayer unique | N/A | BrickLayer is ahead |
| Four-layer routing | None | BrickLayer unique | N/A | BrickLayer is ahead |
| Consensus builder | None | BrickLayer unique | N/A | BrickLayer is ahead |
| EMA training pipeline | muratcankoylan (basic) | BrickLayer advanced | N/A | BrickLayer is significantly more sophisticated |
| Hook enforcement infrastructure | None | BrickLayer unique | N/A | BrickLayer is ahead |
| SPARC phases | None | BrickLayer unique | N/A | BrickLayer is ahead |

---

## Top 5 Recommendations

### 1. Semantic Context Degradation Detection [4h, HIGH]

**What to build**: Extend `masonry-context-monitor.js` to detect semantic degradation patterns, not just token count. Add checks for: (a) lost-in-middle — compare agent's last 3 responses against the original task specification for semantic drift using Ollama embeddings, (b) context poisoning — detect when contradictory information appears in the context (simple keyword contradiction scan), (c) compaction trigger — when context exceeds 70% capacity, emit a structured warning with suggested compaction strategy.

**Why it matters**: BrickLayer's campaigns can run for hours. Context degradation causes agents to silently ignore early instructions and produce low-quality findings. A hook-level detector would catch this before it compounds across multiple questions.

**Implementation sketch**: In `masonry-context-monitor.js`, when token count exceeds 100K, spawn an Ollama call comparing the current task against the agent's last output. If cosine similarity drops below 0.6, emit a DEGRADATION_WARNING to the claims board. Also add a `masonry-context-compress.js` hook that fires at 70% capacity with a suggested compaction summary.

### 2. LLM-as-Judge Evaluation for Agent Optimization [6h, HIGH]

**What to build**: Extend `masonry/scripts/eval_agent.py` to support LLM-as-Judge scoring modes alongside the current heuristic metrics. Add: (a) pairwise comparison mode — given two agent outputs, ask a judge LLM which is better on each rubric dimension, (b) rubric generation — auto-generate domain-specific rubrics from high-quality examples, (c) position bias mitigation — run each pairwise comparison twice with swapped order, use agreement score.

**Why it matters**: BrickLayer's DSPy optimization loop uses heuristic scoring (verdict match, evidence quality, confidence calibration). These heuristics miss nuanced quality dimensions that matter for research output. LLM-as-Judge with bias mitigation would produce better signal for prompt optimization, especially for agents like competitive-analyst and synthesizer where quality is subjective.

**Implementation sketch**: Add `--eval-mode llm-judge` flag to `improve_agent.py`. Judge model: Haiku (cheap, fast). Rubric schema: `{dimension: str, score: 1-5, reasoning: str}`. Aggregate rubric scores and compare to current EMA score. Revert if LLM-judge says no improvement.

### 3. Spec-Miner Skill (/spec-mine) [3h, MEDIUM]

**What to build**: A `/spec-mine` skill that dispatches an agent to reverse-engineer the implicit specification of an existing codebase. Output: contracts (what functions promise to do), invariants (what must always be true), patterns (what conventions are being enforced), entry points (where execution starts), integration points (what external systems are called).

**Why it matters**: BrickLayer's `/plan` assumes you're building something new. When onboarding to a legacy codebase or inheriting a project, there's no skill for "understand what this code is supposed to do before we change it." Spec-miner fills this gap and pairs naturally with the existing `/plan` flow.

**Implementation sketch**: New skill file `~/.claude/agents/spec-miner.md`. Trigger: `/spec-mine [path]`. Agent reads key source files, tests, README, and any existing docs. Outputs `spec-mined.md` to `.autopilot/` directory. `/plan` checks for this file and incorporates it into the spec as "Existing System Behavior" section.

### 4. Standardize Gotchas Sections in All Agent Definitions [2h, MEDIUM]

**What to build**: Add a `## Gotchas` section to every agent definition file following the pattern: 5-7 specific failure modes per agent, written as "Gotcha: [what goes wrong] — [why it happens] — [how to avoid it]". The muratcankoylan repo demonstrated that standardizing this section significantly reduces agent failure rates.

**Why it matters**: BrickLayer's 50+ agent files have inconsistent documentation of failure modes. Some have none. When agents fail, the failure modes aren't documented for the optimization loop to learn from. Standardizing Gotchas sections gives the EMA training pipeline more signal about what to avoid.

**Example for research-analyst.md**:
```
## Gotchas
- Gotcha: Treating the first plausible result as the answer — LLMs have a bias toward early information. Always search for disconfirming evidence before writing the finding.
- Gotcha: Conflating correlation with causation in quantitative findings — always state the inference mechanism, not just the statistical relationship.
- Gotcha: Confidence score inflation — don't assign >0.85 confidence unless you have primary source evidence. Secondary/tertiary sources cap at 0.75.
```

### 5. Product Discovery Skill (/discover) [5h, HIGH if product work is in scope]

**What to build**: A `/discover` skill that chains ux-researcher + experiment-designer + discovery-coach patterns. Takes a vague product idea and outputs: user segment definition, 3 testable hypotheses (Jobs-to-be-Done format), minimum experiment design for each hypothesis (what to build, what metric moves, how long to run), and a PRD stub.

**Why it matters**: BrickLayer's research capabilities are excellent for business model stress-testing and competitive analysis, but there's no skill for early-stage product discovery. Adding `/discover` would extend BrickLayer's value to the product design phase, not just the validation phase.

**Implementation sketch**: New skill dispatches three sub-agents in parallel: (1) persona-generator takes target user description and generates 2 user archetypes, (2) jtbd-analyst takes each archetype and generates Jobs-to-be-Done statements, (3) experiment-designer takes each JTBD and generates a testable experiment. Synthesizer agent combines outputs into `discovery.md`.

---

## Novel Patterns to Incorporate (Future)

**Progressive disclosure for skill content**: Skills load name/description into context immediately; full content loads only when the skill is activated. BrickLayer currently loads all agent content on mention. As the agent fleet grows past 80 agents, progressive disclosure would reduce context cost in multi-agent campaigns.

**Skill chaining documentation in decision trees**: The explicit format of "Task X: skill A → skill B → skill C → verify with skill D" is a more usable format than BrickLayer's current prose routing docs. Worth adopting for the BrickLayer CLAUDE.md.

**Frontmatter trigger keywords**: The `triggers:` metadata in SKILL.md files lets Mortar match skills without an LLM call. BrickLayer could add trigger keywords to agent frontmatter to improve deterministic routing layer coverage.

**Skill-level failure mode testing**: alirezarezvani's `skill-tester` and `plugin-audit` skills test whether a skill correctly handles edge cases before deployment. BrickLayer could add a `masonry-skill-test` command that runs the skill through known failure scenarios before registering it in the agent registry.

**Orchestration patterns named and documented**: The four patterns (Solo Sprint, Domain Deep-Dive, Multi-Agent Handoff, Skill Chain) provide a vocabulary for discussing multi-agent coordination that BrickLayer lacks. Adding this vocabulary to Mortar's routing documentation would improve how Tim thinks about dispatching agents.

**BDI cognitive architecture for long-running agents**: For Trowel's campaign conductor, formally modeling beliefs (what we know), desires (what the campaign is trying to find out), and intentions (the current plan of attack) could improve campaign coherence across wave boundaries.
