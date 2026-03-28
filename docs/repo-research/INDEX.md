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
| [forrestchang/andrej-karpathy-skills](forrestchang-andrej-karpathy-skills.md) | 2026-03-28 | 6 | 1 (SKILL.md) | 4 | Surgical Changes constraint + pre-implementation assumption gate in developer agent |
| [mk-knight23/AGENTS-COLLECTION](agents-collection.md) | 2026-03-28 | 3,475 | 700+ | 8 | Blind review system (3 reviewers + Devil's Advocate) |
| [0xfurai/claude-code-subagents](0xfurai-claude-code-subagents.md) | 2026-03-28 | 138 | 138 | 3 | Harvest 15 stack-matched agents directly |
| [wshobson/agents](wshobson-agents.md) | 2026-03-28 | 72 plugins | 112 | 5 | PluginEval statistical quality system (3-layer, Elo, Monte Carlo) |
| [quemsah/awesome-claude-plugins](quemsah-awesome-claude-plugins.md) | 2026-03-28 | catalog | 9,094 repos | 4 | chrome-devtools-mcp + code-review-graph (6.8x token reduction) |
| [nextlevelbuilder/ui-ux-pro-max-skill](nextlevelbuilder-ui-ux-pro-max-skill.md) | 2026-03-28 | ~30 | 7 skills | 5 | ui-reasoning.csv (161-row industry-specific design table) + BM25 search engine |
| [HKUDS/CLI-Anything](HKUDS-CLI-Anything.md) | 2026-03-28 | ~40 | gap-analyst + skill_generator | 4 | SKILL.md capability advertisement format + gap-analyst pre-build SOP |
| [yamadashy/repomix](yamadashy-repomix.md) | 2026-03-28 | 8 MCP tools | generate_skill | 4 | repomix MCP server + `generate_skill` auto-packaging (~70% token compression) |
| [promptfoo/promptfoo](promptfoo-promptfoo.md) | 2026-03-28 | 400+ | 40+ red-team plugins | 5 | Replace eval_agent.py with promptfoo (50+ assertions, native Claude, MCP vuln testing) |
| [coreyhaines31/marketingskills](coreyhaines31-marketingskills.md) | 2026-03-28 | 33 | 33 skills | 3 | Harvest 7 priority marketing skills for ADBP/JellyStream |
| [K-Dense-AI/claude-scientific-skills](K-Dense-AI-claude-scientific-skills.md) | 2026-03-28 | ~20 | 5+ agents | 4 | H0/H1/prediction triad + GRADE confidence replaces scalar 0-1 in BL findings |
| [nicobailon/visual-explainer](nicobailon-visual-explainer.md) | 2026-03-28 | ~20 | 1 SKILL + 8 commands | 8 | HTML synthesis reports — make findings/synthesis.md navigable browser HTML |
| [pbakaus/impeccable](pbakaus-impeccable.md) | 2026-03-28 | 210+ (21 skills × 10 providers) | 21 skills | 9 | AI Slop Test + quantitative Nielsen scoring (0-40) + Context Gathering Protocol |
| [tambo-ai/tambo](tambo-ai-tambo.md) | 2026-03-28 | large monorepo | 2 skills + 4 Charlie playbooks | 3 | Charlie proactive playbooks (dead-code cleanup, coverage bumping, release notes — weekly scheduled) |
| [VoltAgent/awesome-claude-code-subagents](voltagent-awesome-claude-code-subagents.md) | 2026-03-28 | 127+ agents | 127 | 4 | BGPT MCP for academic paper search + BrickLayer Claude plugin marketplace entry |
| [Skills Libraries Cross-Reference](skills-libraries.md) | 2026-03-28 | ~1,700+ across 5 repos | 205+ skills (alirezarezvani) | 3 | Semantic context degradation detection + LLM-as-Judge eval + spec-miner skill |

---

## Cross-Repo Synthesis

### Patterns appearing in 2+ repos:
- **Autonomous loops / Karpathy iteration** — ralph, autoresearch, ZEUS LOKI, pua, andrej-karpathy-skills: every serious repo has some form of evaluate→modify→keep/discard loop. BL has this but it's the exception to surfaced it explicitly.
- **Statistical agent evaluation** — wshobson PluginEval (3-layer, Monte Carlo, Elo) + AGENTS-COLLECTION EDD pass@N/^N: quality scoring is a recurring theme. BL's heuristic loop is behind.
- **Parallel multi-agent debugging** — wshobson agent-teams debug preset + AGENTS-COLLECTION ZEUS LOKI: competing hypothesis parallel investigators is a proven pattern.
- **Fail-closed defaults** — AGENTS-COLLECTION TITAN/ZEUS + wshobson defaults-to-FAIL: every quality system defaults FAIL, must earn PASS.
- **AST/semantic context** — code-review-graph, lsp-index-engineer: blast-radius context injection instead of exhaustive file reads.
- **SKILL.md capability advertisement** — CLI-Anything, impeccable, tambo, visual-explainer, VoltAgent, antigravity, alirezarezvani: YAML frontmatter on SKILL.md is converging as the standard for agent discoverability. BL uses .md without structured frontmatter.
- **Plugin marketplace distribution** — tambo, impeccable, VoltAgent, visual-explainer, CLI-Anything: every major skills repo ships a `.claude-plugin/marketplace.json`. BL agents are distributed by cloning — no packaging.
- **Project context file gates skill execution** — impeccable (`.impeccable.md`), CLI-Anything (`skill_generator.py`), tambo (`devdocs/CLAUDE_SKILLS.md`): all serious skill repos gate execution on an explicit context file. BL has `project-brief.md` for campaigns but not for dev tasks.
- **Proactive automation (scheduled AI)** — tambo Charlie (4 weekly playbooks): scheduled AI runs creating PRs/issues/coverage bumps. BL automation is 100% reactive.
- **Quantitative scoring rubrics** — impeccable (Nielsen 0-40, audit 0-20) + wshobson PluginEval + AGENTS-COLLECTION EDD: numeric scores enable training signal. BL uses qualitative verdicts.
- **HTML visual output** — visual-explainer (8 commands, slide decks, Mermaid zoom/pan): all agent output as markdown is readable but not navigable. HTML output is a clear step up.
- **H0/H1 formal hypotheses** — K-Dense-AI-claude-scientific-skills: null/alternative hypothesis + prediction triad for falsifiable research. BL questions lack formal falsification conditions.
- **Context engineering as explicit discipline** — muratcankoylan Agent-Skills-for-Context-Engineering: 13 dedicated skills covering degradation detection, compression strategies, LLM-as-Judge, BDI architecture. BL's context management is implicit (token count hook only).
- **Skill decision tree chaining** — Jeffallan/claude-skills: explicit workflow sequences (Feature Dev → Bug Fix → Legacy Migration) as documentation patterns. BL's Mortar routing docs don't provide this level of task-specific chain guidance.
- **Structured challenge modes** — the-fool skill (antigravity, Jeffallan): devil's advocate + first principles + inversion + pre-mortem + Socratic — five modes for stress-testing decisions. BL's design-reviewer has no equivalent structured challenge pattern.
- **Gotchas sections** — muratcankoylan standardizes 5-9 failure mode entries per skill. BL agent files have no standardized failure documentation format.

---

## Build Queue (from repo research)

### CRITICAL Priority
- [ ] **Statistical agent quality system (BL-PluginEval)** — 3-layer eval: static analysis → LLM judge → Monte Carlo (N=50 runs, Wilson CI); Elo ranking for agent_db; 10-dimension scoring rubric; anti-pattern detection on onboard_agent.py (from wshobson/agents)
- [ ] **Agent anti-pattern detection** — OVER_CONSTRAINED, EMPTY_DESCRIPTION, MISSING_TRIGGER, BLOATED_SKILL, ORPHAN_REFERENCE checks in masonry-agent-onboard.js (from wshobson/agents)
- [ ] **Replace eval_agent.py with promptfoo** — YAML test suites, 50+ assertion types, `promptfoo eval --model claude-sonnet-4-6`, native Anthropic provider, dataset replay (from promptfoo/promptfoo)
- [ ] **promptfoo red-team campaigns** — `promptfoo redteam --plugins harmful:all,overreliance,excessive-agency,mcp`; 40+ plugins; MCP privilege escalation testing for masonry MCP tools (from promptfoo/promptfoo)
- [ ] **ui-reasoning.csv ingestion** — 161-row industry-specific design reasoning table → BM25 search in uiux-master workflow; `product_type` column maps to style + color + typography + anti-patterns (from nextlevelbuilder/ui-ux-pro-max-skill)

### HIGH Priority
- [ ] **Semantic context degradation detection** — Extend `masonry-context-monitor.js` to detect lost-in-middle, poisoning, distraction, and clash patterns via Ollama cosine similarity; emit DEGRADATION_WARNING to claims board when cosine similarity < 0.6 against original task (from muratcankoylan/Agent-Skills-for-Context-Engineering — 4h)
- [ ] **LLM-as-Judge evaluation** — Add `--eval-mode llm-judge` to `improve_agent.py`; pairwise comparison with position bias mitigation (run twice, swap order); rubric generation from high-quality examples; integrate alongside EMA heuristics (from muratcankoylan/Agent-Skills-for-Context-Engineering — 6h)
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
- [ ] **repomix MCP server** — `npx repomix-mcp`; 8 tools incl. `pack_codebase`, `grep_repomix_output`, `generate_skill`; Tree-sitter ~70% token compression; auto-generate BL skill packages (from yamadashy/repomix)
- [ ] **SKILL.md capability advertisement format** — Add YAML frontmatter (`name`, `description`, `triggers`, `model`, `tools`) to all BL agent .md files; update onboard_agent.py to parse it; enables `/subagent-catalog:search` style discoverability (from HKUDS/CLI-Anything + tambo + VoltAgent + antigravity + alirezarezvani)
- [ ] **gap-analyst agent** — runs inventory scan → re-scans after context build → priority gap analysis → confirm → implement; formalizes the pre-build SOP (from HKUDS/CLI-Anything)
- [ ] **HTML synthesis reports** — visual-explainer's SKILL.md + css-patterns.md + libraries.md as BL `/visual-report` skill; convert synthesis.md/build summaries/verify reports to navigable HTML with Mermaid zoom/pan, KPI cards, collapsible sections (from nicobailon/visual-explainer)
- [ ] **Visual diff review command** — port `diff-review.md` with 10-section structure, fact-sheet verification checkpoint, decision confidence tiers (sourced/inferred/not-recoverable), cognitive debt surfacing, re-entry context (from nicobailon/visual-explainer)
- [ ] **AI Slop Test + quantitative Nielsen scoring** — impeccable's `critique/SKILL.md` Nielsen heuristics (0-40, 10 heuristics), `audit/SKILL.md` 5-dimension 0-20 scoring, named anti-pattern vocabulary ("Inter trap", "glassmorphism trap") into uiux-master (from pbakaus/impeccable)
- [ ] **Context Gathering Protocol (.bricklayer.md)** — port impeccable's `teach-impeccable` skill; one-time project setup: discovers design context, asks targeted questions, writes `.bricklayer.md`; gates all dev/UI agent execution (from pbakaus/impeccable)
- [ ] **Charlie proactive playbooks** — 4 weekly scheduled runs: dead-code cleanup, coverage threshold bumping, release notes fetch, team updates; each creates Linear/GitHub issues autonomously (from tambo-ai/tambo)
- [ ] **@claude GitHub Actions responder** — `.github/workflows/claude.yml` using `anthropics/claude-code-action@beta`; triggers on `@claude` mentions in issues/PR comments; remote async Claude access (from tambo-ai/tambo)
- [ ] **BrickLayer Claude plugin marketplace entry** — `.claude-plugin/marketplace.json` + `plugins/bricklayer/` with skills for `/masonry-run`, `/build`, `/plan`, `/verify`; enables `claude plugin marketplace add bricklayer` one-command install (from VoltAgent + tambo + impeccable)
- [ ] **BGPT MCP for academic paper search** — `npx bgpt-mcp` at bgpt.pro/mcp/sse; `mcp__bgpt__search_papers` with 25+ fields; injects peer-reviewed citations into BL research campaign findings (from VoltAgent/awesome-claude-code-subagents)
- [ ] **Harvest 15 stack-matched agents** from 0xfurai/claude-code-subagents — python, rust, go, kotlin, bash, postgres, redis, neo4j, fastapi, nextjs, kafka, docker, opentelemetry, github-actions, vector-db (from 0xfurai research)
- [ ] **Harvest niche domain agents** from VoltAgent catalog — chaos-engineer, reinforcement-learning-engineer, legacy-modernizer, scientific-computing, geospatial-developer, embedded-developer, game-developer (from VoltAgent/awesome-claude-code-subagents)
- [ ] **Product discovery skill (/discover)** — chains ux-researcher + experiment-designer + discovery-coach patterns; takes vague product idea → user segment + 3 JTBD hypotheses + minimum experiment designs + PRD stub (from alirezarezvani/claude-skills — 5h)

### MEDIUM Priority
- [ ] **Constitutional AI critique loop** — Add critique-revise pass to `optimize_with_claude.py` after generating improved instructions; check against 10 anti-patterns; max 3 rounds (from wshobson/agents — S complexity)
- [ ] **Staged agent rollout** — 5%→20%→50%→100% with rollback triggers in `improve_agent.py` snapshot history (from wshobson/agents)
- [ ] **trailofbits/skills** — Add `differential-review`, `second-opinion` (multi-model Gemini/Codex), `semgrep-rule-creator` to BL security skill set (from quemsah catalog)
- [ ] **Karpathy 4 principles — Surgical Changes constraint** — Add explicit anti-adjacent-edit rule + dead-code ownership qualifier to `developer.md`, `fix-implementer.md`, `senior-developer.md`: "every changed line traces to the task; match existing style; only remove YOUR orphaned imports" (from forrestchang/andrej-karpathy-skills — 2h)
- [ ] **Karpathy 4 principles — Pre-implementation ambiguity gate** — Add Step 0 "Surface Ambiguities" before RED phase in `developer.md` and `fix-implementer.md`; state assumptions, pick most conservative interpretation, flag for redirect (from forrestchang/andrej-karpathy-skills — 3h)
- [ ] **Karpathy 4 principles — Before/after examples in agent prompts** — Add concrete bad-vs-correct code diffs to behavioral sections of `developer.md`, `typescript-specialist.md`, `python-specialist.md` (from forrestchang/andrej-karpathy-skills EXAMPLES.md — 4h)
- [ ] **Spec-miner skill (/spec-mine)** — reverse-engineer implicit specification from existing codebase; output contracts/invariants/patterns/entry-points to `.autopilot/spec-mined.md`; `/plan` picks it up as "Existing System Behavior" section (from Jeffallan/claude-skills + alirezarezvani — 3h)
- [ ] **Gotchas sections standardization** — Add 5-7 failure mode entries to every BL agent .md file following muratcankoylan format: "Gotcha: [what] — [why] — [how to avoid]"; gives EMA optimization loop structured failure signal (from muratcankoylan/Agent-Skills-for-Context-Engineering — 4h)
- [ ] **The Fool challenge modes** — Integrate 5 structured challenge modes (devil's advocate, first principles, inversion, pre-mortem, Socratic) into design-reviewer and hypothesis-generator agents (from Jeffallan + sickn33/antigravity)
- [ ] **Release manager skill (/release)** — reads conventional commits → bumps semver → generates structured release notes → runs readiness checklist (tests passing, migrations documented, rollback plan) (from alirezarezvani/claude-skills)
- [ ] **LOKI Reflect phase** in research loop — spawn reflect agent between specialist verdict and writing finding; flags low-confidence verdicts as UNCERTAIN (from AGENTS-COLLECTION — ZEUS LOKI)
- [ ] **LSP/semantic code index** — unified symbol graph via pyright/tsserver/gopls; `masonry_lsp_query` MCP tool; replaces exhaustive file reads in developer/diagnose agents (from AGENTS-COLLECTION — lsp-index-engineer)
- [ ] **Context compression skill** — formal compaction trigger at 70% utilization; active summarization targeting ≤500-token handoff; what to summarize (old tool outputs) vs preserve (original goal, key decisions, live state) (from muratcankoylan/Agent-Skills-for-Context-Engineering — AGENTS-COLLECTION — 3h)
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
- [ ] **H0/H1/prediction triad in questions.md** — Formal null hypothesis + alternative + falsification condition for every BL research question; GRADE evidence downgrade/upgrade rules replace scalar confidence (from K-Dense-AI/claude-scientific-skills)
- [ ] **GRADE confidence system** — replace 0.0-1.0 scalar with HIGH/MODERATE/LOW/VERY_LOW + deterministic downgrade triggers (study design, inconsistency, indirectness, imprecision, publication bias) in FindingPayload schema (from K-Dense-AI/claude-scientific-skills)
- [ ] **Competing hypotheses for INDETERMINATE** — When a question returns INDETERMINATE, spawn 2 specialist agents with opposing hypotheses; adversarial deliberation before final finding (from K-Dense-AI/claude-scientific-skills)
- [ ] **7 priority marketing skills** — harvest from coreyhaines31/marketingskills: product-positioning, go-to-market-strategy, content-marketing, growth-hacking, social-media-marketing, email-marketing, seo-strategy (from coreyhaines31/marketingskills)
- [ ] **Persona-based UX testing** — impeccable's 5 personas (Alex/Power User, Jordan/First-Timer, Sam/Accessibility, Riley/Stress Tester, Casey/Mobile) with selection matrix by interface type; add to uiux-master (from pbakaus/impeccable)
- [ ] **Interaction state checklist** — impeccable's `/polish` covers all 8 states (default/hover/focus/active/disabled/loading/error/success); add systematic checklist to code-reviewer for frontend PRs (from pbakaus/impeccable)
- [ ] **Plan review visual output** — port visual-explainer's `plan-review.md` to BL `/plan` output: current/planned architecture diagrams, blast radius mapping, understanding gaps dashboard (from nicobailon/visual-explainer)
- [ ] **Proactive table rendering** — BL agents auto-intercept 4+ row tables and render as HTML alongside markdown output (from nicobailon/visual-explainer)
- [ ] **DX optimizer agent** — build time targets, HMR thresholds, test suite satisfaction metrics; quantitative build performance goals (from VoltAgent/awesome-claude-code-subagents — dx-optimizer)
- [ ] **Chaos engineer agent** — hypothesis-driven chaos experiments, blast radius control, game day facilitation, CI/CD fault injection (from VoltAgent/awesome-claude-code-subagents)
- [ ] **Conventional commits + release-please** — `release-please.yml` GitHub Action; auto-generates release PRs from conventional commits; pairs with `/commit` skill (from tambo-ai/tambo)
- [ ] **multi-provider skills build system** — impeccable's `build.js` pattern: single source SKILL.md → 10 provider outputs (Claude, Cursor, Gemini, Codex, etc.); enables BL skills to target multiple AI coding tools (from pbakaus/impeccable)
- [ ] **Slide deck command** — port visual-explainer's `generate-slides.md` for BL campaign synthesis → magazine-quality slide decks with SlideEngine.js, 4 presets, scroll-snap navigation (from nicobailon/visual-explainer)
- [ ] **Persona concept for BrickLayer** — define 2-3 BL personas (Startup CTO, Research Analyst, Platform Engineer) as CLAUDE.md injection patterns that configure Mortar routing priorities and agent defaults (from alirezarezvani/claude-skills)
- [ ] **MCP developer skill (/mcp-build)** — takes OpenAPI spec, scaffolds MCP server (TypeScript or Python) with manifest.json, tool definitions, and basic tests (from Jeffallan/claude-skills + alirezarezvani)
- [ ] **Skill decision tree documentation** — document BL agent dispatch chains as explicit workflow sequences in CLAUDE.md: "Task X: agent A → agent B → verify with agent C" (from Jeffallan/claude-skills)
- [ ] **Context compression trigger** — `masonry-context-compress.js` hook fires at 70% capacity; outputs suggested compaction summary with what to summarize vs preserve (from muratcankoylan/Agent-Skills-for-Context-Engineering)

### LOW Priority
- [ ] soul.md ethical constraint doc per agent (from AGENTS-COLLECTION — ClawSec)
- [ ] AARRR / PLFS growth + ethical scoring agent (from AGENTS-COLLECTION — PULSE)
- [ ] SRE incident responder agent with blameless postmortem template (from AGENTS-COLLECTION — NEW-AGENTS)
- [ ] Spatial computing agents — visionOS/XR/Metal GPU (from AGENTS-COLLECTION — AGENCY-SOURCE)
- [ ] Chinese platform marketing specialists (from AGENTS-COLLECTION — AGENCY-SOURCE/MARKETING)
- [ ] Semantic release automation from conventional commits (from AGENTS-COLLECTION — ci-cd-workflows)
- [ ] SBOM + license compliance in security pipeline (from AGENTS-COLLECTION — security-workflows)
- [ ] VoltAgent language specialists — elixir-expert, swift-expert, rails-expert, kotlin-specialist for gaps (from VoltAgent catalog)
- [ ] n8n-skills — n8n workflow building skills for homelab automation context (from quemsah catalog)
- [ ] andrej-karpathy-skills principles — [fully researched](forrestchang-andrej-karpathy-skills.md); Surgical Changes + assumption-surface gate are HIGH gaps; see build queue items above
- [ ] Vercel share integration — visual-explainer's `share.sh` + vercel-deploy skill; one-command HTML report publishing (from nicobailon/visual-explainer)
- [ ] surf-cli AI image generation in slide decks (from nicobailon/visual-explainer)
- [ ] mcp-developer agent from VoltAgent — MCP server development, JSON-RPC 2.0 specialist (from VoltAgent)
- [ ] BDI cognitive architecture for Trowel — formal belief/desire/intention mental model for campaign conductor; improves wave boundary coherence (from muratcankoylan/Agent-Skills-for-Context-Engineering)
- [ ] Regulatory compliance skills (ISO 13485, MDR 2017/745, FDA 21 CFR Part 820, ISO 27001, GDPR) — relevant only if BL targets regulated industries (from alirezarezvani/claude-skills)
- [ ] C-level advisory agents (CTO/CFO/CMO personas) — out of BL's core domain but useful for ADBP strategic decisions (from alirezarezvani/claude-skills)
- [ ] Chaos engineer skill — fault injection planning, blast radius analysis, hypothesis-driven chaos experiments (from Jeffallan/claude-skills + sickn33/antigravity)
- [ ] Incident commander skill — P0-P4 severity classifier, runbook lookup, PIR generator (from sickn33/antigravity + alirezarezvani)
- [ ] Fine-tuning / LoRA skills — ML training pipeline, PEFT; outside BL's scope (from Jeffallan/claude-skills)
- [ ] Multi-tool format conversion — single source SKILL.md → Cursor/Aider/Windsurf outputs (from alirezarezvani/claude-skills)
- [ ] Skill security auditor — scan new agent .md files for injection/exfiltration patterns before onboarding (from sickn33/antigravity + alirezarezvani)

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
- `trailofbits/skills` — differential-review, second-opinion, semgrep-rule-creator (security-focused skills)
- `snarktank/everything-claude-code` — instinct system with `/loop-start`, `/quality-gate`
