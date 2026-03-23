# BrickLayer 2.0 Architecture Summary

**Comprehensive technical reference for BrickLayer 2.0 implementation — basis for Masonry framework design.**

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Data Models](#core-data-models)
3. [Module Inventory & Purposes](#module-inventory--purposes)
4. [Data Flow Patterns](#data-flow-patterns)
5. [Constraint System](#constraint-system)
6. [Verdict Lifecycle](#verdict-lifecycle)
7. [Agent Integration](#agent-integration)
8. [Evaluation Layers](#evaluation-layers)
9. [Integration Patterns](#integration-patterns)
10. [Question Type Classification](#question-type-classification)
11. [Operational Modes](#operational-modes)
12. [Healing & Repair Loops](#healing--repair-loops)
13. [Configuration & Initialization](#configuration--initialization)

---

## System Overview

BrickLayer 2.0 is an adaptive AI-driven research and evaluation framework that:
- Generates hypothesis-driven questions from a project brief
- Routes questions to specialized agents for evaluation
- Persists findings and verdict history with regression detection
- Synthesizes campaigns and recommends next actions (CONTINUE/STOP/PIVOT)
- Provides optional external memory (Recall) and skill creation/registry
- Supports both legacy BL 1.x (fixloop) and new BL 2.0 (healloop) repair mechanisms

**Core Philosophy:** Questions feed findings → findings inform next waves → synthesis enables adaptive feedback loops.

---

## Core Data Models

### Question Dict
```python
{
  "id": str,                          # D1, D5.1, F4.3, A6.1 (BL 2.0) or Q2.4 (BL 1.x)
  "mode": str,                        # diagnostic mode (correctness, performance, agent, quality, static, http, benchmark, etc.)
  "title": str,                       # human-readable question title
  "status": str,                      # PENDING, DONE, IN_PROGRESS, or terminal verdict (INCONCLUSIVE, DIAGNOSIS_COMPLETE, etc.)
  "question_type": str,               # "behavioral" (requires live evidence) or "code_audit" (static analysis)
  "target": str,                      # target component/file/service under evaluation
  "hypothesis": str,                  # falsifiable hypothesis to test
  "test": str,                        # test procedure/verification command
  "verdict_threshold": str,           # acceptance criteria/threshold definition
  "agent_name": str,                  # agent assigned (e.g., "diagnose-analyst", "quantitative-analyst")
  "finding": str,                     # finding ID to read (for healloop synthetic questions)
  "source": str,                      # origin of question (e.g., "goal.md", "hypothesis-generator")
  "operational_mode": str,            # diagnose, fix, audit, validate, monitor, frontier, predict, research, evolve, agent
  "resume_after": str,                # ISO-8601 gate timestamp (optional resume delay)
  "session_context": str,             # preamble context injected into agent session (optional)
}
```

### Result/Verdict Envelope
```python
{
  "verdict": str,                     # HEALTHY, FAILURE, WARNING, INCONCLUSIVE, DIAGNOSIS_COMPLETE, FIXED, FIX_FAILED, COMPLIANT, NON_COMPLIANT, BLOCKED, etc.
  "summary": str,                     # one-sentence summary (<=120 chars)
  "details": str,                     # detailed evidence/explanation
  "data": dict,                       # structured evaluation data (test results, metrics, etc.)
  "confidence": str,                  # high, medium, low, uncertain (from classify_confidence)
  "failure_type": str | None,         # syntax, logic, hallucination, tool_failure, timeout, unknown (from classify_failure_type)
}
```

### Finding Markdown File
```markdown
# Finding: {qid} — {question_title}

**Question**: {question.hypothesis}
**Verdict**: {verdict}
**Severity**: {High|Medium|Low|Info}
**Failure Type**: {failure_type} (if applicable)
**Mode**: {question.operational_mode}
**Type**: {BEHAVIORAL|CODE-AUDIT}
**Target**: {question.target}

## Summary
{result.summary}

## Evidence
{result.details[:3000]}

## Raw Data
{json.dumps(result.data, indent=2)[:2000]}

## Verdict Threshold
{question.verdict_threshold}

## Mitigation Recommendation
[filled by agent analysis]

## Open Follow-up Questions
[if verdict is FAILURE or WARNING]

## Heal Cycle {N} — {STATUS}
[appended by healloop for each cycle]
```

### Agent Verdict Scoring
```python
_SUCCESS_VERDICTS = {HEALTHY, FIXED, COMPLIANT, CALIBRATED, IMPROVEMENT, OK, PROMISING, DIAGNOSIS_COMPLETE, NOT_APPLICABLE, DONE}  # 1.0 credit
_PARTIAL_VERDICTS = {WARNING, PARTIAL, WEAK, DEGRADED, DEGRADED_TRENDING, FIX_FAILED, PENDING_EXTERNAL, BLOCKED, SUBJECTIVE, IMMINENT, PROBABLE, POSSIBLE, UNLIKELY, HEAL_EXHAUSTED}  # 0.5 credit
_FAILURE_VERDICTS = {FAILURE, INCONCLUSIVE, NON_COMPLIANT, ALERT, UNKNOWN, UNCALIBRATED, NOT_MEASURABLE, REGRESSION}  # 0.0 credit

score = (success_count + partial_count * 0.5) / total_runs  # range 0.0–1.0
```

---

## Module Inventory & Purposes

### Campaign Orchestration
- **campaign.py** (845 lines, 22x frequency): Main campaign loop. Sentinels, peer-reviewer spawning every 10 questions, overseer intervention every 10 questions, verdict routing logic, question-to-agent mapping, result persistence.

### Question Management
- **questions.py** (241 lines, 13x frequency): Question I/O and lifecycle. parse_questions() from questions.md. Status tracking via results.tsv. Terminal verdict preservation.
- **followup.py** (347 lines): Follow-up question generation (C-04 constraint). Generates sub-questions after FAILURE/WARNING. Single-level depth only (Q2.4 → Q2.4.1, Q2.4.2, Q2.4.3).
- **goal.py** (343 lines): Goal-directed campaign question generation (C-03 constraint). Reads goal.md, generates focused falsifiable questions (QG1.1, QG1.2, etc.).
- **hypothesis.py** (251 lines): Hypothesis generator adaptive feedback loop. Reads campaign findings, generates next-wave PENDING questions.

### Agent Execution
- **runners/agent.py** (10x frequency): Agent execution harness. Spawns and manages agent processes, handles timeouts, collects results.

### Verdict Analysis
- **findings.py** (537 lines): Verdict envelopes, failure classification, confidence signaling, results.tsv updates, findings directory writing.
  - classify_failure_type(result, mode) → syntax|logic|hallucination|tool_failure|timeout|unknown|None
  - classify_confidence(result, mode) → high|medium|low|uncertain
  - score_result(result) → float 0.0–1.0 (evidence_quality * 0.4 + verdict_clarity * 0.4 + execution_success * 0.2)
  - write_finding(question, result) → Path (writes to findings/{qid}.md)
  - update_results_tsv(qid, verdict, summary, failure_type) → upserts results.tsv row
  - _mark_question_done(qid, verdict) → updates questions.md status

- **agent_db.py** (232 lines): Verdict-based agent scoring and overseer intervention.
  - record_run(project_root, agent_name, verdict) → float (updated score)
  - get_score(project_root, agent_name) → float (current score, default 1.0)
  - record_repair(project_root, agent_name) → None (increments repair_count)
  - get_underperformers(project_root, threshold=0.40, min_runs=3) → list[dict] (eligible for overseer)
  - get_summary(project_root) → list[dict] (all tracked agents, sorted by score)

- **crucible.py** (692 lines, 46x frequency): Agent benchmarking system with 8 scorers.
  - Scorers: correctness, robustness, precision, recall, latency, completeness, clarity, actionability
  - SQLite history.db backend with (question_id, verdict, scorer_name, score, timestamp, run_id)
  - Verdict distribution analysis: `compute_score_distribution()`
  - Aggregate scoring: avg/median/std over scorer population per verdict
  - No regression detection — tracks historical trends for reporting

- **history.py** (228 lines): SQLite-backed verdict_history ledger with regression detection.
  - record_verdict(qid, verdict, failure_type, confidence, summary, run_id) → appends to verdict_history table
  - detect_regression(qid) → list[str] (transitions like HEALTHY→FAILURE, COMPLIANT→NON_COMPLIANT, etc.)
  - Index on (question_id, timestamp) for efficient lookups

- **local_inference.py** (172 lines): Ollama endpoint (192.168.50.62:11434, qwen2.5:7b) with fallback-first pattern.
  - classify_failure_type_local(result, mode) → str|None (via Ollama)
  - classify_confidence_local(result) → str|None (via Ollama)
  - score_result_local(result) → float|None (via Ollama)
  - is_available() → bool (2.0s timeout health check)
  - Falls back to heuristics if Ollama unavailable

- **quality.py** (45 lines): Remediation feasibility estimation (C-29 constraint).
  - estimate_remediation_feasibility(action_type, current_mean, healthy_threshold, floor, n_affected, corpus_size) → dict|None
  - Handles "amnesty" action type: boosts memories below floor TO floor
  - Formula: max_delta = (floor - current_mean) * (n_affected / corpus_size)

### Synthesis & Reporting
- **synthesizer.py** (237 lines): Campaign synthesizer.
  - Reads all findings/*.md + results.tsv
  - Severity-aware corpus truncation (max 12,000 chars; high-severity findings retained first, low-severity dropped first)
  - CONTINUE | STOP | PIVOT decision logic

### Healing & Repair
- **healloop.py** (352 lines): BL 2.0 self-healing loop (distinct from legacy fixloop).
  - State machine: FAILURE → diagnose-analyst → DIAGNOSIS_COMPLETE → fix-implementer → FIXED or FIX_FAILED
  - Max 3 cycles (configurable BRICKLAYER_HEAL_MAX_CYCLES)
  - run_heal_loop(original_question, initial_result, finding_path) → dict (final result)
  - Synthetic questions: "{original_id}_heal{cycle}_{short_type}" where short_type = "diag"|"fix"
  - F-mid.1: HEAL_EXHAUSTED verdict written to results.tsv when cycles exhausted

- **fixloop.py** (162 lines): Legacy BL 1.x fix loop (C-06 constraint).
  - Enabled: cfg.fix_loop_enabled or --fix-loop flag
  - Max 2 attempts
  - Workflow: FAILURE → spawn fix-agent subprocess → re-run question → if HEALTHY return, else retry
  - Appends "## Fix Attempt {attempt} — {status}" sections to finding files
  - Agent invocation: subprocess.run([claude, ...], 600-second timeout)

### Skill Management
- **skill_forge.py** (148 lines): Skill registry and persistence.
  - Skills stored at ~/.claude/skills/{name}/SKILL.md
  - Project registry: {project_dir}/skill_registry.json
  - write_skill(name, content, project_root, description, source_finding) → writes SKILL.md + registers
  - read_skill(name) → content|None
  - list_project_skills(project_root) → list[dict] with metadata (created, last_updated, repair_count)
  - global_skill_inventory() → all skills in ~/.claude/skills/

### External Integration
- **recall_bridge.py** (145 lines): Optional Recall memory integration (192.168.50.19:8200) with graceful failure.
  - RECALL_STORE_VERDICTS: 15 verdict types (FAILURE, WARNING, DIAGNOSIS_COMPLETE, FIXED, FIX_FAILED, etc.)
  - store_finding(question, result, project) → bool (success/failure)
  - search_before_question(question, project) → str (formatted memories or "")
  - _is_available() → bool (2.0s timeout health check)
  - Graceful ImportError handling for optional httpx dependency

### Configuration
- **config.py** (103 lines): Mutable config singleton.
  - Hardcoded defaults: Recall API (192.168.50.19:8200), Ollama (192.168.50.62:11434), qwen2.5:7b
  - init_project(project_name) → loads project.json, mutates cfg singleton before any runner executes
  - Searches: {autosearch_root}/projects/{name} and {autosearch_root}/{name}
  - Backward compatibility: "recall_src" vs legacy "target_git" field names in project.json

---

## Data Flow Patterns

### Question Lifecycle
```
question.md (PENDING)
    ↓
campaign.py: get_next_pending()
    ↓
determine agent + operational_mode
    ↓
recall_bridge.py: search_before_question() [optional — inject relevant prior findings]
    ↓
runners/agent.py: run_agent(question) → result dict
    ↓
findings.py: classify_failure_type(), classify_confidence(), score_result()
    ↓
healloop.py (if FAILURE/DIAGNOSIS_COMPLETE + enabled) [optional]
    ↓
findings.py: write_finding(), update_results_tsv()
    ↓
questions.py: _mark_question_done(qid, verdict) → updates questions.md
    ↓
history.py: record_verdict() → SQLite verdict_history
    ↓
agent_db.py: record_run() → updates agent_db.json score
    ↓
crucible.py: apply_rubric() [if benchmarking enabled] → SQLite history.db
    ↓
recall_bridge.py: store_finding() [optional — persist to Recall] (if verdict in RECALL_STORE_VERDICTS)
    ↓
campaign.py: verdict_routing() → determines next action (new question, sentinel, synthesis, etc.)
```

### Campaign Iteration
```
Wave N questions (PENDING)
    ↓
campaign.py: iterate through questions
    ↓
[Question Lifecycle × N questions]
    ↓
synthesizer.py: synthesize_campaign()
    ↓
decision: CONTINUE → hypothesis.py: generate Wave N+1 questions
         STOP → campaign end
         PIVOT → goal.py: regenerate focused questions
```

---

## Constraint System

**Constraints enforce evaluation rigor and prevent verdict inflation.**

### C-03: Goal-Directed Questions
- goal.py reads goal.md (user-supplied high-level objectives)
- Generates focused, falsifiable questions tied to goal achievement
- Question IDs: QG1.1, QG1.2, QG2.1, etc. (QG-prefixed, wave-indexed)
- Prevents drift from core objectives

### C-04: Follow-Up Sub-Questions
- followup.py generates after FAILURE or WARNING
- Max 1 level depth: Q2.4 → Q2.4.1, Q2.4.2, Q2.4.3 (no Q2.4.1.1)
- Prevents infinite recursion of drill-downs
- Auto-extracted from question hypothesis and failure details

### C-06: Legacy Fix Loop
- fixloop.py supports BL 1.x projects (distinct from BL 2.0 healloop)
- Max 2 fix attempts per question
- Controlled via cfg.fix_loop_enabled or --fix-loop flag
- Spawns blocking fix-agent subprocess (600-second timeout)

### C-29: Remediation Feasibility
- quality.py: estimate_remediation_feasibility()
- Handles "amnesty" action type: boosts memories below floor TO floor
- Formula: max_delta = (floor - current_mean) * (n_affected / corpus_size)
- Prevents overly optimistic repair claims

### C-30: Code-Audit Verdict Constraints
- findings.py: code_audit questions cannot produce HEALTHY verdicts (downgraded to WARNING)
- Confidence capped at medium for code_audit mode
- Enforces: code_audit requires live HTTP/test evidence, not just static analysis
- Constraint applied in write_finding() before persisting to findings/*.md

### F-series Fixes (Framework Refinements)
- **F2.3**: Copy not alias in healloop (preserves fix_result["verdict"]="FIX_FAILED")
- **F2.5**: Synthetic question ID format "{original_id}_heal{cycle}_{short_type}" where short_type = "diag"|"fix"
- **F2.6**: Track actual exit cycle for EXHAUSTED note (not max_cycles)
- **F3.1**: Overseer intervention spawning (every 10 questions)
- **F4.2**: Write fix finding with correct ID in healloop
- **F4.3**: Accept BL 2.0 IDs in questions.md (D1, F2.1, A4..., not just Q-prefix)
- **F4.4**: Reset synthetic heal questions to "behavioral" (not code_audit)
- **F5.1**: Body **Mode** field takes priority over bracket tag in questions.md
- **F8.2**: Preserve failure/violation verdicts in questions.md for human visibility
- **F-mid.1**: HEAL_EXHAUSTED verdict written to results.tsv (not pre-heal FAILURE) so synthesizer/crucible/agent_db see correct final state

---

## Verdict Lifecycle

### Terminal Verdicts (Preserved in questions.md)
```
INCONCLUSIVE, DIAGNOSIS_COMPLETE, PENDING_EXTERNAL, FIXED, FIX_FAILED, BLOCKED,
FAILURE, NON_COMPLIANT, WARNING, REGRESSION, ALERT, HEAL_EXHAUSTED
```

### Success Verdicts (1.0 agent score credit)
```
HEALTHY, FIXED, COMPLIANT, CALIBRATED, IMPROVEMENT, OK, PROMISING, DIAGNOSIS_COMPLETE, NOT_APPLICABLE, DONE
```

### Partial Verdicts (0.5 agent score credit)
```
WARNING, PARTIAL, WEAK, DEGRADED, DEGRADED_TRENDING, FIX_FAILED, PENDING_EXTERNAL, BLOCKED,
SUBJECTIVE, IMMINENT, PROBABLE, POSSIBLE, UNLIKELY, HEAL_EXHAUSTED
```

### Failure Verdicts (0.0 agent score credit)
```
FAILURE, INCONCLUSIVE, NON_COMPLIANT, ALERT, UNKNOWN, UNCALIBRATED, NOT_MEASURABLE, REGRESSION
```

### Verdict Routing in campaign.py
```
FAILURE or DIAGNOSIS_COMPLETE → healloop (if enabled) → FIXED or FIX_FAILED
FAILURE/WARNING → followup.py: generate sub-questions (C-04)
NON_COMPLIANT → followup.py: generate sub-questions
Success verdicts (HEALTHY, COMPLIANT, etc.) → campaign advances to next question
Terminal verdicts → results.tsv updates, questions.md status locked
```

### Regression Detection (history.py)
```
Watched transitions:
  HEALTHY → FAILURE, WARNING
  COMPLIANT → NON_COMPLIANT
  FIXED → FAILURE
  WARNING → FAILURE
  DIAGNOSIS_COMPLETE → FAILURE
  etc.

Recorded in SQLite with (question_id, timestamp) index for efficient query
```

---

## Agent Integration

### Agent Assignment
- agents_dir: {project_root}/.claude/agents/{name}.md
- Question.agent_name matched to agent file for run_agent() dispatch
- Agent receives:
  - Question dict with full context
  - Optional prior findings (from recall_bridge.search_before_question)
  - Session preamble (from question.session_context)
  - Finding content for healloop synthetic questions

### Agent Performance Tracking
- **agent_db.py**: Verdict-based scoring
  - record_run(project_root, agent_name, verdict) increments runs + verdicts counts, updates score
  - Score = (success_count + partial_count * 0.5) / total_runs (range 0.0–1.0)
  - Overseer intervention triggered when score < 0.40 AND runs >= 3

- **crucible.py**: Rubric-based benchmarking (optional, independent)
  - 8 scorers: correctness, robustness, precision, recall, latency, completeness, clarity, actionability
  - Each scorer produces 0.0–1.0 score; average across scorers = overall score
  - SQLite history.db tracks per-question per-scorer performance
  - No regression detection (different purpose from agent_db)

### Overseer Intervention
- campaign.py spawns overseer agent every 10 questions (F3.1)
- Reviews agents with score < UNDERPERFORMER_THRESHOLD (0.40) AND runs >= MIN_RUNS_FOR_REVIEW (3)
- Agent repair may be recommended; repair_count incremented on remediation

---

## Evaluation Layers

### Layer 1: Failure Classification (findings.py)
```
classify_failure_type(result, mode) → syntax|logic|hallucination|tool_failure|timeout|unknown|None

- Tries local Ollama (qwen2.5:7b) first (temperature 0.0 for strict classification)
- Falls back to heuristic keyword matching if Ollama unavailable or returns unexpected value
- Returns None for non-failure verdicts (_NON_FAILURE_VERDICTS frozenset)

Heuristic keywords:
  - timeout: "timeout", "timed out", "readtimeout", "connecttimeout", "time limit exceeded"
  - tool_failure: connection errors, import errors, subprocess failures, HTTP errors
  - syntax: "syntaxerror", "indentationerror", "parse error", "invalid syntax"
  - logic: mode in (correctness, performance)
  - hallucination: no evidence keywords if mode in (agent, quality, static)
  - unknown: fallback
```

### Layer 2: Confidence Assessment (findings.py)
```
classify_confidence(result, mode) → high|medium|low|uncertain

Performance mode:
  - stages >= 3 → high
  - stages < 3 → medium
  - early_stop detected → low
  - no stages → uncertain

Correctness mode:
  - total >= 10 → high
  - total >= 3 → medium
  - total < 3 → low
  - total == 0 → uncertain

Agent/quality/static mode:
  - concrete_signals >= 4 → high (line, .py:, function, def, file:, /src/, test_, error:, warning:, assert, found)
  - concrete_signals >= 2 → medium
  - concrete_signals >= 1 → low
  - no signals, has data dict → medium
  - no signals, no data → uncertain

INCONCLUSIVE always → uncertain (explicit override)
```

### Layer 3: Result Scoring (findings.py)
```
score_result(result) → float 0.0–1.0

Tries local Ollama (qwen2.5:7b) first; falls back to:
  evidence_quality = _CONFIDENCE_EVIDENCE[confidence] (high→1.0, medium→0.7, low→0.3, uncertain→0.0)
  verdict_clarity = _VERDICT_CLARITY[verdict] (HEALTHY→1.0, WARNING→0.7, INCONCLUSIVE→0.0, etc.)
  execution_success = _FAILURE_EXECUTION[failure_type] (None→1.0, logic→0.9, syntax→0.8, hallucination→0.4, timeout→0.3, tool_failure→0.0)

  score = (evidence_quality * 0.4) + (verdict_clarity * 0.4) + (execution_success * 0.2)
  return round(score, 3)
```

---

## Integration Patterns

### Fallback-First Architecture
**Pattern:** Try precise, try heuristic, return sensible default

```
classify_failure_type:
  try Ollama (192.168.50.62:11434, qwen2.5:7b, temp=0.0)
  ↓ (on failure or unavailability)
  fallback to keyword heuristics
  ↓ (if no keywords match)
  return mode-dependent default (logic for correctness/performance, unknown otherwise)

classify_confidence:
  try Ollama (same as above)
  ↓
  fallback to mode-specific heuristics (performance, correctness, agent/quality/static)

score_result:
  try Ollama (same as above)
  ↓
  fallback to weighted formula (evidence * 0.4 + clarity * 0.4 + execution * 0.2)

Recall memory:
  try store_finding() via httpx POST
  ↓ (on network error, timeout, or unavailability)
  graceful return False (logged but non-fatal)

Ollama health check:
  _is_available() → GET /api/tags with 2.0s timeout
  Returns bool; if False, all local_inference calls skip Ollama and use heuristics
```

### External Memory Bridge (recall_bridge.py)
```
Before question execution (campaign.py):
  search_before_question(question, project) → str
  ↓ (inject as session_context for agent)
  agent.run()

After verdict recorded:
  if verdict in RECALL_STORE_VERDICTS:
    store_finding(question, result, project) → bool
    ↓
    persists to Recall at 192.168.50.19:8200
    tags: ["bl:mode:{op_mode}", "bl:verdict:{verdict}", "bricklayer"]

Graceful failure:
  network error, timeout, or unavailability → log warning, continue (non-fatal)
```

### Skill Creation (skill_forge.py)
```
Agents may create skills during execution:
  write_skill(name, content, project_root, description, source_finding)
  ↓
  writes to ~/.claude/skills/{name}/SKILL.md
  registers in {project_dir}/skill_registry.json with metadata:
    - created (ISO-8601)
    - last_updated
    - description
    - source_finding (qid that created the skill)
    - campaign (campaign name)
    - repair_count (incremented on re-registration)

Skill discovery:
  list_project_skills(project_root) → list of project-scoped skills
  global_skill_inventory() → all skills in ~/.claude/skills/
```

---

## Question Type Classification

### Behavioral Questions (Requires Live Evidence)
- **Tags:** performance, correctness, agent, http, benchmark
- **Verdict constraint:** No C-30 downgrades
- **Definition:** Requires live HTTP calls, running tests, or real agent execution
- **Examples:** "Does the API respond within 200ms?" (performance), "Do all unit tests pass?" (correctness)

### Code-Audit Questions (Static Analysis Only)
- **Tags:** quality, static, code-audit
- **Verdict constraint:** C-30 applies
  - HEALTHY downgraded to WARNING (requires live evidence)
  - Confidence capped at medium
- **Definition:** Analysis of code structure, style, security without live execution
- **Examples:** "Is the code properly typed?" (quality), "Are there SQL injection vulnerabilities?" (static)

### Classification Logic (questions.py)
```
If explicit **Type**: behavioral|code_audit field → use it
Else if tag in _CODE_AUDIT_TAGS (quality, static, code-audit) → code_audit
Else if tag in _BEHAVIORAL_TAGS (performance, correctness, agent, http, benchmark) → behavioral
Else → default to behavioral
```

---

## Operational Modes

Determines agent role, question routing, and evaluation criteria:

| Mode | Agent Role | Use Case |
|------|-----------|----------|
| diagnose | Root cause analysis, hypothesis formation | Primary investigation mode |
| fix | Implement remediation from DIAGNOSIS_COMPLETE | Repair execution |
| audit | Compliance/policy verification | Regulatory/internal compliance |
| validate | Acceptance test verification | Feature/release gate |
| monitor | Runtime health observation | Production system checks |
| frontier | Experimental/edge case exploration | Boundary testing |
| predict | Forecasting, trend analysis | Future-state scenario analysis |
| research | Exploratory investigation | Unknown territories |
| evolve | Improvement/optimization analysis | Continuous enhancement |
| agent | Agent-mode question (healloop synthetic) | Self-healing loop |

---

## Healing & Repair Loops

### BL 2.0 Self-Healing Loop (healloop.py)
**Enabled:** BRICKLAYER_HEAL_LOOP=1 (environment variable)

```
State Machine:
  FAILURE → diagnose-analyst → DIAGNOSIS_COMPLETE → fix-implementer → FIXED ✓
                                                                       → FIX_FAILED → (next cycle)
  DIAGNOSIS_COMPLETE → fix-implementer → FIXED ✓
                                       → FIX_FAILED → diagnose-analyst → (next cycle)

Max cycles: 3 (default, override BRICKLAYER_HEAL_MAX_CYCLES=N)
Synthetic questions: "{original_id}_heal{cycle}_{short_type}"
  where short_type = "diag" (diagnose-analyst) | "fix" (fix-implementer)

Exhaustion:
  After max_cycles reached without FIXED, write HEAL_EXHAUSTED to results.tsv
  Append "## Heal Cycle {last_cycle} — EXHAUSTED" to findings/{qid}.md
  Human intervention required

Agent preamble (extra_context):
  [HEAL LOOP CONTEXT: This is cycle {N}/{max_cycles}...]
  [Read finding at {current_finding_id}.md...]
  [Produce {next_verdict} with Fix Specification...]

Distinct from legacy fixloop.py (max 2 attempts, simpler state machine)
```

### BL 1.x Legacy Fix Loop (fixloop.py)
**Enabled:** cfg.fix_loop_enabled or --fix-loop flag

```
Workflow:
  FAILURE → spawn fix-agent subprocess → re-run question
  ↓
  if verdict == HEALTHY → return result ✓
  else if attempts < max_attempts → retry
  else → return result (still FAILURE)

Max attempts: 2 (hardcoded)
Subprocess: claude CLI with 600-second timeout
Assignment payload includes: question_id, failure_summary, failure_details, failure_type, finding (first 3000 chars)
Progress appended to findings/{qid}.md as "## Fix Attempt {N} — {status}"

Non-fatal failure: FileNotFoundError if claude not found, TimeoutExpired if exceeded 600s
Both logged; fixloop continues gracefully
```

---

## Configuration & Initialization

### config.py
**Mutable singleton imported by all modules; mutated by init_project() before any runner executes.**

```python
# Hardcoded defaults
base_url = "http://192.168.50.19:8200"  # Recall API
api_key = os.environ["RECALL_API_KEY"]  # from environment, never hardcoded
request_timeout = 10.0
local_ollama_url = "http://192.168.50.62:11434"
local_model = "qwen2.5:7b"
recall_src = "C:/Users/trg16/Dev/Recall"
autosearch_root = Path(__file__).parent.parent

# init_project(project_name) workflow:
# 1. Search {autosearch_root}/projects/{name} and {autosearch_root}/{name}
# 2. Load project.json:
#    {
#      "name": str,
#      "recall_src": str (optional, overrides default),
#      "api_key": str (optional, overrides default),
#      ... (backward compatibility for legacy "target_git")
#    }
# 3. Mutate cfg singleton:
#    cfg.project_root = {project_path}
#    cfg.findings_dir = project_root / "findings"
#    cfg.results_tsv = project_root / "results.tsv"
#    cfg.questions_md = project_root / "questions.md"
#    cfg.history_db = project_root / "history.db"
#    cfg.agents_dir = project_root / ".claude" / "agents"
# 4. Create findings_dir if needed
# 5. All subsequent module imports see updated cfg
```

---

## High-Frequency Modules (Execution Hotspots)

Based on call frequency:
1. **campaign.py** (22x) — Campaign orchestration loop
2. **questions.py** (13x) — Question I/O and status
3. **runners/agent.py** (10x) — Agent execution
4. **crucible.py** (46x) — Benchmarking rubric application
5. **questions.md** (126x) — Central question bank (not a module, but highest-frequency file)

Focus optimization efforts on campaign.py, runners/agent.py, and crucible.py.

---

## Design Principles for Masonry

Based on BrickLayer 2.0 architecture:

1. **Adaptive Feedback Loops:** Findings inform next waves → synthesis recommends CONTINUE/STOP/PIVOT
2. **Constraint-Driven Evaluation:** Explicit constraints (C-03, C-04, C-06, C-29, C-30) enforce rigor
3. **Fallback-First External Integration:** Try precise (Ollama, Recall), fall back to heuristics, never fail
4. **Terminal Verdict Preservation:** Keep terminal verdicts visible in primary questions.md (don't collapse to DONE)
5. **Multi-Layer Evaluation:** Failure classification + confidence assessment + result scoring (3 independent layers)
6. **Regression Detection:** SQLite history with watched verdict transitions flag regressions early
7. **Agent Performance Tracking:** Dual-system (agent_db for verdict-based scores, crucible for rubric-based benchmarks)
8. **Healing Loops as Framework Capability:** Self-healing (BL 2.0) distinct from legacy fix (BL 1.x); both available for projects that need them
9. **Optional External Memory:** Graceful degradation if Recall unavailable; skill creation and registry for campaign-generated knowledge
10. **Configuration as State Machine:** init_project() mutates singleton before execution; all modules see consistent config

---

## End-to-End Example: Single Question Evaluation

```
1. questions.md → Question D2 [compliance]: "Are we compliant with GDPR data retention?"
   - status: PENDING
   - agent_name: regulatory-researcher
   - operational_mode: audit
   - question_type: code_audit

2. campaign.py → get_next_pending() → D2 selected

3. recall_bridge.py → search_before_question(D2, project)
   - Queries Recall for prior GDPR findings
   - Returns formatted list of 5 most-relevant prior results
   - Injected into agent session preamble

4. runners/agent.py → run_agent(D2)
   - Spawns regulatory-researcher agent
   - Agent reads finding inputs, executes investigation
   - Returns result dict: {verdict: "NON_COMPLIANT", summary: "...", details: "...", data: {...}, confidence: "high", failure_type: None}

5. findings.py → classify_failure_type(result, "audit")
   - Result.verdict = NON_COMPLIANT (in _NON_FAILURE_VERDICTS) → returns None

6. findings.py → classify_confidence(result, "audit")
   - Heuristic: concrete_signals detected (GDPR clause refs, data categories, retention dates) → "high"

7. findings.py → score_result(result)
   - evidence_quality = 1.0 (high)
   - verdict_clarity = 1.0 (NON_COMPLIANT is explicit)
   - execution_success = 1.0 (failure_type = None)
   - score = 1.0 * 0.4 + 1.0 * 0.4 + 1.0 * 0.2 = 1.0

8. findings.py → write_finding(D2, result)
   - Writes findings/D2.md with all data, verdict, evidence, threshold

9. findings.py → update_results_tsv(D2, NON_COMPLIANT, "...", None)
   - Appends row to results.tsv: "D2\tNON_COMPLIANT\t\t...\t{timestamp}"

10. questions.py → _mark_question_done(D2, NON_COMPLIANT)
    - Updates questions.md: "## D2 [compliance]...\n**Status**: NON_COMPLIANT"

11. history.py → record_verdict(D2, NON_COMPLIANT, None, high, "...", run_123)
    - Appends to SQLite verdict_history with (question_id=D2, verdict=NON_COMPLIANT, timestamp=..., run_id=run_123)
    - detect_regression(D2) checks for prior COMPLIANT → NON_COMPLIANT transition (none in this case)

12. agent_db.py → record_run(project_root, "regulatory-researcher", NON_COMPLIANT)
    - Increments regulatory-researcher runs (now 5)
    - Increments NON_COMPLIANT count in verdicts dict
    - score = (success_count + partial_count * 0.5) / 5
    - Updates agent_db.json with new score

13. crucible.py → apply_rubric(D2, result, "audit")
    - 8 scorers evaluate: correctness, robustness, precision, recall, latency, completeness, clarity, actionability
    - Each scorer produces 0.0–1.0; average = 0.87
    - Appends to SQLite history.db: (question_id=D2, verdict=NON_COMPLIANT, scorer_scores={...})

14. recall_bridge.py → store_finding(D2, result, project)
    - Verdict NON_COMPLIANT in RECALL_STORE_VERDICTS → stores to Recall
    - Tags: ["bl:mode:audit", "bl:verdict:NON_COMPLIANT", "bricklayer"]
    - Returns True (success)

15. campaign.py → verdict_routing(D2, NON_COMPLIANT)
    - NON_COMPLIANT in _FAILURE_VERDICTS → trigger followup
    - followup.py → generate sub-questions: D2.1, D2.2, D2.3 (targeted remediation questions)

16. campaign.py → continue to next PENDING question
    - Every 10 questions: spawn overseer agent (F3.1)
    - Periodically: synthesizer.py synthesizes campaign findings → CONTINUE/STOP/PIVOT decision
```

---

## Summary for Masonry Design

BrickLayer 2.0 demonstrates:
- **Decoupled layers:** Classification, confidence, scoring operate independently with local fallbacks
- **Adaptive orchestration:** Campaign feedback loops driven by synthesis decisions
- **Constraint enforcement:** Explicit rules (C-series, F-series) ensure evaluation quality
- **Optional integrations:** Ollama, Recall, healing loops are "pluggable" with graceful degradation
- **Regression detection:** SQLite enables post-hoc analysis of verdict transitions
- **Agent transparency:** Dual benchmarking (verdict-based + rubric-based) provides 360° view
- **Modular question generation:** Separate systems for follow-ups, goal-driven, and hypothesis-driven questions

Masonry should inherit these patterns while abstracting away BrickLayer-specific terminology (verdict → result, finding → evidence, etc.) to support broader evaluation domains.

