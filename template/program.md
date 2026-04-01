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
7. **Pre-flight scan** (run once after question bank is generated, before Wave 1 begins):
   For each question in questions.md, read its target file(s) and assess whether the H1
   hypothesis is *plausible* based on a surface read. Produce a one-line note:
   - `NULL-GATE` — H0 is almost certainly true; deprioritize (run last)
   - `HIGH-RISK` — H1 looks likely; run first and generate sub-hypotheses now
   - `NORMAL` — unclear; run in default order
   Record the pre-flight assessment as a comment in questions.md (e.g., `<!-- HIGH-RISK -->`).
   This prevents reactive follow-up questions from stalling Wave 1 momentum.
   *(RETRO-H2: skipping pre-flight costs ~4 unplanned follow-up questions per 25-question campaign.)*

8. **Session-start self-check** (run before any question):
   - **Marker check** — Read this file (program.md) fully into context. Verify ALL THREE
     of the following substrings are present in what you just read:
     1. `spawn peer-reviewer` (marker A — Live Discovery peer review spawn)
     2. `spawn forge-check` (marker B — Live Discovery fleet gap spawn)
     3. `agent-auditor` (marker C — Live Discovery audit spawn)

     **If all three are present**: continue to the next checks.
     **If any marker is absent**:
     1. Re-read this file from disk using the Read file tool (do not rely on session cache).
     2. Re-check all three markers.
     3. If now present: continue.
     4. If still absent: write `findings/SELF_CHECK_FAILURE.md` with the missing markers
        listed, then STOP. Do not process any questions. Human action required.

     *(Q7.6: these markers target operative spawn instructions, not section headers.
     They survive header-level reformatting and detect the Session A failure mode where
     Live Discovery was missing, causing 20+ waves of unreviewed findings.)*

   - **Peer review gap** — Count findings in `findings/` that do NOT contain a `## Peer Review`
     section. If > 50% of non-INCONCLUSIVE findings lack peer review, log a warning:
     `peer_review_gap: N findings unreviewed` before running the first question.
   - **Baseline run** — Run `python simulate.py` to confirm the baseline verdict is HEALTHY.
     If WARNING or FAILURE on a clean run, stop and investigate before starting.
9. **Confirm and go.**

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

4. **HHI diversity sentinel with severity-exemption gate** (skip until ≥ 10 WARNING/FAILURE
   findings exist — early campaigns have too few data points for stable HHI):

   **CRITICAL FAILURE definition** — a finding is CRITICAL FAILURE if **both**:
   - Header contains: `**Verdict**: FAILURE`
   - Title or first 30 lines contains at least one of:
     `never surfaced` / `never retrieved` / `never injected` / `data loss` /
     `silently drops` / `regression` / `split-brain confirmed` / `0 prefetch hits` /
     `0 hits ever` / `memory never` / regex: `hit rate [0-9]\.`

   **Exemption window** — when a CRITICAL FAILURE is recorded for category C in wave W:
   - C is exempt from HHI redirect for waves W through W+4 (5 waves inclusive).
   - Early expiry: exempt status clears if C transitions to WARNING/HEALTHY in 3 consecutive
     findings AND no new FAILURE in C in the last 2 waves AND restricted-HHI < 0.40.

   **HHI computation** (on restricted set):
   1. Collect all WARNING+FAILURE findings.
   2. Remove findings in currently-exempt categories from the denominator.
   3. Compute HHI on the restricted set.
   4. If restricted set has 0 categories: skip HHI entirely, emit AUDIT_REPORT advisory.
   5. If restricted set has 1 category: advisory-only mode (no redirect useful).
   6. If HHI > 0.40: identify the most-underrepresented non-exempt category.
      Tie-break: fewer questions asked, then alphabetical.
      Emit: inject 2 PENDING questions per wave toward that category.

   **Zero-findings floor** — any category with zero findings after Wave 10 gets a mandatory
   floor redirect (higher priority than HHI threshold).

   *(Q7.5: per-category exemption prevents suppression of critical deep-dives like the
   wave 13 retrieval cluster. Multi-CRITICAL case degrades gracefully — HHI narrows to
   non-exempt categories, and suspends entirely when all categories are exempt.)*

### SUBJECTIVE Verdict Handling (Model B Queue)

A finding with `**Verdict**: SUBJECTIVE` means sufficient evidence was gathered but only
a human can resolve the verdict. Mark the question DONE and annotate the Status line:

    **Status**: DONE  <!-- SUBJECTIVE: awaiting human resolution -->

**At each wave-start sentinel check**, count unresolved SUBJECTIVE annotations in the
current wave. If backlog > 5, output a list of unresolved IDs to the terminal before
continuing. If backlog > 10, append `<!-- ESCALATION: review debt >10 -->` to the wave
header. Do not halt the campaign on either condition.

**Resolution (Tim's action)**: Read the finding. Update `**Verdict**` to the actual
verdict. Add `## Human Resolution` section (1-3 sentences). Remove the SUBJECTIVE
annotation from the Status line. Campaign target: resolve ≥ 70% of SUBJECTIVE findings
per wave before the next wave-start check.

**SUBJECTIVE is not INCONCLUSIVE.** INCONCLUSIVE = insufficient evidence.
SUBJECTIVE = evidence gathered, human judgment required to weigh it.

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
**Confidence**: 0.0–1.0 *(required; 0.9+ = strong evidence with line citations; 0.7 = reasonable inference; <0.5 = speculative)*

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

## Peer Review
*(Required for FAILURE and Critical/High severity findings. Omit for WARNING/HEALTHY/Low/Info.)*

Re-read the source independently (do not re-use evidence already cited above). Confirm or
deny the verdict. Append one of:
- `CONFIRMED — [one-sentence independent evidence]`
- `CONCERNS — [what differs from the primary finding]`
- `OVERRIDE — [verdict should be X because ...]`

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
