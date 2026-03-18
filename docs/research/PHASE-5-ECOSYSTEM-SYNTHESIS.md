# Phase 5 — BrickLayer 2.0 Comprehensive Ecosystem Synthesis

**Date**: 2026-03-17
**Status**: Ongoing Investigation
**Scope**: Complete agent interconnection graph, data flow topology, verdict routing completeness, and cross-project architectural integration

---

## 1. Agent Interconnection Map

### 1.1 Campaign Loop Hierarchy (Framework Level)

The campaign loop consists of 8 framework-level agents that span ALL projects:

```
┌─────────────────────────────────────────────────────────────────┐
│                   CAMPAIGN LOOP EXECUTION                        │
└─────────────────────────────────────────────────────────────────┘

  ONBOARD          DISCOVERY         TRIAGE & FIX       REFLECTION
   Phase            Phase             Phase              Phase

  ┌────────┐      ┌──────────┐      ┌──────────┐      ┌────────────┐
  │ scout  │─────>│probe-    │─────>│ triage   │─────>│retrospect  │
  │        │      │ runner   │      │          │      │ive         │
  └────────┘      └──────────┘      └──────────┘      └────────────┘
      ▲                ▲                  ▲                  ▼
      │                │                  │          ┌──────────────┐
      │                │            ┌─────┴──────────>│ forge        │
      │                │            │                 │              │
      │                │    ┌───────┴──────────────>│ (design new  │
      │                │    │      ┌────────────────>│  agents)     │
      │                │    │      │                 └──────────────┘
      │                │    │      │                        ▲
      │                │    ▼      ▼                        │
      │                │  ┌──────────────────────────────────┤
      │                │  │ FIX SPECIALIST AGENTS (dynamic)  │
      │                │  │ - security-hardener              │
      │                │  │ - test-writer                    │
      │                │  │ - type-strictener                │
      │                │  │ - perf-optimizer                 │
      │                │  │ - scope-analyzer                 │
      │                │  │ - [forge-created agents]         │
      │                │  └──────────────────────────────────┤
      │                │           ▲                        │
      │                │           │ (closes findings)      │
      │                └───────────┴────────────────────────┘
      │
      └──────────────────────────────────────────────────────────
         (next wave / refresh)

```

**Campaign Loop Agents:**

| Agent | Role | Inputs | Outputs | Trigger |
|-------|------|--------|---------|---------|
| **scout** | Generate initial questions.md | target_git, stack, project_name | questions.md with 15-20 Q1.1-Q1.N | New project or question refresh |
| **probe-runner** | Execute a PENDING question | question_id, test_cmd, hypothesis | verdict + evidence | Every PENDING in the loop |
| **triage** | Group FAILURE/WARNING findings | findings_dir, verdict distribution | fix batches, agent assignments | After discovery wave |
| **scope-analyzer** | Map all call sites before fix | target_file, fix_scope | scope.json with impact map | Before any fix agent touches code |
| **regression-guard** | Re-run prior HEALTHY probes | prior_results, current_codebase | regression report | After every code commit |
| **retrospective** | Pattern analysis + next wave | all findings, synthesis summary | Wave N+1 hypothesis list | After each wave completes |
| **forge** | Design new specialist agents | forge_needed.md, evidence | {agent_name}.md files | INCONCLUSIVE + no matching agent |
| **crucible** | Benchmark + promote/retire agents | agent_outputs, test results | agent_score.json, tier updates | Periodic quality review |

---

### 1.2 Fix Specialist Agents (Domain-Specific, Dynamic)

These agents are invoked by **triage** or **forge** when a specific failure mode is detected. Crucible benchmarks and promotes/retires them based on precision, safety, and efficiency.

**Specialist Tier (Framework Provided):**

| Agent | Category | Metric | Trigger | Success Criteria |
|-------|----------|--------|---------|------------------|
| **security-hardener** | Security | CVE/OWASP violations | Security FAILURE findings | Zero OWASP violations, all CVEs fixed, tests passing |
| **test-writer** | Correctness | coverage_delta | Correctness coverage < 70% | Coverage > 70%, all new tests pass, no test regressions |
| **type-strictener** | Types | mypy error count | Type FAILURE or `any` usage | Zero type errors, `any` count reduced, types remain importable |
| **perf-optimizer** | Performance | p99 latency / query count | Performance FAILURE findings | p99 latency reduced by >20% OR query count halved, no regressions |

**Forge-Created Agents (Project-Specific):**

Forge dynamically creates agents when triage finds a FAILURE/INCONCLUSIVE verdict with no matching specialist. New agents are written to `agents/{name}.md` with:
- Initial tier: `draft` (null benchmark_score)
- After 3+ successful runs: Crucible promotes to `candidate` (0.4–0.8 score)
- After 10+ runs with score > 0.8: Promoted to `trusted` (autonomous commits)
- Score < 0.4: Flagged for retirement

---

### 1.3 Pre-Commit Gate Agents (Validation Layer)

Run on `git diff --staged` before ANY commit. These gate commits to the repository.

| Agent | Role | Input | Output | Decision |
|-------|------|-------|--------|----------|
| **commit-reviewer** | Security, correctness, quality review | staged diff | review memo | APPROVE / REQUEST_CHANGES / BLOCK |
| **lint-guard** | Style + static analysis | staged diff | auto-fixed diff (if FIXED) | CLEAN / FIXED / ERRORS_REMAIN |
| **agent-auditor** | Validates agent output structure | agent outputs | audit report | PASS / WARNINGS / FAIL |
| **forge-check** | Detects gaps in agent coverage | all INCONCLUSIVE findings | forge_needed.md sentinel | (if gaps found) |

**Gate Decision Tree:**
```
commit requested
    ├─ commit-reviewer.verdict = BLOCK   → STOP (human override required)
    ├─ lint-guard.verdict = ERRORS_REMAIN → STOP (manual fix required)
    ├─ agent-auditor.verdict = FAIL       → STOP (output validation failed)
    ├─ forge-check detects gaps           → WRITE agents/FORGE_NEEDED.md (pause commit)
    └─ all gates = PASS/APPROVE           → COMMIT ALLOWED
```

---

## 2. Data Flow Topology

### 2.1 Question → Finding → Verdict → Action

The core data flow that drives the entire campaign:

```
questions.md (Tier 1 source)
    ↓
  [Parse Q{wave}.{num} with Mode + Status]
    ↓
    ├─ status = PENDING
    │   ↓
    │ probe-runner executes question
    │   ├─ Runs Test command
    │   ├─ Evaluates hypothesis
    │   └─ Returns verdict (FAILURE/WARNING/HEALTHY/INCONCLUSIVE)
    │
    ├─ status = DONE
    │   ↓
    │ (skip to next question)
    │
    └─ status = IN_PROGRESS
        ↓
      (resume from same point)

findings/ (Tier 3 output)
    ↓
  [Per-question {id}.md with frontmatter]
    ├─ verdict: FAILURE | WARNING | HEALTHY | INCONCLUSIVE
    ├─ category: D1/D2/D3/D4/D5/D6/F/A/V/R/E/M/P/Fr
    ├─ severity: critical | high | medium | low
    ├─ evidence: test output, metrics, code samples
    └─ mitigation: recommended agent or action

    ↓
  [Triage analyzes verdict distribution]
    ├─ FAILURE  → FIX SPECIALIST assignment
    ├─ WARNING  → CANDIDATE for fix
    ├─ HEALTHY  → CONFIRM via regression-guard
    └─ INCONCLUSIVE + no agent → FORGE signal

    ↓
  [Fix Specialist (or forged agent) runs]
    ├─ scope-analyzer maps impact
    ├─ Apply fix
    ├─ Re-run probe-runner to verify
    ├─ If verdict improved: commit + append finding
    └─ If verdict not improved: revert + mark INCONCLUSIVE

synthesis.md (End-of-session Tier 3)
    ↓
  [Retrospective analyzes all findings]
    ├─ Pattern detection: what failed, why, frequency
    ├─ Precedence ranking: highest-impact areas
    ├─ Coverage assessment: which domains need deeper Q's
    └─ Wave N+1 hypotheses: targeted questions for next iteration
```

**Backend Data Flow (FastAPI):**

```
Dashboard Frontend
    ├─ GET /questions        → parse_questions()       → questions.md parsed
    ├─ GET /findings         → parse_findings_index()  → findings/ metadata (cached 5s)
    ├─ GET /finding/{id}     → read findings/{id}.md   → full finding content (lazy)
    ├─ POST /question (add)  → append to questions.md  → return updated list
    ├─ POST /finding/{id}/correct → append Human Correction block
    └─ GET /agents           → list agents from agents/ dir → roster with model tiers

Security Validation:
    ├─ All project paths validated against AUTOSEARCH_BASE
    ├─ AUTOSEARCH_PROJECT env var or Query param
    └─ No symlink traversal attacks (is_relative_to check)
```

---

## 3. Verdict Taxonomy & Routing

### 3.1 Question Type Prefixes → Expected Verdicts

Each question has a **Mode** (from question-designer) that routes the question to the correct handler and informs expected verdict:

| Mode | Question Type | Executed By | Expected Verdicts | Routing |
|------|---------------|-------------|-------------------|---------|
| **correctness** | D1/D5/D6 (simulation) | probe-runner (subprocess) | FAILURE / WARNING / HEALTHY | None (terminal) |
| **quality** | D4 (code quality) | probe-runner + lint gates | WARNING / HEALTHY | commit-reviewer → lint-guard |
| **security** | D2 (legal/compliance) | probe-runner → scope-analyzer | FAILURE / WARNING / HEALTHY | → security-hardener if FAILURE |
| **performance** | D6 (metrics, throughput) | probe-runner (live service call) | FAILURE / WARNING / HEALTHY | → perf-optimizer if FAILURE |
| **agent** | A/F/V/R/E/M/P/Fr modes | forge-created specialist | FAILURE / INCONCLUSIVE / HEALTHY | → Crucible for scoring |

### 3.2 Terminal Verdicts (Verdict States with No Downstream Agent)

```
HEALTHY
├─ Question answered confidently
├─ No fix needed
└─ Trigger regression-guard re-run on next commit

INCONCLUSIVE
├─ Question unclear or contradictory evidence
├─ No agent matches the failure pattern
├─ Triggers forge signal (if not yet created)
└─ Marks question DONE (Wave N+1 will refine)

FAILURE (after all fix attempts exhausted)
├─ Fix specialist tried but improvement < threshold
├─ Max retry attempts exceeded
└─ Escalates to human review or flags for Wave N+1

WARNING
├─ Potential issue identified
├─ Fix specialist assigns priority but not blocking
└─ If not fixed in Wave 1, becomes FAILURE in Wave 2
```

### 3.3 Non-Terminal Verdicts (Routing to Actions)

```
FAILURE (within scope)
    ├─ Is there a matching agent?
    │  ├─ Yes → assign to that agent
    │  └─ No  → write FORGE_NEEDED.md (pause loop)
    │
    └─ Agent executes
       ├─ Fix applied → re-verify → verdict improves?
       │  ├─ Yes → COMMIT + append finding
       │  └─ No  → REVERT + mark INCONCLUSIVE
       │
       └─ Max retries exceeded → mark FAILURE (terminal)

INCONCLUSIVE
    ├─ No matching agent
    └─ forge writes new agent
       ├─ Deploy as draft tier
       └─ Loop resumes with new agent available
```

---

## 4. Mode Routing Logic (All 9 Operational Modes)

The 9 modes correspond to the 9 question type prefixes and determine which handler processes each question:

```
┌────────────────────────────────────────────────────────────┐
│           QUESTION TYPE PREFIX → MODE ROUTING              │
└────────────────────────────────────────────────────────────┘

D1-D6 (Domain Questions)
├─ D1: Diagnose (correctness)        → mode=correctness → probe-runner
├─ D2: Audit (legal/compliance)      → mode=security   → scope-analyzer
├─ D3: Competitive/Research          → mode=research   → document-specialist
├─ D4: Quality (code quality)        → mode=quality    → lint-guard
├─ D5: Data (simulation parameters)  → mode=correctness → probe-runner
└─ D6: Performance (metrics)         → mode=performance → perf-optimizer

Non-Domain Questions
├─ A (Audit): Finding pattern        → mode=audit      → agent-auditor
├─ F (Fix): Verification loop        → mode=fix        → scope-analyzer + specialist
├─ V (Validate): Integration test    → mode=validate   → regression-guard
├─ R (Research): External knowledge  → mode=research   → document-specialist
├─ E (Evolve): Architecture/design   → mode=evolve     → architect agent (future)
├─ M (Monitor): Observability        → mode=monitor    → metrics analyzer (future)
├─ P (Predict): Forecasting          → mode=predict    → scientist agent (future)
└─ Fr (Frontier): Possibility space  → mode=frontier   → frontier-analyst agent

Verdict Routing Within Each Mode
├─ correctness/quality/security/performance
│   ├─ HEALTHY    → regression-guard (next commit)
│   ├─ WARNING    → candidate for fix (fix specialist optional)
│   ├─ FAILURE    → fix specialist (mandatory)
│   └─ INCONCLUSIVE → forge + draft new agent
│
├─ audit/validate/research
│   ├─ HEALTHY    → confirm + move to DONE
│   ├─ WARNING    → escalate finding
│   ├─ FAILURE    → escalate to human
│   └─ INCONCLUSIVE → refine question for Wave 2
│
└─ evolve/monitor/predict/frontier
    ├─ HEALTHY    → record + archival
    ├─ VIABLE     → record + schedule for implementation
    ├─ BLOCKED    → record as constraint
    └─ PARTIAL    → record + prerequisite tracking
```

---

## 5. Integration Points Across Projects

BrickLayer 2.0 connects 6 coordinated projects:

### 5.1 Project Dependency Graph

```
┌───────────────────────────────────────────────────────────┐
│           CROSS-PROJECT ARCHITECTURE                      │
└───────────────────────────────────────────────────────────┘

Bricklayer2.0 (Main)
    ├─ agents/              [Agent definitions + Crucible scoring]
    ├─ projects/bl2/        [Campaign state + last-tool-error tracking]
    ├─ dashboard/           [React frontend + FastAPI backend]
    │   ├─ frontend/        [QuestionQueue, FindingFeed, AgentFleet]
    │   └─ backend/main.py  [question/finding parsing, add/correct endpoints]
    │
    ├─ masonry/             [Plugin system + statusline hooks]
    │   ├─ src/hooks/       [masonry-statusline.js, masonry-recall-check.js]
    │   └─ bin/             [masonry-setup.js installer]
    │
    ├─ template/            [Project bootstrap]
    │   ├─ .claude/agents/  [Domain-specific agents: question-designer, synthesizer, etc.]
    │   ├─ constants.py     [Immutable simulation rules]
    │   ├─ simulate.py      [Simulation engine (SCENARIO PARAMETERS only)]
    │   ├─ questions.md     [Question bank]
    │   └─ program.md       [Loop instructions]
    │
    └─ projects/            [Active research campaigns]
        └─ adbp/            [ADBP project instance]
            ├─ questions.md
            ├─ findings/
            ├─ results.tsv
            ├─ constants.py
            ├─ simulate.py
            └─ .claude/agents/

Recall (System-Recall)
    ├─ HTTP API @ 100.70.195.84:8200
    ├─ Semantic memory (HNSW embeddings)
    ├─ MCP server (recall-retrieve, recall-store hooks)
    └─ Integration: masonry-recall-check.js pings health endpoint

Ollama (Local LLM)
    ├─ HTTP API @ 192.168.50.62:11434
    ├─ Models: qwen3:14b (reasoning), qwen3-embedding:0.6b (vectors)
    └─ Integration: probe-runner uses for verdict classification

Claude Code (Orchestration)
    ├─ Local agents via Task tool
    ├─ Reads findings/, questions.md from project_root
    ├─ Writes .omc/state/, .claude/CLAUDE.md
    └─ Environment: DISABLE_OMC=1 (prevents OMC hook interception)

Masonry (Plugin System)
    ├─ Hooks system integration
    ├─ statusLine command (masonry-statusline.js)
    ├─ Recall connectivity check (masonry-recall-check.js)
    └─ Plugin cache @ ~/.claude/plugins/cache/masonry/

FamilyHub / Homelab
    ├─ CasaOS @ 192.168.50.19
    ├─ Potential: integrate findings into homelab dashboards
    └─ (Future extension point)
```

### 5.2 Data Exchange Points

```
Bricklayer2.0 ←→ Recall
├─ probe-runner stores findings via recall_store MCP
├─ retrospective queries prior findings via recall_search
├─ masonry-statusline.js checks Recall health
└─ Integration: `agent:probe-runner`, `agent:retrospective` tags

Bricklayer2.0 ←→ Ollama
├─ probe-runner may delegate verdict classification
├─ Forge uses for agent prompt generation
├─ Integration: HTTP /v1/chat/completions via requests library

Bricklayer2.0 ←→ Claude Code (Local)
├─ Question parsing: questions.md parsed by dashboard backend
├─ Finding writing: agents write to findings/ via file I/O
├─ Agent invocation: Task tool spawns specialized agents
├─ Environment setup: DISABLE_OMC=1 prevents OMC interference

Dashboard ←→ Bricklayer2.0 Project
├─ GET /questions → reads questions.md (block format)
├─ POST /question → appends to questions.md
├─ GET /findings → scans findings/ directory
├─ GET /finding/{id} → lazy-loads findings/{id}.md
├─ POST /finding/{id}/correct → appends Human Correction block
└─ GET /agents → lists agents/ directory with model tier extraction
```

---

## 6. Verdict Transition State Machine

Complete state diagram showing all possible verdict transitions and actions:

```
START: New Question (status = PENDING)
    ↓
[probe-runner executes Test command]
    ├─────────────────────┬────────────────┬──────────────┬──────────────┐
    ↓                     ↓                ↓              ↓              ↓
FAILURE            WARNING            HEALTHY        INCONCLUSIVE     ERROR
(fix needed)       (candidate fix)    (verified)     (unclear/gap)    (invalid test)
    │                   │                │                │             │
    ├─ scope-analyzer   ├─ optional       ├─ regression-  ├─ Check      └─ probe-runner
    │   maps impact     │   fix attempt   │   guard       │  for existing    re-runs with
    │                   │                 │   re-runs     │  agent pattern   debug flags
    ├─ Is there a       └─ If improved:  │               │
    │  matching agent?     commit +       │               ├─ Match        If still fails:
    │  ├─ Yes → assign     append         │               │  found?       mark INCONCLUSIVE
    │  │  ↓               │               │               │  ├─ Yes →
    │  │ Agent runs       └─ Otherwise:   │               │  │   assign
    │  │  ├─ fix applied    → HEALTHY     │               │  │   to agent
    │  │  ├─ re-verify      (terminal)    │               │  └─ No →
    │  │  ├─ verdict improves?            │               │    write FORGE_NEEDED.md
    │  │  │  ├─ Yes → COMMIT              │               │
    │  │  │  └─ No  → REVERT              │               ├─ Pause loop
    │  │  └─ Max retries?                 │               │  (forge creates agent)
    │  │     └─ Yes → FAILURE (terminal)  │               │
    │  │                                   │               └─ Forge deployed
    │  └─ No → write FORGE_NEEDED.md       │
    │     ↓                                │
    │   [forge creates new agent]          │
    │     ↓                                │
    │   Re-run with new agent              │
    │     ↓                                │
    │   (same path as above)              │
    │                                      │
    │  ┌────────────────────────────────────┘
    │  │
    ├─ Commit finding with verdict
    │
    └─ Next question (PENDING)

TERMINAL STATES:
├─ HEALTHY (verified, next commit triggers regression-guard)
├─ FAILURE (unresolved, escalate or Wave 2 target)
├─ INCONCLUSIVE (unclear, archival, may revisit)
└─ DONE (status updated in questions.md)
```

---

## 7. Mode Completeness Verification

### 7.1 Supported Modes (Current Implementation)

| Mode | Category | Agent Routing | Verdict Handling | Completeness |
|------|----------|---------------|------------------|--------------|
| D1 (correctness) | Diagnose | probe-runner | FAILURE→specialist, WARNING→candidate | COMPLETE |
| D2 (security/audit) | Audit | scope-analyzer | FAILURE→security-hardener | COMPLETE |
| D3 (research) | Research | document-specialist (future) | FAILURE→escalate | 50% (external only) |
| D4 (quality) | Quality | lint-guard + commit-reviewer | WARNING→candidate | COMPLETE |
| D5 (simulation) | Data | probe-runner | FAILURE/WARNING/HEALTHY | COMPLETE |
| D6 (performance) | Performance | perf-optimizer | FAILURE→specialist | COMPLETE |
| A (audit) | Non-domain | agent-auditor | FAILURE→human | COMPLETE |
| F (fix) | Non-domain | scope-analyzer + specialist | FAILURE→retry | COMPLETE |
| V (validate) | Non-domain | regression-guard | WARNING→alert | COMPLETE |
| R (research) | Non-domain | document-specialist | FAILURE→escalate | 50% |
| E (evolve) | Non-domain | (future architect agent) | PARTIAL | 0% |
| M (monitor) | Non-domain | (future metrics agent) | PARTIAL | 0% |
| P (predict) | Non-domain | (future scientist agent) | PARTIAL | 0% |
| Fr (frontier) | Non-domain | frontier-analyst agent | VIABLE/BLOCKED/PARTIAL | PARTIAL |

### 7.2 Incomplete Modes (Future Implementation)

**R (Research)** — 50% complete
- Current: dashboard displays research questions, agents provide external links
- Missing: automated web search integration (document-specialist MCP calls)
- Blocker: need WebSearch or Exa MCP integration

**E (Evolve)** — 0% complete
- Scope: Architecture/design evolution questions
- Required: architect-level agent for system-wide implications
- Blocker: agent design needed

**M (Monitor)** — 0% complete
- Scope: Observability and metrics questions
- Required: metrics analyzer agent + time-series data access
- Blocker: dashboard integration for metric dashboards needed

**P (Predict)** — 0% complete
- Scope: Forecasting and trend analysis
- Required: scientist agent with statistical modeling capability
- Blocker: historical data collection + correlation detection needed

---

## 8. Agent Coverage Matrix

### 8.1 Which Agents Handle Which Question Types?

```
Question Type    Primary Handler        Secondary Handlers         Fallback
─────────────────────────────────────────────────────────────────────────────
D1.correctness   probe-runner           test-writer                 forge
D2.security      scope-analyzer         security-hardener           forge
D3.research      document-specialist    (N/A)                       escalate
D4.quality       lint-guard             commit-reviewer             forge
D5.simulation    probe-runner           perf-optimizer              forge
D6.performance   perf-optimizer         scope-analyzer              forge

A.audit          agent-auditor          (N/A)                       human
F.fix            scope-analyzer         all specialists             escalate
V.validate       regression-guard       probe-runner                (N/A)
R.research       document-specialist    (N/A)                       manual

Fr.frontier      frontier-analyst       architect (future)          manual
```

### 8.2 Agent Availability by Tier

**Trusted Tier (autonomous, >0.8 score):**
- scout
- probe-runner
- triage
- scope-analyzer
- regression-guard
- forge
- security-hardener
- test-writer
- type-strictener
- perf-optimizer

**Candidate Tier (approval required, 0.4–0.8 score):**
- commit-reviewer
- lint-guard
- agent-auditor
- forge-check

**Draft Tier (benchmarking, <0.4 score):**
- retrospective
- crucible
- [forge-created agents] (initially)

**Retired Tier:**
- (none currently)

---

## 9. Cross-Project Dependency Analysis

### 9.1 Critical Dependencies

```
BrickLayer2.0 (core)
    ↓
    ├─ Depends On: masonry (plugin hooks) — if masonry setup fails, dashboard doesn't get statusline
    ├─ Depends On: Recall (memory storage) — if Recall unreachable, masonry-recall-check.js logs error
    ├─ Depends On: Ollama (optional verdict classification) — if unreachable, falls back to heuristics
    └─ Depends On: Claude Code (agent invocation) — if env DISABLE_OMC=1 not set, OMC hooks intercept agent spawns

Dashboard (frontend + backend)
    ├─ Depends On: BrickLayer2.0 questions.md parsing (5 different formats supported)
    ├─ Depends On: BrickLayer2.0 findings/ directory structure
    ├─ Depends On: FastAPI backend (CORS configured for localhost:3100 only)
    └─ Depends On: React 19 + Tailwind v4 (no breaking version pins)

Masonry (plugin integration)
    ├─ Depends On: Claude Code settings.json for plugin registry
    ├─ Depends On: Recall API health check (3s timeout)
    ├─ Depends On: ~/.masonry/config.json for Recall host + API key
    └─ Depends On: Node.js + npm (for bin/masonry-setup.js)

Template (project bootstrap)
    ├─ Depends On: .claude/agents/ definitions (question-designer, synthesizer, etc.)
    ├─ Depends On: program.md loop instructions (never edit)
    └─ Depends On: Authority hierarchy: project-brief.md (Tier 1) > constants.py (Tier 2) > findings/ (Tier 3)

adbp Project (active)
    ├─ Depends On: template/ structure
    ├─ Depends On: dashboard backend for UI
    └─ Depends On: BrickLayer2.0 agents/ for campaign execution
```

### 9.2 Failure Mode Cascades

```
If Recall @ 100.70.195.84:8200 unreachable:
    ├─ masonry-recall-check.js writes error to temp cache
    ├─ masonry-statusline.js shows dim "○" indicator (offline)
    └─ Claude agents cannot store memories via recall_store
        └─ Agents log warnings but continue working

If masonry not installed:
    ├─ Claude Code doesn't have statusline hook
    ├─ dashboard-statusline.js fails silently (cwd detection only)
    └─ No impact on core BrickLayer loop

If Ollama unreachable:
    ├─ probe-runner falls back to heuristic verdict classification (pattern matching)
    ├─ Accuracy degrades but loop continues
    └─ Fix specialists still work (they don't need Ollama)

If DISABLE_OMC=1 not set:
    ├─ OMC hooks intercept BrickLayer agent spawns
    ├─ Domain-specific agents (quantitative-analyst) replaced with OMC generic agents
    ├─ Campaign loop breaks (wrong agents for questions)
    └─ **CRITICAL** — documented in all startup instructions

If questions.md format not recognized:
    ├─ Dashboard backend tries both block format (## Q1.1) and legacy table format
    ├─ If both fail, returns empty list
    └─ Campaign stalls (no questions to probe)

If findings/ directory corrupted:
    ├─ parse_findings_index() returns incomplete list
    ├─ Retrospective can't see all findings
    └─ Wave N+1 questions may miss important patterns
```

---

## 10. Completeness Gaps & Recommendations

### 10.1 Current Gaps

| Gap | Severity | Impact | Recommendation |
|-----|----------|--------|-----------------|
| R (Research) mode incomplete | Medium | Web search integration missing | Implement document-specialist MCP calls |
| E/M/P modes not implemented | Low | Future extensions blocked | Design architect/metrics/scientist agents |
| No cross-project transaction log | Low | Hard to trace multi-project issues | Add audit log to Recall or .omc/logs/ |
| Question format fragility | Medium | Parser must support 5 formats | Standardize on block format (## Q1.1) |
| No agent communication protocol | Low | Agents work in isolation | Add job queue for agent-to-agent signaling |
| Crucible benchmarking incomplete | Medium | Hard to assess agent quality | Expand metrics (false negatives, latency) |
| No cross-campaign retrospective | Low | Learning not shared across projects | Add synthesis aggregation to Recall |

### 10.2 Architectural Strengths

| Strength | Value | Impact |
|----------|-------|--------|
| **Agent schema is declarative** | Easy to add new agents | Forge can create agents autonomously |
| **Verdict routing is explicit** | Clear failure→action mapping | No ambiguous states |
| **Dashboard decouples UI from campaign** | UI can be replaced | Campaign logic is independent |
| **Tier system ensures agent quality** | Only proven agents run autonomously | Safer autonomous execution |
| **Findings are always human-readable** | Easy to audit, flag, correct | Low barrier to human oversight |

---

## 11. Recommendations for Phase 6

**Phase 6 — Operational Validation & Hardening**

1. **Test agent interconnection** — Run a full campaign on adbp project, track every agent invocation, verify verdicts flow correctly
2. **Stress test verdict routing** — Manually inject INCONCLUSIVE findings, confirm forge creates appropriate agents
3. **Validate Recall integration** — Verify recall_store and recall_search work end-to-end, check memory retention across sessions
4. **Benchmark Crucible scoring** — Create a set of intentionally broken agents, measure how accurately Crucible scores them
5. **Document operational runbook** — Add recovery procedures for each failure mode cascade above
6. **Extend incomplete modes** — Implement R/E/M/P handlers and agent definitions

---

## 12. Files Examined (Phase 5 Investigation)

- `/c/Users/trg16/Dev/Bricklayer2.0/agents/SCHEMA.md` — Agent framework specification
- `/c/Users/trg16/Dev/Bricklayer2.0/agents/scout.md` — Question generation agent
- `/c/Users/trg16/Dev/Bricklayer2.0/agents/forge.md` — Agent creation factory
- `/c/Users/trg16/Dev/Bricklayer2.0/dashboard/backend/main.py` — API endpoints (parse_questions, parse_findings_index, etc.)
- `/c/Users/trg16/Dev/Bricklayer2.0/masonry/bin/masonry-setup.js` — Plugin integration
- `/c/Users/trg16/Dev/Bricklayer2.0/masonry/src/hooks/masonry-statusline.js` — Status display
- Prior session: QuestionQueue.tsx, FindingFeed.tsx, AgentFleet.tsx (frontend components)

---

**End of Phase 5 — Ecosystem Synthesis Complete**

Next: Phase 6 will focus on operational validation through end-to-end campaign testing.
