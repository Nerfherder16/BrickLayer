---
name: bl-run
description: Start or resume a BrickLayer 2.0 campaign
---

# /bl-run — Start or Resume a BrickLayer Campaign

When invoked, detect the active project, check pending question state, and print the exact command to launch BrickLayer.

## Steps

### 1. Detect the current project

- Check if the current working directory (or any parent) contains both `questions.md` and `program.md` — if yes, that is the project.
- If not found in cwd, list subdirectories of `C:/Users/trg16/Dev/Bricklayer2.0/` that contain `questions.md` and ask:
  ```
  Which project?
  {numbered list of project dirs}
  ```

### 2. Check question bank quality

Read `questions.md`. First check if it contains template placeholder text — any of:
- `[parameter X]`
- `[volume / adoption / usage]`
- `[critical dependency]`
- `{PROJECT NAME}`

If placeholder text is found, the question bank was never generated. Run the question designer now:

```
Act as the question-designer-bl2 agent in .claude/agents/question-designer-bl2.md.
Project root: {project-root}/
Read project-brief.md, all files in docs/, constants.py, and simulate.py.
Generate the initial question bank in questions.md.
```

After generation, re-read questions.md and continue.

### 3. Count PENDING questions

Count lines/entries with status `PENDING`.

- If 0 PENDING:
  ```
  No PENDING questions in {project}/questions.md.

  Options:
  - Run the hypothesis generator to add a new wave
  - Check bl-status for current state
  ```
  Stop here.

- If >0 PENDING: continue.

### 4. Find the next question

Extract the first PENDING question: its ID and title. Show:
```
Project: {project-name}
Pending questions: {n}
Next: {Q-ID} — {question title} [{operational_mode if present}]
```

### 5. Detect frontier project

Check if `modes/frontier.md` exists in the project directory. If yes, this is a frontier project — note it in the output (frontier projects do not run simulations).

### 6. Determine start vs resume

- If `results.tsv` is empty or has only a header row → this is a **new campaign**
- If `results.tsv` has data rows → this is a **resume**

Use the appropriate `program.md` language in the command ("Begin" vs "Resume").

### 7. Print the launch command

Print both options every time:

```
Ready to {start/resume} — {n} questions pending.

── Single worker (VS Code terminal) ─────────────────────────────────────
cd C:/Users/trg16/Dev/Bricklayer2.0/{project-name}
git checkout -b {project-name}/$(date +%b%d | tr '[:upper:]' '[:lower:]')
claude --dangerously-skip-permissions "Act as the trowel agent in .claude/agents/trowel.md. Campaign directory: $(pwd). Run the BrickLayer 2.0 research loop from questions.md. If any simulate.py edit fails, run git reset --hard HEAD and retry. NEVER STOP."

── Parallel workers (~3x faster, opens Windows Terminal) ────────────────
cd C:/Users/trg16/Dev/Bricklayer2.0
./bl-parallel.ps1 -Project {project-name} -Workers 3

  Workers run in a separate WT window — you can minimize it.
  Check progress anytime: python bl/claim.py status {project-name}
```

If n > 10 PENDING, append:
```
Tip: {n} questions pending — parallel workers will finish this ~3x faster.
```

## Notes

- Masonry hooks auto-detect BL projects (via `program.md` + `questions.md`) and exit silently inside BL subprocesses — no env var needed.
- Each session should use a new dated git branch: `{project}/{monthday}` (e.g., `adbp/mar20`).
- Parallel workers open in Windows Terminal (separate from VS Code). Minimize WT and use `claim.py status` to monitor — do not run workers fully blind in the background.
- Do not run the claude command yourself — print it for the user to execute in their own terminal.
