---
name: visual-plan
description: >-
  Generate a self-contained HTML task dependency graph from .autopilot/spec.md.
  Color-coded by status. No CDN. Includes phase markers and re-entry context note.
---

# /visual-plan — Visual Task Dependency Graph

**Invocations**:
- `/visual-plan` — reads the current `.autopilot/spec.md` and `progress.json`
- `/visual-plan <description>` — generates a graph from the provided description

## What It Does

Generates a self-contained HTML visualization of the current build plan as a dependency
graph. Each task is a node, dependencies are arrows, and tasks are color-coded by status.

## Output

Writes to: `~/.agent/diagrams/visual-plan-{timestamp}.html`

- `~/.agent/diagrams/` is created if it does not exist
- Timestamp format: `YYYYMMDD-HHmmss`
- Print the full absolute path after generation

## Data Sources

**When invoked without arguments (spec mode):**

1. Read `.autopilot/spec.md` — extract all tasks:
   - Task number and description
   - `[depends:N,M]` annotations for dependency edges
   - `[phase_end]` annotations for phase boundary markers
2. Read `.autopilot/progress.json` (optional) — get task statuses:
   - `PENDING`, `IN_PROGRESS`, `DONE`, `BLOCKED`
   - If progress.json does not exist, treat all tasks as PENDING

**When invoked with a description:**

Parse the description to extract a task list. Generate simple sequential edges unless
the description explicitly mentions dependencies. Treat all tasks as PENDING.

**Fallback:**

If `.autopilot/spec.md` does not exist when invoked without arguments, generate a simple
text summary of any description provided rather than an empty graph.

## Parsing Dependencies from spec.md

Scan each task line for the pattern `[depends:N]` or `[depends:N,M,...]`:

```
Task 5 — Do something [depends:3,4]
```

This means task 5 has edges from task 3 and task 4.

Tasks with no `[depends:...]` annotation are independent — connect them to the phase
start node (a small diamond node at the start of each phase), not left floating.

**Cycle detection:** If A depends on B and B depends on A, render both nodes with an
orange dashed border and add a warning label: "⚠ Circular dependency detected."
Do not silently collapse cycles.

## HTML Structure (self-contained, no CDN)

All CSS must be inline. Use SVG or HTML+CSS for the graph — no external charting
libraries (no D3, no Mermaid CDN, no Cytoscape CDN).

### Required Sections (in order)

**1. Header**
- Title: "Build Plan — {project name from spec or 'Current Build'}"
- Generation timestamp
- Summary: "N tasks total, X done, Y in progress, Z pending, W blocked"

**2. Dependency Graph**

Render as an SVG embedded directly in the HTML:

- **Task nodes**: rounded rectangles with the task number and a short label
  - Gray (`#6c757d`) = PENDING
  - Yellow (`#ffc107`) = IN_PROGRESS
  - Green (`#28a745`) = DONE
  - Red (`#dc3545`) = BLOCKED
- **Arrows**: directed edges showing dependencies (A → B means "B depends on A" / "A must complete before B")
  - Use SVG `<line>` or `<path>` elements with arrowhead markers
  - Arrows point FROM prerequisite TO dependent task
- **Phase markers**: horizontal dashed lines or labeled separators grouping tasks by phase
  - Label each phase region: "Phase 1", "Phase 2", etc.
  - Place the separator at every `phase_end` annotation in the spec
- **Cycle warning**: orange dashed border on any node involved in a circular dependency

**Layout approach (when no layout library is available):**
- Arrange tasks in rows by phase (each phase is a row or block)
- Within a phase, spread tasks horizontally
- For cross-phase dependencies, draw long arrows between rows
- Keep it readable — prefer spacing over compactness

**3. Legend**
- Compact color legend: Gray = Pending, Yellow = In Progress, Green = Done, Red = Blocked
- Arrow notation: "A → B means B depends on A"

**4. Task List (fallback table)**
- A simple HTML table below the graph listing all tasks with: #, Description, Status, Depends On
- This provides a readable fallback if the SVG renders poorly in the user's browser

**5. Re-entry Context Note**
- A clearly-marked box at the bottom
- Content: "Build is at task N of M. Next unblocked task: {task number and description}.
  Phase progress: {X of Y phases complete}."
- If all tasks are DONE: "All N tasks complete."
- If any tasks are BLOCKED: list them and their block reason if available

## HTML Layout Guidelines

```css
/* Suggested inline style skeleton */
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       margin: 0; padding: 20px; background: #f5f5f5; color: #333; }
.header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
svg { background: white; border: 1px solid #ddd; border-radius: 8px; display: block; width: 100%; }
.legend { display: flex; gap: 16px; margin: 12px 0; font-size: 14px; }
.legend-item { display: flex; align-items: center; gap: 6px; }
.legend-swatch { width: 16px; height: 16px; border-radius: 3px; }
table { width: 100%; border-collapse: collapse; background: white; }
th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
th { background: #ecf0f1; }
.reentry { background: #e8f4f8; border-left: 4px solid #3498db;
           padding: 16px; margin-top: 20px; border-radius: 4px; }
```

## Edge Cases

- If `.autopilot/spec.md` does not exist and no description is given, output a text
  message: "No spec found. Run `/plan` first or invoke `/visual-plan <description>`."
- If `progress.json` does not exist, treat all tasks as PENDING (gray).
- If dependency cycles exist, render both nodes with a warning marker — do not skip them.
- If there are more than 30 tasks, increase the SVG canvas height to avoid overlap.
- Tasks with `[depends:N]` referencing a non-existent task number should show a dashed
  border and note "dependency not found" in the table row.

## Example Invocations

```
/visual-plan
/visual-plan Auth service: task 1 setup DB, task 2 login endpoint [depends:1], task 3 logout [depends:2]
/visual-plan Phase 1: scaffold; Phase 2: implement; Phase 3: test
```
