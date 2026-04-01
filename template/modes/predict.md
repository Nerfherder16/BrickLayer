# Predict Mode — Program

**Purpose**: Given the current finding graph, project what will fail next.
Not finding new failures (Diagnose) — reasoning forward from known failures
to their downstream consequences. Answer: "If we don't fix X, what breaks?"

**Input**: `findings/synthesis.md` + all open FAILURE/WARNING findings
**Verdict vocabulary**: IMMINENT | PROBABLE | POSSIBLE | UNLIKELY
**Output**: A prioritized failure cascade map

---

## Loop Instructions

### Pre-flight

1. Read `findings/synthesis.md` — understand the current open failure landscape
2. Read all FAILURE and WARNING findings — understand each root cause
3. Read `project-brief.md` — understand the system's stated invariants
4. Build a causal graph: for each open failure, ask "what does this failure enable?"

### Per-question

Questions reason about causal chains:
- "If the double-decay bug is not fixed, what happens to corpus quality in 30 days?"
- "If the retrieval coverage failure persists, what downstream features degrade?"
- "If the floor-clamped pool reaches 2,000 memories, does query performance degrade?"
- "What is the interaction between failure X and failure Y when they co-occur?"

Evidence gathering:
- Read the original findings to understand current state and trajectory
- Use `benchmarks.json` to establish growth/decay rates
- Use `simulate.py` to project parametric trends forward
- Use mathematical reasoning: "at current rate of N per day, threshold T reached in T/N days"

Verdict assignment (objective criteria required — not subjective):

**Quantitative chains** (measurable metric, known rate):
- `IMMINENT` — threshold crossed in ≤30 days at current rate
- `PROBABLE` — threshold crossed in 31–90 days at current rate
- `POSSIBLE` — threshold crossed in 91–180 days at current rate, requires ≥1 precondition still pending
- `UNLIKELY` — threshold crossed in >180 days OR requires ≥3 preconditions none of which are active

**Qualitative chains** (behavioral/cascading failure without a metric):
- `IMMINENT` — 3+ documented instances of the triggering failure pattern active simultaneously
- `PROBABLE` — 2 documented instances; a third is structurally predictable
- `POSSIBLE` — 1 documented instance; cascade requires ≥2 additional co-occurring conditions
- `UNLIKELY` — failure mode is documented but no active precursor found in findings

**Interaction pairs**: Analyze top 3–5 most dangerous co-occurring failure pairs only. Do not enumerate all O(N²) combinations — filter to pairs that share a causal pathway.

### Causal chain format

Every finding must include:
```
## Causal Chain
Trigger: [existing finding ID] — [current state]
    ↓ [mechanism]
Cascade: [what fails]
    ↓ [mechanism]
Impact: [user-visible or system-critical consequence]
Timeline: [IMMINENT / days / weeks]
```

### Wave structure

- One question per major open failure + one question per failure interaction pair
- No hypothesis generator — questions come directly from the open finding graph
- Stop condition: all FAILURE findings have been projected forward; all interaction pairs analyzed

### Session end

Produce `failure-cascade-map.md`:
- All causal chains identified
- Priority order: IMMINENT first, then PROBABLE, then POSSIBLE
- Recommended intervention order (which fix prevents the most downstream damage)
- The cascade map is the input to Fix mode prioritization
