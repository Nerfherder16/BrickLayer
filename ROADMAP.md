# BrickLayer Roadmap

BrickLayer is a **universal autonomous research framework**. It runs structured question campaigns against any target — live APIs, codebases, documents, ML models, business processes, smart contracts — collects evidence, and identifies failure boundaries.

The human defines what matters. The agent asks the questions, runs the experiments, and reports what it found.

---

## Coordination Board

**Two conversations may be working on this simultaneously. Before touching anything, check CLAIMED status.**

| # | Area | Work Item | Status | Claimed By |
|---|------|-----------|--------|------------|
| C-01 | Architecture | Python module split — break simulate.py into `campaign.py`, `questions.py`, `findings.py`, `quality.py`, `scout.py` | **DONE** | conv:mar13-main |
| C-02 | Architecture | Runner Registry — formalize `Runner(Protocol)` plugin interface | **DONE** | conv:mar17 |
| C-03 | Campaign | Goal-directed campaigns via `goal.md` — agent generates question set from a target + goal | **DONE** | conv:mar17 |
| C-04 | Campaign | Adaptive follow-up -- FAILURE/WARNING auto-generates drill-down sub-questions (Q2.4 -> Q2.4.1) | **DONE** | bl2 self-audit (F7.2, F12.3) |
| C-05 | Campaign | Verdict history + regression detection -- flag regressions across runs | **DONE** | bl2 self-audit (F12.1, F12.2) |
| C-06 | Campaign | Fix loop integration -- FAILURE -> spawn fix agent -> re-run -> confirm HEALTHY | **DONE** | bl2 self-audit (healloop.py, F2.1-F2.6, F-mid.1) |
| C-07 | Runners | `http` runner formalization — extract from simulate.py into `runners/http.py` | **DONE** | bl2 self-audit |
| C-08 | Runners | `subprocess` runner formalization — extract into `runners/subprocess.py` | **DONE** | bl2 self-audit |
| C-09 | Runners | `static` runner formalization — extract into `runners/static.py` | **DONE** | bl2 self-audit (alias: quality runner) |
| C-10 | Runners | `browser` runner — Playwright-driven UI interaction testing | **FREE** | — |
| C-11 | Runners | `benchmark` runner — ML model ablation, latency, accuracy sweeps | **FREE** | — |
| C-12 | Runners | `document` runner — completeness/accuracy/consistency checks on docs vs code | **FREE** | — |
| C-13 | Runners | `contract` runner — Solana/EVM invariant checking and edge case fuzzing | **FREE** | — |
| C-14 | Meta-agents | Hypothesis-generator: generate Wave N+1 questions from findings patterns | **DONE** | bl2 self-audit (F9.1, F10.1, F10.2, F24.1) |
| C-15 | Meta-agents | Crucible: benchmark existing agents, promote/retire by score | **DONE** | bl2 self-audit (F17.1, F15.2, F22.1-F25.2) |
| C-16 | Dashboard | Question status live-update in dashboard UI | **DONE** | conv:mar17 |
| C-17 | Integrations | GitHub Actions hook — run campaign on PR, post findings as review comments | **FREE** | — |
| C-18 | Phase 3 | Hypothesis generation from git diffs — auto-question on commit | **FREE** | — |
| C-19 | Phase 3 | Cross-project knowledge transfer — bug patterns propagate across projects | **FREE** | — |
| C-20 | Campaign | Failure taxonomy — `classify_failure_type()` wired into every result; `failure_type` in findings + results.tsv | **DONE** | conv:mar13-afternoon |
| C-21 | Campaign | Confidence signaling — agents emit `high\|medium\|low\|uncertain`; orchestrator uses to route | **DONE** | conv:mar13-afternoon |
| C-22 | Campaign | Eval/scoring harness — lightweight scorer grades agent outputs; scores written to results.tsv | **DONE** | conv:mar17 |
| C-23 | Campaign | Introspection decorator — per-step trace `{thought, tool_call, result, tokens, latency, confidence, error_type}` written to Recall | **DONE** | conv:mar17 |
| C-24 | Engine | Skill retrieval gap — wire skill list from `~/.claude/skills/` into `session_ctx_block` in scout.py so agents see available skills | **DONE** | conv:mar17 |
| C-25 | Engine | D25.1 fix — `check_block()` in `_score_hypothesis_generator` uses BL 1.x field names (`Test:`, `Hypothesis:`) instead of BL 2.0 (`**Method**:`, `**Hypothesis**:`) | **DONE** | conv:mar17 |
| C-26 | Engine | A10.1 fix — `_build_findings_corpus()` sorts alphabetically, biasing corpus when over budget; should sort by severity before trimming | **DONE** | bl2 self-audit (F11.3 — severity sort already on line 64 of synthesizer.py) |
| C-27 | Agents | Model routing per agent — `model:` frontmatter in all template agents; `_read_frontmatter_model()` in `runners/agent.py` wires `--model` into `claude -p` subprocess | **DONE** | conv:mar17-agents |
| C-28 | Dashboard | Agent Fleet tab — `GET /api/agents` endpoint; `AgentFleet.tsx` with tier filter pills (opus/sonnet/haiku) and tier summary footer; tab bar added to App.tsx | **DONE** | conv:mar17-agents |
| C-29 | Meta-agents | `frontier-analyst` agent — exploration epistemology (possibility mapping, NOT falsification); `FRONTIER_VIABLE / FRONTIER_PARTIAL / FRONTIER_BLOCKED` verdicts; meta-campaign finding #5 | **DONE** | conv:mar17-agents |
| C-30 | Engine | Mortar Phase 2 hardening — WM1 startup validation (Mode field pre-flight), #7 finding validation (stub on failure), #8 global sentinel via `wc -l results.tsv`, #9 overseer escalation on FLEET_UNDERPERFORMING | **DONE** | conv:mar17-agents |
| C-31 | Agents | Planner → QD-BL2 interface — `planner.md` writes BL 2.0 Mode Allocation table to CAMPAIGN_PLAN.md; `question-designer-bl2.md` reads it via pre-flight bash check; meta-campaign finding #12 | **DONE** | conv:mar17-agents |
| C-32 | Engine | Hollow section bypass fix — `score_agent()` in agent-meta/simulate.py uses two-phase heading+body scan; `len(body_text) < 10` → -20 penalty; meta-campaign finding #10 | **DONE** | conv:mar17-agents |
| C-33 | Docs | `template/docs/question-schema.md` — canonical BL 2.0 question schema reference; all fields, valid Mode values with routing table, common mistakes; meta-campaign finding #13 | **DONE** | conv:mar17-agents |
| C-34 | Docs | QUICKSTART + CLAUDE.md updated with planner → qd-bl2 two-step question generation workflow; Agent Reference tables updated; meta-campaign finding #11 | **DONE** | conv:mar17-agents |

### Sessions active

| Session | Label | Focus |
|---------|-------|-------|
| mar13-afternoon | `conv:mar13-afternoon` | Infra: hooks, gateway, path fixes |

### How to claim work

When starting an item, update its row:
```
| C-03 | Campaign | Goal-directed campaigns ... | **IN PROGRESS** | conv:mar13-afternoon |
```

When done:
```
| C-03 | Campaign | Goal-directed campaigns ... | **DONE** | conv:mar13-afternoon |
```

Use a short label for `Claimed By` — date + session context is enough (`conv:mar13-morning`, `conv:mar14`).

---

## Completed Work

| Item | Description | Commit |
|------|-------------|--------|
| simulate.py root move | Moved simulate.py to autosearch root; fixed AUTOSEARCH_ROOT path constant (.parent.parent → .parent) | `conv:mar13-afternoon` |
| Path refs updated | prepare.md, retrospective.md, launcher prompt — all recall/simulate.py → simulate.py | `conv:mar13-afternoon` |
| settings.json cleanup | Removed stale temp-dir PostToolUse hook; recall-session-summary timeout 30→10s | `conv:mar13-afternoon` |
| bricklayer .claude.json | Replaced individual MCP server entries with single gateway endpoint | `conv:mar13-afternoon` |
| Stop hook speed fix | recall-session-summary.js timeouts cut to 4s; hard 8s cap added | `conv:mar13-afternoon` |
| bricklayer-retro.js | Async stop hook writes .retro-pending marker; launcher detects on startup | `conv:mar13-afternoon` |
| Launcher DISABLE_OMC | BrickLayer terminals launch with DISABLE_OMC=1 --no-mcp --dangerously-skip-permissions | `conv:mar13-afternoon` |
| FastMCP gateway | mcp_gateway.py proxying recall/github/context7/firecrawl/exa on port 8350 | `conv:mar13-afternoon` |
| Gateway auto-start | Launcher starts gateway before opening Claude; green dot status indicator in header | `conv:mar13-afternoon` |
| Wave 1–10 campaigns | Full BrickLayer campaign against Recall — 10 waves, 11+ findings | `aee05df` |
| Dashboard | React+FastAPI dashboard — question bank, live status, block-format parser | `efd7cfd` |
| Pre-commit hook | `scripts/pre-commit.py` — lint-guard + commit-reviewer + noqa escape | `71d2495` |
| 6 framework agents | scout, probe-runner, triage, retrospective, test-writer, type-strictener | `d62a072` |
| forge-check | Detects agent fleet gaps, writes `FORGE_NEEDED.md` sentinel | `93d2306` |
| agent-auditor | Audits agent fleet, writes `AUDIT_REPORT.md` | `93d2306` |
| peer-reviewer | Re-runs tests and appends CONFIRMED/CONCERNS/OVERRIDE to findings | `93d2306` |
| mortar | Campaign conductor agent — owns the loop, routes questions, fires sentinels, handles OVERRIDE re-queuing | `conv:mar17` |
| planner | Pre-campaign strategic planner — D1–D6 domain risk ranking, writes CAMPAIGN_PLAN.md | `conv:mar17` |
| code-reviewer | Pre-commit quality gate — diff review, lint, regression check, APPROVED/NEEDS_REVISION/BLOCKED | `conv:mar17` |
| agent-meta campaign | `projects/agent-meta/` — meta-campaign that stress-tests the agent fleet itself; baseline: 28/28 HEALTHY, 96.1/100 avg | `conv:mar17` |
| BL 1.x agent upgrades | Added `## Inputs`, `## Output contract`, `## Recall` sections + BL 2.0 verdicts to 12 legacy agents | `conv:mar17` |
| simulate.py YAML fix | Block scalar description parser in agent-meta/simulate.py — handles `description: >` multi-line blocks | `conv:mar17` |
| forge v2.0 | Sentinel-driven autonomous agent factory — reads `FORGE_NEEDED.md`, creates agents, deletes sentinel | `2fb34b3` |
| Async checkpoint pattern | All meta-agents use background Popen spawn; only Forge is blocking | `fad9611` |
| program.md async wiring | Live Discovery + wave-start sentinel check added to template, recall, adbp program.md | `6882c0e` |
| simulate.py checkpoints | `_check_sentinels()`, `_spawn_agent_background()`, `_run_forge_blocking()`, `_inject_override_questions()` wired into `--campaign` loop | `9059d28` |
| Silent exception fixes | 3 bare `except Exception: pass` → logged stderr warnings | `d2895d4` |
| Failure taxonomy | `classify_failure_type()` in simulate.py — `syntax\|logic\|hallucination\|tool_failure\|timeout\|unknown`; `failure_type` field in verdict envelope, finding .md, and results.tsv | `conv:mar13-afternoon` |
| Confidence signaling | `classify_confidence()` + `CONFIDENCE_ROUTING` in simulate.py — `high\|medium\|low\|uncertain` → `accept\|validate\|escalate\|re-run`; wired into verdict envelope, finding .md, results.tsv | `conv:mar13-afternoon` |
| Eval/scoring harness | `score_result()` wired into `update_results_tsv()` — `eval_score` column (0.000–1.000) on every result; dashboard `parse_results()` picks it up via dynamic header zip; backward-compat with old TSVs; 8 new tests | `conv:mar17` |
| Agent model routing | `model:` frontmatter on all 27 template agents (opus/sonnet/haiku); `_read_frontmatter_model()` + `_MODEL_MAP` in `runners/agent.py`; `--model <full-id>` passed to every `claude -p` subprocess | `conv:mar17-agents` |
| Dashboard Agent Fleet | `GET /api/agents` reads `.claude/agents/*.md` frontmatter; `AgentFleet.tsx` with color-coded tier cards, filter pills, summary footer; Findings\|Agents tab bar in App.tsx | `conv:mar17-agents` |
| frontier-analyst agent | New agent for exploration-mode questions — possibility mapping, analogue identification, feasibility tiers; `FRONTIER_VIABLE/PARTIAL/BLOCKED` verdicts | `conv:mar17-agents` |
| Mortar Phase 2 hardening | WM1 startup validation pre-flight; finding validation with INCONCLUSIVE stub; global sentinel via `wc -l results.tsv` (survives resume); overseer escalation on FLEET_UNDERPERFORMING | `conv:mar17-agents` |
| Planner→QD-BL2 interface | Planner writes BL 2.0 Mode Allocation table; qd-bl2 reads CAMPAIGN_PLAN.md pre-flight; severed interface repaired | `conv:mar17-agents` |
| Hollow section bypass fix | agent-meta/simulate.py `score_agent()` two-phase heading+body scan; body < 10 chars → -20 penalty (harsher than missing) | `conv:mar17-agents` |
| question-schema.md | Canonical BL 2.0 question schema reference in `template/docs/`; all fields, Mode routing table, common mistakes | `conv:mar17-agents` |

---

## Architecture

### Current (v0.1)

```
autosearch/
  simulate.py           ← monolith: campaign runner + runners + quality scanner + scout
  agents/               ← specialist agents (md files, invoked via claude -p)
  template/             ← project template
  projects/             ← Gen2 projects (code-driven via simulate.py --campaign)
  adbp/ recall/         ← Gen1 projects (manual loop via program.md)
  dashboard/            ← FastAPI + React monitoring UI
  scripts/              ← pre-commit hook
```

### Target (v0.2 — module split)

```
autosearch/
  simulate.py           ← thin CLI entry point only
  campaign.py           ← --campaign loop, sentinel checks, agent spawning
  questions.py          ← parse/update questions.md
  findings.py           ← write findings, update results.tsv
  quality.py            ← source file scanning, pattern matching
  scout.py              ← Scout context assembly
  runners/
    base.py             ← Runner(Protocol) interface
    http.py             ← HTTP load + latency runner
    subprocess.py       ← pytest/cargo/jest runner
    static.py           ← agent-based static analysis runner
    browser.py          ← Playwright UI runner (Phase 2)
    benchmark.py        ← ML model runner (Phase 2)
```

### Verdict envelope (universal — all runners return this)

```json
{
  "question_id": "Q2.4",
  "verdict": "FAILURE | WARNING | HEALTHY | INCONCLUSIVE",
  "summary": "one-line evidence",
  "data": {},
  "details": "full evidence text"
}
```

---

## Phase 1 — Universal Foundation (Near-term)

These are the highest-value items before BrickLayer is used on new projects.

| # | Item | Notes |
|---|------|-------|
| 1.1 | **Runner Registry** | `Runner(Protocol)` — any runner that returns the verdict envelope plugs in. Board item C-02. |
| 1.2 | **Goal-Directed Campaigns** | Replace static `questions.md` with `goal.md`. Agent generates questions from goal + target. Board item C-03. |
| 1.3 | **Adaptive Follow-up** | FAILURE/WARNING auto-drills down. `Q2.4 -> Q2.4.1, Q2.4.2`. Board item C-04. **DONE** (bl2 self-audit) |
| 1.4 | **Verdict History** | Flag regressions (`HEALTHY -> FAILURE`). Board item C-05. **DONE** (bl2 self-audit) |
| 1.5 | **Fix Loop** | FAILURE -> fix agent -> re-run -> HEALTHY. Board item C-06. **DONE** (healloop.py, bl2 self-audit) |
| 1.6 | **Module Split** | Break simulate.py into focused modules. Board item C-01. |

---

## Phase 2 — Target Breadth (Medium-term)

Each item adds a new class of targets BrickLayer can run against.

| # | Item | Target |
|---|------|--------|
| 2.1 | ML Model Runner | Ollama models — accuracy, latency, ablation sweeps |
| 2.2 | Document Runner | Docs vs code — completeness, accuracy, consistency |
| 2.3 | Smart Contract Runner | Solana/Anchor — invariant checking, authority bypass |
| 2.4 | Browser/UI Runner | Playwright — interaction testing, visual regression |
| 2.5 | Multi-Agent Swarm | Parallel perf/correctness/security/quality campaigns |
| 2.6 | Baseline Anchoring | Lock known-good snapshot. Every run diffs against it. Deploy gate. |

---

## Phase 3 — Autonomy (Longer-term)

| # | Item |
|---|------|
| 3.1 | Self-improving question banks — upweight questions that find bugs, prune dead ones |
| 3.2 | Hypothesis generation from diffs — auto-question on each git commit |
| 3.3 | Cross-project knowledge transfer — bug patterns propagate to new projects |
| 3.4 | Natural language entry point — "I just added concurrent Neo4j writes" → 4 questions, 3 minutes |
| 3.5 | BrickLayer audits BrickLayer -- eats its own dog food (25 waves, 49 fixes, STOP recommended) |

---

## Design Principles

1. **Universal verdict envelope.** Every runner, every target, every question type produces the same `{verdict, summary, data, details}` shape.
2. **Questions are the product.** The question bank has compounding value. A good question asked 100 times across 100 projects is worth more than 100 one-off tests.
3. **Humans set goals, agents set questions.** The human knows what matters. The agent knows what to ask technically. Don't conflate them.
4. **Verdicts must be falsifiable.** HEALTHY requires specific evidence. FAILURE requires a reproduction path.
5. **Cheap at scale beats thorough occasionally.** 500 fast questions overnight finds more than 5 exhaustive questions quarterly.
6. **Failure boundaries, not pass/fail.** The goal isn't "does it work?" — it's "where does it stop working?"

---

## Target Universe

| Category | Examples |
|----------|---------|
| **APIs** | REST, GraphQL, WebSocket, gRPC |
| **Codebases** | Python, Rust, Kotlin, TypeScript, Solidity |
| **Test suites** | pytest, cargo test, jest, go test, anchor test |
| **ML models** | Ollama, OpenAI, HuggingFace — accuracy, latency, regression |
| **Documents** | API docs, READMEs, legal specs, architecture docs |
| **Smart contracts** | Anchor programs, EVM contracts, invariant checking |
| **Web UIs** | Playwright-driven interaction and visual regression |
| **Simulations** | Business models, financial projections, game theory |
| **Pipelines** | CI/CD, data pipelines, ETL |
| **Infrastructure** | Docker, Kubernetes, Proxmox — health and config drift |

---

## Current Integrations

- **Recall** (FastAPI + Qdrant + Neo4j) — first full campaign, v0.1 validation target
- **Exa MCP** — semantic research for question generation and finding enrichment
- **Firecrawl MCP** — documentation crawling for document runner

## Planned Integrations

- **GitHub Actions** — run campaign on every PR, post findings as review comments
- **ADBP Solana programs** — contract runner against benefit-credits and redemption programs
- **ADBP Kotlin services** — subprocess runner against Ktor test suites
- **BrowserMCP** — browser runner for web portal testing
