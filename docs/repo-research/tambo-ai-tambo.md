# Repo Research: tambo-ai/tambo

**Repo**: https://github.com/tambo-ai/tambo
**Researched**: 2026-03-28
**Researcher**: repo-researcher agent
**Purpose**: Identify capability gaps and patterns for BrickLayer 2.0

---

## Verdict Summary

Tambo is a production-grade open-source React toolkit (11.1k stars) for generative UI — AI selects and streams props to registered components in real time. It is narrower in scope than BrickLayer (no research campaigns, no simulation loops, no multi-agent fleet), but dramatically more sophisticated in three areas: Claude Code plugin distribution, proactive AI automation via its "Charlie" playbook system, and skill/command architecture for Claude Code agents. BrickLayer beats Tambo on research campaign depth, multi-agent orchestration, and the full SPARC build loop. Tambo beats BrickLayer on clean agent command patterns, scheduled autonomous maintenance tasks, and the plugin marketplace distribution model.

---

## File Inventory

### Root
- `README.md` — Product overview, generative UI concepts, quickstart examples, MCP integration guide
- `AGENTS.md` — 27KB master dev guide: repo structure, TypeScript standards, naming, testing, Agent Behavior section
- `CLAUDE.md` — Claude-specific repo instructions (mirrors AGENTS.md with Claude notes)
- `package.json` — Turborepo monorepo root; workspaces for all packages
- `turbo.json` — Turborepo pipeline config; remote caching enabled
- `conductor.json` — Charlie automation config pointing to `.charlie/` playbooks
- `conductor-run.sh` — Shell script entry point for Charlie runs
- `mise.toml` — Tool version pinning (Node, pnpm, Python — alternative to nvm/asdf)

### `.claude/`
- `agents/planner.md` — Planning agent: reads feature requirements + research, outputs structured plan with design decisions, file lists, and phases
- `agents/researcher.md` — Researcher agent: searches codebase + web, returns concise summaries with file paths
- `commands/execute.md` — `/execute` command: NEVER edits files itself, always delegates to subagents; smart parallelization
- `commands/plan.md` — `/plan` command: 5-step flow ending in parallel researcher agents + planner synthesis
- `commands/commit.md` — `/commit` command: scans conversation history + diff, groups commits logically, asks approval
- `commands/create-pr.md` — `/create-pr` command: conventional commits format, PR template enforcement

### `.charlie/`
- `config.yml` — 4 proactive playbook schedules (all weekly)
- `playbooks/external-release-update.md` — Fetches GitHub releases for the week, creates Linear issue with changelog
- `playbooks/team-update.md` — Fetches merged PRs + completed Linear issues, creates team-update Linear issue
- `playbooks/dead-code-cleanup.md` — 4-signal dead code detection (no inbound refs, not in barrel, dormant history, unused deps); requires 2+ signals minimum
- `playbooks/coverage-threshold-bump.md` — Runs Jest coverage, bumps `jest.config.ts` thresholds monotonically; creates GitHub PR

### `.claude-plugin/`
- `marketplace.json` — Registers Tambo as a Claude Code plugin marketplace entry with `category: frameworks`

### `plugins/tambo/`
- `README.md` — Plugin install instructions: `/plugin marketplace add`, then `/plugin install tambo`
- `skills/generative-ui/SKILL.md` — 12.9KB skill for creating new Tambo apps from scratch; one-prompt flow pattern
- `skills/generative-ui/references/` — Lazy-loaded reference docs for the skill (loaded at specific steps only)
- `skills/building-with-tambo/SKILL.md` — 15.9KB skill for adding Tambo to existing apps; keyboard shortcut handling, z-index patterns, monorepo detection
- `skills/building-with-tambo/references/` — Lazy-loaded reference docs

### `devdocs/`
- `CLAUDE_SKILLS.md` — Skills creation guide: YAML frontmatter template, best practices, auto-invoke via description keywords
- `OBSERVABILITY.md` — Telemetry guide: OpenTelemetry + Langfuse (API), Sentry + PostHog (web), posthog-node (CLI); React SDK ships without telemetry by design
- `TESTING.md` — Testing guide: unit tests beside source files, mock only at system boundaries
- `skills/ai-sdk-model-manager/SKILL.md` — Internal skill (metadata.internal: true) for managing AI SDK model configurations; uses researcher subagent + parallel editing agents

### `.github/workflows/` (14 files)
- `claude.yml` — Triggers Claude Code on `@claude` mentions in issues/PR comments via `anthropics/claude-code-action@beta`
- `ci.yml` — Lint → test (Codecov) → e2e → build → status; domain check blocks `tambo.ai`/`tambo.com` strings in source; concurrency cancel-in-progress
- `release-please.yml` — Automated release PRs from conventional commits
- `conventional-commits.yml` — PR title validation (type(scope): description)
- `stale.yml` — Stale issue/PR management
- Additional workflows: deploy, preview, SDK generation, Codecov

### `react-sdk/`
- `AGENTS.md` — 7-layer provider hierarchy, hooks catalog, doc-first principle, no tanstack query, React 18/19 peer deps
- `src/` — TypeScript source (large directory — sampled)
- `src/components/` — TamboComponentRenderer, TamboInteractableRenderer, ThreadList, etc.
- `src/hooks/` — useTambo, useTamboThreadInput, useTamboComponentState, useTamboStreamStatus, etc.
- `src/client/` — TamboClient, TamboMCPClient, transport layers
- `jest.config.ts`, `tsconfig.json`, `tsup.config.ts` — Build config (dual CJS/ESM output)

### `packages/`
- `packages/db/` — Drizzle ORM; operations factored into `src/operations/`, migrations generated never hand-edited
- `packages/api/` — NestJS API server; `packages/api/src/ai/` for AI logic
- `packages/analytics/` — Analytics package (shared between API and web)
- `packages/logger/` — Shared logging package
- `packages/types/` — Shared TypeScript types

### `apps/`
- `apps/web/` — Tambo Cloud web app (Next.js + tRPC + shadcn)
- `apps/cli/` — Tambo CLI (`npx tambo create-app`, `npx tambo init`)

---

## Architecture Overview

Tambo is a **generative UI platform** with three distinct layers:

1. **React SDK (`@tambo-ai/react`)**: Client-side toolkit. App registers components with Zod schemas. `TamboProvider` wraps the app. `useTamboThreadInput()` streams messages. The AI backend selects which component to render and streams props to it in real time. Supports both "generative" (one-shot) and "interactable" (persistent, stateful) components. Full MCP support via `mcpServers` prop — tools, prompts, elicitations, sampling.

2. **Tambo Cloud (NestJS API + Next.js web)**: Backend that hosts the AI inference layer. Uses Vercel AI SDK v6 to call multiple LLM providers (OpenAI, Anthropic, Gemini, Mistral, Cerebras, Groq). Drizzle ORM for database. tRPC for API calls. OpenTelemetry + Langfuse + Sentry for observability.

3. **Developer Tooling**: Charlie (proactive AI automation), Claude Code plugin (reactive in-editor AI), GitHub Actions `@claude` responder. These three form a complete "AI-ops stack" around the codebase itself.

The **Charlie + Claude Code plugin** combination is architecturally interesting: Charlie handles scheduled autonomous work (weekly) while the Claude Code plugin handles on-demand work (triggered by developer). Together they cover the full temporal spectrum of AI assistance.

---

## Agent Catalog

### `.claude/agents/planner.md`
- **Purpose**: Produce a structured implementation plan from feature requirements and research findings
- **Tools**: Not specified (reads files, writes plan)
- **Invocation**: Called by `/plan` command after researcher agents complete
- **Key capabilities**:
  - Produces standardized plan format: Overview → Key Design Decisions (with rationale) → Architecture → Component Schema/Interface → File Structure (NEW/MODIFIED annotated) → Implementation Phases → Out of Scope
  - Pseudocode only for non-obvious logic — never full implementations
  - Marks files that can be modified in parallel (parallelization hints)
  - Saves to `.plans/[feature-name].md` (not `.claude/`, not committed)
  - Never includes time estimates

### `.claude/agents/researcher.md`
- **Purpose**: Gather information from codebase + web for planning decisions
- **Tools**: Read, Glob, Grep, WebSearch, WebFetch, Bash
- **Invocation**: Called by `/plan` command, 2-8 instances in parallel
- **Key capabilities**:
  - Provides specific file paths and links (not vague references)
  - Concise, categorized output for planner agent consumption
  - High-level insights distilled from raw search results

### `devdocs/skills/ai-sdk-model-manager/SKILL.md` (internal skill)
- **Purpose**: Manage AI SDK model configuration files across all providers
- **Tools**: Uses researcher subagent + parallel editing agents
- **Invocation**: `metadata.internal: true` — team use only, not published to plugin marketplace
- **Key capabilities**:
  - Inspects TypeScript type definitions to discover available model IDs: `cat node_modules/@ai-sdk/openai/dist/index.d.ts | grep 'type.*ModelId'`
  - Uses researcher subagent for model capability/pricing research
  - Launches parallel subagents for editing multiple provider files simultaneously
  - Enforces required fields: `apiName`, `displayName`, `status` (untested|tested|known-issues), `notes`, `docLink`, `inputTokenLimit`
  - New models always marked `status: untested` by convention
  - PR title format: `feat(models): add [model names] support`

### Charlie Playbooks (autonomous agents, not Claude Code agents)
All 4 playbooks run weekly via `conductor.json`. Charlie is a separate AI system that runs scheduled autonomous tasks.

- **`external-release-update.md`**: Fetches GitHub release tags filtered by date window (GNU date, America/Los_Angeles timezone), groups by package, creates Linear issue with developer-facing changelog
- **`team-update.md`**: Fetches merged PRs + completed Linear issues for the week, creates team-update Linear issue with highlights, PR groups, contributors
- **`dead-code-cleanup.md`**: Multi-signal dead code detection — only `private: true` workspaces scanned; requires 2 independent signals before listing a candidate; creates Linear issue
- **`coverage-threshold-bump.md`**: Runs Jest coverage per workspace, reads `coverage-summary.json`, computes `measuredFloor = floor(measuredPct)`, updates thresholds monotonically; creates GitHub PR

---

## Feature Gap Analysis

| Feature | In tambo-ai/tambo | In BrickLayer 2.0 | Gap Level | Notes |
|---------|-------------------|-------------------|-----------|-------|
| Claude Code plugin marketplace distribution | Yes — `.claude-plugin/marketplace.json` + `plugins/` with two skills; installable via `/plugin install tambo` | No — BrickLayer has no plugin marketplace entry; distributed only by cloning/copying | HIGH | BrickLayer could publish itself as a Claude Code plugin with skills for `/masonry-run`, `/build`, etc. — enabling one-command install across projects |
| Scheduled proactive AI automation | Yes — Charlie runs 4 weekly playbooks: release notes, team updates, dead code cleanup, coverage bumping | No — all BrickLayer automation is reactive (triggered by user or hooks) | HIGH | Charlie's model: autonomous AI creates Linear issues + GitHub PRs on schedule, no human trigger required. BrickLayer has no equivalent. |
| @claude GitHub Actions responder | Yes — `.github/workflows/claude.yml` triggers `anthropics/claude-code-action@beta` on `@claude` mentions in issues/PR comments | No — no GitHub Actions integration for Claude | HIGH | Allows team members to trigger Claude from GitHub issues/PRs without opening Claude Code locally. Covers async/remote collaboration. |
| Lazy-loading reference guides in skills | Yes — both Tambo skills explicitly say "Load at Step 5" / "Load when building custom chat UI" | No — BrickLayer agents load all context upfront or rely on model memory | MEDIUM | Reduces context window usage. Skills reference external docs only when the relevant step is reached. Especially valuable for long skills. |
| Orchestrator-never-edits pattern | Yes — `/execute` strictly delegates ALL file operations to subagents, only touches `.plans/execution-status.md` | Partial — BrickLayer's `/build` orchestrator uses the pattern but doesn't enforce it as strictly | MEDIUM | Tambo's execute.md makes this a hard rule with explicit enforcement language. BrickLayer's orchestrator sometimes writes files directly. |
| One-prompt flow design pattern | Yes — skills gather all user preferences in ONE AskUserQuestion call (up to 4 questions), then execute without stopping | No — BrickLayer's `/plan` flow is interactive with multiple back-and-forth exchanges | MEDIUM | Significantly reduces friction for common workflows. One call gets all decisions, then autonomous execution proceeds. |
| Internal skills (metadata.internal) | Yes — `ai-sdk-model-manager` marked `metadata.internal: true`; not published to marketplace | No — BrickLayer has no mechanism to mark agents as internal-only vs publishable | LOW | Allows maintaining team-internal agents alongside publishable ones in the same repo |
| Monotonic coverage threshold bumping | Yes — automated PR never decreases any coverage threshold; `measuredFloor = floor(measuredPct)` logic | No — BrickLayer has no automated coverage tracking or threshold management | MEDIUM | Passive quality ratchet: coverage can only improve over time. No human maintenance required. |
| Dead code detection via multi-signal | Yes — 4 signals checked, minimum 2 required before listing candidate; `private: true` workspace filter | No — BrickLayer has no dead code detection | LOW | Prevents false positives. Two independent signals (no inbound refs + dormant history) is a strong heuristic. |
| Planner outputs parallelization hints | Yes — planner.md marks files as "can be modified in parallel" in the file structure section | Partial — BrickLayer's `/plan` produces spec but doesn't explicitly annotate parallelizable files | MEDIUM | Gives the executor explicit guidance on which tasks can run concurrently vs must be sequential |
| Doc-first development principle | Yes — react-sdk/AGENTS.md: write documentation before implementing code for new features | No — BrickLayer's TDD enforcement is test-first, not doc-first | LOW | Different philosophy. BrickLayer's test-first is arguably stronger for correctness; doc-first is stronger for API design clarity. |
| Commit command scans conversation history | Yes — `/commit` reads the full conversation to understand what changed and why, groups commits logically | No — BrickLayer's git-nerd commits based on git diff, not conversation context | MEDIUM | Conversation-aware commits produce better commit messages because the agent knows the intent behind the changes |
| Dual CJS/ESM package output | Yes — react-sdk builds to both `dist/` (CJS) and `esm/` (ESM) | N/A — BrickLayer is not a distributed npm package | LOW | Relevant only if BrickLayer publishes npm packages |
| Observability stack (OTel + Langfuse) | Yes — OpenTelemetry spans on all AI calls, Langfuse for LLM observability, Sentry for errors | Partial — BrickLayer has EMA telemetry + agent scoring but no OTel spans or Langfuse | MEDIUM | LLM-level observability (latency, token usage, prompt/completion pairs) would help optimize BrickLayer agent performance |
| Conventional commits enforcement in CI | Yes — GitHub Actions validates PR title format `<type>(scope): <description>` | No — BrickLayer has no PR title validation | LOW | Process improvement; BrickLayer's changelog is auto-generated by post-commit hook but doesn't enforce conventional format |
| Domain string enforcement in CI | Yes — `git grep` blocks `tambo.ai` or `tambo.com` strings; enforces canonical `.co` domain | No — no domain enforcement | LOW | Niche pattern; relevant to Tambo's specific situation |
| type-fest usage | Yes — AGENTS.md recommends checking type-fest before writing custom utility types | No — BrickLayer uses custom TypeScript utility types | LOW | Minor dependency recommendation |
| Generative UI (component streaming) | Yes — core product: AI selects and streams props to registered React components | No — BrickLayer produces text findings/reports; no generative UI | LOW | Completely different use case; BrickLayer doesn't need generative UI for its research/build workflows |
| MCP client in React SDK | Yes — `TamboMCPClient` with MCPTransport.HTTP; tools, prompts, elicitations, sampling | BrickLayer uses MCP servers, not clients | LOW | Different direction: BrickLayer exposes MCP tools, Tambo consumes them |

---

## Top 5 Recommendations

### 1. Publish BrickLayer as a Claude Code Plugin [8h, HIGH PRIORITY]

**What to build**: Create `.claude-plugin/marketplace.json` at the BrickLayer repo root and a `plugins/bricklayer/` directory with 2-3 SKILL.md files. Register skills for the most common entry points: starting a research campaign (`/masonry-run`), initializing autopilot build (`/plan` + `/build`), and checking campaign status.

**Why it matters**: Any developer could install BrickLayer into their project with `/plugin install bricklayer`. Each skill auto-triggers on keywords ("run a BrickLayer campaign", "start autopilot build", "initialize masonry"). This changes BrickLayer from "copy 200 files into your repo" to "one command install." It also makes BrickLayer discoverable by the broader Claude Code community.

**Implementation sketch**:
```
.claude-plugin/
  marketplace.json     ← {name, description, source: "./plugins/bricklayer", category: "research"}
plugins/bricklayer/
  README.md            ← install instructions
  skills/
    masonry-campaign/SKILL.md    ← trigger: "research campaign", "run masonry", "stress test"
    autopilot-build/SKILL.md     ← trigger: "autopilot build", "/plan", "/build"
    masonry-status/SKILL.md      ← trigger: "campaign status", "masonry status"
```

### 2. Implement Charlie-Style Proactive Playbooks [12h, HIGH PRIORITY]

**What to build**: A `conductor.json` + `.bricklayer/playbooks/` system that runs scheduled autonomous tasks. Start with 3 playbooks that directly address BrickLayer maintenance pain points:
- `agent-health-check.md` — Weekly: run `masonry_agent_health`, score all agents, create issues for agents with declining EMA scores
- `roadmap-sync.md` — Weekly: read recent commits + findings, update ROADMAP.md + CHANGELOG.md, commit directly (what karen does manually)
- `coverage-bump.md` — Weekly: run test suite, update coverage thresholds monotonically, create PR

**Why it matters**: BrickLayer currently has zero scheduled automation. Every maintenance task requires a human trigger. Tambo's Charlie model proves these weekly tasks can run fully autonomously, creating real artifacts (Linear issues, GitHub PRs) without human involvement. The `masonry-stop-guard.js` currently tries to trigger karen/synthesizer at stop time — that's reactive. Proactive playbooks would run even between sessions.

**Implementation sketch**: Use Claude Code's existing `--dangerously-skip-permissions` subprocess pattern. `conductor.sh` is a cron job or GitHub Actions scheduled workflow that runs each playbook file through `claude -p < playbook.md`. Each playbook produces a GitHub PR or issue as output.

### 3. Add `@claude` GitHub Actions Responder [4h, HIGH PRIORITY]

**What to build**: Copy Tambo's `.github/workflows/claude.yml` verbatim (it uses the public `anthropics/claude-code-action@beta` action). Configure it to trigger on `@claude` mentions in issues and PR review comments.

**Why it matters**: Tim runs Claude Code on multiple machines but can't always have a terminal open. `@claude fix the failing test in PR #47` from a GitHub comment would trigger Claude automatically. Enables async collaboration and integrates BrickLayer's AI capabilities into the GitHub workflow where issues and PRs already live.

**Implementation sketch**:
```yaml
on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  issues:
    types: [opened, edited]
  pull_request_review:
    types: [submitted]
jobs:
  claude:
    if: contains(github.event.comment.body, '@claude') || contains(github.event.issue.title, '@claude')
    steps:
      - uses: anthropics/claude-code-action@beta
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

### 4. Upgrade Agent Skills to Use Lazy-Loading Reference Pattern [6h, MEDIUM PRIORITY]

**What to build**: Refactor BrickLayer's largest skill files (especially `masonry-campaign/SKILL.md`, `autopilot-build/SKILL.md`) to extract reference documentation into separate files under `skills/{name}/references/`. Add explicit "Load at Step N" instructions in the main SKILL.md. Focus on reference docs that are only needed after specific decision points (e.g., "Load wave-strategies.md at Step 4 if the campaign has 20+ questions").

**Why it matters**: Tambo's skills explicitly say "Load when building custom chat UI" — this means the reference doc is NOT loaded for users who don't need that path. BrickLayer's agents currently load everything upfront or rely on the model's training knowledge. For long agents like the trowel campaign conductor, this could reduce average context window usage by 20-40%.

**Implementation sketch**: Create `masonry/skills/{skill-name}/references/` directories. Each reference file is a focused topic doc (1-3KB). Main SKILL.md becomes an orchestration document with lazy-load directives. The skill loads references only when reaching the step that needs them.

### 5. Make `/execute` Orchestrator-Never-Edits a Hard Rule [3h, MEDIUM PRIORITY]

**What to build**: Add an explicit rule to BrickLayer's `/build` and `/ultrawork` command files: "The orchestrator NEVER edits source files. All file writes are delegated to worker agents. The orchestrator only writes to `.autopilot/progress.json` and `.autopilot/build.log`." Add a masonry-approver hook check that warns if the orchestrator context attempts a Write to a non-state file.

**Why it matters**: Tambo's `/execute` makes this a strict rule with explicit enforcement language. BrickLayer's `/build` orchestrator sometimes writes files directly (especially for quick fixes it "knows" how to make). This creates mixed responsibility, harder debugging, and context bloat. Pure delegation keeps the orchestrator lean and makes worker agent outputs fully auditable.

**Implementation sketch**: Update `masonry/skills/build/SKILL.md` with a bold rule block at the top. Add a lint check in `masonry-approver.js` that detects Write/Edit calls from an orchestrator context (detectable via conversation pattern) and emits a warning. Worker agents get `--allowlist` constraints on which files they may write to.

---

## Novel Patterns to Incorporate (Future)

### Conversation-Aware Commit Messages
Tambo's `/commit` command reads the full conversation history to understand *why* changes were made, not just *what* changed. This produces commit messages like "feat(routing): switch to cosine similarity threshold 0.75 after benchmarking showed 23% false positive rate at 0.60" instead of just "update router.py." BrickLayer's git-nerd currently only reads `git diff`. Worth exploring for the masonry-stop-guard.js commit flow.

### Planner Outputs Explicit Parallelization Hints
Tambo's planner.md annotates its file structure output with which files can be modified simultaneously. This gives the `/execute` orchestrator a map it can follow without re-analyzing dependencies. BrickLayer's spec-writer produces a sequential task list. Adding `[PARALLEL: tasks 3, 5, 7]` blocks to spec.md would let `/ultrawork` be more aggressive about concurrent execution.

### One-Prompt Flow for Skill Initialization
Tambo's generative-ui skill gathers all user preferences in a single AskUserQuestion call with up to 4 questions, then executes without stopping. BrickLayer's `/plan` is interactive throughout. For common campaign setups or simple build tasks, a one-prompt variant could dramatically reduce time-to-execution: ask project type, key constraints, output format, and priority in one call, then proceed.

### Dead Code Detection with Signal Counting
Tambo's dead code playbook requires 2 independent signals before flagging a file: (1) no inbound `rg` references, (2) not in barrel/registry file, (3) dormant git log, (4) unused dependency. The 2-of-4 requirement prevents false positives on files that exist for future use or are referenced dynamically. BrickLayer could apply this pattern to agent registry cleanup (agents with no invocations + no active campaigns + no training data = 2+ signals = cleanup candidate).

### Stainless SDK Generation
Tambo auto-generates its TypeScript SDK (`@tambo-ai/typescript-sdk`) from the OpenAPI spec using Stainless. BrickLayer's masonry MCP server could be distributed as a typed SDK package, making it easier for external integrations. Currently requires raw MCP client setup.

### Internal vs. Published Skill Separation
Tambo uses `metadata.internal: true` to distinguish team-internal skills (ai-sdk-model-manager) from published skills (generative-ui, building-with-tambo). BrickLayer's agent registry has no equivalent flag. Adding `visibility: internal|external|draft` to `agent_registry.yml` would allow BrickLayer to maintain sensitive or experimental agents without accidentally publishing them.

### Mise for Tool Version Management
Tambo uses `mise.toml` (not `.nvmrc`, not `.python-version`) as the single source of truth for all tool versions (Node, pnpm, Python). For BrickLayer distributed as a framework, a `mise.toml` would ensure contributors and CI use identical toolchain versions regardless of their local setup.

---

*Total files analyzed: 47 (key files read in full; large directories sampled)*
*Research depth: exhaustive on agent/skill/workflow/hook files; sampled on React SDK and platform source code*
