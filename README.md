# BrickLayer

**Autonomous failure boundary research for complex systems.**

BrickLayer runs an AI agent loop that stress-tests business models, financial systems, and operational architectures — iterating on parameters, running simulations, and mapping exactly where things break. Not where things perform best. Where they fail, and why.

Most analysis asks: *what's the optimal scenario?*
BrickLayer asks: *what kills this?*

---

## How It Works

```
questions.md → agent picks question → simulate.py → verdict
     ↑                                                  ↓
hypothesis-generator ← findings/*.md ← finding written
```

The loop is autonomous. An AI orchestrator works through a question bank, runs simulations or qualitative research, writes findings, and generates new questions based on what it discovers. It never stops until you tell it to.

Each question maps to a failure hypothesis. Each simulation either confirms the system survives — or finds the exact parameter values that collapse it.

---

## Architecture

```
bricklayer/
├── bl/                        # Campaign engine (modular Python package)
│   ├── campaign.py            # Main loop — picks question, runs, records verdict
│   ├── questions.py           # questions.md parser + results.tsv I/O
│   ├── config.py              # Project config singleton
│   ├── history.py             # SQLite verdict history + regression detection
│   ├── followup.py            # Adaptive follow-up question generation (C-04)
│   ├── fixloop.py             # FAILURE → fix agent → re-run loop (C-06)
│   ├── goal.py                # Goal-directed question generation from goal.md (C-03)
│   ├── crucible.py            # Agent benchmarking via structural rubrics (C-15)
│   ├── hypothesis.py          # Hypothesis generation (local LLM)
│   └── runners/               # Mode-specific test runners
│       ├── performance.py     # Async HTTP load tests (locust-style sweeps)
│       ├── correctness.py     # pytest subprocess runner
│       ├── quality.py         # Static source analysis
│       ├── agent.py           # Claude CLI agent dispatcher
│       ├── http.py            # Single HTTP request/response checks (C-07)
│       └── subprocess_runner.py  # Arbitrary subprocess with verdict parsing (C-08)
├── agents/                    # Global specialist agents (shared across projects)
├── template/                  # Copy to start a new project
│   ├── simulate.py            # The model (agent edits SCENARIO PARAMETERS only)
│   ├── constants.py           # Immutable rules — never touched by agents
│   ├── program.md             # Loop instructions
│   ├── questions.md           # Question bank
│   ├── project-brief.md       # Human ground truth (Tier 1 authority)
│   ├── docs/                  # Supporting documents (specs, legal, research)
│   ├── findings/              # Per-question findings (*.md)
│   ├── results.tsv            # Run log
│   ├── analyze.py             # PDF report generator
│   └── .claude/agents/        # Project-specific agents
├── dashboard/                 # Web monitoring UI
│   ├── backend/               # FastAPI — reads project files, serves API
│   └── frontend/              # React + Vite — live question queue, findings feed
└── .claude/CLAUDE.md          # Master context — Claude reads this at session start
```

---

## Specialist Agents

BrickLayer uses a team of domain-specialist agents. Each knows its lane. Each stores and retrieves from shared memory so they don't duplicate work.

| Agent | Domain | What it does |
|-------|--------|--------------|
| `question-designer` | Init | Reads all project documents, identifies conflicts, generates the initial question bank. Applies 3-tier source authority — human docs override agent output. |
| `quantitative-analyst` | Live API testing | Makes real HTTP calls against the target system. Stores test memories, queries with paraphrases, runs consolidation, measures dedup behavior. Returns empirical verdicts, not simulated ones. |
| `regulatory-researcher` | Legal/Compliance | Researches regulatory classification, licensing, tax treatment, and case law. Uses live web sources. Flags post-training-cutoff items for validation. |
| `competitive-analyst` | Market | Maps analogous system failures, benchmarks fees and participation rates, assesses competitive moats. Pulls live pricing data from the web. |
| `benchmark-engineer` | Baselines | Establishes performance baselines before stress testing. Used when simulate.py calls live services. |
| `hypothesis-generator` | Discovery | Scans recent findings for patterns and gaps. Generates Wave N questions every 5 completed questions. Keeps high-severity threads alive. |
| `synthesizer` | Synthesis | Reads all findings at session end. Produces a cross-domain dependency map, failure mode hierarchy, and minimum viable change set. |
| `security-hardener` | Hardening | Audits source files for OWASP patterns, race conditions, and silent failure paths. Commits fixes with security tests. |
| `test-writer` | Coverage | Writes unit and integration tests for modules with coverage gaps. Follows the same RED-GREEN-REFACTOR cycle as the campaign loop. |
| `type-strictener` | Type safety | Reduces mypy errors, migrates deprecated APIs, replaces `Any` types. Bounded scope — one file at a time. |
| `fix-agent` | Fix loop | Invoked automatically on FAILURE verdicts (C-06). Reads the finding, applies a targeted fix, and returns a re-run verdict. Max 2 attempts before escalating to human. |

### Live Discovery

When a Critical or High severity finding is written, the loop immediately generates follow-up questions and inserts them before any remaining lower-priority work. The system self-directs — it doesn't wait for the next wave.

Every 5 completed questions, `hypothesis-generator` scans for cross-domain patterns that no initial question bank anticipates. This is where the interesting findings come from.

---

## Campaign Engine (`bl/`)

The `bl/` package is the modular campaign runner that powers the research loop. It can be used standalone via `python simulate.py --campaign` or embedded in larger automation pipelines.

### Runner Modes

Each question in `questions.md` declares a `[MODE]` in its header. The campaign engine dispatches to the matching runner:

| Mode | Runner | What it runs |
|------|--------|-------------|
| `performance` | `bl/runners/performance.py` | Async HTTP load sweeps — concurrent users, p50/p95/p99 latency, error rates |
| `correctness` | `bl/runners/correctness.py` | pytest subprocess — pass/fail verdict from test output |
| `quality` | `bl/runners/quality.py` | Static source analysis — reads files, identifies patterns |
| `agent` | `bl/runners/agent.py` | Spawns a specialist agent via `claude -p` |
| `http` | `bl/runners/http.py` | Single HTTP request/response checks — status, body, latency threshold |
| `subprocess` | `bl/runners/subprocess_runner.py` | Arbitrary subprocess with `expect_exit`, `expect_stdout` directives |

### Adaptive Behaviors

| Feature | Flag | What it does |
|---------|------|-------------|
| **Adaptive follow-up** (C-04) | on by default | On FAILURE or WARNING, generates sub-questions (Q2.4 → Q2.4.1/2/3) and appends them to `questions.md`. One level deep only. |
| **Fix loop** (C-06) | `--fix-loop` or `BRICKLAYER_FIX_LOOP=1` | On FAILURE, spawns `fix-agent` to fix and re-run. Max 2 attempts. Records `## Fix Attempt N` in the finding. |
| **Goal-directed campaigns** (C-03) | `--goal` | Reads `goal.md` from the project root, passes to local LLM (qwen2.5:7b), generates QG-prefixed questions targeting the stated goal. |
| **Local inference routing** (C-25) | automatic | Routes hypothesis generation and goal question synthesis to a local Ollama model, not the Claude API. Keeps token costs low for bulk generation. |
| **Verdict history** (C-05) | automatic | Persists all verdicts to `history.db` (SQLite). Detects regressions — if a previously HEALTHY question flips to FAILURE, it is flagged. |

### Agent Benchmarking (Crucible, C-15)

The Crucible benchmarks specialist agents against structural rubrics before trusting their verdicts in production campaigns. Each agent is scored on:

- Output schema compliance (required fields present)
- Verdict accuracy on known cases
- Evidence quality (specificity, sourcing)
- Commit behavior (did it actually write and commit the fix?)

Scores persist to `history.db`. Agents are tagged `promoted`, `active`, `flagged`, or `retired`. Run with:

```bash
python simulate.py --crucible
```

---

## Memory & Inter-Agent Communication

BrickLayer integrates with [System-Recall](https://github.com/Nerfherder16/System-Recall) for persistent, cross-session agent memory.

Each agent stores findings under a domain-scoped tag:

```
agent:quantitative-analyst    → failure boundaries, sensitivity rankings
agent:regulatory-researcher   → legal frameworks, INCONCLUSIVE flags
agent:competitive-analyst     → market analogues, fee/participation benchmarks
agent:synthesizer             → dependency maps, minimum viable change sets
agent:hypothesis-generator    → wave summaries, gap analysis
```

Agents query each other's prior work before running their own analysis:

```python
# regulatory-researcher checking what competitive-analyst found about enforcement trends
recall_search(
    query="enforcement regulatory shutdown analogues",
    domain="myproject-autoresearch",
    tags=["agent:competitive-analyst"]
)
```

This means a regulatory finding from session 1 informs the quantitative model in session 3 — without re-running the research.

**Without Recall**: each session starts cold. Agents re-research the same ground.
**With Recall**: agents build on each other's work across sessions, across questions, across domains.

---

## Web Research Tools

The regulatory and competitive agents use live web sources rather than relying on training data for time-sensitive questions:

| Tool | Used for |
|------|---------|
| `WebSearch` | Recent regulatory guidance, enforcement actions, rule changes |
| `WebFetch` | Primary source documents — actual regulatory text, fee schedules |
| `Exa` (MCP) | Semantic search for legal analysis, industry research, startup postmortems |
| `Firecrawl` (MCP) | Scraping regulatory agency pages, competitor pricing, industry data |

All sourced findings include the URL and access date. Anything not web-verified is flagged as training-data-only.

---

## Hooks

BrickLayer is designed to run inside Claude Code with hooks managing session lifecycle:

| Hook | Event | What it does |
|------|-------|-------------|
| `UserPromptSubmit` | Session start | Queries Recall for relevant prior findings, injects context into the prompt |
| `PostToolUse` | After file edits | Extracts facts from finding files, stores to Recall automatically |
| `Stop` | Session end | Stores session summary to Recall for the next session to pick up |

The hooks mean the agent never starts cold. Prior work surfaces automatically without explicit retrieval commands in every prompt.

---

## Dashboard

A lightweight web UI for monitoring runs without reading raw files.

**http://localhost:3100**

- **Status bar** — live question counts by status (PENDING / IN_PROGRESS / DONE / INCONCLUSIVE), verdict distribution (FAILURE / WARNING / HEALTHY)
- **Question queue** — full question bank with status, domain, and hypothesis. Add questions mid-loop without touching the file.
- **Finding feed** — findings as they land, sorted by verdict severity. Click to read the full finding.
- **Corrections** — flag a finding as wrong and add a human correction directly from the UI. The correction is appended to the finding file as Tier 1 authority — agents treat it as ground truth.
- **Project switcher** — switch between projects from the top bar. One dashboard instance serves multiple research projects.

---

## Source Authority Hierarchy

Agents are grounded in a 3-tier authority model that prevents hallucination-driven research:

| Tier | Source | Who edits | Authority |
|------|--------|-----------|-----------|
| 1 | `project-brief.md`, `docs/` | Human only | Ground truth. Agent output never overrides this. |
| 2 | `constants.py`, `simulate.py` | Human (constants) / Agent (scenario params only) | Structural constraints. |
| 3 | `findings/`, `questions.md` | Agent output | Lower authority. Overridden by Tier 1/2 on conflict. |

If Tier 1 and Tier 3 conflict, the agent writes a `CONFLICTS.md` for human resolution before continuing.

---

## What BrickLayer Is Good At

### Financial & Business Model Stress Testing
Any model with defined revenue mechanics, cost structures, and growth assumptions can be stress-tested. BrickLayer finds:
- The exact parameter values that push a model into insolvency
- How many simultaneous stressors a system can survive (compound failure)
- Whether recovery is possible and how long it takes
- What bridge capital is required and for how long
- The sensitivity ranking of every variable — what matters most

### Regulatory & Compliance Risk Mapping
Systems operating in ambiguous legal territory (fintech, crypto, benefits, healthcare, telecom) benefit from systematic regulatory questioning:
- Which regulatory frameworks apply and at what scale thresholds
- Where safe harbors exist vs. genuine unsettled law
- What licensing or no-action letters are required before expansion
- How design choices (transferability, redemption, custody) change the regulatory classification

### Platform & Network Economics
Two-sided marketplaces, loyalty programs, token ecosystems, and closed-loop payment systems have complex interdependencies:
- Chicken-and-egg cold start viability
- Network effect failure modes (defection, fragmentation, competitive entry)
- Recirculation and velocity dynamics
- Maximum concentration risk (what % of one party can exit before collapse)

### Infrastructure & Operational Resilience
Any system with SLAs, capacity constraints, or dependencies on third-party infrastructure:
- Outage duration vs. business impact thresholds
- Single point of failure exposure
- Cascade failure from component failure
- Wind-down liability and reserve adequacy

---

## Industries

BrickLayer has been applied to or is well-suited for:

| Industry | What it tests |
|----------|--------------|
| **Fintech / Payments** | Float economics, interchange viability, MSB licensing thresholds, closed-loop failure modes |
| **Benefits & HR Tech** | Participation rate assumptions, ERISA exposure, employer concentration risk, credit economics |
| **Crypto / Web3** | Token velocity, NonTransferable bypass vectors, upgrade authority risk, wind-down liability |
| **SaaS / Marketplaces** | Unit economics at scale, churn-to-growth sensitivity, competitive defection scenarios |
| **Healthcare** | Network adequacy, payer mix sensitivity, regulatory reclassification triggers |
| **Real Estate / PropTech** | Cap rate stress, occupancy thresholds, debt service coverage, portfolio concentration |
| **Insurance** | Actuarial assumption stress, reserve adequacy, catastrophe compounding |
| **Supply Chain** | Supplier concentration, lead time shock, inventory velocity, demand collapse |

---

## Key Metrics Produced

Every session produces a structured output across these dimensions:

- **Failure thresholds** — exact parameter values where verdict flips from HEALTHY to WARNING to FAILURE
- **Break-even analysis** — minimum scale, volume, or rate required for viability
- **Bridge capital requirements** — how much runway capital is needed, for how long, under what scenarios
- **Sensitivity rankings** — which variables move the needle most (where to focus)
- **Compound failure analysis** — which stressor combinations are worse than the sum of parts
- **Recovery timelines** — how long after a shock before the system returns to health
- **Regulatory exposure map** — which questions require outside counsel vs. internal monitoring
- **Minimum viable change set** — the smallest set of changes that eliminates the critical failure modes

---

## Getting Started

```bash
# Clone
git clone https://github.com/Nerfherder16/BrickLayer.git
cd BrickLayer

# Copy the template for your project
cp -r template/ myproject/
cd myproject/

# Set your project up
# 1. Edit project-brief.md — what the system does, key invariants
# 2. Drop specs/docs into docs/
# 3. Edit constants.py — real thresholds
# 4. Edit simulate.py — your actual model
# 5. Verify: python simulate.py → should print verdict: HEALTHY

# Start the dashboard (separate terminal)
bash ../dashboard/start.sh $(pwd)
# Open http://localhost:3100

# Generate the initial question bank
# Open Claude Code in myproject/ and run:
# "Act as the question-designer agent in .claude/agents/question-designer.md.
#  Read project-brief.md, all files in docs/, constants.py, and simulate.py.
#  Generate the initial question bank in questions.md."

# Start the research loop
claude --dangerously-skip-permissions \
  "Read program.md and questions.md. Begin the research loop from the first PENDING question. \
   If any file edit fails, follow the self-recovery steps in program.md immediately. NEVER STOP."
```

See `QUICKSTART.md` for the full reference including Wave 2 generation, session resumption, corrections, and report generation.

---

## Requirements

- Claude Code CLI
- Python 3.10+ with `reportlab`, `uvicorn`, `fastapi`
- Node.js 18+ (dashboard frontend)
- [System-Recall](https://github.com/Nerfherder16/System-Recall) (optional — enables cross-session agent memory)
- **Exa** (`exa-mcp-server`) — cloud API, key from [exa.ai](https://exa.ai). Enables semantic web search for regulatory and competitive agents.
- **Firecrawl** (`firecrawl-mcp`) — self-hostable ([github.com/mendableai/firecrawl](https://github.com/mendableai/firecrawl)) or cloud. Point `FIRECRAWL_API_URL` at your instance. Enables deep page scraping for regulatory text, fee schedules, and competitor data.

---

## Acknowledgments

BrickLayer is influenced by Andrej Karpathy's insight that the most productive use of a language model isn't answering questions — it's running in a tight feedback loop where each output becomes the next input. The idea that you can give an LLM a simulator, a question bank, and a write-back mechanism, then walk away while it maps the failure surface of a complex system, is a direct expression of that principle.

---

## License

MIT
