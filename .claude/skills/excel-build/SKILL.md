---
name: excel-build
description: Build an Excel workbook from scratch — P&L, budget, dashboard, data model, or any structured spreadsheet
---

# /excel-build

## Purpose
Autonomously build a production-quality Excel workbook. Handles structure,
formulas, formatting, verification, and visual QA in one pass.

## Trigger Conditions
- "build me a spreadsheet"
- "create an Excel file"
- "make a P&L / budget / model / tracker"
- "I need an Excel template"
- "build a dashboard in Excel"

## Agent
Invoke the `spreadsheet-wizard` agent from `~/.claude/agents/spreadsheet-wizard.md`.

## Workflow

### Phase 1: Requirements Clarification
Before any tool calls, confirm:
- File path (where to save the .xlsx file)
- Workbook type (P&L, budget, tracker, dashboard, etc.)
- Sheet structure (one sheet or multi-sheet)
- Data: user provides it, or the agent generates sample/template data
- Formatting preference (default template or specific company template)

If the user provides a partial spec (e.g., "build me a P&L"), infer reasonable
defaults and state them before proceeding.

### Phase 2: File Creation
If the file doesn't exist:
```python
from openpyxl import Workbook
wb = Workbook()
wb.save("absolute/path/to/file.xlsx")
```
Then proceed with MCP tools.

### Phase 3: Structure
Write headers and row labels first. No formulas yet.
Confirm structure by reading back before writing formulas.

### Phase 4: Data and Formulas
Write hardcoded values first. Then write formula rows.
Follow all formula rules: absolute refs, XLOOKUP over VLOOKUP, IFERROR wrapping,
US comma syntax.

### Phase 5: Verification
- Read back with showFormula:true — confirm formula text
- Read back with showFormula:false — confirm computed values
- Cross-check aggregations against expected results

### Phase 6: Formatting
Apply standard template unless user specified otherwise:
- Header: #1F3864 fill, white bold 11pt
- Alternating rows: #FFFFFF / #F2F7FF
- Totals: bold + top border
- Number formats: currency "$#,##0.00", percent "0.0%"

### Phase 7: Visual QA
Take screenshot. Describe what you see (don't just say "screenshot taken").

### Phase 8: Delivery
Report: file path, sheets created, formula count, any Python-fallback features used,
any capabilities that required Python vs MCP.

## Standard Formula Reference
See the spreadsheet-wizard agent for full formula library, verification protocol,
Python fallback guide, and edge case handling.

## Output
Fully formatted, verified .xlsx file at the specified path.
Screenshot evidence of the final state.
