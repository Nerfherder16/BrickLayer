# Agent & Skill Reference

Quick reference for all available agents and skills. Custom agents live in `~/.claude/agents/`, skills live in `~/.claude/skills/`.

---

## Skills (`/hats`)

The Six Thinking Hats system. Run with `/hats <command> <context>`.

| Command | Hat | Role |
|---------|-----|------|
| `/hats blue <context>` | Blue | **Master Conductor** — design the thinking sequence, synthesize findings, define next steps |
| `/hats white <context>` | White | **Data Detective** — facts vs assumptions, information gaps, questions to investigate |
| `/hats red <context>` | Red | **Intuition Unpacker** — emotions, gut feelings, hidden fears/desires, stakeholder reactions |
| `/hats black <context>` | Black | **Risk Architect** — failure points ranked by likelihood, pre-mortem, fragile assumptions |
| `/hats yellow <context>` | Yellow | **Value Hunter** — benefits, optimism, untapped potential, vs doing nothing |
| `/hats green <context>` | Green | **Growth Catalyst** — unconventional alternatives, lateral thinking, reverse the problem |
| `/hats full <context>` | All | **Decision Matrix** — all 6 hats in sequence → recommendation + confidence rating (1–10) |
| `/hats journal` | — | Review saved analyses at `~/.claude/hats-journal.md` |

**Sequence for full spectrum:** Blue → White → Red → Black → Yellow → Green → Blue (synthesis)

**After any analysis:** Claude will offer to save to `~/.claude/hats-journal.md` with date, hat(s) used, confidence rating, key findings, and decision/next step.

---

## Custom Agents (Local — `~/.claude/agents/`)

Quick reference for all available agents. Custom agents live in `~/.claude/agents/` and are invoked automatically by Claude based on task context, or explicitly via the Agent tool.

---

## Custom Agents (Local — `~/.claude/agents/`)

### Rust

| Agent | Model | Tools | Use For |
|-------|-------|-------|---------|
| `rust-developer` | sonnet | Read, Glob, Grep, Edit, Write, Bash, LSP | Implementing Rust code, refactoring, adding features, writing tests and benchmarks |
| `rust-analyst` | opus | Read, Glob, Grep, Bash, LSP | Code review, soundness analysis, security vulnerabilities, performance anti-patterns, dependency audits — **read-only, produces findings report** |

### Infrastructure & Architecture

| Agent | Model | Tools | Use For |
|-------|-------|-------|---------|
| `devops` | default | default | CI/CD pipelines, Docker/K8s, infrastructure as code, deployment automation |
| `security` | default | default | Application security, vulnerability assessment, hardening |
| `architect` | default | default | System design, scalability patterns, technical decision making |

---

## OMC Agents (`oh-my-claudecode:` prefix)

Invoked via the Agent tool with `subagent_type: "oh-my-claudecode:<name>"`. Pass `model` to override.

### Build & Analysis Lane

| Agent | Default Model | Role |
|-------|--------------|------|
| `explore` | haiku | Internal codebase discovery — symbol/file mapping, pattern searches |
| `analyst` | opus | Requirements clarity, acceptance criteria, hidden constraints |
| `planner` | opus | Task sequencing, execution plans, risk flags |
| `architect` | opus | System design, boundaries, interfaces, long-horizon tradeoffs |
| `debugger` | sonnet | Root-cause analysis, regression isolation, failure diagnosis |
| `executor` | sonnet | Code implementation, refactoring, feature work |
| `deep-executor` | opus | Complex autonomous goal-oriented tasks requiring multi-step reasoning |
| `verifier` | sonnet | Completion evidence, claim validation, test adequacy |

### Review Lane

| Agent | Default Model | Role |
|-------|--------------|------|
| `quality-reviewer` | sonnet | Logic defects, maintainability, anti-patterns, performance hotspots, complexity |
| `security-reviewer` | sonnet | Vulnerabilities, trust boundaries, authn/authz |
| `code-reviewer` | opus | Comprehensive review — API contracts, versioning, backward compatibility |

### Domain Specialists

| Agent | Default Model | Role |
|-------|--------------|------|
| `test-engineer` | sonnet | Test strategy, coverage, flaky-test hardening, TDD workflows |
| `build-fixer` | sonnet | Build/toolchain/type failures — minimal diffs, no arch changes |
| `designer` | sonnet | UX/UI architecture, interaction design, component systems |
| `writer` | haiku | Docs, migration notes, README, API docs, comments |
| `qa-tester` | sonnet | Interactive CLI/service runtime validation via tmux |
| `scientist` | sonnet | Data analysis, statistical analysis, research execution |
| `document-specialist` | sonnet | External documentation & reference lookup (fetches current library docs) |

### Coordination

| Agent | Default Model | Role |
|-------|--------------|------|
| `critic` | opus | Plan/design critical challenge — challenges assumptions, finds gaps |

---

## General-Purpose Built-in Agents

Available via the Agent tool with these `subagent_type` values:

| Agent | Use For |
|-------|---------|
| `general-purpose` | Complex multi-step research, multi-file codebase searches, exploratory tasks |
| `Explore` | Fast codebase exploration — find files by pattern, search for keywords, answer codebase questions |
| `Plan` | Implementation planning — returns step-by-step plans with architectural trade-offs |

---

## Model Routing Guide

| Task Complexity | Model | Example |
|----------------|-------|---------|
| Quick lookups, narrow checks, lightweight scans | `haiku` | "Which file handles routing?" |
| Standard implementation, debugging, reviews | `sonnet` | "Add input validation to the login flow" |
| Architecture, deep analysis, complex refactors | `opus` | "Refactor the auth/session layer across the API" |

---

## Common Workflows

**Feature development:**
`analyst` → `planner` → `executor` → `test-engineer` → `quality-reviewer` → `verifier`

**Bug investigation:**
`explore` + `debugger` → `executor` → `test-engineer` → `verifier`

**Code review:**
`quality-reviewer` + `security-reviewer` + `code-reviewer`

**Rust work:**
`rust-developer` (implement) → `rust-analyst` (review) → fix → repeat

**Large autonomous build:**
`/team` or `/autopilot` — stages: plan → PRD → exec → verify → fix loop
