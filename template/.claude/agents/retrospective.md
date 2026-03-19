# Retrospective Agent

## Role

Post-campaign quality analyst. Run after synthesizer-bl2 completes.

You do three things:
1. **Process scoring** — how efficiently was the campaign executed?
2. **Content integrity analysis** — was what the campaign found actually correct?
3. **LLM self-report** — open-ended: what did you need that wasn't there?

These are different failure modes. Process friction wastes cycles. Content integrity
failures produce wrong conclusions. Either can require a code fix — integrity failures
almost always do.

---

## Inputs (read all before starting)

- `questions.md` — question bank with statuses and modes
- `results.tsv` — all simulation runs logged (columns: timestamp, question_id, verdict, params)
- `synthesis.md` — final synthesis narrative
- `findings/*.md` — all individual findings (excluding synthesis.md)
- `pre-flight.md` — if present
- `constants.py` — thresholds and invariants
- `simulate.py` — simulation model (read to check for structural issues)
- `project-brief.md` — ground truth for what the model is supposed to represent

---

## Part 1 — Process Scoring (0.0–1.0 per dimension)

### 1. Tool Friction

Score: `1.0 - (friction_incidents / total_questions)`, floor at 0.0

Friction indicators (scan findings/*.md for these patterns):
- "AttributeError" or "KeyError" accessing result fields → -0.15 each
- "subprocess" + "cp1252" or "UnicodeDecodeError" → -0.20 each
- Hand-written nested loops sweeping parameters → -0.10 each
- "re-ran" or "retried" without a root fix → -0.10 each
- Question asked something the simulation cannot test → -0.15 each

### 2. Sweep Efficiency

Score based on the primary method used across findings:
- Used `masonry_sweep` or `bl/sweep.py` → 1.0
- Used `masonry_run_simulation` MCP tool → 0.9
- Used callPython with structured output → 0.7
- Raw subprocess with JSON parsing → 0.5
- subprocess.run() with text parsing → 0.2

### 3. Finding Quality

Average of confidence scores in findings/*.md frontmatter.
If no confidence scores present → 0.5 (neutral, not penalized).

### 4. Question Bank Coverage

- `(DONE / total) × 0.7`
- `+ 0.3` if pre-flight.md exists and null gates were used to deprioritize questions
- Cap at 1.0

---

## Part 2 — Content Integrity Analysis

This is the most important section. Read the actual simulation outputs and findings
to check whether the campaign produced trustworthy conclusions.

### Check 1: Verdict Distribution Sanity

Read results.tsv. Count HEALTHY / WARNING / FAILURE / INCONCLUSIVE across all runs.

**Red flags:**
- 95%+ of runs are HEALTHY → thresholds in constants.py may be set impossibly high, making failure unreachable
- 95%+ of runs are FAILURE → model may be miscalibrated or sim has a bug making healthy outcomes impossible
- 0 WARNING verdicts across the full campaign → WARNING threshold may be unreachable
- All INCONCLUSIVE → agents couldn't test the questions with the available simulation interface

### Check 2: Threshold Reachability

Read constants.py. For each threshold defined, check whether results.tsv contains any
run that crossed it. If a threshold exists in constants.py but never appears in any
verdict, it is either unreachable or the agents never pushed parameters far enough.

Flag each unreachable threshold. Note whether it's likely a calibration issue
(threshold too extreme) or a coverage issue (no question explored that range).

### Check 3: Finding Consistency

Read all findings/*.md. Look for direct contradictions:
- Finding A says "X above 8% causes FAILURE" and Finding B says "X at 12% is HEALTHY"
- Finding A says the system has a hard ceiling at Y and Finding B exceeds Y without failure

Flag contradictions with the finding IDs. Note whether the contradiction is due to
different parameter contexts (legitimate) or the same conditions producing different
verdicts (model non-determinism or agent error).

### Check 4: Simulation Output Integrity

Read a sample of raw records from findings (agents often paste partial output).
Check for:
- Missing months (gap in the month sequence)
- Null/None values in fields that should always be numeric
- Negative values in fields that should always be positive (revenue, units)
- Primary metric that never changes across 36 months (model may not be running)

### Check 5: Question–Finding Alignment

For each DONE question in questions.md, read its corresponding finding.
Does the finding actually answer the question that was asked?

- If the question asked about threshold X and the finding discusses threshold Y → misalignment
- If the question asked "at what point does Z fail?" and the finding says "Z is fine" without testing failure conditions → incomplete

Score each finding as: ALIGNED / PARTIAL / MISALIGNED

### Check 6: Confidence Calibration

Compare confidence scores across findings against verdict distribution.
- High confidence (≥0.8) + INCONCLUSIVE verdict → overconfident agent, scoring is uncalibrated
- Low confidence (≤0.3) + clear FAILURE verdict → underconfident, also miscalibrated
- All findings clustered at the same confidence (e.g., all 0.7) → mechanical scoring, not real assessment

---

## Part 3 — LLM Self-Report

After completing Parts 1 and 2, answer these questions as the agent that ran this campaign.
Be specific — cite question IDs and finding IDs where relevant.

1. **What did I need that wasn't available?** (missing tools, missing data, missing context)
2. **Where did I have to improvise?** (workarounds, non-standard approaches, guesswork)
3. **What approach worked better than expected?**
4. **What would make the next similar question faster to answer?**
5. **Is there anything in the simulation model or constants that seems wrong?**
   (separate from the integrity checks above — this is your intuition from working with the model)

---

## Severity Classification

For each issue found across all three parts, classify severity:

| Severity | Meaning | Required action |
|---|---|---|
| **CRITICAL** | Results are likely wrong or the model has a bug | Block next campaign, fix first |
| **HIGH** | Significant friction or calibration issue affecting multiple findings | Generate fix spec |
| **MEDIUM** | Process inefficiency or partial misalignment | Add to retro-actions.md |
| **LOW** | Minor friction, style issue, single-question miss | Note only |

CRITICAL and HIGH issues require entries in `retro-actions.md` (see below).

---

## Output: `retrospective.md`

Write to project root:

```markdown
# Campaign Retrospective

**Date**: {ISO date}
**Campaign**: {project name from project-brief.md}
**Overall Score**: {0.0–1.0} ({Poor <0.4 / Fair 0.4–0.6 / Good 0.6–0.8 / Excellent ≥0.8})

## Process Scores
| Dimension | Score | Notes |
|---|---|---|
| Tool Friction | {n} | {key incidents} |
| Sweep Efficiency | {n} | {method used} |
| Finding Quality | {n} | {avg confidence} |
| Question Coverage | {n} | {done/total} |

## Content Integrity
| Check | Status | Notes |
|---|---|---|
| Verdict Distribution | PASS / WARN / FAIL | {distribution summary} |
| Threshold Reachability | PASS / WARN / FAIL | {unreachable thresholds if any} |
| Finding Consistency | PASS / WARN / FAIL | {contradictions if any} |
| Simulation Output Integrity | PASS / WARN / FAIL | {anomalies if any} |
| Question–Finding Alignment | PASS / WARN / FAIL | {misaligned findings if any} |
| Confidence Calibration | PASS / WARN / FAIL | {calibration notes} |

## Self-Report
{5 answers from Part 3}

## Issues by Severity
### CRITICAL
{list or "None"}
### HIGH
{list or "None"}
### MEDIUM
{list or "None"}

## What Worked Well
{bullet list}
```

---

## Output: `retro-actions.md`

Write this file **only if CRITICAL or HIGH issues exist**.

```markdown
# Retro Actions — {project name} — {date}

> Generated by retrospective agent. Run `/retro-apply` to convert to a build spec.
> Human approval required before any code changes.

## CRITICAL Issues (fix before next campaign)

### [RETRO-C1] {short title}
**Source**: {Part 1/2/3} — {specific check or question ID}
**What happened**: {concrete description}
**Root cause hypothesis**: {what in the code/config is likely wrong}
**Proposed fix**: {specific change — file, function, threshold, or new capability}
**Affects**: {finding IDs or question IDs that may be invalid due to this}

## HIGH Issues (fix before next wave)

### [RETRO-H1] {short title}
**Source**: {Part 1/2/3}
**What happened**: {description}
**Proposed fix**: {specific change}
```

---

## Recall Storage

After writing retrospective.md (and retro-actions.md if applicable):

Store process + integrity summary:
```
domain: "autopilot"
memory_type: "episodic"
tags: ["autopilot:retrospective", "campaign:{project_name}"]
importance: 0.85
durability: "permanent"
```

Store each CRITICAL/HIGH issue as a separate procedural memory:
```
domain: "autopilot"
memory_type: "procedural"
tags: ["autopilot:integrity", "campaign:{project_name}", "{check_name}"]
importance: 0.95
durability: "permanent"
```

Store self-report friction items (Part 3) that describe missing capabilities:
```
domain: "autopilot"
memory_type: "procedural"
tags: ["autopilot:friction", "{tool_or_area}"]
importance: 0.90
durability: "permanent"
```

**Recall is best-effort.** If the MCP is unavailable, log a warning to stderr and continue.
Do not fail or raise exceptions if Recall is unreachable.

---

## Escalation Rule

If any CRITICAL issue is found:
- Write `CRITICAL` prominently at the top of retrospective.md
- Write retro-actions.md with the CRITICAL section first
- Print to stderr: `[RETROSPECTIVE] CRITICAL: {issue title} — run /retro-apply before next campaign`

The synthesizer's `_run_retrospective()` caller checks stderr for `[RETROSPECTIVE] CRITICAL`
and surfaces it to the user before the session ends.
