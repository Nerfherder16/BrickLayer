# Repo Research: mk-knight23/AGENTS-COLLECTION

**Repo**: https://github.com/mk-knight23/AGENTS-COLLECTION
**Researched**: 2026-03-28
**Researcher**: github-researcher agent (general-purpose)
**Purpose**: Identify capability gaps and high-value patterns to incorporate into BrickLayer 2.0

---

## Verdict Summary

AGENTS-COLLECTION is a **reference archive** — broad coverage of agent patterns across 11 platforms, 700+ agents, multiple production deployments. BrickLayer is an **executable framework** — deeper in its domain. They are complementary.

**BrickLayer leads on:** execution runtime, research loop depth, 4-layer routing, DSPy prompt optimization, Recall integration, Kiln monitoring, 13-hook ecosystem.

**AGENTS-COLLECTION leads on:** security depth (post-quantum, DAST, SBOM), deployment infrastructure (blue-green, canary), eval rigor (pass@N/^N), skill packaging, cross-platform portability, growth/GTM agents.

---

## File Inventory

### Root Level
- `/README.md` — Master overview, 700+ agents, 11 platforms, statistics
- `/CLAUDE.md` — Kazi's Agents Army (10 mega-agents for Claude Code)
- `/AGENTS.md` — Same 10 agents for OpenAI Codex format
- `/.cursorrules` — Same 10 agents for Cursor IDE
- `/.gemini/GEMINI.md` — Same 10 agents for Google Gemini CLI
- `/.github/copilot-instructions.md` — Same 10 agents for GitHub Copilot
- `/INDEX.md` — Master index of all source locations
- `/AGENTIC_UPGRADE.md` — Manifest from 69-agent refinement pass
- `/CONTRIBUTING.md` — Contribution guidelines
- `/SECURITY.md` — Security disclosure policy

### HOOKS/
- `CLAUDE-CODE/hooks-collection.md` — 10 production hook implementations
- `QUALITY/quality-hooks.md` — pre-commit-config.yaml + linter configs
- `SECURITY/security-hooks.md` — DevSecOps pre-commit hooks
- `OPENCLAW/CLAWSEC-ADVISORY-GUARDIAN` — ClawSec hook directory

### WORKFLOWS/
- `CI-CD/ci-cd-workflows.md` — 7 GitHub Actions CI templates
- `SECURITY/security-workflows.md` — Full DevSecOps pipeline
- `DEPLOYMENT/deployment-workflows.md` — Blue-green/canary/rolling/GitOps
- `OPENCLAW/WORKFLOWS/update_clawdbot.md` — ClawDBot update workflow

### MCP/
- `CLAUDE-CODE/mcp.json` — 20 MCP server configurations
- `AWESOME-SERVERS/mcp-servers-collection.md` — 23 categorized MCP servers
- `NANOCLAW/.mcp.json` — NanoClaw-specific MCP config

### AGENTS/EVERYTHING-CC/
- `architect.md`, `planner.md`, `code-reviewer.md`, `database-reviewer.md`
- `doc-updater.md`, `e2e-runner.md`, `go-build-resolver.md`, `go-reviewer.md`
- `python-reviewer.md`, `refactor-cleaner.md`, `security-reviewer.md`
- `tdd-guide.md`, `build-error-resolver.md`

### AGENTS/NEW-AGENTS/
- `api-security-tester.md`, `performance-engineer.md`, `sre-incident-responder.md`
- `cloud-architect.md`, `data-engineer.md`, `mobile-architect.md`, `vulnerability-scanner.md`

### AGENTS/AGENCY-SOURCE/SPECIALIZED/
- `agentic-identity-trust.md`, `agents-orchestrator.md`, `lsp-index-engineer.md`
- `specialized-cultural-intelligence-strategist.md`, `specialized-developer-advocate.md`

### AGENTS/AGENCY-SOURCE/SPATIAL-COMPUTING/
- `visionOS-spatial-engineer.md`, `macos-spatial-metal-engineer.md`
- `xr-cockpit-interaction-specialist.md`, `xr-immersive-developer.md`
- `xr-interface-architect.md`, `terminal-integration-specialist.md`

### AGENTS/OPENCLAW/ (20 multi-agent folder listings)
- FEATURE-DEV: PLANNER, DEVELOPER, REVIEWER, TESTER, VERIFIER, SETUP
- BUG-FIX: TRIAGER, INVESTIGATOR, FIXER, PR, SETUP, VERIFIER
- SECURITY-AUDIT: SCANNER, PRIORITIZER, FIXER, TESTER, VERIFIER, PR, SETUP
- MAIN orchestrator

### DOCS/NANOCLAW/
- `SPEC.md` — Full NanoClaw architecture specification
- `nanoclaw-architecture-final.md` — Skills architecture deep spec

### DOCS/OFFICIAL-CLAWSEC/
- `clawsec-feed-SKILL.md`, `clawtributor-SKILL.md`, `prompt-agent-SKILL.md`
- `soul.md`, `guardian.md`, `heartbeat.md`, `alert-system.md`
- `community-patches-SKILL.md`, `update-protocol-SKILL.md`

---

## Architecture Overview

The repo is organized around 5 concepts:

1. **Kazi Mega-Agents (ZEUS–ORACLE)** — 10 hyper-specialized agents covering PM/architecture, eval-driven dev, 6-phase verification, security, design, growth, automation, competitive intel, documentation, database. Implemented identically across 5 platforms (Claude Code, Codex, Cursor, Gemini, Copilot).

2. **OpenClaw Named Pipelines** — Pre-defined multi-agent workflows (FEATURE-DEV, BUG-FIX, SECURITY-AUDIT) with typed handoff artifacts between named agents. Each agent has one role; artifacts are passed by reference.

3. **NanoClaw Personal Assistant Platform** — A full channel-abstracted AI assistant runtime. Skill package system with `manifest.yaml`, SHA-256 integrity verification, git merge-file conflict resolution. Sessions persist across restarts via Agent SDK `resume`.

4. **ClawSec Security Advisory System** — Community CVE feed with exploitability scoring, community incident reporting (CLAW-YYYY-NNNN format), scheduled audit cron, and `soul.md` ethical constraint documents per agent.

5. **Reference Library** — Hooks, CI/CD workflows, MCP configs, system prompts, deployment templates. Production-quality patterns ready to copy into any project.

---

## Key Agent Catalog

### ZEUS (Master PM/Architect)
- **Phase 0–6 lifecycle**: Discovery → Strategy → Build → Harden → Launch → Scale → Evolve
- **LOKI autonomous mode**: Reason → Act → Reflect → Verify (per-action, not just per-task)
- **Blind review**: 3 independent reviewers + Devil's Advocate (whose only job is finding failure modes)
- **98.6% context compression target** at handoff
- **Conductor artifacts**: Typed `conductor.json` consumed by downstream agents
- **Fail-closed**: Default verdict REJECT, must earn PASS

### NEXUS/EDD (Eval-Driven Development)
- Evals written **before** features (eval-first, stricter than TDD)
- **pass@1**: Passes on a single run
- **pass@3**: Passes on 3 independent runs
- **pass^3**: Passes 3 **consecutive** runs (eliminates flaky false positives)
- Behavioral evals, not just unit tests

### TITAN (6-Phase Verification)
- Build → TypeCheck → Lint → Test → Security → DiffReview (strict sequence)
- Default verdict: NEEDS WORK (not LGTM)
- Chooses London TDD (mockist) vs Chicago TDD (integration) per component type
- Chaos engineering built into phase 5

### SENTINEL (Security)
- STRIDE + DREAD scoring matrix (not just OWASP)
- Ed25519 agentic identity — each agent has a cryptographic identity
- Post-quantum: ML-DSA (Dilithium), ML-KEM (Kyber), SLH-DSA (SPHINCS+)
- Zero Trust for agent-to-agent communication

### PULSE (Growth/GTM)
- AARRR framework
- PLFS ethical scoring (Persuasion/Legitimacy/Fairness/Safety)
- 14-factor CRO index, Van Westendorp pricing model
- 5-phase launch playbook

### HERMES (Automation)
- Automation scoring 0.0–1.0 (quantifies how automatable a workflow is)
- Circuit breaker pattern for fragile automations
- MCP dynamic tool creation at runtime
- Multi-transport bots simultaneously (WhatsApp/Telegram/Slack/Discord)

### NanoClaw Skill Package System
```yaml
# manifest.yaml
adds:
  - path: src/feature.ts
    template: add/feature.ts.hbs
modifies:
  - path: src/index.ts
    strategy: append  # append | prepend | replace | merge
structured:
  - path: package.json
    merge: deep
conflicts:
  - path: src/config.ts
    resolution: user
depends:
  - discord
test: npm test -- --grep "feature"
```
SHA-256 hash of every modified file stored in `state.yaml`. Hash mismatch = refuse to apply skill.

---

## Feature Gap Analysis

| Feature | In AGENTS-COLLECTION | In BrickLayer 2.0 | Priority |
|---------|---------------------|-------------------|----------|
| **Fail-closed quality gates** | Default verdict REJECT/NEEDS WORK | /verify reports, doesn't block | HIGH |
| **Pass@N / Pass^N evals** | pass@1/3/^3 | TDD only, no flakiness guard | HIGH |
| **Devil's Advocate stage** | ZEUS — required pipeline stage | Not present | HIGH |
| **PR-writer agent** | OpenClaw PR agent | git-nerd commits but no PR writing | HIGH |
| **Dependency audit hook** | post-install scan, blocks on HIGH vulns | Lint only | HIGH |
| **File size enforcement hook** | 800-line hard block | Rule only, not enforced | HIGH |
| **Build verification on push** | PreToolUse Bash guard | Not present | HIGH |
| **Named pipeline templates** | FEATURE-DEV/BUG-FIX/SECURITY-AUDIT YAML | Generic orchestrator+worker | HIGH |
| **Scheduled tasks / cron MCP** | NanoClaw 8 MCP tools | Campaigns run to completion only | HIGH |
| **Golden examples in prompts** | Worked examples in planner.md | Abstract format descriptions only | HIGH |
| **sequential-thinking MCP** | In mcp.json configs | Not present | HIGH |
| **Confidence-gated output** | >80% threshold, log 60–80%, discard <60% | All findings surfaced | MEDIUM |
| **LOKI self-audit loop (RARV)** | Per-action Reason→Act→Reflect→Verify | Verify step only at task end | MEDIUM |
| **Agent phase lifecycle (0–6)** | ZEUS Discovery→Evolve | PENDING/IN_PROGRESS/DONE only | MEDIUM |
| **Context compression metric** | 98.6% target | Handoff protocol only | MEDIUM |
| **London + Chicago TDD** | TITAN chooses per component | Single TDD style | MEDIUM |
| **Chaos engineering in CI** | TITAN phase 5 | Not present | MEDIUM |
| **Session resume (Agent SDK)** | NanoClaw native | progress.json only | MEDIUM |
| **Skill package system** | manifest.yaml + SHA-256 + git merge | Copy-paste .md install | MEDIUM |
| **Skill hash integrity check** | SHA-256 state.yaml, refuse on mismatch | Not present | MEDIUM |
| **Change-detection CI** | dorny/paths-filter | No CI at all | MEDIUM |
| **Sharded test matrix** | strategy.matrix.shard | Not present | MEDIUM |
| **Semantic release automation** | .releaserc.json | Not present | MEDIUM |
| **STRIDE + DREAD scoring** | SENTINEL, system-prompts | OWASP only | MEDIUM |
| **SRE incident responder** | NEW-AGENTS | Not present | MEDIUM |
| **CVE feed with exploitability** | ClawSec | Not present | MEDIUM |
| **ADR format** | architect, system-prompts | Not present | MEDIUM |
| **Performance budget YAML** | system-prompts | Not present | MEDIUM |
| **Circuit breaker in automations** | HERMES | Not present | MEDIUM |
| **Soul.md / ethical constraints** | Per-agent ClawSec doc | Not present | LOW |
| **Agentic identity (Ed25519)** | SENTINEL, AGENCY-SOURCE | Not present | LOW |
| **Post-quantum crypto** | ML-DSA/ML-KEM/SLH-DSA | Not present | LOW |
| **Channel abstraction** | NanoClaw Channel interface | Not present | LOW |
| **AARRR growth framework** | PULSE | Not present | LOW |
| **Automation scoring** | HERMES 0.0–1.0 | Not present | LOW |
| **5-layer competitive analysis** | ORACLE | Not present | LOW |
| **Weak signal detection** | ORACLE | Not present | LOW |
| **Blue-green deployment** | deployment-workflows | Not present | LOW |
| **Canary + Prometheus gate** | Argo Rollouts AnalysisTemplate | Not present | LOW |
| **GitOps (ArgoCD)** | deployment-workflows | Not present | LOW |
| **SBOM generation** | security-workflows | Not present | LOW |
| **DAST (OWASP ZAP)** | security-workflows | Not present | LOW |
| **License compliance check** | security-workflows | Not present | LOW |
| **Multi-format portability** | .md/.mdc/SKILL.md/Pi/.toml | .md only | LOW |
| **Community incident reporting** | ClawSec clawtributor | Not present | LOW |
| **claude-teams MCP** | cs50victor/claude-code-teams-mcp | Mortar (custom) | LOW |
| **visionOS / XR agents** | AGENCY-SOURCE | Not present | LOW |
| **LSP indexing agent** | lsp-index-engineer | Not present | LOW |
| **Cultural intelligence agent** | Specialized agent | Not present | LOW |
| **Developer advocate agent** | Specialized agent | Not present | LOW |

---

## Top 5 Recommendations

### 1. Fail-Closed Defaults + Confidence Gating [2h, HIGH]

Add to all BrickLayer reviewer agents:
- Default verdict = FAIL. Must earn PASS with explicit positive evidence.
- Confidence threshold: only surface findings ≥80%. Log 60–79% internally. Discard <60%.
- Add masonry-stop-guard.js block: if `verify-report.md` verdict=FAIL, block Stop.

### 2. PR-Writer Agent [4h, HIGH]

New agent `pr-writer.md` that runs at `/build` completion:
- Reads progress.json task descriptions + git commits + changed files
- Produces: summary, change list, testing notes, review checklist, linked issues
- Invoked by build orchestrator after all tasks DONE; feeds into `gh pr create`

### 3. File Size + Dependency Audit Hooks [3h, HIGH]

Extend `masonry-lint-check.js`:
- Hard block on files >300 lines (not test files, not .min.)
- When package.json/requirements.txt/go.mod changes: run `npm audit --audit-level=high` / `pip-audit` / `govulncheck`
- Warn (non-blocking) on dep vulns; block on CRITICAL severity

### 4. Named Pipeline Templates [8h, HIGH]

New `.autopilot/pipelines/*.yml` schema with agent roles, `consumes`/`produces` artifact contracts, parallel/sequential dispatch. Three starter templates: `feature-dev.yml`, `bug-fix.yml`, `security-audit.yml`. /build orchestrator reads pipeline YAML instead of generic task list.

### 5. sequential-thinking MCP + pass^N [5h, HIGH]

Add `@modelcontextprotocol/server-sequential-thinking` to Masonry MCP config. Tag critical pipeline tasks with `reasoning: deep` → inject sequential-thinking into worker agents. Add pass^3 to test-writer for `@critical`-annotated tests (auth, payment, migrations, external API).

---

## Novel Patterns to Incorporate (Future)

- **LOKI RARV loop**: After every tool call — Reason, Act, Reflect, Verify. Not just at task boundaries.
- **Golden examples in agent prompts**: Add worked examples to spec-writer, question-designer-bl2, synthesizer.
- **Conductor artifacts**: Typed `conductor.json` coordination artifact passed between /build pipeline agents.
- **Devil's Advocate as required stage**: Dedicated spawn whose only job is finding failure modes before shipping.
- **Dual verification (REVIEWER ≠ VERIFIER)**: Code quality review and spec compliance verification as separate agents.
- **TRIAGER before BUG-FIX**: Severity/impact assessment before any investigation or code changes.
