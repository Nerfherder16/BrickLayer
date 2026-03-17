# Autoresearch Quickstart

---

## Start the Dashboard (always do this first)

```bash
cd C:/Users/trg16/Dev/autosearch/dashboard
./start.sh C:/Users/trg16/Dev/autosearch/adbp   # swap project path as needed
```

Open: http://localhost:3100

Switch projects anytime from the project switcher in the top bar.

---

## Starting a New Project

### 1. Copy the template
```bash
cp -r C:/Users/trg16/Dev/autosearch/template/ C:/Users/trg16/Dev/autosearch/{project}/
cd C:/Users/trg16/Dev/autosearch/{project}/
```

### 2. Write the project brief (recommended)
Edit `project-brief.md` — fill in:
- What the system actually does (your words, not Claude's)
- The key invariants that cannot be wrong
- Anything Claude has misunderstood about this project before

Delete the file if the project is simple enough that docs/ + README are sufficient.

### 3. Add supporting documents
Drop specs, legal memos, design briefs into `docs/`. The agents read everything here
before generating questions. These are your authoritative sources.

### 4. Adapt the simulation
- `constants.py` — set your real thresholds (immutable during the loop, get it right first)
- `simulate.py` — replace the stub revenue model with your actual model
- Verify: `python simulate.py` → should print `verdict: HEALTHY`

### 5a. (Recommended) Run the planner first

For new or complex projects, run the planner before generating questions. It ranks research domains by risk, queries Recall for prior campaign findings, and produces a `CAMPAIGN_PLAN.md` targeting brief that question-designer uses to set mode allocations.

```
Act as the planner agent in .claude/agents/planner.md.
Inputs: project_brief=project-brief.md, docs_dir=docs/, constants_file=constants.py, simulate_file=simulate.py, prior_campaign=none
```

Skip this step for simple projects where all domains are equally uncertain.

### 5b. Generate the question bank

Open Claude Code in the project directory and invoke the question-designer agent:

```
Act as the question-designer-bl2 agent in .claude/agents/question-designer-bl2.md.
Read project-brief.md, all files in docs/, constants.py, and simulate.py.
If CAMPAIGN_PLAN.md exists, read it first and use its BL 2.0 Mode Allocation table.
Generate the initial question bank in questions.md.
```

If `CONFLICTS.md` is created, resolve the conflicts before continuing.

### 6. Initialize git
```bash
git init
git add .
git commit -m "chore: init {project} autoresearch"
git checkout -b {project}/$(date +%b%d | tr '[:upper:]' '[:lower:]')
```

### 7. Start the loop
```bash
# Supervised — you watch
claude --dangerously-skip-permissions

# Autonomous — walk away
claude --dangerously-skip-permissions "Read program.md and questions.md. Begin the research loop. NEVER STOP."
```

---

## Starting a New Session on an Existing Project

The loop is resumable. Claude picks up wherever it left off.

### 1. Check where things stand
```bash
cd C:/Users/trg16/Dev/autosearch/{project}/
grep "Status" questions.md | head -20      # see which questions are PENDING
tail -10 results.tsv                        # see last 10 results
ls findings/                                # see completed findings
```

Or just open the dashboard — it shows everything at a glance.

### 2. Resume the loop
```bash
git status                                  # make sure no uncommitted experiment is dangling
git log --oneline -5                        # orient yourself

claude --dangerously-skip-permissions "Read program.md, questions.md, and the most recent 3 findings in findings/. Resume the research loop from the first PENDING question. NEVER STOP."
```

### 3. If the loop left an uncommitted experiment
```bash
git diff --stat                             # see what changed
# If it was a FAILURE/WARNING scenario that needs a finding:
git add simulate.py && git commit -m "experiment: resume - {description}"
# Write the finding, then continue
# If it was a HEALTHY scenario that should have been reset:
git reset --hard HEAD
```

---

## Injecting Questions Mid-Loop

**Via dashboard**: Click "Add Question" in the Question Queue panel. Set domain, write
the question, choose Next (jumps the queue) or End (appends). The loop picks it up
automatically on the next iteration.

**Via file**: Add to `questions.md` directly:
```markdown
### Q{next_number}: {Short title}
**Question**: {Your question}
**Hypothesis**: {What you expect}
**Simulation path**: {What to vary}
**Status**: PENDING
```
Insert before the first PENDING question to make it run next.

---

## Making a Correction

When you see the loop getting something wrong:

**Via dashboard**: Open the finding, click "Flag as Wrong", type your correction.
This appends a `## Human Correction` block to the finding file. Agents treat this
as Tier 1 (ground truth), overriding the original finding.

**Via file**: Append to the relevant `findings/{id}.md`:
```markdown
## Human Correction
**Flagged by**: human
**Correction**: {What is actually true}
**This overrides the finding above. Agents must treat this section as Tier 1 authority.**
```

**For systematic misunderstandings** (Claude keeps getting the same thing wrong):
- Add it to `project-brief.md` under "What has been misunderstood before"
- Use `/anchor` in Claude Code to store it in Recall permanently:
  ```
  /anchor
  ```
  Then describe the fact. It will surface in every future session automatically.

---

## Generating the End-of-Session Report

```bash
cd C:/Users/trg16/Dev/autosearch/{project}/
python analyze.py
# PDF saved to reports/
```

Run this after invoking the synthesizer agent for best results:
```
Read all findings in findings/. Produce a synthesis following the format in synthesizer.md.
Write it to findings/synthesis.md.
```

---

## Agent Quick Reference

| Agent | When to invoke |
|-------|---------------|
| `planner` | Once at project init (before question-designer) — ranks domains by risk, writes CAMPAIGN_PLAN.md |
| `question-designer-bl2` | Once at project init (after planner) — generates questions.md using BL 2.0 modes |
| `question-designer` | BL 1.x only — use question-designer-bl2 for new projects |
| `quantitative-analyst` | D1/D5/D6 simulation questions |
| `regulatory-researcher` | D2 legal/compliance questions |
| `competitive-analyst` | D3 market/analogues questions |
| `benchmark-engineer` | When simulate.py calls a live service |
| `hypothesis-generator` | When questions.md is exhausted, or every 5 questions |
| `synthesizer` | At session end, before running analyze.py |

Invoke any agent by telling Claude Code:
```
Act as the {agent-name} agent as defined in .claude/agents/{agent-name}.md.
The current question is: {question text}.
```

---

## File Reference

| File | Purpose | Who edits it |
|------|---------|-------------|
| `project-brief.md` | Ground truth, highest authority | Human only |
| `docs/` | Supporting documents | Human only |
| `constants.py` | Immutable simulation rules | Human only |
| `simulate.py` | Simulation engine | Agent (SCENARIO PARAMETERS only) |
| `questions.md` | Question bank | Agent + human via dashboard |
| `results.tsv` | Loop output log | Agent |
| `findings/*.md` | Per-question findings | Agent + human corrections |
| `CONFLICTS.md` | Source contradictions to resolve | Agent writes, human resolves |
| `program.md` | Loop instructions | Human only |

---

## Common Issues

**Loop stopped asking questions**: `questions.md` has no PENDING questions. Invoke
`hypothesis-generator` to generate a new wave, or add questions via the dashboard.

**Simulation always returns HEALTHY**: The SCENARIO PARAMETERS aren't being stressed
enough. Check `constants.py` — the FAILURE_THRESHOLD may be too low, or the baseline
parameters are too conservative.

**Claude committed a HEALTHY scenario**: Run `git reset --hard HEAD~1`. This is
expected — sometimes the agent misses the reset step.

**Finding is wrong**: Flag it via dashboard or append a `## Human Correction` block.
Then add the correct understanding to `project-brief.md` so it doesn't recur.

**Agent misunderstood the project**: Add the misunderstanding to `project-brief.md`
under "What has been misunderstood before". Use `/anchor` in Claude Code to make it
permanent in Recall.
