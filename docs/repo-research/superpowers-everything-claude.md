# superpowers + everything-claude-code Analysis

**Repos**: https://github.com/obra/superpowers | https://github.com/affaan-m/everything-claude-code
**Researched**: 2026-03-28
**Researcher**: repo-researcher agent
**Purpose**: Identify capability gaps and patterns for BrickLayer 2.0

---

## obra/superpowers

### What it is

Superpowers is a composable skills framework for agentic software development, distributed as a Claude Code plugin (also supports Cursor, Codex, OpenCode, Gemini CLI). The core concept is a skills library where each "skill" is a SKILL.md file with frontmatter (`name`, `description`) that Claude reads automatically. The session-start hook injects the `using-superpowers` index into every session, which tells the agent which skills exist and when to invoke them. Skills are not manually called — the agent recognizes when it's doing something a skill covers and triggers it automatically.

The workflow is: brainstorm (Socratic design + spec) → writing-plans (implementation blueprint with TDD steps) → subagent-driven-development or executing-plans (dispatch per task) → two-stage review per task (spec compliance, then code quality) → finishing-a-development-branch.

### Key files/structure

```
skills/
  brainstorming/SKILL.md                    — Hard-gated design phase before any code
  brainstorming/visual-companion.md         — Browser-based visual mockup companion
  brainstorming/spec-document-reviewer-prompt.md
  writing-plans/SKILL.md                    — Blueprint with exact code, paths, commands
  writing-plans/plan-document-reviewer-prompt.md
  subagent-driven-development/SKILL.md      — Per-task subagent dispatch + two-stage review
  subagent-driven-development/implementer-prompt.md
  subagent-driven-development/spec-reviewer-prompt.md
  subagent-driven-development/code-quality-reviewer-prompt.md
  systematic-debugging/SKILL.md             — 4-phase root-cause-first debugging protocol
  systematic-debugging/root-cause-tracing.md
  systematic-debugging/defense-in-depth.md
  systematic-debugging/condition-based-waiting.md
  systematic-debugging/find-polluter.sh     — Bisect test pollution script
  test-driven-development/SKILL.md          — RED-GREEN-REFACTOR enforcement
  executing-plans/SKILL.md                  — Batch execution with human checkpoints
  dispatching-parallel-agents/SKILL.md      — Concurrent subagent workflows
  requesting-code-review/SKILL.md           — Pre-review checklist
  receiving-code-review/SKILL.md            — Responding to feedback
  using-git-worktrees/SKILL.md              — Isolated branch per feature
  finishing-a-development-branch/SKILL.md   — Merge/PR decision workflow
  verification-before-completion/SKILL.md   — Verify before declaring done
  writing-skills/SKILL.md                   — Meta-skill for creating new skills
  using-superpowers/SKILL.md                — Index injected at session start
hooks/
  session-start                             — Bash script: inject using-superpowers into session
  hooks.json                                — Minimal: SessionStart only
  run-hook.cmd                              — Windows compatibility wrapper
agents/                                     — Empty (no agents defined — skills only)
commands/                                   — Empty (no slash commands defined)
docs/                                       — Platform-specific install docs
.claude-plugin/                             — Plugin manifest
.cursor-plugin/, .codex/, .opencode/        — Multi-platform install configs
```

### Novel patterns vs BrickLayer

**1. Hard-gated brainstorming with SPEC_FIRST invariant**

The brainstorming SKILL.md has an explicit `<HARD-GATE>` block:
> "Do NOT invoke any implementation skill, write any code, scaffold any project, or take any implementation action until you have presented a design and the user has approved it. This applies to EVERY project regardless of perceived simplicity."

BrickLayer has `/plan` which writes a spec, but the hard-gate pattern — enforced in the prompt itself with a special XML tag — is more explicit. The spec is also written to a dated file (`docs/superpowers/specs/YYYY-MM-DD-topic-design.md`), self-reviewed inline by the agent, and then user-reviewed before any plan is written. BrickLayer's `/plan` skill does the spec but doesn't have the explicit anti-pattern enforcement or the self-review phase before user handoff.

**2. Two-stage per-task review (spec compliance first, then code quality)**

The subagent-driven-development skill enforces a strict ordering:
1. Implementer subagent completes task → self-review → commit
2. Spec compliance reviewer subagent: confirms nothing is missing or extra
3. Code quality reviewer subagent: confirms implementation is well-built
4. If either fails: implementer fixes → re-review (repeat until both pass)
5. Only then: mark task DONE and move to next task

BrickLayer has code-reviewer after every developer task but does not have a separate "spec compliance" gate that explicitly checks for over-building (added features not in spec) and under-building (missing features from spec). The sequential ordering — spec compliance must pass before quality review even starts — is novel.

**3. Explicit model selection by task complexity within a build loop**

The subagent-driven-development skill documents an explicit cost-optimization model selection policy:
- Mechanical tasks (1-2 files, clear spec): cheap model (Haiku)
- Integration/multi-file tasks: standard model (Sonnet)
- Architecture/review: most capable model (Opus)

BrickLayer passes `model` to subagents but does not have a documented policy for dynamically selecting model tier based on task complexity signals at dispatch time.

**4. Writing-plans blueprint format (complete code in every step, no placeholders)**

The writing-plans skill enforces that every task step contains exact file paths, complete runnable code, exact test commands with expected output, and commit commands. It explicitly bans placeholders ("TBD", "similar to Task N", "add appropriate error handling") and requires every test be written out in full even if similar to a prior task (since the engineer may read tasks out of order).

BrickLayer's spec-writer produces a spec, not a step-by-step implementation blueprint. The plan format in superpowers is significantly more prescriptive — it's designed so a context-isolated subagent can execute each task without any codebase knowledge beyond what the plan provides.

**5. Socratic design exploration with visual companion**

The brainstorming skill offers a browser-based "visual companion" for questions involving mockups, wireframes, layout comparisons, and architecture diagrams. The agent decides per-question whether to use the browser or terminal based on whether the user would understand it better visually vs. reading text. This is offered with explicit consent before use.

BrickLayer has no equivalent interactive design exploration phase. The `/plan` skill writes a spec but does not explore alternatives, propose 2-3 approaches with trade-offs, or offer visual companions.

**6. Systematic debugging with architectural escalation gate**

The systematic-debugging skill has a documented "3+ fixes failed = question the architecture" protocol. After 3 failed fix attempts, the agent is required to stop and discuss whether the architecture is wrong rather than attempting a 4th fix. It also ships a `find-polluter.sh` script for bisecting test pollution (finding which test in a suite causes another to fail).

BrickLayer has diagnose-analyst and fix-implementer which handle escalation, but the 3-fix architectural gate is not explicitly documented as a hard rule. The test pollution bisect script is not present.

**7. Condition-based waiting pattern (anti-sleep)**

The `systematic-debugging/condition-based-waiting.md` file documents a specific pattern for replacing `sleep(N)` with condition polling loops in tests and scripts. This is a specific technique reference that can be injected into debugging context.

**8. Spec self-review (inline, not a subagent)**

After writing the spec document, the brainstorming skill instructs the agent to self-review inline for: placeholder scan, internal consistency, scope check, and ambiguity check. This is done in the main session, not dispatched to a subagent, and any issues are fixed immediately. BrickLayer's spec-writer does not have a documented self-review phase.

**9. Git worktree per feature (mandatory isolation)**

The brainstorming skill's workflow requires creating a git worktree for every feature before any code is written. This isolates branch state from main. BrickLayer's git-nerd handles commits and branches but does not mandate per-feature worktree isolation before implementation begins.

**10. Session-start hook injects skill index (not a system prompt)**

Rather than hardcoding everything in CLAUDE.md, Superpowers uses the SessionStart hook to inject only the `using-superpowers` skill index at startup. All other skills are loaded lazily on demand via the `Skill` tool. This keeps the always-present context minimal and loads skill detail only when needed.

BrickLayer's CLAUDE.md is comprehensive and always-present. The lazy-load approach is more token-efficient.

### Specific items to harvest

- `skills/subagent-driven-development/SKILL.md` — two-stage review pattern and model selection policy
- `skills/subagent-driven-development/spec-reviewer-prompt.md` — prompt for spec compliance review
- `skills/subagent-driven-development/code-quality-reviewer-prompt.md` — prompt for code quality review
- `skills/brainstorming/SKILL.md` — hard-gate XML pattern, spec self-review checklist, Socratic design process
- `skills/writing-plans/SKILL.md` — "no placeholders" invariant, blueprint format with inline code
- `skills/systematic-debugging/SKILL.md` — 3-fix architectural gate, 4-phase root-cause protocol
- `skills/systematic-debugging/find-polluter.sh` — test pollution bisect script
- `hooks/session-start` — lazy skill loading via SessionStart hook

### Priority: HIGH

The two-stage per-task review (spec compliance then code quality), the hard-gate brainstorming protocol, and the complete-code-in-every-step plan format are all directly applicable to BrickLayer's `/build` workflow and would measurably improve output quality. The systematic-debugging 3-fix architectural gate is a specific guardrail BrickLayer's fix-implementer agent lacks.

---

## affaan-m/everything-claude-code

### What it is

Everything Claude Code (ECC) is a comprehensive agent harness framework positioned as a "performance optimization system" for Claude Code and other coding agents. It ships 28 agents, 125 skills, 60 slash commands, and an extensive hook system. The core differentiators are:

1. An "instinct" system — a continuous learning pipeline that extracts behavioral patterns from sessions and stores them as project-scoped or global instincts with confidence scores, which can be promoted into skills, commands, or agents via the `/evolve` command
2. Multi-model orchestration — Claude as "Code Sovereign" with Codex and Gemini as dirty prototype generators, all managed through a plan → execute → audit loop
3. A DevFleet MCP integration for running parallel agents in isolated git worktrees with dependency DAG management
4. Session management with aliases, metadata (branch, worktree), and cross-session context restoration
5. Cost tracking per session and MCP health monitoring

### Key files/structure

```
agents/ (28 total)
  architect.md                   — System design and scalability
  build-error-resolver.md        — Fix build/type errors
  chief-of-staff.md              — Multi-channel communication triage (email/Slack/LINE/Messenger)
  code-reviewer.md               — Code quality and maintainability
  cpp-build-resolver.md          — C++ build error resolution
  cpp-reviewer.md                — C++ code review
  database-reviewer.md           — PostgreSQL/Supabase specialist
  doc-updater.md                 — Documentation and codemaps
  docs-lookup.md                 — Documentation and API research
  e2e-runner.md                  — Playwright end-to-end testing
  flutter-reviewer.md            — Flutter code review
  go-build-resolver.md           — Go build error resolution
  go-reviewer.md                 — Go code review
  harness-optimizer.md           — Harness config reliability/cost tuning
  java-build-resolver.md         — Java/Maven/Gradle error resolution
  java-reviewer.md               — Java/Spring Boot code review
  kotlin-build-resolver.md       — Kotlin/Gradle error resolution
  kotlin-reviewer.md             — Kotlin/Android/KMP review
  loop-operator.md               — Autonomous loop execution monitor
  planner.md                     — Implementation planning
  python-reviewer.md             — Python code review
  pytorch-build-resolver.md      — PyTorch/CUDA/training error resolution
  refactor-cleaner.md            — Dead code cleanup
  rust-build-resolver.md         — Rust build error resolution
  rust-reviewer.md               — Rust code review
  security-reviewer.md           — Vulnerability detection
  tdd-guide.md                   — Test-driven development
  typescript-reviewer.md         — TypeScript/JavaScript code review

skills/ (125 total — large directory, sampled via commands/)
  continuous-learning-v2/        — Instinct observation, storage, evaluation
    hooks/observe.sh             — Fires on every PreToolUse and PostToolUse
    scripts/instinct-cli.py      — CLI for status/export/import/evolve

commands/ (60 total)
  aside.md                       — Answer side question without losing task context
  build-fix.md                   — Fix build errors via resolver agents
  checkpoint.md                  — Save task progress checkpoint
  claw.md                        — Workflow command
  code-review.md                 — Trigger code-reviewer agent
  context-budget.md              — Show context window usage
  cpp-build.md / cpp-review.md / cpp-test.md
  devfleet.md                    — Multi-agent orchestration via DevFleet MCP
  docs.md                        — Docs lookup via context7
  e2e.md                         — Playwright E2E test runner
  eval.md                        — Evaluate session patterns
  evolve.md                      — Promote instincts to skills/commands/agents
  go-build.md / go-review.md / go-test.md
  gradle-build.md
  harness-audit.md               — Audit harness config
  instinct-export.md             — Export instincts to file
  instinct-import.md             — Import instincts from file
  instinct-status.md             — Show learned instincts with confidence bars
  kotlin-build.md / kotlin-review.md / kotlin-test.md
  learn-eval.md                  — Evaluate what was learned in session
  learn.md                       — Extract reusable patterns from session
  loop-start.md / loop-status.md — Autonomous loop management
  model-route.md                 — Show model routing decisions
  multi-backend.md               — Multi-model backend orchestration
  multi-execute.md               — Multi-model collaborative execution (plan→prototype→refactor→audit)
  multi-frontend.md              — Multi-model frontend orchestration
  multi-plan.md                  — Multi-model planning
  multi-workflow.md              — Multi-model full workflow
  orchestrate.md                 — Agent orchestration command
  plan.md                        — Implementation planning
  pm2.md                         — PM2 process manager integration
  projects.md                    — Project management
  promote.md                     — Promote project instinct to global
  prompt-optimize.md             — Optimize prompts
  prune.md                       — Prune low-confidence instincts
  python-review.md
  quality-gate.md                — Run quality gate checks
  refactor-clean.md              — Trigger refactor-cleaner agent
  resume-session.md              — Resume from saved session
  rules-distill.md               — Distill rules from session
  rust-build.md / rust-review.md / rust-test.md
  save-session.md                — Save current session state
  sessions.md                    — Session management (list/load/alias/info)
  setup-pm.md                    — Set up package manager
  skill-create.md                — Create new skill
  skill-health.md                — Check skill health
  tdd.md                         — TDD workflow
  test-coverage.md               — Test coverage report
  update-codemaps.md             — Update codebase maps
  update-docs.md                 — Update documentation
  verify.md                      — Verification command

hooks/hooks.json (events and hooks)
  PreToolUse:
    - block-no-verify: block git --no-verify to protect pre-commit hooks
    - auto-tmux-dev: auto-start dev servers in tmux with directory-based session names
    - pre-bash-tmux-reminder: suggest tmux for long-running commands
    - pre-bash-git-push-reminder: review reminder before git push
    - doc-file-warning: warn about non-standard documentation files
    - suggest-compact: suggest /compact at logical intervals (~50 tool calls)
    - observe (async): capture tool use for continuous learning
    - insaits-security-wrapper (opt-in): AI-to-AI security monitor
    - governance-capture (opt-in): capture secrets/policy violations
    - config-protection: block modifications to linter/formatter configs
    - mcp-health-check: check MCP server health before MCP tool execution
  PreCompact:
    - pre-compact: save state before context compaction
  SessionStart:
    - session-start: load previous context, detect package manager
  PostToolUse:
    - post-bash-pr-created: log PR URL after gh pr create
    - post-bash-build-complete (async): background build analysis
    - quality-gate (async): quality checks after edits
    - post-edit-format (strict): auto-format JS/TS with Biome or Prettier
    - post-edit-typecheck (strict): tsc --noEmit after .ts/.tsx edits
    - post-edit-console-warn: warn about console.log in edits
    - governance-capture (opt-in)
    - observe (async): capture results for continuous learning
  PostToolUseFailure:
    - mcp-health-check: track failed MCP calls, mark unhealthy servers, attempt reconnect
  Stop:
    - check-console-log: check all modified files for console.log
    - session-end (async): persist session state
    - evaluate-session (async): evaluate session for extractable patterns
    - cost-tracker (async): track token/cost metrics per session
    - desktop-notify (async): macOS desktop notification with task summary
  SessionEnd:
    - session-end-marker (async): lifecycle marker

mcp-configs/mcp-servers.json (14 configured servers)
  github, firecrawl, supabase, memory, sequential-thinking, vercel, railway,
  cloudflare-docs/workers-builds/workers-bindings/observability, clickhouse,
  exa-web-search, context7, magic (MagicUI), filesystem, insaits, playwright,
  fal-ai, browserbase, browser-use, devfleet, token-optimizer, confluence

ecc2/
  Cargo.toml / Cargo.lock / src/  — Rust CLI tool (ECC v2, early development)

schemas/                          — JSON schemas for hook input/output validation
rules/                            — Always-on guidelines (common + per-language)
contexts/                         — Context injection files
plugins/                          — Plugin manifests
manifests/                        — Deployment manifests
```

### Novel patterns vs BrickLayer

**1. Instinct system — continuous behavioral learning with confidence scores**

ECC's most novel feature. The continuous-learning-v2 skill fires observe hooks on every PreToolUse and PostToolUse (async, non-blocking). Each observation is stored and analyzed. Instincts are extracted behavioral patterns with: trigger condition, action, confidence score (0-100%), domain tag, and scope (project-specific or global).

- Project instincts: `~/.claude/homunculus/projects/<project-id>/instincts/`
- Global instincts: `~/.claude/homunculus/instincts/`
- `/instinct-status` shows all instincts with ASCII confidence bars
- `/learn` explicitly extracts patterns from the current session
- `/learn-eval` evaluates what was learned in a session
- `/prune` removes low-confidence instincts
- `/promote` promotes a project instinct to global scope
- `/instinct-export` and `/instinct-import` for sharing instinct sets

BrickLayer has EMA training (telemetry.jsonl → ema_history.json with α=0.3) that tracks agent performance over time. But EMA tracks aggregate agent scores, not individual behavioral patterns. Instincts are more granular: they capture specific "when X, do Y" rules that can be reviewed, pruned, promoted, and promoted into formal artifacts. This is a different abstraction layer — behavioral rules vs. agent performance scores.

**2. /evolve — promote instincts into formal artifacts**

The `/evolve` command analyzes clustered instincts and suggests (or generates) skills, commands, or agents:
- 2+ related instincts about user-invoked actions → Command candidate
- 2+ instincts about automatic behaviors → Skill candidate
- 4+ instincts about a multi-step process → Agent candidate

This creates a self-improving feedback loop: observe → instinct → evolve → formal artifact → use → observe. BrickLayer has agent auto-onboarding (masonry-agent-onboard.js detects new agent files) but does not have an instinct extraction layer that feeds artifact creation.

**3. /aside — side question without losing task context**

The `/aside` command answers a question mid-task with explicit "freeze the task state" and "resume after answering" semantics. Format: `ASIDE: [question]` / `[answer]` / `— Back to task: [one-liner]`. It handles edge cases: question reveals a blocker (flag it, wait for decision), question is actually a task redirect (disambiguate), multiple asides in sequence.

BrickLayer has no equivalent. Currently if you ask a question mid-build, context is polluted. The aside pattern preserves task continuity explicitly.

**4. Session management with metadata and aliases**

ECC stores session state to `~/.claude/session-data/` with metadata: project name, branch, worktree path, started/updated timestamps. Sessions can be aliased (`/sessions alias <id> <name>`), loaded by alias, and listed with branch/worktree columns. This allows disambiguation when running multiple parallel sessions across worktrees.

BrickLayer tracks sessions via the session-start hook (restore context) and stop hooks (persist), but does not have a browsable session registry with aliases and worktree metadata that can be queried by command.

**5. Cost tracking per session**

The Stop hook `cost-tracker.js` emits lightweight token/cost telemetry markers after each response. The `/sessions info` command shows this alongside branch and worktree. BrickLayer has no per-session cost tracking.

**6. MCP health monitoring**

PreToolUse and PostToolUseFailure hooks run `mcp-health-check.js` which: tracks MCP server health, marks servers as unhealthy after failures, blocks MCP tool calls to unhealthy servers, and attempts reconnect. This is particularly relevant because unhealthy MCP servers cause cryptic failures. BrickLayer has 20+ MCP tools via the Masonry server but no health monitoring hook.

**7. Config protection hook**

PreToolUse Write/Edit/MultiEdit fires `config-protection.js` which blocks modifications to linter/formatter config files (eslint, prettier, ruff.toml, etc.). This prevents the common pattern where an agent weakens linting rules to fix failing checks instead of fixing the code. BrickLayer's masonry-lint-check enforces linting after writes but does not block config modifications.

**8. Multi-model orchestration (Claude as Code Sovereign)**

The `multi-execute.md` command implements a full multi-model pipeline:
- Plan via `/multi-plan` (Claude plans)
- Prototype via Codex or Gemini running as background processes (`run_in_background: true`) — they output Unified Diff Patches only, never write files
- Refactor: Claude reads the diff, runs a "mental sandbox", refactors the prototype to production-grade code, applies changes
- Audit: parallel Codex + Gemini code review, synthesis with trust rules (backend follows Codex, frontend follows Gemini)

The "dirty prototype" model is novel: use cheap/fast models to generate a structural draft, then have Claude refactor it to meet quality standards. BrickLayer dispatches specialist agents but all agents are Claude instances. The Codex/Gemini integration pattern is out-of-scope for BrickLayer's current architecture.

**9. DevFleet multi-agent orchestration with dependency DAG**

The DevFleet MCP (`/devfleet` command) orchestrates parallel Claude Code agents in isolated git worktrees via a dependency DAG. `plan_project(prompt)` breaks a description into chained missions, `dispatch_mission()` starts agents, missions auto-dispatch as dependencies complete, and `get_report()` returns structured summaries. Each agent auto-merges its worktree on completion.

BrickLayer has `/masonry-team` for partitioning builds across N Claude instances and Trowel for campaign orchestration. DevFleet is specifically designed for software development workloads with auto-merge and structured reports. The dependency DAG with auto-dispatch is not present in BrickLayer.

**10. Loop operator agent + autonomous loop monitoring**

The `loop-operator.md` agent handles autonomous loop execution: detecting stalls, intervening when an agent gets stuck, and safely managing loop lifecycle. The `/loop-start` and `/loop-status` commands manage these loops. BrickLayer runs campaigns autonomously but does not have a dedicated loop monitor that can intervene on stalls from outside the loop context.

**11. Language-specific build resolver agents**

ECC has dedicated build resolver agents for: C++, Go, Kotlin, Java, PyTorch/CUDA, Rust. Each knows the specific error patterns, toolchain quirks, and resolution strategies for its ecosystem. BrickLayer has a generic `diagnose-analyst` + `fix-implementer` pattern that handles any language but lacks the domain-specific error knowledge of these specialists.

**12. Flutter reviewer agent**

BrickLayer has no Flutter/Dart specialist. ECC's `flutter-reviewer.md` is 14KB — the largest agent definition in the repo, suggesting significant depth. Relevant for Tim's JellyStream project (Android/Kotlin) and future mobile work.

**13. Chief-of-staff agent for multi-channel communication triage**

A personal communication agent that triages email, Slack, LINE, and Messenger using a 4-tier system (skip/info_only/meeting_info/action_required), generates draft replies matching relationship tone from a `relationships.md` file, and enforces post-send follow-through via PostToolUse hooks. BrickLayer has no communication management capability.

**14. PreCompact hook for state preservation**

ECC's `pre-compact.js` saves state before Claude's context compaction runs. BrickLayer does not have a PreCompact hook. This is important because compaction can lose task context mid-build if state isn't persisted first.

**15. Block --no-verify git flag**

The `block-no-verify` PreToolUse hook (via `npx block-no-verify@1.1.2`) blocks any Bash command containing `--no-verify`, preventing Claude from bypassing pre-commit hooks. BrickLayer's masonry-stop-guard blocks on uncommitted changes but does not prevent hook bypass.

**16. Auto-tmux for long-running processes**

`auto-tmux-dev.js` detects dev server commands (npm run dev, cargo watch, etc.) and starts them in named tmux sessions based on directory. This ensures log access and prevents blocking the main session. BrickLayer has no equivalent.

**17. Runtime hook profiles (minimal/standard/strict)**

ECC hooks support `ECC_HOOK_PROFILE=minimal|standard|strict` and `ECC_DISABLED_HOOKS="hook-id,hook-id"` env vars. This allows per-project hook customization without editing hook config files. BrickLayer hooks are always-on with no profile system.

**18. Instinct export/import for sharing**

`/instinct-export` and `/instinct-import` allow teams to share learned behavioral patterns. BrickLayer's EMA history and agent registry are local only with no export/import mechanism.

### Specific items to harvest

- `hooks/hooks.json` — PreCompact hook, config-protection hook, mcp-health-check hook, block-no-verify hook, cost-tracker hook
- `commands/aside.md` — side question pattern with task freeze/resume semantics
- `commands/evolve.md` — instinct promotion pipeline to skills/commands/agents
- `commands/sessions.md` — session management with aliases and metadata
- `commands/instinct-status.md` — confidence bar display pattern
- `commands/learn.md` — post-session pattern extraction
- `commands/devfleet.md` — DAG-based multi-agent orchestration
- `agents/loop-operator.md` — autonomous loop monitoring
- `agents/chief-of-staff.md` — 4-tier communication triage, hooks-over-prompts insight
- `agents/build-error-resolver.md` — generic build error resolution pattern
- `agents/flutter-reviewer.md` — Flutter/Dart specialist
- `agents/pytorch-build-resolver.md` — PyTorch/CUDA specialist
- `commands/multi-execute.md` — dirty prototype model (for future multi-model consideration)
- `hooks/README.md` — hook profile system design

### Priority: HIGH (instincts/evolve, aside, PreCompact hook, MCP health, config-protection) / MEDIUM (sessions, cost-tracker, build-resolvers) / LOW (multi-model orchestration, chief-of-staff, Flutter)

---

## Feature Gap Analysis

| Feature | In superpowers | In ECC | In BrickLayer 2.0 | Gap Level | Notes |
|---------|---------------|--------|-------------------|-----------|-------|
| Hard-gated brainstorming before code | YES — HARD-GATE XML block | Partial | Partial — /plan writes spec but no hard gate | HIGH | Superpowers enforces design approval before any code |
| Spec compliance review (separate from quality) | YES — spec-reviewer subagent | No | No | HIGH | Checks over-building and under-building explicitly |
| Model selection policy by task complexity | YES — documented in SKILL.md | No | Partial — model param passed but no policy | MEDIUM | Haiku for mechanical, Sonnet for integration, Opus for architecture |
| Blueprint format (no placeholders, inline code) | YES — writing-plans enforces this | No | No | HIGH | Plans must have runnable code and exact commands, no TBDs |
| Spec self-review (inline, before user handoff) | YES | No | No | MEDIUM | Agent self-reviews for consistency/placeholders before user sees it |
| 3-fix architectural gate | YES — documented rule | No | No | HIGH | After 3 failed fixes, stop and question the architecture |
| Test pollution bisect script | YES — find-polluter.sh | No | No | LOW | Useful but niche |
| Condition-based waiting reference | YES | No | No | LOW | Anti-sleep pattern doc |
| Git worktree per feature | YES — mandatory | No | No | MEDIUM | Isolation before implementation begins |
| Lazy skill loading (minimal session context) | YES — SessionStart injects index only | No | No | MEDIUM | Token-efficient vs always-present CLAUDE.md |
| Instinct system (behavioral learning with confidence) | No | YES | Partial — EMA agent scores only | HIGH | ECC tracks per-behavior rules; BL tracks per-agent scores |
| /evolve (instincts → formal artifacts) | No | YES | No | HIGH | Self-improving feedback loop |
| /aside (side question without losing context) | No | YES | No | HIGH | No equivalent in BrickLayer |
| Session aliases and metadata (branch/worktree) | No | YES | No | MEDIUM | Useful for multi-session disambiguation |
| Cost tracking per session | No | YES | No | MEDIUM | Token/cost telemetry per Stop event |
| PreCompact hook (save before compaction) | No | YES | No | HIGH | Prevents context loss during compaction |
| MCP health monitoring hooks | No | YES | No | MEDIUM | Blocks calls to unhealthy MCP servers |
| Config protection hook (block linter config edits) | No | YES | Partial — lint enforces after write | HIGH | Prevents agent from weakening linting rules |
| Block --no-verify git flag | No | YES | No | MEDIUM | Prevents pre-commit hook bypass |
| Auto-tmux for long-running processes | No | YES | No | LOW | Useful for dev servers |
| Runtime hook profiles (minimal/standard/strict) | No | YES | No | MEDIUM | Per-project hook customization |
| Loop operator / stall detection | No | YES | Partial — 3-strike escalation | MEDIUM | ECC has dedicated loop monitor agent |
| Language-specific build resolvers (Go, Rust, Java, Kotlin, PyTorch, C++) | No | YES | No | MEDIUM | Domain-specific error knowledge vs generic diagnose-analyst |
| Flutter/Dart specialist | No | YES | No | LOW | Relevant if mobile work expands |
| Chief-of-staff communication triage | No | YES | No | LOW | Out of scope for dev workflow |
| DevFleet DAG-based multi-agent orchestration | No | YES | Partial — /masonry-team | MEDIUM | Auto-dispatch on dependency completion |
| Instinct export/import for sharing | No | YES | No | LOW | Team sharing mechanism |
| Multi-model dirty prototype (Codex/Gemini) | No | YES | No | LOW | Requires non-Claude model access |
| Post-edit TypeScript type check hook | No | YES | Partial — lint-check runs eslint | MEDIUM | tsc --noEmit specifically after .ts/.tsx edits |
| Post-edit auto-format (Biome/Prettier auto-detect) | No | YES | Partial — masonry-lint-check | MEDIUM | Auto-detects formatter vs hardcoded |

---

## Top 5 Recommendations

### 1. Add spec-compliance review gate to /build loop [4h, HIGH PRIORITY]

BrickLayer's `/build` loop dispatches developer → code-reviewer → commit per task. Add a spec-compliance review step between developer and code-reviewer that uses a dedicated subagent prompt focused exclusively on two questions: (a) did the implementer build everything in the task spec? (b) did the implementer build anything NOT in the task spec? This prevents over-building (scope creep per task) and under-building (silent skips).

Implementation: Add `spec-reviewer` agent at `template/.claude/agents/spec-reviewer.md` with a focused prompt. Update the `/build` loop to dispatch it between developer and code-reviewer. The spec-reviewer gets the task text and git diff only — no codebase context needed.

### 2. Add PreCompact hook for state preservation [2h, HIGH PRIORITY]

Claude's context compaction runs mid-session and can discard task state if nothing captures it first. Add `masonry-pre-compact.js` on the PreCompact event that saves current `.autopilot/progress.json` state and appends a COMPACT_EVENT entry to `build.log`. This ensures the orchestrator can detect that compaction occurred and re-read its state on resume.

Implementation: Add `masonry-pre-compact.js` to `masonry/hooks/` and register in `settings.json` under PreCompact.

### 3. Implement /aside as a slash command [2h, HIGH PRIORITY]

The aside pattern is immediately useful. Mid-task questions currently pollute the main conversation context. The aside command freezes task state, answers read-only, then resumes. Create `/aside` as a command at `template/.claude/commands/aside.md` adapted from ECC's implementation. The key invariant: no file writes during aside, explicit "Back to task:" footer on every response.

### 4. Add config-protection hook (block linter config weakening) [1h, HIGH PRIORITY]

A common failure mode in BrickLayer builds: agent gets a lint error, edits `.eslintrc` or `ruff.toml` to suppress it instead of fixing the code. Add `masonry-config-protection.js` as a PreToolUse Write/Edit hook that blocks writes to: `eslint.config.*`, `.eslintrc*`, `ruff.toml`, `.prettierrc*`, `pyproject.toml` (when the edit contains `[tool.ruff]` or `[tool.black]`). Log the block and inject a reminder: "Fix the code to satisfy the linter, not the linter config."

### 5. Add instinct extraction to the Stop hook (lightweight version) [6h, MEDIUM PRIORITY]

The full ECC instinct system is substantial (Python CLI, confidence scores, project/global scoping, observe hooks on every tool call). A BrickLayer-appropriate version is lighter: at Stop, evaluate the session for 1-3 reusable behavioral patterns and append them to `masonry/instincts.jsonl` with timestamp, trigger, action, and source session. The existing `masonry-stop-guard.js` is the right hook to extend. Add a `/instinct-status` command to display current instincts. Skip the /evolve promotion pipeline initially — that's a Phase 2 effort once the instinct store has data.

---

## Novel Patterns to Incorporate (Future)

**Dirty prototype model (multi-model)**: Use a cheap/fast model to generate a structural diff, then have Claude refactor it to production quality. Currently out of scope without Codex/Gemini integration, but the "treat external model output as dirty prototype to be refactored" mental model is a useful framing even within Claude-only workflows (treat Haiku output as a draft that Sonnet refactors).

**DevFleet DAG orchestration**: The dependency DAG with auto-dispatch on completion (`plan_project` → `dispatch_mission` → auto-chain) is a more structured alternative to BrickLayer's `/masonry-team`. Worth evaluating for the `/ultrawork` pathway.

**Session aliases and worktree metadata**: Simple quality-of-life improvement for multi-session disambiguation. Useful when Tim runs parallel sessions on casaclaude and proxyclaude. The branch and worktree in session metadata solves the "which session am I looking at?" problem.

**Runtime hook profiles**: The `ECC_HOOK_PROFILE=minimal|standard|strict` pattern allows disabling expensive hooks during rapid iteration without editing config files. Masonry could support `MASONRY_HOOK_PROFILE` env var for the same purpose.

**Language-specific build resolvers**: Go, Rust, Java, Kotlin, PyTorch build resolvers are each meaningful specializations. The current `diagnose-analyst` + `fix-implementer` pattern works for any language but lacks ecosystem-specific error pattern knowledge. For projects in Tim's stack (Python/FastAPI, Rust, Go) these would reduce diagnose cycles.

**Loop operator for stall detection**: For long-running BrickLayer campaigns, an external monitor agent that checks for stalls (no findings written in N minutes, same question retried 3+ times) and intervenes with a recovery action is more reliable than the current self-recovery protocol in `program.md`.
