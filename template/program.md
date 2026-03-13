# Autoresearch Program — Generic Template

This is a business model / system stress-testing experiment. An AI agent (Claude Code)
iterates on scenario parameters in `simulate.py`, runs the simulation, evaluates
whether a failure condition was discovered, and loops autonomously.

The goal is NOT to find the best-performing scenario. The goal is to **map the
failure boundary** — to discover which parameter combinations break the system,
and why.

---

## Setup

To set up a new research session:

1. **Agree on a run tag**: propose a tag based on today's date (e.g., `mar11`).
   The branch `{project}/<tag>` must not already exist.
2. **Create the branch**: `git checkout -b {project}/<tag>` from current main.
3. **Read these files for full context** (do not modify them):
   - `constants.py` — immutable system rules
   - `questions.md` — the question bank organized by domain
4. **Read the editable file**:
   - `simulate.py` — the simulation you will modify
5. **Verify the simulation runs**: `python simulate.py`
   - Confirm you see `verdict: HEALTHY` on the baseline run
6. **Initialize results.tsv**: Create it with just the header row.
7. **Confirm and go.**

---

## What You CAN Do

- Modify `simulate.py` — this is the ONLY file you edit.
  - Change `SCENARIO_NAME` to describe what you're testing
  - Change any value in the SCENARIO PARAMETERS section
  - You may also refine the simulation engine logic if you discover a modeling error,
    but document it as a finding before changing it

## What You CANNOT Do

- Modify `constants.py` — these are immutable system rules
- Modify `program.md` — this is the human's research strategy document
- Modify `questions.md` without logging a finding first
- Install new packages

---

## The Research Loop

Each experiment tests one hypothesis from `questions.md`. Work through questions
in priority order as defined in the question bank.

Note: Some domains may require web research rather than simulation runs. For those,
use your knowledge base and flag any post-2024 information as needing external validation.

### For simulation questions:

1. Pick the next PENDING question from `questions.md`
2. Form a hypothesis: "If [parameter] is set to [value], the system should [expected behavior]"
3. Update `SCENARIO_NAME` in `simulate.py` to describe the hypothesis
4. Modify the scenario parameters
5. `git commit -m "experiment: <scenario description>"`
6. Run: `python simulate.py > run.log 2>&1`
7. Read results: `grep "^verdict:\|^treasury_runway_months:\|^failure_reason:" run.log`
8. Evaluate:
   - `FAILURE` or `WARNING` → **keep the commit**, write a finding to `findings/<question_id>.md`
   - `HEALTHY` → `git reset --hard HEAD~1`, try a different parameter value or move on
9. Log to `results.tsv`
10. Mark the question as DONE (or INCONCLUSIVE) in `questions.md`
11. **Check the finding for follow-ups** (see Live Discovery below)

### For research questions:

1. Pick the next PENDING question
2. Answer from your knowledge base, flagging anything uncertain or potentially outdated
3. Write the finding directly to `findings/<question_id>.md`
4. Log to `results.tsv` as a research run (no commit/reset cycle needed)
5. Mark DONE or INCONCLUSIVE
6. **Check the finding for follow-ups** (see Live Discovery below)

---

## Live Discovery — Questions the Loop Generates Itself

### After every finding (Critical or High severity)

When you write a finding with severity Critical or High, append this section to the finding file:

```markdown
## Suggested Follow-ups
- [New question this finding raises, stated as a falsifiable hypothesis]
- [Another follow-up if applicable]
```

Then immediately insert those questions into `questions.md` as PENDING, placed **before**
any remaining lower-priority questions. Do not wait for the current wave to finish.
This keeps high-severity threads alive while they are hot.

### Every 5 completed questions

Invoke `hypothesis-generator` with the 3 most recent findings as context. It will scan
for gaps and add new questions to `questions.md` as a mid-loop wave. This catches
patterns that only become visible after several findings accumulate — things no initial
question bank anticipates.

The prompt to use:
```
Read the 3 most recent findings in findings/. Identify any failure modes, parameter
interactions, or cross-domain risks they imply that are not covered by remaining PENDING
questions. Add up to 5 new PENDING questions to questions.md. Label them Wave-mid.
```

Do not invoke hypothesis-generator on every question — only every 5. The overhead
of running it too frequently outweighs the benefit.

Also invoke `forge-check` to scan for agent coverage gaps:
```
Act as the forge-check agent in .claude/agents/forge-check.md.
Inventory the agent fleet in .claude/agents/, scan the 5 most recent findings,
and check all PENDING questions for missing agents.
If gaps exist, write agents/FORGE_NEEDED.md. If no gaps, output FLEET COMPLETE.
```

If `agents/FORGE_NEEDED.md` is written, immediately invoke Forge to fill the gap
before continuing the loop.

### Every 10 completed questions

Invoke `agent-auditor` to assess fleet health and recommend promote/retire/update actions:
```
Act as the agent-auditor agent in .claude/agents/agent-auditor.md.
Read all .md files in .claude/agents/, read results.tsv, and read the findings/ directory.
Write the fleet health report to .claude/agents/AUDIT_REPORT.md.
```

Apply any RETIRE recommendations immediately (delete the agent file).
Apply PROMOTE recommendations by updating the agent's `tier` frontmatter field.
Apply UPDATE TRIGGERS recommendations by editing the agent's `trigger:` frontmatter.
Do not apply CRUCIBLE REVIEW recommendations autonomously — flag to the researcher.

### After every fix wave

Invoke `peer-reviewer` on the highest-severity finding from the wave:
```
Act as the peer-reviewer agent in .claude/agents/peer-reviewer.md.
Primary finding: findings/<question_id>.md
Target git: . (current repo)
Agents dir: .claude/agents/
Re-run the original test, review the fix code, and append a ## Peer Review section
to the finding file with your verdict (CONFIRMED | CONCERNS | OVERRIDE).
```

If peer-reviewer returns OVERRIDE, create a new PENDING question in `questions.md`
for the original fix agent to re-examine, then continue the loop. Do not revert the
fix commit without human confirmation.

---

## Output Format

After each `python simulate.py` run, the script prints:
```
verdict: HEALTHY|WARNING|FAILURE
treasury_runway_months: <float>    (or equivalent primary metric)
failure_reason: <str or NONE>
```

Extract key metrics:
```bash
grep "^verdict:\|^primary_metric:\|^failure_reason:" run.log
```

---

## Logging to results.tsv

Tab-separated, NOT comma-separated. Header:
```
commit	question_id	verdict	primary_metric	key_finding	scenario_name
```

Use `N/A` for primary_metric on research questions (no sim run).

---

## Finding Format

Write each finding to `findings/<question_id>.md`:

```markdown
# Finding: <question_id> — <short title>

**Question**: [copy from questions.md]
**Verdict**: FAILURE | WARNING | HEALTHY | INCONCLUSIVE
**Severity**: Critical | High | Medium | Low | Info

## Evidence
[What the simulation output showed, or what your research found. Quote specific numbers.]

## Mitigation Recommendation
[What should change in the model, the system design, or the legal/operational strategy]

## Suggested Follow-ups
[Required for Critical/High severity. Omit for Low/Info. Each line is a falsifiable
hypothesis that this finding directly implies — insert these into questions.md immediately.]
- [follow-up question 1]
- [follow-up question 2]
```

---

## Severity Definitions

| Severity | Meaning |
|----------|---------|
| Critical | System cannot launch or sustain in this scenario. Requires architecture change. |
| High | System survives but with degraded economics or near-term solvency risk. Requires mitigation. |
| Medium | System healthy but a parameter is closer to the failure boundary than modeled. Monitor closely. |
| Low | Edge case unlikely in practice but worth documenting. |
| Info | No risk found. System behaves as expected. |

---

## Agent Tag Convention

When invoking specialist agents, each agent stores its working memory in Recall under a
consistent tag. Use these tags to retrieve an agent's prior work without re-running it:

| Agent | Tag | What it stores |
|-------|-----|----------------|
| `question-designer` | `agent:question-designer` | Wave 1 question bank summary |
| `quantitative-analyst` | `agent:quantitative-analyst` | Failure boundaries, sensitivity rankings |
| `regulatory-researcher` | `agent:regulatory-researcher` | Legal frameworks, INCONCLUSIVE flags |
| `competitive-analyst` | `agent:competitive-analyst` | Market analogues, fee/participation benchmarks |
| `benchmark-engineer` | `agent:benchmark-engineer` | Baselines, regression reports |
| `synthesizer` | `agent:synthesizer` | Dependency map, minimum viable change set |
| `hypothesis-generator` | `agent:hypothesis-generator` | Wave N summaries |

**All agents use `domain="{project}-autoresearch"`** — replace `{project}` with the actual
project name (e.g., `adbp-autoresearch`, `recall-autoresearch`).

To retrieve what any agent stored:
```
recall_search(query="[relevant topic]", domain="{project}-autoresearch", tags=["agent:{name}"])
```

To retrieve everything stored this session across all agents:
```
recall_search(query="[topic]", domain="{project}-autoresearch", tags=["autoresearch"])
```

---

## NEVER STOP

Once the experiment loop has begun, do NOT pause to ask if you should continue.
Do NOT ask "should I keep going?" The researcher may be away from their computer
and expects autonomous work until manually interrupted.

If you run out of questions in the question bank, generate new ones based on
findings so far — each failure state raises new hypotheses. The loop runs until
the researcher interrupts you, period.

When you discover a Critical or High severity finding, write the finding immediately,
commit the scenario, then continue to the next question. Do not stop to report.
The researcher will review findings when they return.
