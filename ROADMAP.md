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
| C-03 | Campaign | Goal-directed campaigns via `goal.md` — agent generates question set from a target + goal | **DONE** | conv:mar13-c03 |
| C-04 | Campaign | Adaptive follow-up — FAILURE/WARNING auto-generates drill-down sub-questions (Q2.4 → Q2.4.1) | **DONE** | conv:mar13-c04 |
| C-05 | Campaign | Verdict history + regression detection — SQLite ledger, flag regressions across runs | **DONE** | conv:mar13-afternoon |
| C-06 | Campaign | Fix loop integration — FAILURE → spawn fix agent → re-run → confirm HEALTHY | **DONE** | conv:mar13-c06 |
| C-07 | Runners | `http` runner formalization — extract from simulate.py into `runners/http.py` | **DONE** | conv:mar13-c07c08 |
| C-08 | Runners | `subprocess` runner formalization — extract into `runners/subprocess.py` | **DONE** | conv:mar13-c07c08 |
| C-09 | Runners | `static` runner formalization — extract into `runners/static.py` | **FREE** | — |
| C-10 | Runners | `browser` runner — Playwright-driven UI interaction testing | **FREE** | — |
| C-11 | Runners | `benchmark` runner — ML model ablation, latency, accuracy sweeps | **FREE** | — |
| C-12 | Runners | `document` runner — completeness/accuracy/consistency checks on docs vs code | **FREE** | — |
| C-13 | Runners | `contract` runner — Solana/EVM invariant checking and edge case fuzzing | **FREE** | — |
| C-14 | Meta-agents | Hypothesis-generator: generate Wave N+1 questions from findings patterns | **DONE** | conv:mar13-afternoon |
| C-15 | Meta-agents | Crucible: benchmark existing agents, promote/retire by score — **checks & balances for Forge output** | **DONE** | conv:mar13-c15 |
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
| C-26 | Campaign | Synthesizer — reads all findings after each wave, calls Claude, produces `synthesis.md`: validated bets, dead ends, unvalidated bets, recommended next action; terminates campaign when confidence converges | **DONE** | conv:mar14 |
| C-27 | Architecture | Project Doctrine — per-project `doctrine.md` injected into every campaign session; defines core hypothesis, key constraints, open bets, and first-principles reasoning; prevents Claude from misinterpreting project context | **FREE** | — |
| C-28 | Campaign | Pre-flight mode validation — before spawning an agent, validate that the question's mode is supported by the project's runner registry; INCONCLUSIVE questions with "Unknown mode" are detected at campaign start, not after wasted execution | **FREE** | — |
| C-29 | Campaign | Remediation feasibility check — before executing corrective actions (backfill, amnesty, reconcile), model expected outcome vs HEALTHY threshold; if projected delta can't cross threshold, abandon and document as "structural fix required" instead of applying an ineffective patch | **FREE** | — |
| C-30 | Campaign | Question type enforcement — tag behavioral questions `[BEHAVIORAL]` (requires HTTP/test evidence) vs `[CODE-AUDIT]` (static analysis only); HEALTHY verdict requires live evidence; CODE-AUDIT questions cap confidence at `medium`; question-designer agent enforces ratio (≥60% BEHAVIORAL) | **FREE** | — |
| C-31 | Campaign | Cross-session status sync — atomic status updates: write DONE to questions.md at the same time as results.tsv, not at session end; add `--sync-status` subcommand that reconciles questions.md against results.tsv to recover from partial-session drift | **FREE** | — |

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
| Hypothesis generator (C-14) | `bl/hypothesis.py` — qwen2.5:7b reads results.tsv findings patterns, generates Wave N+1 PENDING questions in questions.md format; `--hypothesize` flag in simulate.py; auto-triggers when campaign bank exhausted | `conv:mar13-afternoon` |
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

### C-26 — Synthesizer

After each wave, reads all `findings/*.md` + `results.tsv` and calls Claude to produce `synthesis.md`.

**Output structure:**
```markdown
# Campaign Synthesis — Wave N

## Core Hypothesis Verdict
[CONFIRMED | UNCONFIRMED | PARTIALLY CONFIRMED] — one paragraph

## Validated Bets
- [bet]: evidence from Q3.5, Q6.4 — confidence high
- ...

## Dead Ends
- [path]: Q2.2, Q2.3 found nothing — stop probing here

## Unvalidated Bets
- [bet]: not yet tested — suggest Wave N+1 questions
- ...

## Recommended Next Action
CONTINUE | STOP | PIVOT — with specific reasoning
```

**Termination logic:**
- `STOP` when synthesizer says unvalidated bets = 0 or core hypothesis = CONFIRMED/REFUTED with high confidence
- `PIVOT` when a new direction emerges that the current question bank doesn't cover
- `CONTINUE` otherwise — hypothesis generator picks up

**Implementation:**
1. `bl/synthesizer.py` — reads findings dir + results.tsv, builds prompt, calls Claude, writes `synthesis.md`
2. `--synthesize` flag on `simulate.py`; auto-triggers after each wave alongside hypothesis generator
3. Synthesis output fed into hypothesis generator prompt as context (so new questions are grounded in accumulated findings)
4. Campaign loop checks synthesis recommendation before starting next wave

---

### C-27 — Project Doctrine

Per-project `doctrine.md` — injected into every campaign session before any question runs.

**Not a summary. Not a spec.** The reasoning chain: why this project exists, what the core bets are, what constraints are non-negotiable, what has already been decided and why.

**ADBP doctrine example topics:**
- Why 2x amplification — the math, the tax structure, the employer incentive
- Why NonTransferable — the SEC classification dependency, what breaks if removed
- The ERISA line — what triggers it, what must never be implemented
- Credit burn rate — what's been tried, what's uncertain, what the campaign is testing
- MSB partner dependency — why ADBP can't transmit money directly

**Format:**
```markdown
# [Project] Doctrine

## Core Hypothesis
What this project is trying to prove or disprove.

## Non-Negotiable Constraints
Things that cannot change regardless of findings.

## Open Bets (Unvalidated)
Decisions being made without proof — these are BrickLayer campaign targets.

## Closed Bets (Validated or Decided)
What has been confirmed, refuted, or decided with reasoning.

## First Principles
The 5-10 things Claude must understand before touching any question in this campaign.
```

**Injection:** `simulate.py --campaign` reads `doctrine.md` from project dir and prepends to every agent prompt. Claude always has the full context, not just the current question.

---

---

### C-28 — Pre-flight Mode Validation

**Problem**: Q8.1–Q8.4 all returned INCONCLUSIVE with "Unknown mode" errors. The benchmark-engineer agent spent full execution budget on questions whose modes (`concurrency`, `cache`, `embedding`, `logging`) weren't registered in simulate.py. The failure was detectable at parse time, not after 60+ seconds of agent work.

**Root cause**: questions.md accepts any string in the `Mode:` field. The campaign loop passes it directly to the agent with no validation.

**Fix**:
1. Add `REGISTERED_MODES` set to `bl/runners/base.py` — populated when runners are loaded
2. In `simulate.py --campaign`, before spawning any agent: check `question.mode in REGISTERED_MODES`
3. If not registered: immediately record INCONCLUSIVE with `failure_type=configuration`, log "mode '{mode}' not registered — skip", advance to next question
4. Add `--list-modes` flag to simulate.py for question authors to see what's available
5. question-designer agent prompt: inject `REGISTERED_MODES` list so it only generates questions with valid modes

**Expected impact**: Eliminates the entire class of "Unknown mode" INCONCLUSIVE results. Estimated 10–15% of wasted execution cycles in early campaigns.

---

### C-29 — Remediation Feasibility Check

**Problem**: Q11.2 amnesty applied `floor=0.3` to 3,858 memories and corpus mean moved 0.392→0.393 — negligible, and predictable in advance. The amnesty floor (0.3) was below the HEALTHY threshold (0.40). A pre-action calculation would have flagged this before executing.

**Root cause**: The fix loop (C-06) executes remediations without modeling expected outcome first. It acts, then measures.

**Fix**:
1. Add `estimate_remediation_delta(action, params, current_state) → float` to `bl/quality.py`
2. Before any corrective action in the fix loop: call estimator, compare projected state against HEALTHY threshold
3. If `projected_mean < threshold`: skip action, record finding note: "remediation insufficient — projected delta={delta:.3f}, threshold={threshold:.2f}; structural fix required"
4. Document the *correct* fix path in the finding instead of applying an ineffective patch
5. For known action types: codify estimation logic (amnesty: model distribution shift given floor; backfill: model mean delta given n_samples and boost magnitude)

**Design rule**: A remediation that cannot cross the HEALTHY threshold is worse than no remediation — it creates false confidence that action was taken.

---

### C-30 — Question Type Enforcement (Behavioral vs Code-Audit)

**Problem**: Q9.5.1 ("read memory.py and check transaction logic"), Q9.5.2 ("read neo4j_store.py and check rollback") produced low-confidence verdicts with no live evidence. These are static analysis questions dressed up as behavioral questions. The highest-value findings (reranker cv_score, importance calibration, browse crashes) all had HTTP evidence.

**Root cause**: questions.md has no distinction between questions that require live evidence and questions that only require reading source code. The campaign loop treats them identically.

**Fix**:
1. Add required `Type:` field to question format: `[BEHAVIORAL]` | `[CODE-AUDIT]`
2. BEHAVIORAL: requires HTTP call, test execution, or measurable live output to achieve HEALTHY/FAILURE verdict. If agent returns only code analysis: auto-downgrade to INCONCLUSIVE.
3. CODE-AUDIT: accepted as static analysis — caps confidence at `medium`, verdict ceiling at WARNING (can never be HEALTHY, only CONFIRMED/UNCONFIRMED)
4. question-designer agent: enforce ≥60% BEHAVIORAL ratio in each wave; flag CODE-AUDIT questions for pairing with a follow-up BEHAVIORAL companion
5. Add `--type-audit` flag to simulate.py that reports BEHAVIORAL/CODE-AUDIT ratio for the current question bank

**Expected impact**: Shifts campaign output toward evidence-backed verdicts. CODE-AUDIT questions remain useful for generating hypotheses but stop masquerading as confirmed findings.

---

### C-31 — Cross-Session Status Synchronization

**Problem**: After Waves 9–11, ~15 questions in questions.md still showed PENDING despite having DONE results in results.tsv. The campaign loop writes results.tsv and findings/*.md atomically but only updates questions.md status opportunistically (at the start of the next run, or not at all across session boundaries).

**Root cause**: questions.md status update is a separate write that can be skipped if the agent context is compacted, the session ends mid-loop, or the stop hook fires before the final status flush.

**Fix**:
1. Make questions.md status update part of the same atomic write as results.tsv: `record_verdict()` in `bl/findings.py` updates both in a single transaction
2. Add `--sync-status` subcommand: reads results.tsv, finds all question IDs with terminal verdicts (DONE/INCONCLUSIVE), marks them in questions.md — recovers from any accumulated drift
3. Add campaign startup check: before running any question, call `--sync-status` automatically to ensure questions.md reflects actual state
4. Dashboard: expose sync status as a one-click action in the UI (C-16 dependency)

**Expected impact**: Eliminates re-running already-answered questions after session resume. Prevents the "15 PENDING questions that are actually DONE" state that accumulates across long campaigns.

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
