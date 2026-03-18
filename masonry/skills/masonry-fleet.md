---
name: masonry-fleet
description: Manage the agent fleet for a Masonry project — show health scores, add/retire agents, audit capability gaps
---

## masonry-fleet — Fleet Health & Management

View agent health, audit the fleet, add new agents, or retire old ones.

### Usage

```
/masonry-fleet [status|audit|forge|add <name>|retire <name>]
```

---

### Sub-commands

| Command | What it does |
|---------|-------------|
| `status` | List all agents with health scores, run counts, last activity |
| `audit` | Invoke `agent-auditor` to scan for capability gaps |
| `forge` | Invoke `forge-check` to validate agent quality |
| `add <name>` | Scaffold a new agent `.md` file and update registry |
| `retire <name>` | Move agent to `.retired/` and update registry |

---

## Sub-command: `status`

Read and display the fleet health table.

**Step 1 — Read data sources:**

1. Read `registry.json` at project root (agent list + metadata)
2. Read `agent_db.json` at project root (scores + run history) — if missing, show "no scores"
3. Read `masonry-state.json` at project root — if present, highlight the currently active agent

**Step 2 — Format output:**

```
MASONRY FLEET · {project} · {N} agents

Agent                    Model    Tier      Score   Runs   Last Activity
─────────────────────────────────────────────────────────────────────────
benchmark-engineer       sonnet   standard  0.82    12     2h ago
diagnose-analyst         sonnet   standard  0.75     8     4h ago
fix-implementer          sonnet   elite     0.90    15     1h ago
mortar                   sonnet   standard   —       —     active ←
...

Summary: {N} active, {N} elite tier, {N} below 0.40 threshold
```

**Tier rules:**
- `elite` — score ≥ 0.85 and runs ≥ 10
- `standard` — everything else
- Show `←` next to the agent listed in `masonry-state.json`.active_agent

**Score rules:**
- If `agent_db.json` missing: show `—` for Score and Runs, show "agent_db.json not found" in Summary
- If `agent_db.json` exists but agent not in it: show `—` for that row

**Last Activity format:**
- Use `last_run` timestamp from `agent_db.json`
- Display as relative time: "2h ago", "just now", "3d ago"
- If no timestamp: show `—`

---

## Sub-command: `audit`

Invoke the `agent-auditor` agent to scan the fleet for capability gaps.

```
Act as the agent-auditor agent in .claude/agents/agent-auditor.md.
Read registry.json, all agent .md files in .claude/agents/, and questions.md (if present).
Identify gaps: questions that no agent is well-suited to answer, agents with low scores or few runs.
Output findings inline.
```

---

## Sub-command: `forge`

Invoke the `forge-check` agent to validate agent quality.

```
Act as the forge-check agent in .claude/agents/forge-check.md.
Read all agent .md files in .claude/agents/.
Validate: frontmatter completeness, instruction quality, self-nomination sections.
Report agents needing improvement.
```

---

## Sub-command: `add <name>`

Create a new agent and add it to the fleet.

**Step 1 — Scaffold the agent file:**

Create `.claude/agents/{name}.md` with this template:

```markdown
---
name: {name}
model: sonnet
description: Activate when [DESCRIBE TRIGGER CONDITIONS HERE]. [One sentence on what this agent does].
tier: standard
---

You are the {Name} specialist for an autoresearch session.

## Inputs (provided in your invocation prompt)

- `question_text`: The full question text from questions.md
- `project_dir`: Path to the project root

## Your Task

[DESCRIBE WHAT THIS AGENT DOES]

## Output Format

Write a finding to `findings/{question_id}.md` with this structure:

```markdown
# {Question ID}: {Question Title}

**Status**: COMPLETE
**Mode**: {mode}
**Agent**: {name}
**Verdict**: [HEALTHY | WARNING | FAILURE | FIXED | INCONCLUSIVE]

## Findings

[Your findings here]

## Evidence

[Evidence supporting your findings]

## Recommendation

[Actionable recommendation]
```

## Self-Nomination

Append to your finding when relevant:
- `[RECOMMEND: synthesizer-bl2 — sufficient findings for synthesis]` after 10+ findings exist
```

**Step 2 — Update registry:**

```bash
node {masonry_bin}/masonry-fleet-cli.js regen {project_dir}
```

Where `masonry_bin` is `C:/Users/trg16/Dev/Bricklayer2.0/masonry/bin`.

**Step 3 — Confirm:**

Report: "Agent `{name}` created at `.claude/agents/{name}.md`. Edit the description and task sections before deploying to a campaign."

---

## Sub-command: `retire <name>`

Remove an agent from the active fleet.

**Step 1 — Move the file:**

```javascript
const fs = require('fs');
const path = require('path');
const src = `.claude/agents/${name}.md`;
const dest = `.claude/agents/.retired/${name}.md`;
fs.mkdirSync('.claude/agents/.retired', { recursive: true });
fs.renameSync(src, dest);
```

**Step 2 — Update registry:**

```bash
node {masonry_bin}/masonry-fleet-cli.js regen {project_dir}
```

**Step 3 — Confirm:**

Report: "Agent `{name}` moved to `.claude/agents/.retired/{name}.md`. Run `/masonry-fleet status` to verify the updated fleet."

---

## Notes

- All fleet operations are local — no network calls
- `agent_db.json` is written by Mortar during campaigns; it will not exist on a new project
- Retired agents can be restored by moving them back from `.retired/` and re-running the registry generator
- `/masonry-fleet audit` and `/masonry-fleet forge` are conversational — they invoke agents inline, no campaign loop needed
