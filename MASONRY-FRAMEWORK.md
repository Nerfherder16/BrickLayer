# Masonry Framework Design

**Next-generation evaluation and research framework derived from BrickLayer 2.0 architectural patterns.**

---

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [Core Concept: Masonry Units](#core-concept-masonry-units)
3. [Architecture Layers](#architecture-layers)
4. [Data Model](#data-model)
5. [Orchestration Patterns](#orchestration-patterns)
6. [Evaluation Pipeline](#evaluation-pipeline)
7. [Synthesis & Feedback](#synthesis--feedback)
8. [Integration Points](#integration-points)
9. [Implementation Strategy](#implementation-strategy)

---

## Design Philosophy

Masonry is built on architectural patterns proven in BrickLayer 2.0:

1. **Decoupling via Data** — Agents interact through persistent verdict records, not direct messaging. Each agent reads findings and question state, writes conclusions, exits. No long-lived orchestrator state.

2. **Constraint-Driven Routing** — Questions are classified (behavioral vs. static, mode-tagged, type-flagged) and routed by constraint rules, not arbitrary dispatch. Constraints are explicit, enumerable, and versioned.

3. **Verdict as Currency** — A verdict is the atomic unit of evaluation. Verdicts are classified by type (success/partial/failure), stamped with metadata (confidence, failure_type, timestamp), and feed multiple downstream systems (synthesis, regression detection, skill creation).

4. **Adaptive Feedback Loops** — Synthesis drives next-wave question generation. Regression detection flags anomalies. Agent scores inform overseer intervention. The system adjusts based on findings.

5. **Optional External Integration** — Recall, Ollama, skill registries, etc. are pluggable via graceful fallback. If external systems are unavailable, the core loop continues.

6. **Multi-Layer Evaluation** — Agent performance (verdict-based scoring), rubric-based benchmarking (crucible), historical regression detection (history.db), and local confidence classification all run independently but feed the same verdict record.

---

## Core Concept: Masonry Units

A **Unit** is the smallest independently executable piece of work:

```python
class MasonryUnit:
    """
    A unit is a composable evaluation task:
    - Self-contained (minimal external state)
    - Classifiable (mode, type, target, constraints)
    - Evaluable by any agent (same question format)
    - Persistence-backed (findings, verdicts, history)
    """
    id: str                    # B1, B2.1, C3.4 (hierarchical ID)
    mode: str                  # diagnostic mode (correctness, performance, agent, quality, static, etc.)
    hypothesis: str            # falsifiable proposition to evaluate
    target: str                # component/service/file under evaluation
    constraints: List[str]     # routing rules (e.g., "requires_live_evidence", "code_audit_only")
    verdict_threshold: str     # success criteria in natural language
    status: str                # PENDING, IN_PROGRESS, DONE, or terminal verdict

    # Outcome
    finding: Path              # {findings_dir}/{unit_id}.md
    verdict: str               # HEALTHY, FAILURE, WARNING, BLOCKED, DIAGNOSIS_COMPLETE, etc.
    confidence: str            # high, medium, low, uncertain
    failure_type: str | None   # syntax, logic, hallucination, tool_failure, timeout, unknown, or None
```

**Why Units?**
- Composable: units can be generated in waves, sub-units (drill-downs), or goal-directed batches
- Evaluable: agents don't need project context — just unit + finding threshold
- Traceable: unit ID + verdict → regression detection, synthesis input, skill source
- Adaptive: unit generator reads previous findings and generates focused next-wave units

---

## Architecture Layers

### Layer 1: Storage (Persistence)

```
questions.md         — Unit definitions (parsed at runtime, immutable format)
results.tsv          — Verdict ledger (append-only: qid | verdict | failure_type | summary | timestamp)
findings/            — Per-unit findings (*.md files with structured format)
  {unit_id}.md       — Finding report with verdict, evidence, failure classification
history.db           — SQLite regression detection (question_id, verdict, failure_type, run_id, timestamp)
unit_registry.json   — Unit metadata (created, last_updated, generation_wave, has_derived_units, resolved_by)
skill_registry.json  — Skill inventory (skill_name → finding_source, repair_count, created)
```

**Design Pattern:** Append-only writes, no in-place updates except status fields in questions.md. Regression detection works via history.db — can detect HEALTHY→FAILURE, FIXED→FAILURE, etc. by comparing current + previous verdicts.

### Layer 2: Unit Generation

```python
class UnitGenerator:
    """
    Generates units for evaluation. Multiple strategies:

    1. Initial generation (from project-brief.md + docs/)
    2. Followup drill-downs (from FAILURE/WARNING verdict)
    3. Goal-directed units (from goal.md)
    4. Feedback-loop waves (from findings synthesis)
    5. Regression units (from history.db anomalies)
    """

    def generate_initial(project_brief: str, docs: List[str]) -> List[Unit]:
        """Parse project brief, identify key hypotheses, generate units."""
        pass

    def generate_followups(failed_unit: Unit, finding: Finding) -> List[Unit]:
        """Create drill-down units targeting failure root cause. Max 1 level depth."""
        pass

    def generate_from_goals(goal_file: str, existing_findings: List[Finding]) -> List[Unit]:
        """Generate focused units from goal.md assertions."""
        pass

    def generate_next_wave(synthesis: Synthesis) -> List[Unit]:
        """From synthesis output (CONTINUE/PIVOT), generate focused next-wave units."""
        pass

    def generate_from_regression(regression_alert: RegressionAlert) -> List[Unit]:
        """From history.db anomaly (e.g., HEALTHY→FAILURE), create targeted investigation units."""
        pass
```

### Layer 3: Unit Routing & Execution

```python
class UnitRouter:
    """
    Routes units to agents based on constraints.

    Routing Rules:
    - constraint "requires_live_evidence" → agents with HTTP/benchmark capabilities
    - constraint "code_audit_only" → static analysis agents only
    - constraint "mode:performance" → performance-specialized agents
    - constraint "target:*.py" → Python-specialized agents

    No hard-coded routing. All rules are in Unit.constraints.
    """

    def route(unit: Unit, available_agents: List[Agent]) -> Agent:
        """Select agent matching unit's constraints."""
        pass

    def execute(unit: Unit, agent: Agent, timeout: int = 600) -> Verdict:
        """Run agent on unit, collect verdict, classify confidence/failure_type."""
        pass
```

### Layer 4: Verdict Classification & Evaluation

```python
class VerdictClassifier:
    """
    Every verdict goes through classification:
    1. Type classification (success/partial/failure)
    2. Failure type (if failure: syntax|logic|hallucination|tool_failure|timeout|unknown|None)
    3. Confidence (high|medium|low|uncertain) via local Ollama or heuristic
    4. Score (0.0-1.0) via weighted formula or local model
    """

    def classify_verdict(verdict: str, result: Dict) -> VerdictRecord:
        """
        {
          "verdict": str,
          "confidence": str,              # high|medium|low|uncertain
          "failure_type": str | None,     # if verdict in FAILURE_VERDICTS
          "score": float,                 # 0.0-1.0
          "evidence_quality": float,      # 0.0-1.0 from confidence
          "clarity": float,               # 0.0-1.0 from verdict type
          "execution_success": float      # 0.0-1.0 from failure_type
        }
        """
        pass
```

**Scoring Formula (proven in BrickLayer 2.0):**
```
score = (evidence_quality * 0.4) + (clarity * 0.4) + (execution_success * 0.2)
```

### Layer 5: Finding Synthesis

```python
class FindingSynthesizer:
    """
    Aggregates unit findings and recommends next action.

    Input: All findings from current wave (or campaign)
    Output: Synthesis report with CONTINUE | STOP | PIVOT recommendation

    Algorithm:
    1. Severity-aware corpus building (high-severity findings retained first)
    2. Pattern detection (repeated FAILURE → deeper issue, REGRESSION detected)
    3. Coverage analysis (which units passed, which blocked)
    4. Recommendation logic (data-driven CONTINUE/STOP/PIVOT)
    """

    def synthesize(findings: List[Finding], max_chars: int = 12000) -> Synthesis:
        """
        {
          "summary": str,
          "findings_count": int,
          "pass_rate": float,
          "critical_issues": List[str],
          "recommendation": "CONTINUE" | "STOP" | "PIVOT",
          "next_focus": str | None,  # if CONTINUE/PIVOT, what to investigate next
          "confidence": float
        }
        """
        pass
```

### Layer 6: Adaptive Feedback

```python
class AdaptiveFeedback:
    """
    Multiple independent systems ingest verdicts and generate signals:

    1. Agent Scoring (verdict_db.py pattern)
       - Track per-agent verdict distribution
       - Compute score = (success + partial*0.5) / total_runs
       - Trigger overseer intervention if score < 0.40 AND runs >= 3

    2. Rubric-Based Benchmarking (crucible.py pattern)
       - 8+ independent scorers (correctness, precision, recall, clarity, etc.)
       - Each scorer evaluates each verdict independently
       - Aggregate via mean/median/std per verdict type

    3. Regression Detection (history.db pattern)
       - Track verdict transitions per unit
       - Flag HEALTHY→FAILURE, FIXED→FAILURE, COMPLIANT→NON_COMPLIANT, etc.
       - Generate regression alerts for investigation

    4. Local Inference (local_inference.py pattern)
       - Ollama endpoint for confidence/failure classification
       - Fallback-first: try local model, fall back to heuristics
       - Temperature 0.0 for strict classification
    """

    def record_verdict(unit_id: str, verdict: str, agent: str) -> None:
        """Record verdict to all tracking systems (agent_db, crucible, history)."""
        pass

    def get_agent_score(agent_name: str) -> float:
        """Compute agent's performance score based on verdict distribution."""
        pass

    def detect_regressions() -> List[RegressionAlert]:
        """Scan history.db for HEALTHY→FAILURE, FIXED→FAILURE, etc."""
        pass

    def should_intervene_overseer(agent_name: str) -> bool:
        """Check if agent score < 0.40 AND has run >= 3 times."""
        pass
```

---

## Data Model

### Unit Record
```python
{
    "id": str,                         # B1, B2.1, C3.4, etc.
    "mode": str,                       # correctness, performance, agent, quality, static, http, benchmark, monitor, predict, frontier
    "title": str,                      # human-readable title
    "hypothesis": str,                 # falsifiable proposition
    "target": str,                     # component/service under evaluation
    "verdict_threshold": str,          # success criteria in natural language
    "question_type": str,              # "behavioral" or "code_audit"
    "constraints": List[str],          # ["requires_live_evidence", "code_audit_only", "mode:performance", etc.]
    "agent_name": str | None,          # preferred agent, if any
    "operational_mode": str,           # diagnose, fix, audit, validate, monitor, frontier, predict, research, evolve
    "status": str,                     # PENDING, IN_PROGRESS, DONE, or terminal verdict
    "created": datetime,
    "updated": datetime,
    "generation_wave": int,            # which wave generated this unit (1, 2, 3, etc.)
    "parent_unit_id": str | None,      # if followup unit, link to parent
    "has_derived_units": List[str],    # if this generated followups, list them
    "resolved_by_repair": str | None   # if FIXED/FIX_FAILED, link to repair attempt
}
```

### Verdict Record
```python
{
    "unit_id": str,
    "verdict": str,                    # terminal classification
    "confidence": str,                 # high, medium, low, uncertain
    "failure_type": str | None,        # syntax, logic, hallucination, tool_failure, timeout, unknown, None
    "score": float,                    # 0.0-1.0
    "evidence_quality": float,         # 0.0-1.0
    "clarity": float,                  # 0.0-1.0
    "execution_success": float,        # 0.0-1.0
    "summary": str,                    # human-readable summary
    "details": str,                    # evidence details (first 3000 chars)
    "data": dict | None,               # structured result data
    "agent_name": str,                 # which agent evaluated
    "run_id": str,                     # unique run identifier
    "timestamp": datetime,
    "repair_count": int | None         # if unit was repaired, how many attempts
}
```

### Synthesis Report
```python
{
    "campaign_id": str,
    "timestamp": datetime,
    "findings_count": int,
    "pass_rate": float,
    "fail_rate": float,
    "blocked_count": int,
    "critical_issues": List[dict],     # verdict, unit_id, summary
    "patterns_detected": List[str],
    "regression_alerts": List[dict],
    "agent_intervention_flags": List[str],
    "recommendation": "CONTINUE" | "STOP" | "PIVOT",
    "confidence": float,
    "next_focus": str | None,
    "summary": str
}
```

---

## Orchestration Patterns

### Pattern 1: Stateless Orchestrator

The orchestrator maintains minimal state (current wave, unit roster) and drives iterations:

```python
class Orchestrator:
    def run_campaign(campaign_config):
        """
        1. Load units from questions.md
        2. For each PENDING unit:
           a. Route to agent
           b. Collect verdict
           c. Persist finding + verdict
        3. After each wave:
           a. Synthesize findings
           b. Generate next-wave units
           c. Record agent scores, detect regressions
        4. Repeat until synthesis recommends STOP
        """
        pass
```

**Key:** Orchestrator is stateless per-unit. Unit state is in questions.md. Verdict state is in results.tsv and findings/. Agent state is in agent_db.json. This allows:
- Resume from failure without replay
- Parallel unit evaluation (multiple orchestrators can run simultaneously)
- Easy debugging (read unit status from text files)

### Pattern 2: Constraint-Driven Routing

Instead of orchestrator knowing agent capabilities, units declare constraints and router matches:

```
Unit 1: ["requires_live_evidence", "mode:performance"]
  → Route to agent with HTTP+benchmark capability

Unit 2: ["code_audit_only", "target:*.py"]
  → Route to static-analysis agent

Unit 3: ["mode:diagnose", "requires_synthesis"]
  → Route to diagnosis-specialized agent
```

**Why:** Decouples unit generation from agent capabilities. New agents can be added without changing routing logic.

### Pattern 3: Repair Loop (BL 2.0 Pattern)

When a unit verdict is FAILURE:

```
FAILURE → Run diagnostic sub-question (DIAGNOSIS_COMPLETE)
        → If diagnosed, run fix unit (FIXED or FIX_FAILED)
        → If FIX_FAILED, option for second attempt
        → After max attempts, HEAL_EXHAUSTED
```

**Key:** Repair is driven by verdicts, not orchestrator logic. A FAILURE unit generates synthesized diagnostic units via followup generator.

### Pattern 4: Regression Detection Loop

After each verdict is recorded:

```
New verdict recorded
  → history.db checks for regression (HEALTHY→FAILURE, etc.)
  → If regression detected → RegressionAlert generated
  → RegressionAlert feeds next-wave unit generation
```

**Why:** Catches regressions early. Didn't break, don't assume it still works.

---

## Evaluation Pipeline

```
┌─────────────────────────────────────────────────────────┐
│ Wave N: Load PENDING units from questions.md            │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │ For each unit:              │
        │ Route → Agent → Execute     │
        └──────────────┬──────────────┘
                       │
        ┌──────────────┴────────────────────┐
        │ Verdict Classification:           │
        │ - Type (success/partial/failure) │
        │ - Confidence (high/med/low)      │
        │ - Failure type (if applicable)   │
        │ - Score (0.0-1.0)                │
        └──────────────┬────────────────────┘
                       │
        ┌──────────────┴─────────────────┐
        │ Persistence:                   │
        │ - findings/{unit_id}.md        │
        │ - results.tsv append           │
        │ - history.db record            │
        │ - questions.md status update   │
        └──────────────┬─────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │ Multi-Layer Evaluation:      │
        │ - Agent scoring              │
        │ - Crucible benchmarking      │
        │ - Regression detection       │
        │ - Skill creation (if FIXED)  │
        └──────────────┬──────────────┘
                       │
        ┌──────────────┴──────────────────┐
        │ After wave complete:            │
        │ Synthesize findings             │
        │ Generate next-wave units        │
        │ Check recommendation            │
        └──────────────┬──────────────────┘
                       │
            ┌──────────┴──────────┐
            │ Recommendation:     │
            ├─ CONTINUE → Wave+1 │
            ├─ PIVOT → New focus │
            └─ STOP → Campaign end
```

---

## Synthesis & Feedback

### Synthesis Decision Tree

```python
def recommend(findings: List[Finding], agent_scores: Dict) -> Recommendation:
    """
    STOP if:
      - All units DONE and pass_rate > 95%
      - Consensus among synthesizer that investigation complete
      - Diminishing returns detected (last 5 waves < 5% new issues)

    CONTINUE if:
      - pass_rate > 80% but some failures need investigation
      - Agent scores healthy (no overseer intervention needed)
      - Recommendation confidence high (> 0.85)

    PIVOT if:
      - Patterns detected suggest root cause in different area
      - Recommendation confidence medium (0.60-0.85)
      - New focus area identified with high potential for resolution

    If overseer intervention flags detected (agent score < 0.40):
      - Flag but DON'T stop
      - Continue campaign with repair focus
    """
    pass
```

### Multi-Wave Feedback

```
Wave 1: Initial hypotheses
  ↓ (synthesis)
Wave 2: Followups + goal-directed + new hypotheses
  ↓ (synthesis)
Wave 3: Regression checks + agent repair focus + hypothesis generation
  ↓ (synthesis)
...
Final: Synthesize all waves, recommend STOP/CONTINUE/PIVOT
```

Each synthesis output feeds unit generation for the next wave. This creates the adaptive feedback loop.

---

## Integration Points

### External: Recall Memory (Optional)

```python
class RecallBridge:
    """
    Store significant verdicts in Recall for semantic search across campaigns.

    Verdicts stored: FAILURE, WARNING, DIAGNOSIS_COMPLETE, FIXED, FIX_FAILED, PROMISING, BLOCKED, etc.

    Tags: masonry:mode:{mode}, masonry:verdict:{verdict}, masonry:unit_id:{id}

    Graceful fallback: if Recall unavailable (2.0s timeout), continue campaign without error.
    """

    def store_finding(unit: Unit, verdict: Verdict) -> bool:
        """Store finding in Recall if available, return success."""
        pass

    def search_before_unit(unit: Unit) -> str:
        """Query Recall for similar units before execution, inject context into agent."""
        pass
```

### External: Local Inference (Ollama)

```python
class LocalInference:
    """
    Ollama endpoint (192.168.50.62:11434) for:
    - Confidence classification (high|medium|low|uncertain)
    - Failure type classification (syntax|logic|hallucination|tool_failure|timeout|unknown|None)
    - Verdict scoring (0.0-1.0)

    Fallback-first: try local model, fall back to heuristics if unavailable.
    Health check: 2.0s timeout.
    """

    def classify_confidence(result: Dict) -> str | None:
        """Return confidence or None to trigger heuristic fallback."""
        pass

    def classify_failure_type(result: Dict, mode: str) -> str | None:
        """Return failure type or None."""
        pass

    def score_result(result: Dict) -> float | None:
        """Return score 0.0-1.0 or None."""
        pass
```

### External: Skill Registry (Optional)

```python
class SkillRegistry:
    """
    When a unit verdict is FIXED, optionally create a skill from the repair approach.

    Skills stored: ~/.claude/skills/{name}/SKILL.md
    Project registry: {project_dir}/skill_registry.json

    Tracks: skill creation, repair_count, source finding, campaign context.
    """

    def create_skill_from_repair(unit: Unit, repair_verdict: Verdict) -> None:
        """If FIXED, create skill capturing the repair approach."""
        pass

    def list_project_skills(project_root: Path) -> List[Skill]:
        """List skills created by this campaign."""
        pass
```

---

## Implementation Strategy

### Phase 1: Core Framework (Weeks 1-2)

```
1. Define Unit model and question.md parsing
2. Build UnitRouter (constraint-based dispatch)
3. Implement UnitGenerator (initial + followup generation)
4. Create VerdictClassifier (confidence + failure type + score)
5. Persist to results.tsv + findings/ + history.db
```

**Validation:** Run on single-unit test, verify verdict classification + persistence.

### Phase 2: Orchestration Loop (Weeks 3-4)

```
1. Build Orchestrator (wave loop + synthesis trigger)
2. Implement FindingSynthesizer (CONTINUE/STOP/PIVOT)
3. Add next-wave unit generation
4. Agent score tracking + overseer intervention logic
5. Regression detection via history.db
```

**Validation:** Run single-wave campaign, verify feedback loop + synthesis.

### Phase 3: Advanced Features (Weeks 5-6)

```
1. Repair loop (FAILURE → diagnosis → fix)
2. Constraint-driven routing refinement
3. Recall bridge integration (optional)
4. Local Ollama inference (optional)
5. Skill creation from FIXED verdicts
```

**Validation:** Run multi-wave campaign with failures, verify repair flow.

### Phase 4: Optimization & Polish (Weeks 7-8)

```
1. Performance tuning (parallel unit execution)
2. Dashboard/visualization (question tree, verdict timeline)
3. Documentation + agent templates
4. Fallback/error handling comprehensive review
5. Production deployment + monitoring
```

---

## Key Design Differences from BrickLayer 2.0

| Aspect | BrickLayer 2.0 | Masonry |
|--------|----------------|---------|
| **Unit Generation** | Centralized question-designer agent | Multiple generators (initial, followup, goal-driven, feedback-loop, regression) |
| **Routing** | Hard-coded mode-to-agent mapping | Constraint-based dynamic routing |
| **Feedback Loop** | Per-campaign synthesis | Per-wave synthesis + cumulative feedback |
| **Constraint System** | Implicit (code in findings.py) | Explicit (Unit.constraints list) |
| **Agent State** | Per-agent verdicts + overseer intervention | Multi-layer (agent_db, crucible, history, local inference) |
| **Repair Loop** | BL 1.x fixloop (2 attempts) + BL 2.0 healloop (3 cycles) | Unified repair pattern (configurable max cycles) |
| **Storage** | Mixed (JSON + TSV + markdown + SQLite) | Unified append-only + immutable + regression-trackable |
| **Skill Creation** | Explicit agent task | Automatic from FIXED verdicts via synthesis |

---

## Next Steps

1. **Prototype Core Framework** — Implement Phase 1 (Unit model + routing + classification)
2. **Test on Real Campaign** — Run Masonry on a real project, compare results to BrickLayer 2.0
3. **Refine Synthesis Logic** — Tune CONTINUE/STOP/PIVOT decision tree based on prototype results
4. **Build Dashboard** — Port BrickLayer 2.0 dashboard to Masonry schema
5. **Release Alpha** — Documentation + example campaigns + agent templates

---

## References

- BrickLayer 2.0 Architecture Summary: `ARCHITECTURE-SUMMARY.md`
- BrickLayer 2.0 Findings (25 waves): `findings/` directory
- Agent Integration Patterns: `.claude/agents/` directory templates
- Dashboard UI: `dashboard/frontend/src/components/QuestionQueue.tsx`

