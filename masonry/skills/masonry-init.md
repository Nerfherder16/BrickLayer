---
name: masonry-init
description: Initialize a new Masonry project with interactive wizard
---

## masonry-init — Project Initialization

Use the interactive wizard to create a new Masonry project:

```bash
node C:/Users/trg16/Dev/Bricklayer2.0/masonry/bin/masonry-init-wizard.js
```

Or with flags (non-interactive):

```bash
node masonry/bin/masonry-init-wizard.js \
  --name my-project \
  --mode diagnose \
  --path C:/Dev/my-project \
  [--brief path/to/project-brief.md] \
  [--dry-run]
```

**Modes available:** benchmark, evolve, frontier, predict, research, audit, diagnose, validate, monitor, fix

The wizard will:
1. Copy the full template to the target directory
2. Write `masonry.json` with name, mode, and domain
3. Scaffold `evaluate.py` (for evidence modes) or confirm `simulate.py` (for simulation modes)
4. Copy your project brief if provided
5. Generate `registry.json` with all agent metadata

---

### Manual bootstrap (alternative)

### Step 1 — Configure the project

Edit these files:

1. **`project-brief.md`** — What the system does, key invariants, past misunderstandings
2. **`constants.py`** — Set real thresholds (NEVER agent-editable)
3. **`simulate.py`** — Replace stub model with actual model (SCENARIO PARAMETERS section only)
4. **`masonry.json`** — Create this file:
   ```json
   { "name": "{project-name}", "mode": "diagnose", "domain": "{domain}" }
   ```
5. Drop specs/docs into `docs/` — agents read everything here before generating questions

Verify baseline before continuing:
```bash
python simulate.py   # should print verdict: HEALTHY
```

### Step 2 — Install the agent fleet

Mortar is the campaign conductor. All specialist agents must be present in `.claude/agents/`
before the campaign starts.

```bash
cp -r C:/Users/trg16/Dev/Bricklayer2.0/template/.claude/agents/ .claude/agents/
```

**Required agents (BL 2.0 fleet):**

| Agent | File | Role |
|-------|------|------|
| `mortar` | `mortar.md` | **Conductor** — routes questions, manages wave sentinels |
| `planner` | `planner.md` | Campaign planning — ranks domains, writes CAMPAIGN_PLAN.md |
| `question-designer-bl2` | `question-designer-bl2.md` | Initial question bank generation |
| `hypothesis-generator-bl2` | `hypothesis-generator-bl2.md` | Wave N+ question generation |
| `quantitative-analyst` | `quantitative-analyst.md` | simulate mode questions |
| `diagnose-analyst` | `diagnose-analyst.md` | diagnose mode questions |
| `fix-implementer` | `fix-implementer.md` | fix mode questions |
| `compliance-auditor` | `compliance-auditor.md` | audit mode questions |
| `design-reviewer` | `design-reviewer.md` | validate mode questions |
| `competitive-analyst` | `competitive-analyst.md` | market/analogues questions |
| `regulatory-researcher` | `regulatory-researcher.md` | legal/compliance questions |
| `synthesizer-bl2` | `synthesizer-bl2.md` | Session synthesis |
| `forge-check` | `forge-check.md` | Wave sentinel (every 5 questions) |
| `agent-auditor` | `agent-auditor.md` | Wave sentinel (every 10 questions) |
| `peer-reviewer` | `peer-reviewer.md` | Finding validator (after every finding) |

Verify mortar.md is present:
```bash
ls .claude/agents/mortar.md   # must exist before running
```

### Step 3 — (Optional) Run the planner

For complex or multi-domain projects, run the planner first to rank domains and
produce a `CAMPAIGN_PLAN.md` that the question designer will use:

```
Act as the planner agent in .claude/agents/planner.md.
Inputs: project_brief=project-brief.md, docs_dir=docs/, constants_file=constants.py, simulate_file=simulate.py, prior_campaign=none
```

### Step 4 — Generate the initial question bank

```
Act as the question-designer-bl2 agent in .claude/agents/question-designer-bl2.md.
Read project-brief.md, all files in docs/, constants.py, simulate.py, and CAMPAIGN_PLAN.md (if it exists).
Generate the initial question bank in questions.md.
```

### Step 5 — Start the campaign

```bash
git init && git add . && git commit -m "chore: init {project-name} autoresearch"
```

Then start with `/masonry-run`.

Mortar will read `questions.md`, route each question to the appropriate specialist by
**Mode** field, run wave sentinels, and checkpoint progress to Recall every 10 questions.
