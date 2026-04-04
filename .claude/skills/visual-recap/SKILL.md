---
name: visual-recap
description: >-
  Generate a self-contained HTML session summary. Reads git log, build.log, and masonry state.
  Includes action timeline and structured re-entry context note for next session.
---

# /visual-recap — Session Summary

**Invocation**: `/visual-recap`

## What It Does

Generates a self-contained HTML summary of what happened in the current session.
Designed as a re-entry artifact: someone opening a fresh context window can read
this file and know exactly where things stand.

## Output

Writes to: `~/.agent/diagrams/visual-recap-{timestamp}.html`

- `~/.agent/diagrams/` is created if it does not exist
- Timestamp format: `YYYYMMDD-HHmmss`
- Print the full absolute path after generation

## Data Sources

Read all of the following that exist (skip silently if a source is missing):

1. **Git log**: run `git log --oneline -10` for recent commits
2. **`.autopilot/build.log`**: full action timeline from the current build
3. **`.autopilot/progress.json`**: task statuses and test result counts
4. **Masonry session state**: read `masonry/masonry-state.json` or
   `masonry/session-summary.md` for campaign/session context

**Fallback rules:**
- If `build.log` does not exist, the action timeline falls back to git log only
- If no git repository is present, both git-dependent sections show
  "No git data available"
- If masonry state has no session summary, omit the campaign section entirely
  (do not show an error placeholder)

## HTML Structure (self-contained, no CDN)

All CSS and JavaScript must be inline. No external CDN, no external scripts.

### Required Sections (in order)

**1. Session Header**
- Date and time of recap generation
- Current git branch (run `git rev-parse --abbrev-ref HEAD` if available)
- Project name (from `progress.json` if available, otherwise from directory name)
- Build strategy (from `.autopilot/strategy` if it exists)

**2. Action Timeline**
- A vertical timeline of events in chronological order
- Sources (merge in timestamp order):
  - Commits from git log: show hash, message, approximate time
  - Tasks from build.log: show ISO-8601 timestamps, TASK_START, TASK_DONE events
  - HANDOFF and RESUME events from build.log (highlight these prominently)
- Each timeline entry shows: timestamp | type (commit / task start / task done / handoff) | description
- Use a visual timeline style (vertical line with event dots)

**3. Files Changed**
- A table of files modified during this session
- Source: run `git diff --name-status HEAD~N HEAD` where N is the number of commits
  shown in the session header, or `git status --short` for uncommitted changes
- Columns: File Path | Change Type (Created / Modified / Deleted / Renamed)
- If git is unavailable, omit this section

**4. Test Results**
- Passing and failing counts from the most recent test run recorded in `progress.json`
- Format: "N passing, M failing" with green/red color coding
- If `progress.json` has no test data, show "No test data recorded"

**5. Open Items**
- Any tasks with status `BLOCKED` or `PENDING` remaining in `progress.json`
- For each: task number, description, status, and block reason if logged in build.log
- If all tasks are DONE: "All tasks complete — no open items"

**6. Re-entry Context Note** (critical section)
- A clearly-marked box at the bottom — this is the most important section
- Three labeled subsections:

  **What was done:**
  - Bullet list of completed work (tasks that moved to DONE this session)
  - Include the commit hashes for major milestones

  **What's next:**
  - The first PENDING or IN_PROGRESS task with its description
  - Any context needed to start it (dependencies that just completed, etc.)
  - If nothing is pending: "Build complete — run `/verify` to validate"

  **What's blocked:**
  - Any BLOCKED tasks with their block reason
  - If nothing is blocked: "Nothing blocked"

  **Branch:**
  - Current branch name

## HTML Layout Guidelines

```css
/* Suggested inline style skeleton */
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       margin: 0; padding: 20px; background: #f5f5f5; color: #333; }
.header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
.section { background: white; border: 1px solid #ddd; border-radius: 8px;
           padding: 16px; margin-bottom: 16px; }
.section h2 { margin-top: 0; font-size: 16px; color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 8px; }
.timeline { list-style: none; padding: 0; margin: 0; position: relative; }
.timeline::before { content: ''; position: absolute; left: 12px; top: 0; bottom: 0;
                    width: 2px; background: #dee2e6; }
.timeline li { padding: 4px 4px 4px 32px; position: relative; margin-bottom: 4px; font-size: 13px; }
.timeline li::before { content: ''; position: absolute; left: 6px; top: 8px;
                       width: 12px; height: 12px; border-radius: 50%; background: #3498db; }
.timeline li.commit::before { background: #27ae60; }
.timeline li.handoff::before { background: #e74c3c; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
th { background: #ecf0f1; }
.pass { color: #27ae60; font-weight: bold; }
.fail { color: #e74c3c; font-weight: bold; }
.reentry { background: #e8f4f8; border-left: 4px solid #3498db;
           padding: 16px; border-radius: 4px; }
.reentry h2 { color: #2980b9; margin-top: 0; }
.reentry h3 { color: #34495e; font-size: 14px; margin: 12px 0 6px 0; }
.reentry ul { margin: 0; padding-left: 20px; }
.reentry li { margin-bottom: 4px; font-size: 13px; }
.blocked { color: #e74c3c; }
```

## Edge Cases

- If `build.log` does not exist, the action timeline uses git log only and notes
  "build.log not found — showing git history only."
- If no git repository is present, both the timeline (git commits) and files-changed
  sections show "No git data available" and are otherwise empty.
- If `masonry-state.json` has no session summary field, omit the campaign section
  entirely rather than showing an empty or broken placeholder.
- If `progress.json` does not exist, omit the test results section and mark all
  open items as "No progress data available."
- If the build is in COMPLETE state (all tasks DONE), the re-entry note should say
  "Build complete" in the "What's next" subsection rather than listing a next task.

## Example Invocations

```
/visual-recap
```

This skill takes no arguments — it always reads from the current working directory's
`.autopilot/` state and the current git repository.
