# Repo Research Index

Comparative analysis of GitHub repos against BrickLayer 2.0 capabilities.
All findings feed into the BrickLayer roadmap.

## How to run a new research

Invoke the `repo-researcher` agent:
```
Act as the repo-researcher agent in ~/.claude/agents/repo-researcher.md.
repo_url: https://github.com/owner/repo
output_dir: C:/Users/trg16/Dev/Bricklayer2.0/docs/repo-research/
```

Or via Mortar: "research this repo: https://github.com/owner/repo"

---

## Researched Repos

| Repo | Date | Files | Agents | High Gaps | Top Recommendation |
|------|------|-------|--------|-----------|-------------------|
| [mk-knight23/AGENTS-COLLECTION](agents-collection.md) | 2026-03-28 | 3,475 | 700+ | 8 | Blind review system (3 reviewers + Devil's Advocate) |
| [0xfurai/claude-code-subagents](0xfurai-claude-code-subagents.md) | 2026-03-28 | 138 | 138 | 3 | Harvest 15 stack-matched agents directly |
| [wshobson/agents](wshobson-agents.md) | 2026-03-28 | 72 plugins | 112 | 5 | PluginEval statistical quality system (3-layer, Elo, Monte Carlo) |
| [quemsah/awesome-claude-plugins](quemsah-awesome-claude-plugins.md) | 2026-03-28 | catalog | 9,094 repos | 4 | chrome-devtools-mcp + code-review-graph (6.8x token reduction) |
| ui-ux-pro-max-skill | 2026-03-28 | pending | — | — | Pending |
| CLI-Anything | 2026-03-28 | pending | — | — | Pending |
| repomix | 2026-03-28 | pending | — | — | Pending |
| promptfoo | 2026-03-28 | pending | — | — | Pending |
| marketingskills | 2026-03-28 | pending | — | — | Pending |
| claude-scientific-skills | 2026-03-28 | pending | — | — | Pending |
| VoltAgent/awesome-claude-code-subagents | 2026-03-28 | pending | — | — | Pending |
| pbakaus/impeccable | 2026-03-28 | pending | — | — | Pending |
| tambo-ai/tambo | 2026-03-28 | pending | — | — | Pending |

---

## Cross-Repo Synthesis

*(Populated after 3+ repos are researched)*

### Patterns appearing in 2+ repos:
- **Autonomous loops / Karpathy iteration** — ralph, autoresearch, ZEUS LOKI, pua, andrej-karpathy-skills: every serious repo has some form of evaluate→modify→keep/discard loop. BL has this but it's the exception to surfaced it explicitly.
- **Statistical agent evaluation** — wshobson PluginEval (3-layer, Monte Carlo, Elo) + AGENTS-COLLECTION EDD pass@N/^N: quality scoring is a recurring theme. BL's heuristic loop is behind.
- **Parallel multi-agent debugging** — wshobson agent-teams debug preset + AGENTS-COLLECTION ZEUS LOKI: competing hypothesis parallel investigators is a proven pattern.
- **Fail-closed defaults** — AGENTS-COLLECTION TITAN/ZEUS + wshobson defaults-to-FAIL: every quality system defaults FAIL, must earn PASS.
- **AST/semantic context** — code-review-graph, lsp-index-engineer: blast-radius context injection instead of exhaustive file reads.

---

## Build Queue (from repo research)

### CRITICAL Priority
- [ ] **Statistical agent quality system (BL-PluginEval)** — 3-layer eval: static analysis → LLM judge → Monte Carlo (N=50 runs, Wilson CI); Elo ranking for agent_db; 10-dimension scoring rubric; anti-pattern detection on onboard_agent.py (from wshobson/agents)
- [ ] **Agent anti-pattern detection** — OVER_CONSTRAINED, EMPTY_DESCRIPTION, MISSING_TRIGGER, BLOATED_SKILL, ORPHAN_REFERENCE checks in masonry-agent-onboard.js (from wshobson/agents)

### HIGH Priority
- [ ] **chrome-devtools-mcp** — Add `npx chrome-devtools-mcp@latest` to MCP config; performance tracing (LCP/CLS/INP), source-mapped debug, network waterfall. Official Google tool, 31.4K★. (from quemsah catalog)
- [ ] **code-review-graph** — AST knowledge graph for BL codebases; blast-radius context injection; 6.8x token reduction on reviews, 18 langs, incremental git hook. (from quemsah catalog)
- [ ] **worktrunk** — `cargo install worktrunk`; git worktree manager purpose-built for parallel AI agent workflows; `wt switch -c -x claude feat` spins up worktree+Claude in one command. (from quemsah catalog)
- [ ] **Parallel hypothesis debug teams** — `parallel-debugger.md` agent: 3 `diagnose-analyst` subagents with competing hypotheses, synthesis before fix; trigger on 3rd DEV_ESCALATE (from wshobson/agents)
- [ ] **Blind review system** — 3 parallel reviewers + Devil's Advocate agent; weighted consensus (from AGENTS-COLLECTION — ZEUS/TITAN)
- [ ] **Secret scanning hook** — `masonry-secret-scanner.js` PreToolUse with Gitleaks + Semgrep; critical given ADBP Solana keys (from AGENTS-COLLECTION — security-hooks)
- [ ] **Eval-Driven Development harness** — capability/regression/safety evals per agent + pass@1/pass@3/pass^3 metrics extending improve_agent.py (from AGENTS-COLLECTION — NEXUS/EDD)
- [ ] **Fail-closed defaults + confidence gating** in /verify — default verdict FAIL, only surface findings ≥80% confidence (from AGENTS-COLLECTION — TITAN/everything-cc)
- [ ] **PR-writer agent** — writes PR description, review checklist, links issues at /build completion (from AGENTS-COLLECTION — OpenClaw PR agent)
- [ ] **Named pipeline templates** — FEATURE-DEV/BUG-FIX/SECURITY-AUDIT as YAML files with typed agent handoffs (from AGENTS-COLLECTION — OpenClaw)
- [ ] **Dependency audit + file size enforcement hooks** — dep vuln scan on package.json/requirements.txt changes; hard block >300 lines (from AGENTS-COLLECTION — hooks-collection)
- [ ] **TDD depth upgrade** — `tdd-orchestrator` opus agent covering full TDD lifecycle: mutation testing, property-based (Hypothesis/QuickCheck), chaos, ATDD/BDD, Chicago vs London school per component (from wshobson/agents)

### MEDIUM Priority
- [ ] **Constitutional AI critique loop** — Add critique-revise pass to `optimize_with_claude.py` after generating improved instructions; check against 10 anti-patterns; max 3 rounds (from wshobson/agents — S complexity)
- [ ] **Staged agent rollout** — 5%→20%→50%→100% with rollback triggers in `improve_agent.py` snapshot history (from wshobson/agents)
- [ ] **trailofbits/skills** — Add `differential-review`, `second-opinion` (multi-model Gemini/Codex), `semgrep-rule-creator` to BL security skill set (from quemsah catalog)
- [ ] **Karpathy 4 principles** — Inject into CLAUDE.md and developer/code-reviewer agents: (1) state assumptions, (2) simplicity first, (3) surgical changes, (4) goal-driven with success criteria (from quemsah catalog)
- [ ] **LOKI Reflect phase** in research loop — spawn reflect agent between specialist verdict and writing finding; flags low-confidence verdicts as UNCERTAIN (from AGENTS-COLLECTION — ZEUS LOKI)
- [ ] **LSP/semantic code index** — unified symbol graph via pyright/tsserver/gopls; `masonry_lsp_query` MCP tool; replaces exhaustive file reads in developer/diagnose agents (from AGENTS-COLLECTION — lsp-index-engineer)
- [ ] **Context compression** — active summarization at 120K tokens targeting ≤500-token handoff summary (from AGENTS-COLLECTION — ZEUS 98.6% compression)
- [ ] **sequential-thinking MCP** — add `@modelcontextprotocol/server-sequential-thinking`; inject for `reasoning: deep` tasks (from AGENTS-COLLECTION — MCP configs)
- [ ] **Confidence-gated output** (>80% threshold) for code-reviewer and research-analyst
- [ ] **Golden examples in agent prompts** — add worked examples to spec-writer, question-designer-bl2, synthesizer
- [ ] **Dual verification** — separate REVIEWER (quality/style) and VERIFIER (spec compliance/correctness) agents in /build
- [ ] **Agentic identity trust** — Ed25519 keypairs per agent for delegation chain verification (from AGENTS-COLLECTION — agentic-identity-trust)
- [ ] **CI/CD templates** — Node.js/Python/Go GitHub Actions workflows with change-detection (dorny/paths-filter) (from AGENTS-COLLECTION — ci-cd-workflows)
- [ ] **Conductor logical work unit tracking** — extend progress.json with `tracks[]` + `/revert-track` command; revert a feature even if it spans multiple commits (from wshobson/agents — L complexity)
- [ ] **repomix** — `npx repomix` to pack entire repo into single AI-friendly file for research campaign context (from quemsah catalog)
- [ ] **everything-claude-code instinct system** — `/loop-start`, `/loop-status`, `/quality-gate` skills; instinct confidence scoring + evolution loop (from quemsah catalog)
- [ ] **prompt-engineer agent upgrade** — Expand with Constitutional AI, CoT/ToT/self-consistency, model-specific optimization for Claude Sonnet 4.6/Haiku 4.5 (from wshobson/agents)
- [ ] **Harvest 15 stack-matched agents** from 0xfurai/claude-code-subagents — python, rust, go, kotlin, bash, postgres, redis, neo4j, fastapi, nextjs, kafka, docker, opentelemetry, github-actions, vector-db (from 0xfurai research)

### LOW Priority
- [ ] soul.md ethical constraint doc per agent (from AGENTS-COLLECTION — ClawSec)
- [ ] AARRR / PLFS growth + ethical scoring agent (from AGENTS-COLLECTION — PULSE)
- [ ] SRE incident responder agent with blameless postmortem template (from AGENTS-COLLECTION — NEW-AGENTS)
- [ ] Spatial computing agents — visionOS/XR/Metal GPU (from AGENTS-COLLECTION — AGENCY-SOURCE)
- [ ] Chinese platform marketing specialists (from AGENTS-COLLECTION — AGENCY-SOURCE/MARKETING)
- [ ] Semantic release automation from conventional commits (from AGENTS-COLLECTION — ci-cd-workflows)
- [ ] SBOM + license compliance in security pipeline (from AGENTS-COLLECTION — security-workflows)
- [ ] VoltAgent language specialists — elixir-expert, swift-expert, rails-expert, kotlin-specialist for gaps (from quemsah catalog)
- [ ] n8n-skills — n8n workflow building skills for homelab automation context (from quemsah catalog)
- [ ] andrej-karpathy-skills principles — already covered by Karpathy 4 principles item above

---

## Next Repos to Consider

From the quemsah catalog, high-value repos not yet researched:
- `obra/superpowers` (111.8K★) — full dev workflow: spec→plan→subagent TDD, systematic-debugging, using-git-worktrees
- `affaan-m/everything-claude-code` (106.9K★) — instinct system, harness audit scoring, quality-gate commands
- `snarktank/ralph` (13.7K★) — autonomous fresh-context PRD loop
- `tanweai/pua` (11.8K★) — high-agency autonomous self-improvement loop
- `max-sixty/worktrunk` (3.7K★) — Rust worktree manager (already recommended above)
- `tirth8205/code-review-graph` (3.5K★) — AST blast-radius context injection
- `ChromeDevTools/chrome-devtools-mcp` (31.4K★) — official Chrome DevTools MCP
