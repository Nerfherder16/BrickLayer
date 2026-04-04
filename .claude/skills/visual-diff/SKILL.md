---
name: visual-diff
description: >-
  Generate a self-contained HTML artifact showing a visual before/after diff.
  Writes to ~/.agent/diagrams/. No external CDN. Includes decision log and re-entry context note.
---

# /visual-diff — Visual Before/After Comparison

**Invocation**: `/visual-diff <description of what changed>`

## What It Does

Generates a self-contained HTML file showing what changed between two states. Useful for
documenting refactors, design changes, configuration updates, or any before/after comparison.

## Output

Writes to: `~/.agent/diagrams/visual-diff-{timestamp}.html`

- `~/.agent/diagrams/` is created if it does not exist
- Timestamp format: `YYYYMMDD-HHmmss` (colons replaced with hyphens for filesystem safety)
- Print the full absolute path after generation so the user can open it

## Data Collection

Before generating the HTML, collect the actual diff data:

1. If the user provides file paths: read the files and capture before/after states
2. If a git diff is available: run `git diff HEAD` or `git diff <ref>` to get the real changes
3. If the user provides a description only (no file paths, no git diff): generate the HTML
   with `[FILL IN]` placeholders in the Before/After panels

When using git diff:
- Run `git log --oneline -3` to get recent commit context
- Run `git diff HEAD~1 HEAD --stat` to get a file summary
- Run `git diff HEAD~1 HEAD` for the full diff content

## HTML Structure (self-contained, no CDN)

All CSS and JavaScript must be inline — no external CDN links, no external scripts, no
external stylesheets. The file must be viewable offline by opening it in a browser.

### Required Sections (in order)

**1. Header**
- Title: "Visual Diff — {description}"
- Timestamp of generation
- Brief one-line description of what changed

**2. Side-by-Side Panels**
- Left panel labeled "Before"
- Right panel labeled "After"
- Both panels are scrollable if content is long
- Use a monospace font for code/config content
- Highlight differences:
  - Green background (`#d4edda`) for additions (lines/blocks only in After)
  - Red background (`#f8d7da`) for removals (lines/blocks only in Before)
  - Yellow background (`#fff3cd`) for modifications (lines present in both but changed)
  - Neutral/white background for unchanged content

**3. Change Summary**
- A bullet list above the panels (or between header and panels)
- High-level summary of what changed — not line-by-line, but semantic changes
- Example: "Replaced synchronous calls with async/await", "Renamed module X to Y"

**4. Decision Log**
- A table with columns: `Decision` | `Confidence` | `Reasoning`
- `Confidence` values: `HIGH` | `MEDIUM` | `LOW`
- List the key decisions made during this change and the confidence level for each
- Example row: "Used async/await over callbacks" | HIGH | "Consistent with rest of codebase"

**5. Re-entry Context Note** (critical section)
- A clearly-marked box or panel at the bottom of the page
- 3–5 sentences that would allow someone starting a fresh context window to understand:
  - What changed and why
  - What state the system is in now (after the change)
  - What should happen next (next task, next step, or "done")
- This section is the most important — it must be self-sufficient without reading the diff

## HTML Layout Guidelines

Use clean, professional styling inline:

```css
/* Suggested inline style skeleton */
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       margin: 0; padding: 20px; background: #f5f5f5; color: #333; }
.header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; }
.panels { display: flex; gap: 16px; margin: 20px 0; }
.panel { flex: 1; background: white; border: 1px solid #ddd; border-radius: 8px;
         padding: 16px; overflow-x: auto; }
.panel pre { margin: 0; white-space: pre-wrap; font-family: 'Courier New', monospace; }
.add { background: #d4edda; }
.remove { background: #f8d7da; }
.change { background: #fff3cd; }
.decision-table { width: 100%; border-collapse: collapse; }
.decision-table th, .decision-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
.confidence-HIGH { color: #27ae60; font-weight: bold; }
.confidence-MEDIUM { color: #f39c12; font-weight: bold; }
.confidence-LOW { color: #e74c3c; font-weight: bold; }
.reentry { background: #e8f4f8; border-left: 4px solid #3498db;
           padding: 16px; margin-top: 20px; border-radius: 4px; }
```

## Edge Cases

- If the user provides only a description (no file paths), generate the HTML from the
  description and any available git diff; use `[FILL IN]` placeholders where actual diff
  data is unavailable.
- Always create `~/.agent/diagrams/` if it does not exist before writing the file.
- If git is not available (not a git repo), skip git-based data collection and note
  "No git history available" in the change summary.
- If both before and after states are identical (no diff), still generate the file but
  note "No differences detected" in the change summary and leave panels empty.

## Example Invocations

```
/visual-diff Refactored auth module to use JWT
/visual-diff Updated Dockerfile to use multi-stage build
/visual-diff Renamed 3 constants in constants.py to match naming convention
```
