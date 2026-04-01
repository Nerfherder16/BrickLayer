# Repo Research: quemsah/awesome-claude-plugins
**Repo**: https://github.com/quemsah/awesome-claude-plugins
**Researched**: 2026-03-28

---

## Verdict Summary

This is a curated, auto-indexed directory of 9,094 repositories (as of 2026-03-25) that contain Claude Code plugins, skills, or MCPs — ranked by a composite score of stars, subscribers, and plugin count. The README presents the top 100 ranked repos in a sortable table. The repo includes a Next.js/Deno web UI that serves a browseable interface backed by a large `repos.json` (2.9MB). This is primarily a discovery/catalog resource, not a plugin itself. The highest-value items for BrickLayer are scattered across ~20 of the top 100 repos, with several filling real capability gaps: parallel worktree management, codebase knowledge graphs, Chrome DevTools inspection, multi-LLM code review, advanced security auditing, and Karpathy-style autonomous iteration loops.

---

## File Inventory

| File | Description |
|------|-------------|
| `README.md` | Top 100 ranked repos table — name, description, stars, subscribers, plugin count |
| `.github/renovate.json` | Weekly dependency update schedule via Renovate bot |
| `.github/workflows/deno.yml` | Deno CI workflow for the web UI |
| `ui/.gitignore` | Gitignore for the Next.js frontend |
| `ui/.husky/` | Git hook config (husky) |
| `ui/biome.json` | Biome linter/formatter config (4KB) |
| `ui/components.json` | shadcn/ui component registry config |
| `ui/deno.json` | Deno runtime config for build scripts |
| `ui/deno.lock` | Deno lockfile (66KB) |
| `ui/next.config.ts` | Next.js 16.1.7 config |
| `ui/package.json` | Dependencies: Next.js 16, React 19, Recharts, Fuse.js, Zod, Radix UI, Lucide, Tailwind v4 |
| `ui/postcss.config.mjs` | PostCSS config for Tailwind |
| `ui/tsconfig.json` | TypeScript config |
| `ui/public/` | Static assets |
| `ui/src/app/` | Next.js App Router pages: root, `[...repo]`, about, stats, llms.txt, sitemap, robots |
| `ui/src/components/` | React UI components |
| `ui/src/data/repos.json` | Full indexed dataset — 9,094 repos with fields: html_url, stargazers_count, forks_count, subscribers_count, description, owner, plugins_count (2.9MB) |
| `ui/src/data/stats.json` | 135 daily snapshots of total repo count (Oct 2025 → Mar 2026) |
| `ui/src/hooks/` | React custom hooks |
| `ui/src/lib/` | Utilities |
| `ui/src/providers/` | React context providers |
| `ui/src/schemas/repo.schema.ts` | Zod schema: html_url, stargazers_count, forks_count, subscribers_count, description, owner, owner_url, repo_name, plugins_count, id |
| `ui/src/schemas/stats.schema.ts` | Zod schema for growth stats |

---

## Plugin/MCP Catalog

The README indexes 100 repos. Below is the complete catalog of all 100 entries with category, install method, and plugin count.

### Tier 1: Multi-Plugin Powerhouses (10+ plugins)

| # | Repo | Stars | Plugins | Category | Install |
|---|------|-------|---------|----------|---------|
| 6 | [anthropics/claude-code](https://github.com/anthropics/claude-code) | 82.6K | 13 | Core platform | Native |
| 11 | [wshobson/agents](https://github.com/wshobson/agents) | 32.2K | 73 | Multi-agent orchestration | `/plugin marketplace add wshobson/agents` |
| 16 | [davila7/claude-code-templates](https://github.com/davila7/claude-code-templates) | 23.6K | 10 | Templates/config CLI | npm |
| 28 | [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) | 15.1K | 10 | 127+ specialized subagents | `/plugin marketplace add VoltAgent/awesome-claude-code-subagents` |
| 29 | [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) | 14.6K | 119 | Official Anthropic directory | `/plugin install {name}@claude-plugins-official` |
| 42 | [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) | 10.4K | 38 | Knowledge worker role plugins | `/plugin install {name}@knowledge-work-plugins` |
| 43 | [huggingface/skills](https://github.com/huggingface/skills) | 9.9K | 11 | HuggingFace ecosystem | Plugin marketplace |
| 48 | [phuryn/pm-skills](https://github.com/phuryn/pm-skills) | 8.1K | 8 | Product management | Plugin marketplace |
| 53 | [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) | 6.9K | 28 | 192+ skills — engineering/marketing/compliance | Plugin marketplace |
| 54 | [anthropics/financial-services-plugins](https://github.com/anthropics/financial-services-plugins) | 6.8K | 7 | Financial services | Plugin marketplace |
| 61 | [Orchestra-Research/AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs) | 5.6K | 22 | AI/ML research skills | Plugin marketplace |
| 72 | [Pimzino/spec-workflow-mcp](https://github.com/Pimzino/spec-workflow-mcp) | 4.1K | 2 | Spec-driven dev MCP + dashboard | `npx @pimzino/spec-workflow-mcp` |
| 75 | [trailofbits/skills](https://github.com/trailofbits/skills) | 3.9K | 36 | Security research/audit skills | `/plugin marketplace add trailofbits/skills` |
| 84 | [libukai/awesome-agent-skills](https://github.com/libukai/awesome-agent-skills) | 3.5K | 3 | Chinese-community curated skills guide | Manual |
| 89 | [davepoon/buildwithclaude](https://github.com/davepoon/buildwithclaude) | 2.6K | 53 | Hub for skills/agents/commands/hooks | Browse |
| 91 | [myclaude](https://github.com/stellarlinkco/myclaude) | 2.5K | 5 | Multi-agent orchestration (Claude+Codex+Gemini) | Plugin marketplace |
| 92 | [deanpeters/Product-Manager-Skills](https://github.com/deanpeters/Product-Manager-Skills) | 2.5K | 46 | PM framework skills | Plugin marketplace |

### Tier 2: High-Value Single-Purpose Plugins/Tools

| # | Repo | Stars | Purpose | Install |
|---|------|-------|---------|---------|
| 1 | [f/prompts.chat](https://github.com/f/prompts.chat) | 154K | Community prompt sharing | Browse |
| 3 | [obra/superpowers](https://github.com/obra/superpowers) | 111.8K | Full dev workflow: spec→plan→subagent TDD | `/plugin install superpowers@claude-plugins-official` |
| 4 | [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code) | 106.9K | Agent harness optimization: skills, instincts, memory, security | `/plugin install everything-claude-code@everything-claude-code` |
| 5 | [anthropics/skills](https://github.com/anthropics/skills) | 102.7K | Official Anthropic agent skills | Plugin marketplace |
| 7 | [upstash/context7](https://github.com/upstash/context7) | 50.5K | Live library docs for LLMs | `npx @upstash/context7-mcp` |
| 8 | [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | 50.4K | Professional UI/UX design intelligence | Plugin marketplace |
| 10 | [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem) | 40.4K | Persistent AI memory compression across sessions | `/plugin install claude-mem` |
| 12 | [ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp) | 31.4K | Chrome DevTools MCP: automation, perf tracing, debugging | `npx chrome-devtools-mcp@latest` |
| 13 | [sickn33/antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills) | 27.3K | 1,304+ skills for Claude/Cursor/Codex/Gemini | Installer CLI |
| 14 | [eyaltoledano/claude-task-master](https://github.com/eyaltoledano/claude-task-master) | 26.2K | AI task management for Cursor/Lovable/Windsurf | npm/npx |
| 15 | [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser) | 24.8K | Browser automation CLI for AI agents | CLI |
| 17 | [HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything) | 22.9K | Make ALL software agent-native via CLI | Plugin marketplace |
| 18 | [yamadashy/repomix](https://github.com/yamadashy/repomix) | 22.6K | Pack entire repo into single AI-friendly file | `npx repomix` |
| 20 | [steveyegge/beads](https://github.com/steveyegge/beads) | 19.7K | Memory upgrade for coding agents | Plugin marketplace |
| 21 | [abhigyanpatwari/GitNexus](https://github.com/abhigyanpatwari/GitNexus) | 19.6K | Client-side knowledge graph from repos (browser-based) | Web app |
| 22 | [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | 18.5K | Prompt/agent/RAG testing and red teaming | `npx promptfoo` |
| 23 | [OthmanAdi/planning-with-files](https://github.com/OthmanAdi/planning-with-files) | 17.2K | Manus-style persistent markdown planning skill | Plugin marketplace |
| 24 | [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) | 17K | Obsidian integration skills (Markdown, Canvas, CLI) | Plugin marketplace |
| 25 | [tobi/qmd](https://github.com/tobi/qmd) | 16.8K | Local semantic CLI search for docs/notes | CLI |
| 26 | [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) | 16.4K | Marketing/CRO/SEO/analytics skills | Plugin marketplace |
| 27 | [K-Dense-AI/claude-scientific-skills](https://github.com/K-Dense-AI/claude-scientific-skills) | 16.2K | Science/engineering/research/finance skills | Plugin marketplace |
| 30 | [muratcankoylan/Agent-Skills-for-Context-Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering) | 14.3K | Context engineering, multi-agent architecture skills | Plugin marketplace |
| 31 | [snarktank/ralph](https://github.com/snarktank/ralph) | 13.7K | Autonomous agent loop: runs until PRD complete, fresh context each iter | `/plugin marketplace add snarktank/ralph` |
| 32 | [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | 13.4K | Design language enforcement for AI harnesses | Plugin marketplace |
| 33 | [jarrodwatts/claude-hud](https://github.com/jarrodwatts/claude-hud) | 13K | HUD plugin: context usage, active tools, agents, todo progress | Plugin |
| 34 | [kubeshark/kubeshark](https://github.com/kubeshark/kubeshark) | 11.8K | K8s network observability via eBPF — MCP-accessible | MCP server |
| 35 | [tanweai/pua](https://github.com/tanweai/pua) | 11.8K | High-agency skill for autonomous self-improvement loops | Plugin marketplace |
| 36 | [JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills) | 11.5K | Chinese community skills collection | Plugin marketplace |
| 38 | [tambo-ai/tambo](https://github.com/tambo-ai/tambo) | 11.1K | Generative UI SDK for React | npm |
| 39 | [EveryInc/compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin) | 11.1K | Office compound engineering plugin | Plugin marketplace |
| 40 | [toss/es-toolkit](https://github.com/toss/es-toolkit) | 10.9K | Modern JS utility lib (lodash replacement, 97% smaller) | npm |
| 41 | [pipecat-ai/pipecat](https://github.com/pipecat-ai/pipecat) | 10.9K | Voice/multimodal conversational AI framework | pip |
| 44 | [skypilot-org/skypilot](https://github.com/skypilot-org/skypilot) | 9.7K | Multi-cloud AI workload orchestration | pip |
| 45 | [mcp-use/mcp-use](https://github.com/mcp-use/mcp-use) | 9.5K | Fullstack MCP framework for apps and servers | pip/npm |
| 50 | [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) | 7.5K | Karpathy 4 principles: Think→Simple→Surgical→Goal-Driven | `/plugin install andrej-karpathy-skills@karpathy-skills` |
| 51 | [Jeffallan/claude-skills](https://github.com/Jeffallan/claude-skills) | 7.3K | 66 full-stack developer skills | Plugin marketplace |
| 52 | [nicobailon/visual-explainer](https://github.com/nicobailon/visual-explainer) | 6.9K | Rich HTML/slide-deck generation for diffs, plans, data | Plugin |
| 55 | [ykdojo/claude-code-tips](https://github.com/ykdojo/claude-code-tips) | 6.7K | 45 tips + custom status line + Gemini CLI as sub-model | Blog/code |
| 56 | [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill) | 6.5K | Research any topic across Reddit/X/YouTube/HN/web | Plugin marketplace |
| 57 | [Lum1104/Understand-Anything](https://github.com/Lum1104/Understand-Anything) | 6.1K | Codebase → interactive knowledge graph | Plugin marketplace |
| 58 | [vectorize-io/hindsight](https://github.com/vectorize-io/hindsight) | 6K | Agent memory that learns over time | Plugin |
| 59 | [mksglu/context-mode](https://github.com/mksglu/context-mode) | 5.9K | Privacy-first context virtualization layer | MCP |
| 60 | [BrainBlend-AI/atomic-agents](https://github.com/BrainBlend-AI/atomic-agents) | 5.8K | Composable atomic agent building blocks | pip |
| 63 | [Eventual-Inc/Daft](https://github.com/Eventual-Inc/Daft) | 5.3K | High-performance data engine for AI/multimodal workloads | pip |
| 66 | [InsForge/InsForge](https://github.com/InsForge/InsForge) | 5K | Fullstack app backend built for agentic dev | Plugin |
| 69 | [firebase/firebase-tools](https://github.com/firebase/firebase-tools) | 4.4K | Firebase CLI with Claude integration | npm |
| 70 | [Dammyjay93/interface-design](https://github.com/Dammyjay93/interface-design) | 4.3K | Design engineering plugin for Claude Code (memory + enforcement) | Plugin |
| 71 | [exa-labs/exa-mcp-server](https://github.com/exa-labs/exa-mcp-server) | 4.1K | Exa web search + crawl MCP | npx |
| 73 | [SawyerHood/dev-browser](https://github.com/SawyerHood/dev-browser) | 4K | Claude skill for browser control | Plugin |
| 76 | [mixedbread-ai/mgrep](https://github.com/mixedbread-ai/mgrep) | 3.9K | Semantic grep: code, images, PDFs — local | CLI |
| 77 | [czlonkowski/n8n-skills](https://github.com/czlonkowski/n8n-skills) | 3.8K | n8n workflow-building skills for Claude | Plugin marketplace |
| 78 | [mukul975/Anthropic-Cybersecurity-Skills](https://github.com/mukul975/Anthropic-Cybersecurity-Skills) | 3.7K | 734+ MITRE ATT&CK-mapped cybersecurity skills | Plugin marketplace |
| 79 | [max-sixty/worktrunk](https://github.com/max-sixty/worktrunk) | 3.7K | Rust CLI for git worktree management — parallel agent workflows | `cargo install worktrunk` |
| 80 | [mckinsey/vizro](https://github.com/mckinsey/vizro) | 3.6K | Low-code data visualization app toolkit | pip |
| 81 | [dathere/qsv](https://github.com/dathere/qsv) | 3.6K | Blazing-fast data wrangling CLI | cargo |
| 82 | [backnotprop/plannotator](https://github.com/backnotprop/plannotator) | 3.5K | Annotate/review agent plans visually; send feedback with one click | Plugin |
| 83 | [tirth8205/code-review-graph](https://github.com/tirth8205/code-review-graph) | 3.5K | Local AST knowledge graph: 6.8x fewer tokens on reviews, 18 languages | `pip install code-review-graph` + MCP |
| 85 | [memodb-io/Acontext](https://github.com/memodb-io/Acontext) | 3.2K | Agent skills as memory layer | Plugin marketplace |
| 86 | [dosco/graphjin](https://github.com/dosco/graphjin) | 3K | GraphQL compiler connecting AI to databases | Plugin |
| 87 | [darrenhinde/OpenAgentsControl](https://github.com/darrenhinde/OpenAgentsControl) | 2.9K | Plan-first framework: TypeScript/Python/Go/Rust + approval-based exec | Plugin marketplace |
| 88 | [agenticnotetaking/arscontexta](https://github.com/agenticnotetaking/arscontexta) | 2.9K | Knowledge system generation from conversation | Plugin |
| 90 | [ZeframLou/call-me](https://github.com/ZeframLou/call-me) | 2.5K | Plugin that calls you on the phone | Plugin |
| 93 | [apache/hamilton](https://github.com/apache/hamilton) | 2.4K | Modular self-documenting dataflows for data science | pip |
| 94 | [supermemoryai/claude-supermemory](https://github.com/supermemoryai/claude-supermemory) | 2.4K | Real-time knowledge/memory that grows with Claude | Plugin |
| 95 | [AvdLee/SwiftUI-Agent-Skill](https://github.com/AvdLee/SwiftUI-Agent-Skill) | 2.3K | SwiftUI best practices for AI tools | Plugin marketplace |
| 96 | [mikeyobrien/ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator) | 2.3K | Improved Ralph Wiggum technique for autonomous orchestration | Plugin |
| 97 | [uditgoenka/autoresearch](https://github.com/uditgoenka/autoresearch) | 2.3K | Karpathy autoresearch: Modify→Verify→Keep/Discard→Repeat | Plugin marketplace |
| 99 | [lackeyjb/playwright-skill](https://github.com/lackeyjb/playwright-skill) | 2.1K | Playwright browser automation skill | Plugin marketplace |
| 100 | [Wirasm/PRPs-agentic-eng](https://github.com/Wirasm/PRPs-agentic-eng) | 2.1K | PRPs (Product Requirements Prompts) for agentic engineering | Browse |

---

## Official Anthropic Plugin Directory Contents

**Internal plugins** (Anthropic-developed, in `plugins/`):
`agent-sdk-dev`, `clangd-lsp`, `claude-code-setup`, `claude-md-management`, `code-review`, `code-simplifier`, `commit-commands`, `csharp-lsp`, `example-plugin`, `explanatory-output-style`, `feature-dev`, `frontend-design`, `gopls-lsp`, `hookify`, `jdtls-lsp`, `kotlin-lsp`, `learning-output-style`, `lua-lsp`, `math-olympiad`, `mcp-server-dev`, `php-lsp`, `playground`, `plugin-dev`, `pr-review-toolkit`, `pyright-lsp`, `ralph-loop`, `ruby-lsp`, `rust-analyzer-lsp`, `security-guidance`, `skill-creator`, `swift-lsp`, `typescript-lsp`

**External plugins** (partner/community, in `external_plugins/`):
`asana`, `context7`, `discord`, `fakechat`, `firebase`, `github`, `gitlab`, `greptile`, `imessage`, `laravel-boost`, `linear`, `playwright`, `serena`, `slack`, `supabase`, `telegram`, `terraform`

---

## wshobson/agents Plugin Catalog (72 plugins, 112 agents, 146 skills)

This is the largest and most architecturally sophisticated third-party plugin collection. Notable plugins:

**Orchestration**: `full-stack-orchestration`, `agent-teams`, `conductor`, `plugin-eval`
**Languages**: `python-development`, `javascript-typescript`, `backend-development`, `blockchain-web3`, `rust-development`, `go-development`
**Infrastructure**: `kubernetes-operations`, `cloud-infrastructure`, `docker-operations`
**Quality**: `security-scanning`, `comprehensive-review`, `test-automation`
**New (notable)**: `plugin-eval` (3-layer quality evaluation with Monte Carlo + Elo), `agent-teams` (7 presets: review/debug/feature/fullstack/research/security/migration), `conductor` (Context→Spec→Implement workflow)

---

## VoltAgent Subagent Categories (127 agents)

01. Core Development: api-designer, backend-developer, electron-pro, frontend-developer, fullstack-developer, graphql-architect, microservices-architect, mobile-developer, ui-designer, websocket-engineer
02. Language Specialists: typescript-pro, sql-pro, swift-expert, vue-expert, angular-architect, cpp-pro, csharp-developer, django-developer, dotnet-core-expert, elixir-expert, expo-react-native-expert, fastapi-developer, flutter-expert, golang-pro, java-architect, javascript-pro, kotlin-specialist, laravel-specialist, nextjs-developer, php-pro, powershell-5.1-expert, powershell-7-expert, python-pro, rails-expert, react-specialist, rust-engineer, spring-boot-engineer, symfony-specialist
03. Infrastructure: azure-infra-engineer, cloud-architect, database-administrator, docker-expert, deployment-engineer, devops-engineer, kubernetes-specialist, network-engineer, platform-engineer, security-engineer, sre-engineer, terraform-engineer, terragrunt-expert, windows-infra-admin
04. Quality & Security: accessibility-tester, ad-security-reviewer, architect-reviewer, chaos-engineer, code-reviewer, compliance-auditor, debugger, error-detective, penetration-tester, performance-engineer, qa-expert, security-auditor, test-automator
05. Data & AI: (additional agents in this category)

---

## Trail of Bits Security Skills Catalog (36 skills)

**Smart Contract Security**: building-secure-contracts, entry-point-analyzer
**Code Auditing**: agentic-actions-auditor, audit-context-building, burpsuite-project-parser, differential-review, dimensional-analysis, fp-check, insecure-defaults, semgrep-rule-creator, semgrep-rule-variant-creator, sharp-edges, static-analysis, supply-chain-risk-auditor, testing-handbook-skills, variant-analysis
**Malware Analysis**: yara-authoring
**Verification**: constant-time-analysis, property-based-testing, spec-to-code-compliance, zeroize-audit
**Reverse Engineering**: dwarf-expert
**Mobile Security**: firebase-apk-scanner
**Development**: ask-questions-if-underspecified, devcontainer-setup, gh-cli, git-cleanup, let-fate-decide, modern-python, seatbelt-sandboxer, second-opinion, skill-improver, workflow-skill-design

---

## Anthropic Knowledge-Work Plugin Catalog (11 plugins)

| Plugin | Connectors |
|--------|------------|
| productivity | Slack, Notion, Asana, Linear, Jira, Monday, ClickUp, Microsoft 365 |
| sales | Slack, HubSpot, Close, Clay, ZoomInfo, Notion, Jira, Fireflies |
| customer-support | Slack, Intercom, HubSpot, Guru, Jira, Notion |
| product-management | Slack, Linear, Asana, Jira, Notion, Figma, Amplitude, Pendo, Intercom |
| marketing | Slack, Canva, Figma, HubSpot, Amplitude, Notion, Ahrefs, SimilarWeb, Klaviyo |
| legal | Slack, Box, Egnyte, Jira, Microsoft 365 |
| finance | Snowflake, Databricks, BigQuery, Slack, Microsoft 365 |
| data | Snowflake, Databricks, BigQuery, Definite, Hex, Amplitude, Jira |
| enterprise-search | Slack, Notion, Guru, Jira, Asana, Microsoft 365 |
| bio-research | PubMed, BioRender, bioRxiv, ClinicalTrials.gov, ChEMBL, Synapse |
| cowork-plugin-management | (meta — build plugins) |

---

## Feature Gap Analysis

| Plugin/MCP | In This Repo | In BrickLayer 2.0 | Gap Level | Notes |
|------------|-------------|-------------------|-----------|-------|
| chrome-devtools-mcp | Yes (#12, 31.4K★) | No | HIGH | Chrome performance tracing, source-mapped debug, puppeteer automation — complements Playwright |
| code-review-graph | Yes (#83, 3.5K★) | No | HIGH | AST knowledge graph, 6.8x token reduction on reviews, 18 languages, incremental via git hook — direct BL research efficiency win |
| worktrunk | Yes (#79, 3.7K★) | No | HIGH | Rust CLI for git worktrees — enables true parallel Claude agent workflows; BL runs multiple sessions simultaneously |
| wshobson/agents (agent-teams) | Yes (#11, 32.2K★) | Partial (Mortar dispatches, but no preset team configurations) | MEDIUM-HIGH | 7 preset team configs (review/debug/feature/research/security) with parallel subagents |
| wshobson/agents (plugin-eval) | Yes (#11) | No | MEDIUM-HIGH | 3-layer plugin evaluation framework with Monte Carlo + Elo scoring — could evaluate BL agents |
| wshobson/agents (conductor) | Yes (#11) | Partial (/plan + /build covers this) | LOW | Context→Spec→Implement workflow similar to BL autopilot |
| trailofbits/skills (security) | Yes (#75, 3.9K★) | Partial (/masonry-security-review exists) | MEDIUM | semgrep-rule-creator, differential-review, insecure-defaults, supply-chain-risk-auditor, constant-time-analysis are additive |
| superpowers (obra) | Yes (#3, 111.8K★) | Partial (BL /build covers much of this) | LOW | Karpathy-style goal-driven execution, systematic-debugging, dispatching-parallel-agents, using-git-worktrees — good prompt patterns to harvest |
| everything-claude-code | Yes (#4, 106.9K★) | Partial | MEDIUM | Instinct-based continuous learning, session SQLite store, harness audit scoring, `/loop-start`/`/loop-status`/`/quality-gate` commands — several additive |
| autoresearch (Karpathy) | Yes (#97, 2.3K★) | YES — this IS BrickLayer | NONE | BL 2.0 is the more complete implementation of this pattern |
| andrej-karpathy-skills | Yes (#50, 7.5K★) | No | LOW | Prompt principles: Think→Simple→Surgical→Goal-Driven. Harvestable into CLAUDE.md/agent prompts |
| ralph (autonomous loop) | Yes (#31, 13.7K★) | Partial (BL research loop covers this) | LOW | PRD-driven fresh-context loops; /ralph-loop in official Anthropic plugins |
| claude-mem | Yes (#10, 40.4K★) | YES — Recall handles this | NONE | BL's Recall (Qdrant+Neo4j+Ollama) is more powerful than claude-mem's compression approach |
| spec-workflow-mcp | Yes (#72, 4.1K★) | Partial (/plan + /build + Kiln covers this) | LOW | Real-time dashboard + VSCode extension; Kiln already serves this purpose |
| repomix | Yes (#18, 22.6K★) | No | MEDIUM | Packs entire repo into single AI-friendly file — useful for feeding codebases to Claude |
| promptfoo | Yes (#22, 18.5K★) | No | MEDIUM | Prompt/agent testing and red teaming — could validate BL agent quality |
| n8n-skills | Yes (#77, 3.8K★) | No | MEDIUM | n8n workflow-building skills — relevant to automation/homelab context |
| kubeshark | Yes (#34, 11.8K★) | No | LOW-MEDIUM | K8s network observability via MCP — relevant to homelab/Proxmox context |
| context7 (upstash) | Yes (#7, 50.5K★) | YES — already active | NONE | Already in BL MCP stack |
| exa-mcp-server | Yes (#71, 4.1K★) | YES — already active | NONE | Already in BL MCP stack |
| playwright | Yes (#99, 2.1K★) | YES — already active | NONE | Already in BL MCP stack |
| github MCP | Yes (external_plugins) | YES — already active | NONE | Already in BL MCP stack |
| anthropic knowledge-work plugins | Yes (#42, 10.4K★) | No | LOW | Role-specific (sales/legal/finance/bio-research/data) — not core to BL's use case |
| financial-services-plugins | Yes (#54, 6.8K★) | No | LOW | Financial sector — not core BL use |
| Anthropic-Cybersecurity-Skills | Yes (#78, 3.7K★) | Partial | LOW | 734+ MITRE-mapped skills; /masonry-security-review covers basics |
| mgrep | Yes (#76, 3.9K★) | No | LOW | Semantic grep for code/images/PDFs locally — complements codebase search |
| visual-explainer | Yes (#52, 6.9K★) | No | LOW | Rich HTML/slide generation for diffs and plans — nice-to-have |
| HuggingFace/skills | Yes (#43, 9.9K★) | No | MEDIUM | HF ecosystem integration — relevant for ML/AI research pipelines |
| code-review-graph (MCP) | Yes (#83) | No | HIGH | See above — direct token efficiency gain for BL codebase analysis |
| chrome-devtools-mcp | Yes (#12) | No | HIGH | See above — performance profiling + advanced debugging beyond Playwright |
| second-opinion (trailofbits) | Yes (#75 sub-skill) | No | MEDIUM | Runs external LLM CLIs (Gemini/Codex) on code reviews — multi-model review |
| wt (worktrunk) | Yes (#79) | No | HIGH | See above — parallel agent worktrees |
| hindsight | Yes (#58, 6K★) | Partial (Recall covers memory) | LOW | Learning-based memory; Recall is more capable |
| VoltAgent subagents (lang specialists) | Yes (#28) | Partial (BL has language agents but not all) | MEDIUM | elixir-expert, swift-expert, rails-expert, kotlin-specialist, etc. fill language gaps |
| OpenAgentsControl | Yes (#87) | Partial | LOW | Plan-first with approval gates — BL's /build has this |
| impeccable | Yes (#32, 13.4K★) | Partial (ui-design-system skill covers design) | LOW | Design language enforcement rules |
| planning-with-files | Yes (#23, 17.2K★) | Partial (/plan does this) | LOW | Manus-style persistent markdown planning |
| claude-hud | Yes (#33, 13K★) | YES — already built (Masonry HUD in claims-board) | NONE | BL already has a HUD indicator |
| Slack MCP (external_plugins) | Yes | No | MEDIUM | Slack integration for team notifications |
| Linear MCP (external_plugins) | Yes | No | LOW | Issue tracking connector |
| Terraform MCP (external_plugins) | Yes | No | LOW | IaC management |
| Greptile MCP (external_plugins) | Yes | No | MEDIUM | AI code search across repos |
| Serena MCP (external_plugins) | Yes | No | LOW | Unknown specifics |

---

## Top 5 Recommendations

### 1. chrome-devtools-mcp (Priority: Immediate)
**Repo**: https://github.com/ChromeDevTools/chrome-devtools-mcp (31.4K★, Google official)
**Why**: Playwright handles automation but chrome-devtools-mcp adds what it lacks — performance trace analysis (LCP, CLS, INP), source-mapped console stack traces, in-depth network waterfall inspection, and `--slim` headless mode for CI. This is the Chrome DevTools team's official MCP. Complementary to Playwright, not a replacement.
**Install**:
```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    }
  }
}
```

### 2. code-review-graph (Priority: Immediate)
**Repo**: https://github.com/tirth8205/code-review-graph (3.5K★)
**Why**: BrickLayer's agents currently read files broadly. This builds a Tree-sitter AST knowledge graph of the codebase, tracks blast radius (which callers/dependents/tests are affected by a change), and gives Claude precisely the minimal file set needed. Claims 6.8x fewer tokens on reviews, 49x on daily coding tasks. Incremental updates in <2 seconds via git hook. Supports 18 languages including Python, JS/TS, Rust, Go, Kotlin. Direct win for every /build and /verify cycle.
**Install**: `pip install code-review-graph && code-review-graph install && code-review-graph build`

### 3. worktrunk (Priority: High)
**Repo**: https://github.com/max-sixty/worktrunk (3.7K★)
**Why**: Tim explicitly runs Claude Code on multiple machines simultaneously. Worktrunk is a Rust CLI that makes git worktrees as easy as branches — `wt switch -c -x claude feat` creates a worktree + starts Claude in one command. Supports hooks (dev server per worktree, auto port allocation), LLM commit messages, interactive picker with live diff preview. Purpose-built for parallel AI agent workflows. Directly addresses BL's multi-session pattern.
**Install**: `cargo install worktrunk`

### 4. wshobson/agents (plugin-eval + agent-teams) (Priority: High)
**Repo**: https://github.com/wshobson/agents (32.2K★)
**Why**: Two sub-plugins are directly additive to BrickLayer. `plugin-eval` provides a 3-layer evaluation framework (static analysis → LLM judge → Monte Carlo simulation) with 10 quality dimensions and Elo ranking — this could formally score BL's fleet agents. `agent-teams` gives 7 preset parallel team configurations (review/debug/feature/fullstack/research/security/migration) that Mortar could dispatch. Both complement BL's agent optimization loop.
**Install**: `/plugin marketplace add wshobson/agents` then `/plugin install plugin-eval@claude-code-workflows`

### 5. trailofbits/skills (differential-review + second-opinion + semgrep-rule-creator) (Priority: Medium)
**Repo**: https://github.com/trailofbits/skills (3.9K★)
**Why**: Three specific skills fill real BL gaps. `differential-review` does security-focused git diff analysis with history context — runs automatically on every PR. `second-opinion` invokes Gemini CLI or Codex CLI on code changes for multi-model review validation. `semgrep-rule-creator` enables custom vulnerability detection rules for BL codebases. Trail of Bits is a top security firm — these are battle-tested.
**Install**: `/plugin marketplace add trailofbits/skills`

---

## Harvestable Items

### MCPs to add immediately

1. **Add chrome-devtools-mcp to settings.json** — Chrome DevTools inspection, performance tracing, source-mapped debugging. Complement to existing Playwright MCP.

2. **Add code-review-graph MCP** — AST-based codebase knowledge graph, incremental blast-radius analysis. Direct token efficiency gain for all BL build/verify cycles.

3. **Add repomix** (`npx repomix`) — Pack entire repo into single AI-friendly file for feeding to Claude in research campaigns. No MCP needed, pure CLI.

4. **Add greptile MCP** (external_plugins in official Anthropic directory) — AI-powered code search across multiple repos, useful for cross-project research.

5. **Add n8n-skills** — n8n workflow building skills; relevant to Tim's homelab automation context.

### Skills/patterns to harvest into BL agents

6. **Karpathy 4 principles from andrej-karpathy-skills** — Extract into CLAUDE.md or inject into developer/code-reviewer agents: (1) State assumptions explicitly, (2) Simplicity first, (3) Surgical changes, (4) Goal-driven with success criteria.

7. **Superpowers systematic-debugging skill** — 4-phase root cause process (reproduce→isolate→hypothesize→verify) — inject into BL's diagnose-analyst agent.

8. **everything-claude-code harness commands** — `/loop-start`, `/loop-status`, `/quality-gate`, `/model-route` as BL skills. The harness audit scoring concept maps directly to BL's agent eval pipeline.

9. **wshobson/agents conductor workflow** — Context→Spec→Implement with `/conductor:setup`, `/conductor:new-track`, `/conductor:revert` — consider adding track-based reversible development to BL's /build.

10. **worktrunk parallel workflow pattern** — Add a BL skill `/parallel-build` that uses git worktrees to run multiple /build tasks concurrently across separate worktree directories.

### Subagents to consider adding to BL fleet

11. **VoltAgent elixir-expert** — Fills language gap (Elixir/OTP fault-tolerant systems)
12. **VoltAgent swift-expert** — Fills language gap (iOS/macOS)
13. **VoltAgent rails-expert** — Fills language gap (Rails 8.1)
14. **VoltAgent chaos-engineer** — System resilience testing; useful for stress-testing BL simulation invariants
15. **VoltAgent terragrunt-expert** — IaC orchestration beyond basic terraform
16. **trailofbits semgrep-rule-creator** — Custom vulnerability scanning rules for BL-built codebases
17. **trailofbits second-opinion** — Multi-model (Gemini/Codex) code review validation

### Novel patterns to study

18. **plugin-eval framework (wshobson)** — Apply the 3-layer evaluation (static→LLM judge→Monte Carlo) to BL's agent optimization loop instead of current heuristic-only scoring.

19. **Ralph fresh-context loop pattern** — Each Ralph iteration spawns a fresh Claude instance reading only `progress.txt` + `prd.json`. Could apply to long BL campaigns to prevent context decay.

20. **code-review-graph blast-radius** — The concept of computing "which files are affected by this change" via AST traversal could inform BL's masonry-observe hook to trigger more targeted question generation.

21. **everything-claude-code instinct system** — Skills with confidence scoring + import/export + evolution loop. BL's agent optimization uses DSPy-style eval; ECC's instinct system is a complementary continuous-learning approach.

---

## Novel Plugin Patterns Observed

- **Progressive disclosure for skills**: Skills load detailed knowledge only when activated, not at session start. Reduces baseline token cost while preserving full capability depth. (wshobson pattern)
- **Monte Carlo plugin evaluation**: Statistical quality scoring with Wilson score CI, bootstrap CI, Clopper-Pearson exact CI, and Elo ranking — far beyond simple LLM-judge eval. (wshobson/plugin-eval)
- **Blast-radius context injection**: Instead of "read all files," compute the AST dependency graph and give Claude only the files in the change's blast radius. (code-review-graph)
- **Fresh-context loops**: Autonomous loops where each iteration spawns a fresh agent with clean context, with only state files as continuity. Prevents context decay on long runs. (Ralph pattern)
- **Worktree-per-agent**: Git worktrees give each parallel agent a separate working directory. Combined with a worktree manager (worktrunk) this becomes practical. (Worktrunk + superpowers/using-git-worktrees)
- **Multi-model second opinion**: Routing the same code diff through Gemini and Codex for independent review, then synthesizing. (trailofbits/second-opinion)
- **Semantic track-based development with revert**: Breaking work into "tracks" with semantic revert (undo a whole track, not just a commit). (wshobson/conductor)
- **Harness audit scoring**: Deterministic scoring of the AI harness itself (hook coverage, agent quality, skill depth) as a CI gate. (everything-claude-code/harness-audit)

---

```json
{
  "repo": "quemsah/awesome-claude-plugins",
  "report_path": "docs/repo-research/quemsah-awesome-claude-plugins.md",
  "files_analyzed": 24,
  "repos_cataloged": 100,
  "total_repos_indexed": 9094,
  "plugins_found": 557,
  "high_priority_gaps": 4,
  "top_recommendation": "chrome-devtools-mcp + code-review-graph — both fill capability gaps not covered by existing Playwright MCP and directly improve BL build/verify efficiency",
  "verdict": "High-value discovery resource. Not a plugin itself — a live-indexed catalog of 9,094 repos sorted by quality signal. Top 20 entries contain ~5 items worth immediate integration into BrickLayer's MCP stack, plus ~15 skills/patterns worth harvesting into agent prompts. The biggest gaps are: Chrome DevTools inspection (30K+ stars, Google official), AST codebase knowledge graph for token efficiency, parallel worktree management for multi-session workflows, and the plugin-eval quality framework for formal agent scoring."
}
```
