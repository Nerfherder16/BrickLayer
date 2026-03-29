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
7. **Session-start self-check** (run before any question):
   - Confirm this file is fully read — verify the following sections are present:
     `## After writing each finding — spawn peer-reviewer in background` and `## NEVER STOP`.
     If either is missing, re-read program.md completely before continuing.
   - Count findings in `findings/` that do NOT contain a `## Peer Review` section.
     If > 50% of non-INCONCLUSIVE findings lack peer review, log a warning:
     `peer_review_gap: N findings unreviewed` before running the first question.
   - Run `python simulate.py` to confirm the baseline verdict is HEALTHY.
     If WARNING or FAILURE on a clean run, stop and investigate before starting.
8. **Confirm and go.**

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

Invoke `hypothesis-generator-bl2` with the 3 most recent findings as context. It will scan
for gaps and add new questions to `questions.md` as a mid-loop wave. This catches
patterns that only become visible after several findings accumulate — things no initial
question bank anticipates.

The prompt to use:
```
Read the 3 most recent findings in findings/. Identify any failure modes, parameter
interactions, or cross-domain risks they imply that are not covered by remaining PENDING
questions. Add up to 5 new PENDING questions to questions.md. Label them Wave-mid.
```

Do not invoke hypothesis-generator-bl2 on every question — only every 5. The overhead
of running it too frequently outweighs the benefit.

**Immediately after** hypothesis-generator-bl2 completes, spawn forge-check and (if N is a
multiple of 10) agent-auditor as **background agents** — do NOT wait for them:

```
# Always at N % 5 == 0:
Spawn background agent — forge-check:
  "Act as forge-check per .claude/agents/forge-check.md.
   Inputs: agents_dir=.claude/agents/, findings_dir=findings/, questions_md=questions.md.
   Write agents/FORGE_NEEDED.md if gaps found, otherwise output FLEET COMPLETE."

# Additionally at N % 10 == 0:
Spawn background agent — agent-auditor:
  "Act as agent-auditor per .claude/agents/agent-auditor.md.
   Inputs: agents_dir=.claude/agents/, findings_dir=findings/, results_tsv=results.tsv.
   Write the audit report to .claude/agents/AUDIT_REPORT.md."
```

Continue to the next question immediately. Both agents run concurrently with the main loop.
Their outputs are checked at the next **wave-start sentinel check** (see below).

### After writing each finding — spawn peer-reviewer in background

Immediately after writing a finding file and logging to results.tsv, spawn peer-reviewer
as a **background agent** — do NOT wait for it:

```
Spawn background agent — peer-reviewer:
  "Act as peer-reviewer per .claude/agents/peer-reviewer.md.
   primary_finding=findings/<question_id>.md, target_git=., agents_dir=.claude/agents/.
   Re-run the original test independently, review the fix code, append ## Peer Review
   section with verdict CONFIRMED | CONCERNS | OVERRIDE."
```

Continue to the next question immediately. OVERRIDE verdicts are caught at the next
wave-start sentinel check.

### Wave-start sentinel check (runs before EVERY question)

Before picking the next question from questions.md, check for pending sentinel outputs.
This takes <1 second and closes the async loop:

1. **`agents/FORGE_NEEDED.md` exists?**
   → Invoke Forge **synchronously** (blocking) to create missing agents, then delete the file.
   Forge must complete before the next question starts — new agents may be needed for it.

2. **`agents/AUDIT_REPORT.md` exists?**
   → Read it. Apply RETIRE (delete agent file), PROMOTE (update `tier:` field), and
   UPDATE TRIGGERS (edit `trigger:` frontmatter) recommendations immediately.
   Delete `AUDIT_REPORT.md` when done. Continue — this is non-blocking.

3. **Any finding file contains `**Verdict**: OVERRIDE` inside a `## Peer Review` section?**
   → Insert a new PENDING re-examination question at the top of the next wave in
   `questions.md`. Continue — do not revert any commit without human confirmation.

4. **HHI diversity sentinel** (after Wave 5 only — skip in earlier waves):
   Count findings per category from `findings/`. If any single category accounts for
   > 40% of all findings, it is over-concentrated. Before redirecting:
   **Severity-exemption gate**: if the over-concentrated category contains a CRITICAL
   or High-severity finding written in the **current wave**, suppress the diversity
   redirect for that category for the next 3 waves. Only redirect when concentration
   comes from Low/Info redundancy, not active critical investigation.
   If redirection is warranted: insert a PENDING question targeting the category with
   zero findings (any category with zero findings after Wave 10 = mandatory floor
   redirect, higher priority than HHI threshold).

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
question_id	verdict	agent_name	timestamp	summary
```

Append one row per completed question in this exact column order.
Use `N/A` for agent_name on manual runs if no agent was invoked.

---

## Finding Format

Write each finding to `findings/<question_id>.md` (flat directory, no wave subdirectories):

```markdown
# Finding: <question_id> — <short title>

**Question**: [copy from questions.md]
**Agent**: [name of specialist agent that produced this finding, e.g. quantitative-analyst]
**Verdict**: FAILURE | WARNING | HEALTHY | INCONCLUSIVE
**Severity**: Critical | High | Medium | Low | Info

## Evidence
[What the simulation output showed, or what your research found. Quote specific numbers.]

## Mitigation Recommendation
[What should change in the model, the system design, or the legal/operational strategy]

**Files to change** *(required for FAILURE and High severity findings; omit for Medium/Low/Info)*:
- `path/to/file.js` — specific change and why it is required
- `path/to/other.js` — specific change and why it is required

*List EVERY file that must change for this fix to be complete. A fix that touches only
one file when two are required is a partial fix — Wave 2 will catch it, but that wastes
a verification question. RETRO-H3: partial fixes are the #1 source of false-DONE verdicts
in multi-file defects.*

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
| `hypothesis-generator-bl2` | `agent:hypothesis-generator-bl2` | Wave N summaries |

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

## Wave-End Shutdown (question bank exhausted)

When all questions are DONE or INCONCLUSIVE and no new ones remain, run the final audit
**before stopping** — do NOT skip these even if the loop ends naturally:

```
Invoke agent-auditor (foreground):
  "Act as agent-auditor per .claude/agents/agent-auditor.md.
   Inputs: agents_dir=.claude/agents/, findings_dir=findings/, results_tsv=results.tsv.
   Write the final audit report to .claude/agents/AUDIT_REPORT.md."

Invoke forge-check (foreground):
  "Act as forge-check per .claude/agents/forge-check.md.
   Inputs: agents_dir=.claude/agents/, findings_dir=findings/, questions_md=questions.md."

Invoke skill-forge (foreground, if .claude/agents/skill-forge.md exists):
  "Act as skill-forge per .claude/agents/skill-forge.md.
   Distill reusable patterns from this campaign's findings into ~/.claude/skills/."

Invoke synthesizer-bl2 (foreground):
  "Act as synthesizer-bl2 per .claude/agents/synthesizer-bl2.md.
   Read all findings in findings/. Write synthesis.md and update CHANGELOG.md,
   ARCHITECTURE.md, ROADMAP.md."
```

Then stop. This is the only valid stopping condition — question bank exhausted AND
final audit complete.

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
