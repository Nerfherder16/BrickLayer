# BrickLayer Roadmap

BrickLayer is a **universal autonomous research framework**. It runs structured question campaigns against any target — live APIs, codebases, documents, ML models, business processes, smart contracts — collects evidence, and identifies failure boundaries.

The human defines what matters. The agent asks the questions, runs the experiments, and reports what it found.

---

## Coordination Board

**Two conversations may be working on this simultaneously. Before touching anything, check CLAIMED status.**

| # | Area | Work Item | Status | Claimed By |
|---|------|-----------|--------|------------|
| C-01 | Architecture | Python module split — break simulate.py into `campaign.py`, `questions.py`, `findings.py`, `quality.py`, `scout.py` | **DONE** | conv:mar13-main |
| C-02 | Architecture | Runner Registry — formalize `Runner(Protocol)` plugin interface | **DONE** | conv:mar13-afternoon |
| C-03 | Campaign | Goal-directed campaigns via `goal.md` — agent generates question set from a target + goal | **FREE** | — |
| C-04 | Campaign | Adaptive follow-up — FAILURE/WARNING auto-generates drill-down sub-questions (Q2.4 → Q2.4.1) | **FREE** | — |
| C-05 | Campaign | Verdict history + regression detection — SQLite ledger, flag regressions across runs | **DONE** | conv:mar13-afternoon |
| C-06 | Campaign | Fix loop integration — FAILURE → spawn fix agent → re-run → confirm HEALTHY | **FREE** | — |
| C-07 | Runners | `http` runner formalization — extract from simulate.py into `runners/http.py` | **FREE** | — |
| C-08 | Runners | `subprocess` runner formalization — extract into `runners/subprocess.py` | **FREE** | — |
| C-09 | Runners | `static` runner formalization — extract into `runners/static.py` | **FREE** | — |
| C-10 | Runners | `browser` runner — Playwright-driven UI interaction testing | **FREE** | — |
| C-11 | Runners | `benchmark` runner — ML model ablation, latency, accuracy sweeps | **FREE** | — |
| C-12 | Runners | `document` runner — completeness/accuracy/consistency checks on docs vs code | **FREE** | — |
| C-13 | Runners | `contract` runner — Solana/EVM invariant checking and edge case fuzzing | **FREE** | — |
| C-14 | Meta-agents | Hypothesis-generator: generate Wave N+1 questions from findings patterns | **FREE** | — |
| C-15 | Meta-agents | Crucible: benchmark existing agents, promote/retire by score — **checks & balances for Forge output** | **FREE** | — |
| C-16 | Dashboard | Question status live-update in dashboard UI | **FREE** | — |
| C-17 | Integrations | GitHub Actions hook — run campaign on PR, post findings as review comments | **FREE** | — |
| C-18 | Phase 3 | Hypothesis generation from git diffs — auto-question on commit | **FREE** | — |
| C-19 | Phase 3 | Cross-project knowledge transfer — bug patterns propagate across projects | **FREE** | — |
| C-20 | Campaign | Failure taxonomy — `classify_failure_type()` wired into every result; `failure_type` in findings + results.tsv | **DONE** | conv:mar13-afternoon |
| C-21 | Campaign | Confidence signaling — agents emit `high\|medium\|low\|uncertain`; orchestrator uses to route | **DONE** | conv:mar13-afternoon |
| C-22 | Campaign | Eval/scoring harness — lightweight scorer grades agent outputs; scores written to results.tsv | **DONE** | conv:mar13-afternoon |
| C-23 | Campaign | Introspection decorator — per-step trace `{thought, tool_call, result, tokens, latency, confidence, error_type}` written to Recall | **DONE** | conv:mar13-afternoon |
| C-24 | Campaign | ML spec validator — re-run initial baseline questions to confirm model choices, thresholds, and embedding params are still valid | **FREE** | — |
| C-25 | Architecture | Local inference routing — lightweight BrickLayer ops (scoring, failure classification, confidence, hypothesis generation) routed to 3060 Ollama; reserve Claude API for heavy execution | **DONE** | conv:mar13-afternoon |

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
| forge v2.0 | Sentinel-driven autonomous agent factory — reads `FORGE_NEEDED.md`, creates agents, deletes sentinel | `2fb34b3` |
| Async checkpoint pattern | All meta-agents use background Popen spawn; only Forge is blocking | `fad9611` |
| program.md async wiring | Live Discovery + wave-start sentinel check added to template, recall, adbp program.md | `6882c0e` |
| simulate.py checkpoints | `_check_sentinels()`, `_spawn_agent_background()`, `_run_forge_blocking()`, `_inject_override_questions()` wired into `--campaign` loop | `9059d28` |
| Silent exception fixes | 3 bare `except Exception: pass` → logged stderr warnings | `d2895d4` |
| Module split (C-01) | `bl/config.py`, `bl/runners/`, `bl/agents/` — Runner(Protocol) interface; simulate.py thin CLI entry point | `conv:mar13-main` |
| Runner Registry (C-02) | `Runner(Protocol)` interface in `bl/runners/base.py`; http, subprocess, static runners return universal verdict envelope | `conv:mar13-afternoon` |
| Verdict history (C-05) | SQLite ledger in `history.db` per project; `record_verdict()` + `check_regression()` — flags HEALTHY→FAILURE regressions | `conv:mar13-afternoon` |
| AUTOSEARCH_ROOT path fix | Root simulate.py: `.parent.parent` → `.parent` (re-fixed after monolith copy reset it); `errors="replace"` on finding file reads | `conv:mar13-afternoon` |
| Failure taxonomy | `classify_failure_type()` in simulate.py — `syntax\|logic\|hallucination\|tool_failure\|timeout\|unknown`; `failure_type` field in verdict envelope, finding .md, and results.tsv | `conv:mar13-afternoon` |
| Confidence signaling | `classify_confidence()` + `CONFIDENCE_ROUTING` in simulate.py — `high\|medium\|low\|uncertain` → `accept\|validate\|escalate\|re-run`; wired into verdict envelope, finding .md, results.tsv | `conv:mar13-afternoon` |
| Introspection decorator | `@introspect_step` on `_run_and_record` — writes `{agent, phase, thought, tool_call, tool_result, latency_ms, confidence, error_type, timestamp}` to `introspect.jsonl` + fire-and-forget Recall POST | `conv:mar13-afternoon` |
| Eval/scoring harness | `score_result()` — weighted formula (evidence_quality×0.4 + verdict_clarity×0.4 + execution_success×0.2); `score` field in verdict envelope, finding .md, results.tsv | `conv:mar13-afternoon` |
| Local inference routing (C-25) | `classify_failure_type()`, `classify_confidence()`, `score_result()` try qwen2.5:7b at 192.168.50.62 first; heuristic fallback if unreachable | `conv:mar13-afternoon` |

---

## Architecture

### C-25 — Local Inference Routing (3060 Ollama)

The campaign loop has two classes of work:

**Heavy** — needs frontier intelligence, uses Claude API:
- Question execution (agent runner, correctness, quality)
- Fix agents, Forge agent creation
- Retrospective agent

**Light** — bookkeeping and meta-loop, can use local 7B:
- `score_result()` — grade evidence quality, verdict clarity, execution success
- `classify_failure_type()` — syntax|logic|hallucination|tool_failure|timeout
- `classify_confidence()` — high|medium|low|uncertain routing
- `hypothesis-generator` — generate Wave N+1 questions from findings patterns
- Peer-reviewer light pass — re-run test + sanity check (not deep analysis)

The 3060 runs its own Ollama instance at `http://localhost:11434`. The 3090 at
`192.168.50.62:11434` stays dedicated to Recall (signal detection + Graphiti).

**Implementation plan:**
1. Add `local_ollama_url` + `local_model` to `bl/config.py` (default: `http://localhost:11434`, `qwen2.5:7b`)
2. Add `bl/local_inference.py` — thin `ollama_complete(prompt)` wrapper with timeout + fallback
3. Replace regex heuristics in `classify_failure_type()` and `classify_confidence()` with local model calls
4. Replace hardcoded formula in `score_result()` with local model scoring prompt
5. Port `hypothesis-generator` agent to use local model instead of Claude API subprocess
6. Add `--local-inference` flag to simulate.py to opt in (off by default until validated)

**Model recommendation:** `qwen2.5:7b` (4.5GB at Q4_K_M — fits 3060's VRAM with headroom)

---

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
| 1.3 | **Adaptive Follow-up** | FAILURE/WARNING auto-drills down. `Q2.4 → Q2.4.1, Q2.4.2`. Board item C-04. |
| 1.4 | **Verdict History** | SQLite ledger. Flag regressions (`HEALTHY → FAILURE`). Board item C-05. |
| 1.5 | **Fix Loop** | FAILURE → fix agent → re-run → HEALTHY. Board item C-06. |
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
| 3.5 | BrickLayer audits BrickLayer — eats its own dog food |

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
