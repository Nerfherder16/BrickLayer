---
name: bl-init
description: Bootstrap a new BrickLayer 2.0 project
---

# /bl-init — Bootstrap a New BrickLayer 2.0 Project

When invoked, create a new BrickLayer project from template, configure it, and print the startup command.

## Steps

### 1. Ask three questions (ask all at once, not one at a time)

```
I need three things to set up your BrickLayer project:

1. **System name** — What system or codebase are we analyzing? (used as the project folder name, lowercase-hyphenated)
2. **Primary goal** — Which mode best fits your intent?
   - `frontier` — unconstrained idea generation, "what could this become?"
   - `research` — stress-test an assumption against real evidence
   - `diagnose` — find and trace failures to root cause (default)
   - `audit` — check compliance against a standard
3. **Target path** — Where is the target codebase? (full path, or "none" if external/conceptual)
```

Wait for the user's answers before proceeding.

### 2. Copy the correct template

- If goal is `frontier` → copy from `C:/Users/trg16/Dev/Bricklayer2.0/template-frontier/`
- All other goals → copy from `C:/Users/trg16/Dev/Bricklayer2.0/template/`

Destination: `C:/Users/trg16/Dev/Bricklayer2.0/{project-name}/`

```bash
cp -r C:/Users/trg16/Dev/Bricklayer2.0/template{-frontier if frontier}/ C:/Users/trg16/Dev/Bricklayer2.0/{project-name}/
```

If the destination already exists, warn the user and stop — do not overwrite.

### 3. Create `project.json` in the project root

```json
{
  "display_name": "{human-readable name from user input}",
  "recall_src": "{target path from user, or empty string}",
  "stack": [],
  "target_live_url": ""
}
```

Write to: `C:/Users/trg16/Dev/Bricklayer2.0/{project-name}/project.json`

### 4. Print the startup instructions

```
Project created: C:/Users/trg16/Dev/Bricklayer2.0/{project-name}/

Next steps — complete these before starting a campaign:

1. Fill in project-brief.md — ground truth, invariants, what cannot be wrong
2. Drop supporting docs into docs/ — specs, prior research, spreadsheets
3. Write simulate.py — the simulation engine for your model (when ready)
4. Write constants.py — immutable system rules (when ready)

When the above are ready, generate the question bank:

   /bl-questions

Then start the campaign:

   /bl-run
```

Do NOT generate questions or touch simulate.py. The project is a blank scaffold —
the user must build context before research can begin.

## Notes

- For frontier projects, `simulate.py` is not used — evidence is gathered via web search and code analysis.
- `project.json` is BL 2.0 metadata; it does not exist in the original template and must be created fresh.
- Question generation happens inline in the current session — no separate session needed.
