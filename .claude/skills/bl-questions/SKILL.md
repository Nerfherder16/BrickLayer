---
name: bl-questions
description: Generate the question bank for a BrickLayer 2.0 project — run after project-brief.md, docs/, and simulate.py are ready
---

# /bl-questions — Generate Question Bank

Explicitly generates questions for a BL 2.0 project. Only run when the project
has context: project-brief.md filled in, docs/ populated, simulate.py written.

## Steps

### 1. Identify the project

Use the current working directory. If it does not contain `project-brief.md` and
`simulate.py` (or `program.md`), stop and say:

```
No BrickLayer project found in the current directory.
Run /bl-init first, then fill in project-brief.md and simulate.py before generating questions.
```

### 2. Check readiness

Read `project-brief.md`. If it still contains template placeholders (e.g. `[system name]`,
`TODO`, or is fewer than 20 lines), warn:

```
project-brief.md looks incomplete — it may still be a template stub.
Fill in the ground truth before generating questions, or the question bank will be generic.
Proceed anyway? (yes/no)
```

Wait for confirmation before continuing.

### 3. Run the planner (optional but recommended)

If `CAMPAIGN_PLAN.md` does not exist, offer to run the planner first:

```
No CAMPAIGN_PLAN.md found. Running the planner first produces better-targeted questions.
Running planner now...
```

Spawn the `planner` agent:
```
Act as the planner agent in .claude/agents/planner.md.
Inputs: project_brief=project-brief.md, docs_dir=docs/, constants_file=constants.py, simulate_file=simulate.py, prior_campaign=none
```

### 4. Generate the question bank

Spawn the `question-designer-bl2` agent:
```
Act as the question-designer-bl2 agent in .claude/agents/question-designer-bl2.md.
Project root: {cwd}
Read project-brief.md, all files in docs/, constants.py, simulate.py, and CAMPAIGN_PLAN.md (if it exists).
Generate the initial question bank in questions.md.
```

### 5. Verify and report

Confirm questions.md was written with project-specific questions (no template
placeholders like `[parameter X]`). If placeholders remain, re-run the agent.

Report:
```
Question bank ready: {N} questions across {M} domains.

Next: /bl-run to start the campaign.
```
