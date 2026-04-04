---
name: bl-status
description: Show current state and progress of a BrickLayer 2.0 project
---

# /bl-status — BrickLayer Project Status

When invoked, read the project state and report a structured summary.

## Steps

### 1. Detect the current project

Same detection logic as `bl-run`:
- Check if cwd (or any parent) contains `questions.md` and `program.md` → use it.
- Otherwise, list subdirectories of `C:/Users/trg16/Dev/Bricklayer2.0/` that contain `questions.md` and ask the user to pick one.

### 2. Parse `questions.md`

Count occurrences of each status value:

| Status | Description |
|--------|-------------|
| `PENDING` | Not yet investigated |
| `DONE` | Completed (generic) |
| `DIAGNOSIS_COMPLETE` | Root cause identified, fix spec written |
| `FAILURE` | Failure confirmed, root cause not yet isolated |
| `WARNING` | Degraded behavior, recoverable |
| `HEALTHY` | No issue found |
| `INCONCLUSIVE` | Could not determine without more data |
| `FIXED` | Fix was deployed and verified |

Also collect: the first PENDING question (ID + title + operational_mode if tagged), and all questions with status `FAILURE`, `WARNING`, or `DIAGNOSIS_COMPLETE` (these are open items needing attention).

Collect the unique `operational_mode` values seen in PENDING questions (e.g., `diagnose`, `frontier`, `research`).

### 3. Read `results.tsv`

Read the last 5 data rows. Each row is a completed run. Extract: question ID, verdict, timestamp (if present). Format as a compact list.

If `results.tsv` doesn't exist or is empty, note "No results yet."

### 4. Check for synthesis

If `findings/synthesis.md` exists, read the first 3 non-empty lines and include them as a "Synthesis preview."

### 5. Report

Print in this format:

```
Project: {project-name}
Mode(s): {comma-separated unique operational_modes of PENDING questions, or "none pending"}

Progress:
  PENDING:             {n}
  DONE/FIXED/HEALTHY:  {n}  (completed without issues)
  FAILURE:             {n}  (needs attention)
  WARNING:             {n}  (needs attention)
  DIAGNOSIS_COMPLETE:  {n}  (ready for fix)
  INCONCLUSIVE:        {n}

Next question: {Q-ID} — {title} [{mode}]
  (or "None — all questions resolved")

Open items:
  {Q-ID}: {title} [{status}]
  {Q-ID}: {title} [{status}]
  (or "None" if no FAILURE/WARNING/DIAGNOSIS_COMPLETE)

Recent results (last 5):
  {Q-ID}: {verdict} — {timestamp or "no timestamp"}
  ...

{if synthesis.md exists:}
Synthesis (preview):
  {first 3 lines of synthesis.md}
```

### 6. Suggest next action

Based on state:

- PENDING > 0 → "Run `bl-run` to continue the campaign."
- FAILURE > 0 and no PENDING → "All questions answered. FAILURE findings need investigation. Run `bl-run` or generate a new wave targeting these findings."
- DIAGNOSIS_COMPLETE > 0 → "Fix-ready findings exist. Switch to Fix mode or deploy fixes manually."
- All resolved → "Campaign complete. Run the synthesizer, then `python analyze.py` to generate the report."

## Notes

- Do not modify any project files — this is a read-only status check.
- If `questions.md` is malformed or uses a non-standard format, report what was found and ask the user to clarify the status field convention used.
