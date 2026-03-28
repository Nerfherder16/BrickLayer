# Trail of Bits Security Skills + Anthropic Knowledge Work Plugins

**Repos**: https://github.com/trailofbits/skills · https://github.com/anthropics/knowledge-work-plugins
**Researched**: 2026-03-28
**Researcher**: repo-researcher agent
**Stars**: trailofbits/skills 3.9K · anthropics/knowledge-work-plugins 10.4K

---

## Verdict Summary

**trailofbits/skills** is a professional-grade security skill library from one of the world's top security firms. It beats BrickLayer's security agent decisively on depth: mandatory gate-review pipelines, structured false positive verification with 13-item checklists, CI/CD agentic attack surface auditing, supply chain threat modeling, cryptographic timing side-channel analysis, and variant-hunt methodology with CodeQL/Semgrep templates. BrickLayer's security agent does OWASP Top 10 scans; this library does professional security audits.

**anthropics/knowledge-work-plugins** is Anthropic's own official plugin library targeting enterprise knowledge workers (legal, finance, engineering, product, HR, data). Most of it is irrelevant to BrickLayer's research/dev focus — but the engineering plugin's incident response, deploy checklist, and tech-debt skills are directly applicable, and the legal plugin's playbook-based contract review is an interesting pattern for BrickLayer's regulatory-researcher.

BrickLayer beats both on: multi-agent research campaigns, EMA training/prompt optimization, adaptive topology routing, consensus builders, and the Masonry infrastructure layer. Neither repo comes close to BrickLayer's campaign orchestration capability.

---

## trailofbits/skills

### Structure

```
skills/
  CLAUDE.md             — Skill authoring guidelines (quality standards, PR checklist)
  CODEOWNERS            — Per-plugin ownership assignments
  plugins/              — 36 plugin directories
    {plugin}/
      .claude-plugin/plugin.json   — Metadata
      skills/{name}/SKILL.md       — Entry point (frontmatter + behavior)
      skills/{name}/references/    — Detailed supplemental docs
      skills/{name}/resources/     — Templates, CodeQL/Semgrep starters
      agents/                      — Subagent definitions
      hooks/hooks.json             — Claude Code hooks
      commands/                    — Slash commands
  .codex/               — Codex compatibility layer (skill mirrors)
  .github/              — CI validation scripts
```

### Full Skill Inventory

#### Smart Contract Security

| Plugin | Description |
|--------|-------------|
| `building-secure-contracts` | Smart contract security toolkit with vulnerability scanners for 6 blockchains (Ethereum, Solana, etc.) |
| `entry-point-analyzer` | Identify state-changing entry points in smart contracts for security auditing |

#### Code Auditing

| Plugin | Description |
|--------|-------------|
| `agentic-actions-auditor` | Audit GitHub Actions workflows for AI agent security vulnerabilities (9 attack vectors: prompt injection via env vars, direct expression injection, subshell expansion, eval of AI output, dangerous sandbox configs, wildcard allowlists, PR target checkout, CLI data fetch, error log injection) |
| `audit-context-building` | Ultra-granular line-by-line code analysis using First Principles, 5 Whys, 5 Hows methodology — pure context-building phase before vulnerability hunting |
| `burpsuite-project-parser` | Search and extract data from Burp Suite project files |
| `differential-review` | Security-focused differential review of code changes: 7-phase workflow (triage → code analysis → test coverage → blast radius → deep context → adversarial modeling → report), codebase-size adaptive strategy |
| `dimensional-analysis` | Annotate codebases with dimensional analysis comments to detect unit mismatches and formula bugs |
| `fp-check` | Systematic false positive verification: 6-gate review process, standard vs deep verification routing, 13-item devil's advocate checklist, mandatory PoC construction, batch triage with exploit chain detection |
| `insecure-defaults` | Detect fail-open insecure defaults: distinguishes fail-open (CRITICAL) from fail-secure (SAFE), covers hardcoded secrets, weak auth, permissive CORS, debug modes, weak crypto |
| `semgrep-rule-creator` | Create and refine Semgrep rules for custom vulnerability detection |
| `semgrep-rule-variant-creator` | Port existing Semgrep rules to new target languages with test-driven validation |
| `sharp-edges` | Identify error-prone APIs, dangerous configurations, and footgun designs |
| `static-analysis` | Static analysis toolkit: CodeQL skill, Semgrep skill, SARIF parsing skill — three sub-skills with agents |
| `supply-chain-risk-auditor` | Audit dependency supply chain risk against 6 criteria: single maintainer, unmaintained status, low popularity, high-risk features (FFI/deserialization/code execution), past CVEs, absence of security contact |
| `testing-handbook-skills` | Skills from the Trail of Bits Testing Handbook: fuzzers, static analysis, sanitizers, coverage |
| `variant-analysis` | Find similar vulnerabilities via 5-step pattern-based analysis: understand root cause → exact match → identify abstraction points → iteratively generalize (stop at 50% FP rate) → triage; CodeQL + Semgrep templates for 5 languages |

#### Malware Analysis

| Plugin | Description |
|--------|-------------|
| `yara-authoring` | YARA detection rule authoring with linting, atom analysis, and best practices |

#### Verification

| Plugin | Description |
|--------|-------------|
| `constant-time-analysis` | Detect compiler-induced timing side-channels in cryptographic code; includes a Python tool (ct_analyzer) |
| `property-based-testing` | Property-based testing guidance for multiple languages and smart contracts |
| `spec-to-code-compliance` | Specification-to-code compliance checker for blockchain audits |
| `zeroize-audit` | Detect missing or compiler-eliminated zeroization of secrets in C/C++ and Rust |

#### Reverse Engineering

| Plugin | Description |
|--------|-------------|
| `dwarf-expert` | Interact with and understand the DWARF debugging format for binary analysis |

#### Mobile Security

| Plugin | Description |
|--------|-------------|
| `firebase-apk-scanner` | Scan Android APKs for Firebase security misconfigurations |

#### Development

| Plugin | Description |
|--------|-------------|
| `ask-questions-if-underspecified` | Clarify requirements before implementing — minimal frontmatter reference skill |
| `devcontainer-setup` | Create pre-configured devcontainers with Claude Code and language-specific tooling |
| `gh-cli` | Intercept GitHub URL fetches and redirect to authenticated `gh` CLI |
| `git-cleanup` | Safely clean up git worktrees and local branches with gated confirmation |
| `let-fate-decide` | Draw Tarot cards using cryptographic randomness for vague planning decisions |
| `modern-python` | Modern Python tooling: uv, ruff, pytest best practices |
| `seatbelt-sandboxer` | Generate minimal macOS Seatbelt sandbox configurations |
| `second-opinion` | Run code reviews using external LLM CLIs (OpenAI Codex, Gemini) on diffs or commits |
| `skill-improver` | Iterative skill refinement loop using automated fix-review cycles |
| `workflow-skill-design` | Design patterns for workflow-based Claude Code skills with review agent |

#### Team Management / Tooling / Infrastructure

| Plugin | Description |
|--------|-------------|
| `culture-index` | Interpret Culture Index survey results for individuals and teams |
| `claude-in-chrome-troubleshooting` | Diagnose Claude in Chrome MCP extension connectivity issues |
| `debug-buttercup` | Debug Buttercup Kubernetes deployments |

---

### Key Implementation Patterns

**fp-check hooks.json** — Uses two hooks simultaneously:
- `Stop` event: Prompts an LLM to verify completeness of ALL fp-check phases across every bug before allowing session stop. Blocks if any bug is missing any phase. Pattern: LLM-as-completeness-gate.
- `SubagentStop` event: Verifies each subagent (data-flow-analyzer, exploitability-verifier, poc-builder) produced all mandatory structured output sections before allowing the subagent to stop.

**fp-check SKILL.md** — 7 key techniques:
1. "Rationalizations to Reject" table: 6 named reasoning shortcuts with WHY they're wrong and REQUIRED ACTION. Explicitly names LLM bias ("LLMs are biased toward seeing bugs and overrating severity").
2. Routing decision: Standard vs Deep verification based on complexity checklist before any work starts.
3. Step 0 claim restatement: "Half of false positives collapse at this step."
4. Explicit threat model requirement: privilege level, sandbox, what attacker can already do.
5. Six mandatory gate reviews (Process, Reachability, Real Impact, PoC Validation, Math Bounds, Environment) — all must pass for TRUE POSITIVE verdict.
6. Devil's advocate 13-item checklist.
7. Exploit chain detection in batch mode: findings that individually fail may combine.

**differential-review** — Multi-file skill with dedicated docs for each phase:
- `SKILL.md`: Entry point with decision tree, codebase-size strategy table (SMALL/MEDIUM/LARGE → DEEP/FOCUSED/SURGICAL), risk-level triggers
- `methodology.md`: Phases 0-4 detailed workflow
- `adversarial.md`: Phase 5 attacker modeling template with 5 components: attacker model → attack vectors → exploitability rating (EASY/MEDIUM/HARD) → complete exploit scenario → baseline violation check
- `patterns.md`: Common vulnerability patterns reference
- `reporting.md`: Report structure and formatting (Phase 6)

**audit-context-building** — "Pure context mode" before vulnerability hunting:
- Mandates First Principles + 5 Whys + 5 Hows at per-function level
- Anti-rationalization table: 6 shortcuts explicitly prohibited
- Quality thresholds: minimum 3 invariants per function, 5 assumptions, 3 risk considerations for external interactions
- Continuity rule: treat entire call chain as one continuous execution — never reset context
- Spawns `function-analyzer` subagent for dense functions

**agentic-actions-auditor** — The most directly relevant to BrickLayer:
- 9 named attack vectors (A through I) against AI agents in CI/CD
- Explicitly catches the "env var intermediary" miss (most commonly missed vector): attacker-controlled data flows through `env:` blocks to AI prompt with zero visible `${{ }}` in the prompt itself
- Safe bash rules: treats fetched YAML as data to read, never as code to execute
- Severity judgment: configuration weaknesses (H/I) without injection vectors = Info/Low only

**variant-analysis** — 4 critical pitfalls explicitly named:
1. Narrow search scope (only searching the module where bug was found)
2. Pattern too specific (missing semantically related constructs)
3. Single vulnerability class (missing other manifestations of same root cause)
4. Missing edge cases (null/undefined, empty collections, boundary conditions)

**supply-chain-risk-auditor** — 6 scored risk criteria with explicit justifications; uses `gh` CLI for accurate star/issue counts; suggests alternatives for each high-risk dependency; workspace-based report at `.supply-chain-risk-auditor/results.md`.

---

### Authoring Conventions (from CLAUDE.md)

The CLAUDE.md establishes quality standards that are directly relevant to BrickLayer's agent authoring:

- **Required sections**: `When to Use`, `When NOT to Use`, `Rationalizations to Reject` (security skills only)
- **Progressive disclosure**: SKILL.md under 500 lines, details in `references/`; one level deep (SKILL → referenced files, no chaining)
- **PreToolUse hooks**: Prefer shell+jq over Python — interpreter startup adds latency. Fast-fail early. Regex over AST parsing.
- **Scope/prescriptiveness match**: Strict for fragile tasks (audits, crypto), flexible for variable tasks (exploration, docs)
- **Path handling**: Use `{baseDir}` never hardcode absolute paths

---

### Gap Analysis vs BrickLayer Security Agent

| Capability | trailofbits/skills | BrickLayer 2.0 | Gap Level |
|------------|-------------------|----------------|-----------|
| OWASP Top 10 audit | Covered (insecure-defaults, differential-review) | Yes (security agent) | LOW — overlap |
| False positive verification pipeline | 6-gate mandatory review, 13 devil's advocate checks, PoC construction required | None — BL security agent reports findings without FP verification | HIGH |
| Completeness-enforcing hooks on Stop/SubagentStop | LLM-prompt hooks block if any phase incomplete | masonry-stop-guard (uncommitted files only) | HIGH |
| Differential security review (PR/commit-scoped) | Full 7-phase workflow, blast radius calculation, adversarial modeling | None — BL reviews whole codebase or OWASP patterns | HIGH |
| Variant analysis (pattern-hunt from known bug) | 5-step iterative method, CodeQL+Semgrep templates, explicit FP rate gate | None | HIGH |
| Agentic CI/CD audit (prompt injection in Actions) | 9 attack vectors, env var intermediary detection, sandbox config analysis | None — BL has no GitHub Actions security skill | HIGH |
| Audit context building (pre-hunt phase) | Mandatory pure-context phase: 5 Whys, invariants, call chain continuity | research-analyst does context building but no formal pre-hunt separation | MEDIUM |
| Supply chain risk audit | 6 criteria, gh CLI for live data, replacement suggestions | None — BL has no dependency risk analysis | HIGH |
| Static analysis orchestration (CodeQL + Semgrep + SARIF) | Full sub-skills for each tool, SARIF parsing agent | None | HIGH |
| Semgrep rule creation from findings | Iterative rule creation with test validation | None | MEDIUM |
| Timing side-channel analysis | Python ct_analyzer tool, compiler-aware | None | MEDIUM |
| Zeroize audit (secret memory wiping) | C/C++ and Rust specific, compiler elision detection | None | LOW |
| YARA rule authoring | Full authoring skill with linting | None | LOW |
| "Rationalizations to Reject" tables | Every security skill has explicit anti-rationalization lists | Not formalized in any agent | HIGH |
| Fail-open vs fail-secure distinction | Explicit pattern with code examples | OWASP audit covers hardcoded secrets generally | MEDIUM |
| Property-based testing guidance | Multi-language, smart contract variants | masonry-tdd-enforcer (TDD enforcement only) | MEDIUM |
| Threat model requirements | Explicit privilege level, sandbox, attacker position fields | Not required in security agent output | MEDIUM |
| Exploitability rating (EASY/MEDIUM/HARD) | Structured with concrete criteria | Not structured | MEDIUM |
| Blast radius calculation | Quantitative (N callers) for HIGH risk changes | Not in any agent | MEDIUM |
| Secret scanner hook (PreToolUse) | Not present (static analysis only) | masonry-secret-scanner.js hook | LOW (BL wins) |
| OWASP compliance agent | Not specialized | compliance-auditor agent | LOW (BL wins) |
| Multi-agent campaign system | Not present | Full BL 2.0 campaign system | BL wins |

---

### Top Skills to Harvest (trailofbits/skills)

#### Priority 1: fp-check — False Positive Verification Pipeline

**File path**: `plugins/fp-check/skills/fp-check/SKILL.md`
**Hook path**: `plugins/fp-check/hooks/hooks.json`

What to build: A `verification-analyst` agent for BrickLayer that takes security findings from the security agent and runs them through the fp-check 6-gate pipeline. Implement the Stop hook pattern that blocks session termination until all bugs have complete verdicts (TRUE POSITIVE or FALSE POSITIVE). Add the 13 devil's advocate questions as a required checklist section in the security agent's output format.

Why it matters: BrickLayer's security agent currently reports findings without any mechanism to verify they are real. In security audits, false positive rates of 40-60% are common from pattern-matching tools. A mandatory FP verification pass prevents wasted developer time fixing non-issues.

Implementation sketch:
- Add `verification-analyst.md` agent that accepts findings.md from security agent
- Implement standard vs deep routing based on complexity
- Enforce the 6 gates: Process, Reachability, Real Impact, PoC Validation, Math Bounds, Environment
- Add Stop hook (LLM-prompt type) that scans conversation for completeness before allowing stop
- Integrate as post-step in masonry security review workflow

**Priority: HIGH, estimated 8-12h**

---

#### Priority 2: differential-review — Security-Scoped PR Review

**File paths**: `plugins/differential-review/skills/differential-review/SKILL.md`, `adversarial.md`, `methodology.md`, `patterns.md`, `reporting.md`

What to build: A `security-diff-reviewer` agent or skill that hooks into BrickLayer's git-nerd agent and adds security analysis on PRs/commits. Key patterns: codebase-size-adaptive strategy, blast radius calculation (N callers), git blame on removed security code, adversarial modeling with EASY/MEDIUM/HARD exploitability ratings.

Why it matters: BrickLayer's code-reviewer agent does correctness and style. The security agent does full codebase OWASP scans. Neither does security-focused differential analysis — reviewing what changed and whether that change introduced a regression or new vulnerability. This is the highest-value integration point for a development-focused security workflow.

Implementation sketch:
- New `security-diff-reviewer.md` agent triggered after code-reviewer in the `/build` pipeline
- Input: git diff (from git-nerd), codebase size classification
- Phase 1: Classify risk level per changed file (HIGH/MEDIUM/LOW)
- Phase 2: Git blame on removed security code — flag any removal from commits with "security", "CVE", "fix" messages
- Phase 3: Blast radius calculation for HIGH risk changes
- Phase 4: Adversarial modeling for HIGH risk (use adversarial.md template)
- Output: `DIFF_SECURITY_REVIEW.md` in findings/

**Priority: HIGH, estimated 6-10h**

---

#### Priority 3: agentic-actions-auditor — CI/CD AI Agent Security

**File path**: `plugins/agentic-actions-auditor/skills/agentic-actions-auditor/SKILL.md`

What to build: Integrate BrickLayer's security agent with the 9 attack vector methodology for auditing `.github/workflows/` files in repos it analyzes. This is directly relevant to BrickLayer itself — BrickLayer runs Claude Code Actions in CI contexts.

Why it matters: The "env var intermediary" attack vector (Vector A) is the most commonly missed prompt injection path in AI agent CI/CD, per Trail of Bits. Any BrickLayer user who runs agents in GitHub Actions is potentially exposed to this. BrickLayer should audit its own workflows and expose this as an audit capability.

Key patterns to extract:
- The 9 named vectors (A-I) as a structured checklist
- The env var intermediary detection heuristic: look for `env:` blocks with `${{ github.event.* }}` values where the prompt field references env var names (no visible `${{ }}` in prompt)
- Safe bash rules: YAML from remote repos is data, never pipe to shell interpreters
- Severity amplification: H/I alone = Info; H/I + injection vector = elevated severity

**Priority: HIGH, estimated 4-6h**

---

#### Priority 4: variant-analysis — Pattern-Hunt From Known Bugs

**File path**: `plugins/variant-analysis/skills/variant-analysis/SKILL.md`

What to build: Add a `/variant-hunt` skill to BrickLayer's security agent. After a finding is confirmed TRUE POSITIVE by the verification-analyst, trigger variant analysis: start specific, generalize one element at a time, stop at 50% FP rate, output CodeQL/Semgrep rules.

Why it matters: Security audits that stop at the first instance of a bug miss 60-80% of the actual attack surface. Variant analysis is how professionals find the full scope of a vulnerability class across a codebase.

**Priority: HIGH, estimated 4-6h**

---

#### Priority 5: "Rationalizations to Reject" Pattern — Agent Authoring Standard

**File**: Not a single skill — this is an authoring pattern used across all ToB security skills.

What to build: Adopt this as a BrickLayer standard for all security-adjacent agents. Every security agent (security.md, compliance-auditor.md, verification.md, peer-reviewer.md) should have a "Rationalizations to Reject" table listing named reasoning shortcuts, why they're wrong, and what action to take instead.

The explicit naming of LLM bias in fp-check ("LLMs are biased toward seeing bugs and overrating severity — complete devil's advocate review") is directly applicable to BrickLayer's verification and peer-reviewer agents.

**Priority: HIGH, 2-3h per agent to retrofit**

---

## anthropics/knowledge-work-plugins

### Structure

Each plugin follows:
```
{plugin-name}/
  .claude-plugin/plugin.json    — Manifest
  .mcp.json                     — MCP server connections (tools)
  commands/                     — Slash commands (explicit invocation)
  skills/                       — Domain knowledge (automatic activation)
  CONNECTORS.md                 — Tool integration documentation
  README.md                     — Plugin documentation
```

All content is markdown and JSON. No code, no build steps.

### Full Plugin Inventory

| Plugin | Commands | Skills | MCP Connectors |
|--------|----------|--------|----------------|
| `productivity` | — | memory-management, task-management, start, update | Slack, Notion, Asana, Linear, Jira, Monday, ClickUp, Microsoft 365 |
| `sales` | — | (multiple) | Slack, HubSpot, Close, Clay, ZoomInfo, Notion, Jira, Fireflies, Microsoft 365 |
| `customer-support` | — | (multiple) | Slack, Intercom, HubSpot, Guru, Jira, Notion, Microsoft 365 |
| `product-management` | write-spec, roadmap, user-research, competitive, stakeholder | (multiple) | Slack, Linear, Asana, Monday, ClickUp, Jira, Notion, Figma, Amplitude, Pendo, Intercom, Fireflies |
| `marketing` | — | (multiple) | Slack, Canva, Figma, HubSpot, Amplitude, Notion, Ahrefs, SimilarWeb, Klaviyo |
| `legal` | review-contract, triage-nda, vendor-check, brief, respond | contract-review, nda-triage, compliance, canned-responses, legal-risk-assessment, meeting-briefing | Slack, Box, Egnyte, Jira, Microsoft 365 |
| `finance` | reconciliation, journal-entry, variance-analysis, close-checklist, audit-prep | (multiple) | Snowflake, Databricks, BigQuery, Slack, Microsoft 365 |
| `data` | write-query, analyze, explore-data, create-viz, build-dashboard, validate-data, statistical-analysis | analyze, build-dashboard, create-viz, data-context-extractor, data-visualization, explore-data, sql-queries, statistical-analysis, validate-data, write-query | Snowflake, Databricks, BigQuery, Definite, Hex, Amplitude, Jira |
| `enterprise-search` | — | (multiple) | Slack, Notion, Guru, Jira, Asana, Microsoft 365 |
| `bio-research` | — | (multiple) | PubMed, BioRender, bioRxiv, ClinicalTrials.gov, ChEMBL, Synapse, Wiley, Owkin, Open Targets, Benchling |
| `engineering` | standup, review, debug, architecture, incident, deploy-checklist | code-review, incident-response, system-design, tech-debt, testing-strategy, documentation, architecture, deploy-checklist, standup, debug | GitHub, GitLab, Linear, Jira, Datadog, PagerDuty, Slack, Notion |
| `cowork-plugin-management` | — | (multiple — plugin creation workflow) | None |

Also observed in the repo root but not listed in the main marketplace table:
- `human-resources` — HR workflows, performance, hiring
- `operations` — Ops workflows
- `design` — Design workflows
- `partner-built` — Third-party contributed plugins
- `pdf-viewer` — PDF content extraction

### Engineering Plugin Deep Dive

The `engineering` plugin is the most relevant to BrickLayer. Skills and commands:

**Commands** (explicit slash invocations):
- `/standup` — pull recent commits, PRs, tickets; format standup update
- `/review` — structured code review: security, performance, style, correctness
- `/debug` — reproduce → isolate → diagnose → fix structured debugging session
- `/architecture` — ADR format with trade-off analysis
- `/incident` — triage severity → draft communications → track timeline → generate postmortem
- `/deploy-checklist` — verify tests, review changes, check dependencies, confirm rollback plan

**Skills** (automatic activation):
- `code-review` — bugs, security, performance, maintainability
- `incident-response` — status updates, runbooks, postmortems
- `system-design` — architecture diagrams, API design, data modeling
- `tech-debt` — identify, categorize, prioritize; remediation plan
- `testing-strategy` — unit/integration/e2e coverage, test plan creation
- `documentation` — READMEs, API docs, runbooks, onboarding guides
- `architecture` — ADR structure and decision frameworks
- `deploy-checklist` — pre-deployment verification

Settings: `engineering/.claude/settings.local.json` with name, title, team, company, techStack, defaultBranch, deployProcess.

### Legal Plugin Deep Dive

The legal plugin's patterns are relevant to BrickLayer's regulatory-researcher agent:

**NDA Triage**: GREEN/YELLOW/RED classification. BrickLayer's regulatory-researcher produces findings but lacks a traffic-light classification system for routing urgency.

**Playbook-based review**: `legal.local.md` defines organization-specific positions with:
- Standard position
- Acceptable range
- Escalation trigger

This is a useful pattern for BrickLayer research campaigns: a `campaign-brief.md` equivalent that defines what "acceptable" looks like for each question domain.

**Vendor check**: Cross-reference existing agreements before creating new ones. Analogous to BrickLayer's recall search before generating new findings.

### Which Plugins Add Genuine New Capability to BrickLayer

| Plugin | Relevance | What's Novel | Add? |
|--------|-----------|--------------|------|
| `engineering` | HIGH | Incident response workflow, deploy checklist, tech-debt prioritization, structured `/debug` session | Yes — specific skills |
| `legal` | MEDIUM | Playbook-based compliance scoring (GREEN/YELLOW/RED), NDA triage routing, org-specific position definitions | Yes — pattern for regulatory-researcher |
| `data` | MEDIUM | SQL query writing with validation, statistical analysis, data visualization skills | Yes — useful for quantitative-analyst |
| `product-management` | LOW-MEDIUM | Spec writing, competitive tracking — BL has spec-writer and competitive-analyst already | No — duplicates BL |
| `productivity` | LOW | Memory management skill, personal context — BL has Recall for this | No — duplicates Recall |
| `bio-research` | LOW | Specialized connectors (PubMed, ChEMBL, Benchling) — BL doesn't target life sciences | No |
| `sales` | NONE | CRM-centric, no overlap | No |
| `customer-support` | NONE | Ticket triage, no overlap | No |
| `marketing` | NONE | Content and campaign, no overlap | No |
| `finance` | NONE | Journal entries, reconciliation, no overlap | No |
| `enterprise-search` | LOW | Federated search across Slack/Notion/Jira — BL has Recall for this | No |
| `cowork-plugin-management` | MEDIUM | Plugin creation workflow — useful meta-pattern for BrickLayer's agent authoring | Maybe |

### Top Plugins to Harvest (anthropics/knowledge-work-plugins)

#### Priority 1: Engineering Plugin — Incident Response + Deploy Checklist

**File path**: `engineering/skills/incident-response/` and `engineering/skills/deploy-checklist/`

BrickLayer has a devops agent and git-nerd but lacks formal incident response workflow: triage → communicate → mitigate → postmortem. The deploy-checklist skill provides a structured pre-deploy verification pattern that would complement BrickLayer's `/verify` phase.

What to extract:
- `/incident` command structure: triage severity → draft stakeholder communications → track timeline → generate postmortem
- `/deploy-checklist` checklist structure: tests passing, changes reviewed, dependencies checked, rollback plan confirmed

**Priority: MEDIUM, 3-4h**

---

#### Priority 2: Engineering Plugin — Tech Debt Prioritization

**File path**: `engineering/skills/tech-debt/`

BrickLayer has a code-reviewer but no dedicated tech-debt tracking or prioritization skill. A `tech-debt-analyst` agent that identifies, categorizes (by type: architecture, code quality, test coverage, documentation), and produces a prioritized remediation plan would add value for Tim's projects.

**Priority: MEDIUM, 2-3h**

---

#### Priority 3: Legal Plugin — Traffic-Light Compliance Classification

**File path**: `legal/skills/nda-triage/`, `legal/skills/legal-risk-assessment/`

The GREEN/YELLOW/RED routing pattern is directly applicable to BrickLayer's compliance-auditor agent. Currently compliance findings are narrative; adding a structured severity classification with routing recommendations (GREEN = proceed, YELLOW = flag for review, RED = block + escalate) would make compliance findings more actionable.

**Priority: MEDIUM, 2h to retrofit compliance-auditor**

---

#### Priority 4: Data Plugin — SQL + Statistical Analysis Skills

**File path**: `data/skills/write-query/`, `data/skills/statistical-analysis/`, `data/skills/validate-data/`

BrickLayer's quantitative-analyst runs simulations but doesn't have dedicated SQL query writing or statistical analysis skills. These would be useful for Tim's Snowflake/BigQuery/PostgreSQL work (ADBP, JellyStream analytics).

**Priority: LOW-MEDIUM, 3-4h**

---

## Feature Gap Analysis (Combined)

| Feature | In Repos | In BrickLayer 2.0 | Gap Level | Notes |
|---------|----------|-------------------|-----------|-------|
| False positive verification pipeline (6 gates, 13 devil's advocate checks) | trailofbits/fp-check | None | HIGH | Most impactful security gap |
| Completeness-enforcing Stop/SubagentStop hooks (LLM-prompt type) | trailofbits/fp-check | Stop hooks (uncommitted files, pending tasks) | HIGH | ToB pattern blocks on incomplete structured output |
| Security-scoped differential review (PR/commit) | trailofbits/differential-review | None | HIGH | BL reviews whole codebase; nobody reviews what changed |
| Variant analysis (pattern-hunt + CodeQL/Semgrep codegen) | trailofbits/variant-analysis | None | HIGH | Closes the "first instance only" gap |
| Agentic CI/CD audit (9 attack vectors) | trailofbits/agentic-actions-auditor | None | HIGH | Directly applicable to BL's own GitHub Actions |
| "Rationalizations to Reject" in agent prompts | trailofbits (all security skills) | None | HIGH | High-leverage authoring pattern, 2-3h per agent |
| Supply chain dependency risk audit | trailofbits/supply-chain-risk-auditor | None | HIGH | 6 risk criteria + gh CLI for live data |
| Static analysis orchestration (CodeQL + Semgrep + SARIF) | trailofbits/static-analysis | None | HIGH | Structured tool coordination |
| Audit context building (pre-hunt pure-context phase) | trailofbits/audit-context-building | research-analyst (informal) | MEDIUM | Formal separation of context vs. findings phases |
| Semgrep rule creation from security findings | trailofbits/semgrep-rule-creator | None | MEDIUM | Automated detection codification |
| Incident response workflow (triage→comms→postmortem) | anthropics/engineering | devops (informal) | MEDIUM | Structured incident lifecycle |
| Deploy checklist (pre-deployment verification) | anthropics/engineering | /verify phase | MEDIUM | BL verify is spec compliance; deploy-checklist is ops readiness |
| Tech debt identification and prioritization | anthropics/engineering | code-reviewer (informal) | MEDIUM | No dedicated tracking or categorization |
| Traffic-light compliance classification (GREEN/YELLOW/RED) | anthropics/legal | compliance-auditor (narrative) | MEDIUM | Routing urgency not formalized |
| Threat model requirement (privilege level, sandbox, attacker position) | trailofbits/fp-check | Security agent (OWASP patterns) | MEDIUM | BL finds issues but doesn't require threat model |
| Blast radius calculation for code changes | trailofbits/differential-review | None | MEDIUM | Quantitative caller impact before flagging HIGH |
| Exploitability rating (EASY/MEDIUM/HARD) with criteria | trailofbits/differential-review | None | MEDIUM | Structured severity rating |
| Fail-open vs fail-secure distinction | trailofbits/insecure-defaults | OWASP audit (general) | MEDIUM | BL covers secrets; doesn't specifically distinguish fail patterns |
| Property-based testing guidance | trailofbits/property-based-testing | masonry-tdd-enforcer (TDD only) | MEDIUM | PBT is a different methodology |
| Timing side-channel analysis | trailofbits/constant-time-analysis | None | LOW | Niche (crypto code only) |
| YARA rule authoring | trailofbits/yara-authoring | None | LOW | Malware detection niche |
| Firebase APK security scanning | trailofbits/firebase-apk-scanner | None | LOW | Android-specific |
| DWARF debugging format | trailofbits/dwarf-expert | None | LOW | Binary analysis niche |
| Zeroize audit (C/C++/Rust memory wiping) | trailofbits/zeroize-audit | None | LOW | Systems programming niche |
| Secret scanner hook (PreToolUse) | None in ToB | masonry-secret-scanner.js | BL wins | ToB does static analysis, BL blocks at write-time |
| Multi-agent campaign system | None | Full BL 2.0 system | BL wins | Neither repo competes with Trowel/Mortar |
| EMA training / prompt optimization loop | None | EMA pipeline + improve_agent.py | BL wins | No equivalent in either repo |

---

## Top 5 Recommendations

### 1. False Positive Verification Agent [12h, HIGH PRIORITY]

Build a `verification-analyst` agent that operates as a mandatory post-step after the security agent's scan. The agent takes the security agent's findings and runs each through the fp-check 6-gate pipeline. Gate 1 (Process): did we follow the full workflow? Gate 2 (Reachability): is the vulnerable code path reachable? Gate 3 (Real Impact): is this actual security impact, not operational robustness? Gate 4 (PoC Validation): was a proof of concept constructed? Gate 5 (Math Bounds): are integer/bounds calculations correct? Gate 6 (Environment): do environmental protections prevent exploitation?

Add the "Rationalizations to Reject" pattern to the security agent, verification agent, peer-reviewer, and compliance-auditor — explicitly naming LLM over-reporting bias and requiring devil's advocate completion before any TRUE POSITIVE verdict.

Also add an LLM-prompt Stop hook that blocks session termination if any security finding lacks a verified verdict.

**Files to create**: `template/.claude/agents/verification-analyst.md`, update `masonry/hooks/masonry-stop-guard.js` to add fp-check completeness check

---

### 2. Security Differential Reviewer [8h, HIGH PRIORITY]

Add a `security-diff-reviewer` agent that slots into the `/build` pipeline after code-reviewer. It receives the git diff, classifies each changed file by risk level (HIGH/MEDIUM/LOW), performs git blame on any removed security code, calculates blast radius for HIGH risk changes (N callers affected), and for HIGH risk changes runs the adversarial modeling template from differential-review: define attacker model → identify attack vectors → rate exploitability → build complete exploit scenario → check baseline violations.

Trigger: PostToolUse on git commit operations by git-nerd. Output: `findings/diff-security-review-{branch}.md`.

**Files to create**: `template/.claude/agents/security-diff-reviewer.md`

---

### 3. Agentic CI/CD Auditor + Supply Chain Auditor [6h, HIGH PRIORITY]

Merge two complementary skills into a single `supply-chain-auditor` agent covering both dependency risk and CI/CD workflow security:

Part A (supply chain risk): Implement the 6 ToB risk criteria against all project dependencies. Use `gh` CLI for live star counts and issue counts. Produce `findings/supply-chain-risk.md` with high-risk dependencies table, suggested alternatives, and risk factor counts.

Part B (agentic actions audit): When the project contains `.github/workflows/`, scan for the 9 attack vectors against AI agent integrations. Prioritize Vector A (env var intermediary) and Vector D (pull_request_target + checkout) as highest frequency misses.

This also directly audits BrickLayer's own `.github/workflows/` directory for vulnerabilities in how it invokes Claude Code Actions.

**Files to create**: `template/.claude/agents/supply-chain-auditor.md`

---

### 4. Variant Analysis Skill [6h, HIGH PRIORITY]

After any security finding is confirmed TRUE POSITIVE by the verification-analyst, auto-trigger a `/variant-hunt` workflow in the security agent. The 5-step method: understand root cause → match exact known instance first → identify abstraction points (what to keep specific vs. generalize) → generalize ONE element at a time, classifying each new match → stop when FP rate exceeds 50%.

Output: CodeQL/Semgrep rules for the confirmed vulnerability pattern, stored in `findings/variant-rules/{finding-id}/`. These rules become permanent detection tools that BrickLayer can run on future projects.

**Files to create**: `template/.claude/agents/variant-analyst.md` or add as a command in the security agent

---

### 5. Engineering Plugin Integration — Incident Response + Deploy Checklist + Tech Debt [4h, MEDIUM PRIORITY]

Extract three specific skills from the Anthropic engineering plugin and adapt for BrickLayer:

a) Add `/incident` command to BrickLayer's devops agent: triage severity → draft stakeholder communication → track timeline → generate postmortem. Outputs `findings/incident-{date}.md`.

b) Add deploy-checklist pre-step to the `/build` pipeline's completion: tests passing, no uncommitted changes, no critical security findings, rollback plan exists.

c) Add a `tech-debt-analyst` agent that categorizes technical debt by type (architecture, code quality, test coverage, documentation), assigns remediation priority, and produces a prioritized plan. Triggered by karen or by explicit `/tech-debt` command.

**Files to update**: devops agent, masonry-build-guard.js; **Files to create**: `template/.claude/agents/tech-debt-analyst.md`

---

## Novel Patterns to Incorporate (Future)

**LLM-as-completeness-gate hook**: The fp-check `SubagentStop` hook uses a prompt-type hook that asks an LLM "did this subagent produce all required sections?" and blocks if not. BrickLayer's SubagentStart hook tracks agent spawns but nothing verifies agent output completeness. This pattern could be applied to the synthesizer, verification, and peer-reviewer agents — blocking if they stop without all required sections present.

**Codebase-size-adaptive strategy**: The differential-review SMALL/MEDIUM/LARGE → DEEP/FOCUSED/SURGICAL strategy is a clean routing pattern that any BrickLayer agent doing code analysis could use. Currently agents try to read everything regardless of codebase size. Explicit size thresholds and analysis depth contracts would improve both quality and context efficiency.

**Progressive disclosure in agent docs**: ToB's SKILL.md → references/ pattern (SKILL under 500 lines, details in linked files, one level deep only, no chaining) is better discipline than BrickLayer's current agent files which tend to grow without bounds. Applying this to the larger BrickLayer agents (mortar.md, trowel.md) would improve maintainability.

**Skill routing/scoping via "When to Use" / "When NOT to Use"**: Every ToB skill has explicit positive and negative triggers. BrickLayer agents have trigger conditions but not explicit exclusions. Adding "When NOT to Use" sections to all agents would improve Mortar's routing precision and reduce misrouting.

**Per-function quality thresholds**: The audit-context-building skill specifies minimum 3 invariants, 5 assumptions, 3 risk considerations per function — measurable quality gates. BrickLayer's verification agent could adopt analogous minimums for findings: minimum evidence items, minimum reproduction steps, minimum impact assessment criteria before a finding is considered complete.

**CodeQL/Semgrep template resources**: The variant-analysis plugin ships ready-to-use starter templates for Python, JavaScript, Java, Go, and C++ in both CodeQL and Semgrep. BrickLayer could maintain a similar `masonry/security-rules/` directory of project-generated detection rules that accumulate across campaigns.

---

## File Inventory

### trailofbits/skills

| File | Category |
|------|----------|
| `README.md` | docs — full plugin catalog with categories |
| `CLAUDE.md` | docs — authoring guidelines, quality standards, PR checklist |
| `CODEOWNERS` | config — per-plugin GitHub ownership |
| `ruff.toml` | config — Python linting config |
| `.pre-commit-config.yaml` | config — pre-commit hooks |
| `plugins/agentic-actions-auditor/skills/agentic-actions-auditor/SKILL.md` | agent — 9-vector CI/CD AI security audit (21KB) |
| `plugins/agentic-actions-auditor/skills/agentic-actions-auditor/references/` | docs — per-vector reference files (A-I) + foundations + action-profiles + cross-file-resolution |
| `plugins/audit-context-building/skills/audit-context-building/SKILL.md` | agent — pure context building pre-hunt methodology |
| `plugins/audit-context-building/agents/` | agent — function-analyzer subagent |
| `plugins/audit-context-building/commands/` | agent — slash command |
| `plugins/building-secure-contracts/` | agent — blockchain vulnerability scanners |
| `plugins/burpsuite-project-parser/` | agent — Burp Suite file parser |
| `plugins/claude-in-chrome-troubleshooting/` | agent — Chrome MCP extension diagnostic |
| `plugins/constant-time-analysis/skills/` | agent — timing side-channel detection |
| `plugins/constant-time-analysis/ct_analyzer/` | code — Python timing analysis tool |
| `plugins/culture-index/` | agent — Culture Index survey interpretation |
| `plugins/debug-buttercup/` | agent — Kubernetes debug skill |
| `plugins/devcontainer-setup/` | agent — devcontainer configuration |
| `plugins/differential-review/skills/differential-review/SKILL.md` | agent — 7-phase security diff review |
| `plugins/differential-review/skills/differential-review/adversarial.md` | docs — Phase 5 attacker modeling |
| `plugins/differential-review/skills/differential-review/methodology.md` | docs — Phases 0-4 detailed workflow |
| `plugins/differential-review/skills/differential-review/patterns.md` | docs — vulnerability pattern reference |
| `plugins/differential-review/skills/differential-review/reporting.md` | docs — Phase 6 report structure |
| `plugins/dimensional-analysis/skills/` | agent — dimensional analysis annotation |
| `plugins/dimensional-analysis/agents/` | agent — dimensional analysis subagent |
| `plugins/dwarf-expert/` | agent — DWARF format expertise |
| `plugins/entry-point-analyzer/` | agent — smart contract entry point mapping |
| `plugins/firebase-apk-scanner/` | agent — Firebase Android security scan |
| `plugins/fp-check/skills/fp-check/SKILL.md` | agent — false positive verification pipeline |
| `plugins/fp-check/skills/fp-check/references/` | docs — standard-verification, deep-verification, gate-reviews, bug-class-verification, false-positive-patterns, evidence-templates |
| `plugins/fp-check/hooks/hooks.json` | hook — Stop + SubagentStop completeness enforcement |
| `plugins/fp-check/agents/` | agent — data-flow-analyzer, exploitability-verifier, poc-builder subagents |
| `plugins/gh-cli/` | agent — GitHub CLI URL interceptor |
| `plugins/git-cleanup/` | agent — git worktree/branch cleanup |
| `plugins/insecure-defaults/skills/insecure-defaults/SKILL.md` | agent — fail-open vulnerability detection |
| `plugins/insecure-defaults/skills/insecure-defaults/references/examples.md` | docs — fail-open vs fail-secure examples |
| `plugins/let-fate-decide/` | agent — cryptographic randomness for planning |
| `plugins/modern-python/` | agent — modern Python tooling standards |
| `plugins/property-based-testing/` | agent — property-based testing guidance |
| `plugins/seatbelt-sandboxer/` | agent — macOS Seatbelt config generation |
| `plugins/second-opinion/` | agent — external LLM code review |
| `plugins/semgrep-rule-creator/skills/` | agent — Semgrep rule creation |
| `plugins/semgrep-rule-creator/commands/` | agent — slash commands |
| `plugins/semgrep-rule-variant-creator/` | agent — cross-language Semgrep porting |
| `plugins/sharp-edges/` | agent — dangerous API/config detection |
| `plugins/skill-improver/` | agent — iterative skill refinement loop |
| `plugins/spec-to-code-compliance/` | agent — blockchain spec compliance |
| `plugins/static-analysis/skills/codeql/` | agent — CodeQL analysis skill |
| `plugins/static-analysis/skills/semgrep/` | agent — Semgrep analysis skill |
| `plugins/static-analysis/skills/sarif-parsing/` | agent — SARIF output parsing |
| `plugins/static-analysis/agents/` | agent — static analysis subagents |
| `plugins/supply-chain-risk-auditor/skills/supply-chain-risk-auditor/SKILL.md` | agent — 6-criteria dependency risk audit |
| `plugins/supply-chain-risk-auditor/skills/supply-chain-risk-auditor/resources/` | docs — results-template.md |
| `plugins/testing-handbook-skills/` | agent — Testing Handbook fuzzing/sanitizer skills |
| `plugins/variant-analysis/skills/variant-analysis/SKILL.md` | agent — 5-step pattern-hunt methodology |
| `plugins/variant-analysis/skills/variant-analysis/METHODOLOGY.md` | docs — detailed variant analysis strategy |
| `plugins/variant-analysis/skills/variant-analysis/resources/` | docs — CodeQL/Semgrep templates (5 languages each) |
| `plugins/workflow-skill-design/` | agent — plugin design pattern guidance |
| `plugins/yara-authoring/` | agent — YARA rule authoring |
| `plugins/zeroize-audit/` | agent — C/C++/Rust memory zeroization audit |
| `.codex/` | config — Codex compatibility skill mirrors |
| `.github/scripts/validate_codex_skills.py` | code — CI validation script |

### anthropics/knowledge-work-plugins

| File | Category |
|------|----------|
| `README.md` | docs — 11 plugin catalog with connectors |
| `.claude-plugin/marketplace.json` | config — full marketplace metadata (15KB) |
| `bio-research/` | agent — life sciences research skills |
| `cowork-plugin-management/skills/` | agent — plugin creation workflow |
| `customer-support/` | agent — ticket triage, response drafting |
| `data/skills/analyze/` | agent — data analysis skill |
| `data/skills/build-dashboard/` | agent — dashboard building |
| `data/skills/create-viz/` | agent — visualization creation |
| `data/skills/data-context-extractor/` | agent — dataset context extraction |
| `data/skills/explore-data/` | agent — exploratory data analysis |
| `data/skills/sql-queries/` | agent — SQL query writing |
| `data/skills/statistical-analysis/` | agent — statistical methods |
| `data/skills/validate-data/` | agent — data validation |
| `data/skills/write-query/` | agent — query writing with validation |
| `data/.mcp.json` | config — Snowflake, Databricks, BigQuery MCP connections |
| `design/` | agent — design workflow skills |
| `engineering/skills/architecture/` | agent — ADR creation and evaluation |
| `engineering/skills/code-review/` | agent — code review skill |
| `engineering/skills/debug/` | agent — structured debugging |
| `engineering/skills/deploy-checklist/` | agent — pre-deployment verification |
| `engineering/skills/documentation/` | agent — technical doc writing |
| `engineering/skills/incident-response/` | agent — incident lifecycle management |
| `engineering/skills/standup/` | agent — standup generation |
| `engineering/skills/system-design/` | agent — system architecture skill |
| `engineering/skills/tech-debt/` | agent — tech debt tracking |
| `engineering/skills/testing-strategy/` | agent — test strategy design |
| `engineering/.mcp.json` | config — GitHub, GitLab, Linear, Jira, Datadog, PagerDuty MCP |
| `enterprise-search/` | agent — federated search across tools |
| `finance/` | agent — financial workflows |
| `human-resources/` | agent — HR workflows |
| `legal/skills/brief/` | agent — legal briefing skill |
| `legal/skills/compliance-check/` | agent — compliance verification |
| `legal/skills/legal-response/` | agent — templated response generation |
| `legal/skills/legal-risk-assessment/` | agent — risk severity framework |
| `legal/skills/meeting-briefing/` | agent — meeting prep |
| `legal/skills/review-contract/` | agent — playbook-based contract review |
| `legal/skills/signature-request/` | agent — signature workflow |
| `legal/skills/triage-nda/` | agent — GREEN/YELLOW/RED NDA classification |
| `legal/skills/vendor-check/` | agent — vendor agreement status |
| `legal/.mcp.json` | config — Slack, Box, Egnyte, Jira, Microsoft 365 MCP |
| `marketing/` | agent — content and campaign skills |
| `operations/` | agent — operational workflow skills |
| `partner-built/` | agent — third-party contributed plugins |
| `pdf-viewer/` | agent — PDF extraction skill |
| `product-management/skills/` | agent — spec writing, roadmap, competitive |
| `productivity/skills/memory-management/` | agent — memory and context management |
| `productivity/skills/task-management/` | agent — task tracking skill |
| `productivity/skills/dashboard.html` | code — 97KB productivity dashboard HTML |
| `sales/` | agent — sales research and outreach skills |
