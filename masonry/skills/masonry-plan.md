---
name: masonry-plan
description: Interactive planning mode — create a spec for /masonry-build. "plan this", "plan the", "I want to build". Creates .autopilot/spec.md.
---

## masonry-plan — Interactive Specification

You are a **planning architect**. Your job is to produce a precise, complete spec that `/masonry-build` can execute without asking questions.

### State Machine

```
(inactive) → /masonry-plan → PLANNING → approve → /masonry-build → BUILDING
                 ↑                                        ↑
                 └──── revise ─────────────────────────────┘
```

### Step 1 — Explore First

Before asking anything, explore the codebase:
- Read `CLAUDE.md` or `README.md` if present
- List the top-level directory structure
- Identify the tech stack (package.json, pyproject.toml, etc.)
- Note existing patterns you must follow

### Step 2 — Interview

Ask the user these questions (combine into one message, answer all before proceeding):

1. **What** needs to be built? (feature, bug fix, refactor)
2. **Where** does it fit? (which files/modules are affected)
3. **Why** does it need to exist? (the problem being solved)
4. **How** should it work? (key behaviors, edge cases)
5. **Done** looks like what? (acceptance criteria)

Do NOT ask about things you can determine by reading the code.

### Step 3 — Write the Spec

Create `.autopilot/` directory and write `spec.md`:

```
.autopilot/
  mode     ← write "plan"
  spec.md  ← the specification
```

**`spec.md` format:**

```markdown
# Spec: {title}

## Context
{1-3 sentences on why this exists}

## Tech Stack
{language, framework, key dependencies}

## Tasks
| # | Description | Files | Est |
|---|-------------|-------|-----|
| 1 | {task} | {files} | S/M/L |

## Acceptance Criteria
- [ ] {criterion 1}
- [ ] {criterion 2}

## Constraints
- {constraint 1}

## Design System
{If .ui/tokens.json exists: inject token summary here}
{If .ui/components.json exists: list available components}
```

### Step 4 — Present & Approve

Show the spec to the user, then use the **AskUserQuestion** tool to present a choice:

```
Question: "Spec ready — what would you like to do?"
Options:
  - "Approve & compact then build"
  - "Approve & build now"
  - "Revise the spec"
  - "Cancel"
```

Do NOT start building without explicit approval.

**On "Approve & compact then build":**
1. Write `"build"` to `.autopilot/mode`
2. Write `.autopilot/compact-state.json`:
   ```json
   { "auto_build": true, "spec": "spec.md", "approved_at": "<ISO-8601>" }
   ```
3. Write the Mortar session token to `masonry-state.json` (merge, don't overwrite):
   ```bash
   node -e "
   const fs = require('fs');
   const p = 'masonry-state.json';
   let s = {};
   try { s = JSON.parse(fs.readFileSync(p, 'utf8')); } catch {}
   s.mortar_consulted = true;
   s.mortar_session_id = new Date().toISOString();
   fs.writeFileSync(p, JSON.stringify(s, null, 2));
   "
   ```
4. Tell the user:
   > "Spec approved. Run `/compact` now — after compaction I'll automatically resume with `/masonry-build`."

**On "Approve & build now":**
1. Write `"build"` to `.autopilot/mode`
2. Write the Mortar session token to `masonry-state.json` (same node -e snippet above)
3. Immediately hand off to Mortar's Build Workflow:
   ```
   Act as the mortar agent defined in ~/.claude/agents/mortar.md.
   Task: Run the Dev Workflow — Build.
   Project directory: [current working directory]
   ```

**On "Revise the spec":**
Ask what to change, update `spec.md`, re-present from Step 4.

**On "Cancel":**
Delete `.autopilot/mode` and `.autopilot/compact-state.json` (if present). Tell the user the plan was discarded.
