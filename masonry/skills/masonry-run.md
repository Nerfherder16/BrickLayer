---
name: masonry-run
description: Start or resume a Masonry research loop campaign
---

## masonry-run — Start or Resume a Campaign

Read `masonry.json` from the current working directory to get project configuration.
If `masonry.json` doesn't exist, use the directory basename as the project name.

### Step 1 — Detect campaign state

Check for `masonry-state.json` in the current directory:
- If it exists → this is a **resume** (Mortar reads its own Recall checkpoint to restore state)
- If it doesn't exist → this is a **new campaign**

Check `questions.md` for PENDING questions. If none exist:
```
Act as the hypothesis-generator-bl2 agent in .claude/agents/hypothesis-generator-bl2.md.
Read findings/synthesis.md and the 5 most recent findings.
Generate Wave N questions and add them to questions.md.
```

Verify `.claude/agents/mortar.md` exists in the project directory. If it doesn't:
- Warn the user: "mortar.md not found in .claude/agents/ — copy agents from the template first"
- Show: `cp -r C:/Users/trg16/Dev/Bricklayer2.0/template/.claude/agents/ .claude/agents/`
- Stop until the agent fleet is in place.

### Step 2 — Load RECALL_API_KEY

Read `~/.masonry/config.json` and extract `recallApiKey`. Set it as the environment variable
before launching.

### Step 3 — Construct the launch command

Mortar is the conductor. It owns the loop, routes questions to specialists, and manages
all wave sentinels. The launch prompt activates Mortar directly.

**New campaign (bash/zsh):**
```bash
cd {project-path}
# masonry-run will inject RECALL_API_KEY from ~/.masonry/config.json automatically
claude --dangerously-skip-permissions "Act as the Mortar agent defined in .claude/agents/mortar.md. Read questions.md and project-brief.md. Begin the campaign from the first PENDING question. NEVER STOP."
```

**Resume existing campaign (bash/zsh):**
```bash
cd {project-path}
# masonry-run will inject RECALL_API_KEY from ~/.masonry/config.json automatically
claude --dangerously-skip-permissions "Act as the Mortar agent defined in .claude/agents/mortar.md. Read questions.md, project-brief.md, and findings/synthesis.md. Resume the campaign from the first PENDING question. NEVER STOP."
```

**Windows PowerShell — new campaign:**
```powershell
cd {project-path}
# masonry-run will inject RECALL_API_KEY from ~/.masonry/config.json automatically
claude --dangerously-skip-permissions "Act as the Mortar agent defined in .claude/agents/mortar.md. Read questions.md and project-brief.md. Begin the campaign from the first PENDING question. NEVER STOP."
```

**Windows PowerShell — resume:**
```powershell
cd {project-path}
# masonry-run will inject RECALL_API_KEY from ~/.masonry/config.json automatically
claude --dangerously-skip-permissions "Act as the Mortar agent defined in .claude/agents/mortar.md. Read questions.md, project-brief.md, and findings/synthesis.md. Resume the campaign from the first PENDING question. NEVER STOP."
```

### Step 4 — Log session start

After presenting the command, store a session-start note to Recall:
- Content: `Masonry campaign started/resumed: {project}, wave {N}, {pending} questions pending. Mortar is conductor.`
- Domain: `{project}-bricklayer`
- Tags: `["masonry", "project:{project}", "masonry:session-start", "agent:mortar"]`
- Importance: 0.4

### Notes

- Mortar reads `.claude/agents/mortar.md` — all specialist agents must be present in `.claude/agents/`
- Do NOT set `DISABLE_OMC=1` — Masonry is the orchestration layer
- Mortar stores checkpoints in Recall every 10 questions under `domain="{project}-bricklayer"` — resume picks them up automatically
- If Recall is unavailable, Mortar continues from questions.md status alone — mention this but do not block launch
- The old `program.md` loop is superseded by Mortar for all BL 2.0 projects
