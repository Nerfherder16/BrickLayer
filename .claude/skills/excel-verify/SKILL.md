---
name: excel-verify
description: Audit an Excel workbook — verify formulas, check computed values, inspect formatting, report findings
---

# /excel-verify

## Purpose
Non-destructive audit of an existing Excel workbook. Reads everything,
reports all findings, proposes fixes but does not apply them unless confirmed.

## Trigger Conditions
- "check my spreadsheet"
- "verify formulas"
- "audit this Excel file"
- "are the numbers right?"
- "something looks wrong in column D"
- "formula errors"

## Agent
Invoke the `spreadsheet-wizard` agent from `~/.claude/agents/spreadsheet-wizard.md`.

## Workflow

### Phase 1: Workbook Inventory
```
excel_describe_sheets → list all sheets, dimensions, table names
```
Report: "Workbook has N sheets: [names]. Primary data appears to be on [sheet]."

### Phase 2: Formula Audit
For each sheet:
```
excel_read_sheet with showFormula: true
```
Catalog every formula cell. Build a list: `[CellAddr, FormulaText, ComputedValue]`

### Phase 3: Error Detection
```
excel_read_sheet with showFormula: false
```
Flag any cell showing: #REF!, #NAME?, #VALUE!, #DIV/0!, #N/A, #NULL!, #NUM!, #SPILL!

### Phase 4: Value Cross-Check
For each SUM/SUMIF/SUMIFS formula:
- Read the source range values
- Compute expected result independently
- Flag if deviation > 0.01

For each XLOOKUP/VLOOKUP:
- Read 3 test lookup values (match, non-match, edge case)
- Confirm each returns expected result

### Phase 5: Formatting Audit
```
excel_read_sheet with showStyle: true
```
Check:
- Header row has bold + fill color
- Number columns have numFmt (not just default)
- Date columns have date numFmt
- Percentage columns have "%" numFmt
- No merged cells in data ranges (flag as warning)

### Phase 6: Visual Inspection
```
excel_screen_capture → header + first 20 rows
```
Report: describe what you see.

### Phase 7: Report

```markdown
## Verification Report — [filename]

### Summary
| Check | Status |
|-------|--------|
| Total formula cells | N |
| Passing | N |
| Errors | N |
| Warnings | N |
| Formatting issues | N |

### Errors (Must Fix)
- [Cell] [Formula] → [Error type]: [Diagnosis and recommended fix]

### Warnings (Should Fix)
- [Cell]: [Issue] — [Recommendation]

### Suggestions (Nice to Have)
- [Observation] — [Suggestion]

### Verdict
PASS / NEEDS FIXES / CRITICAL ERRORS
```

### Phase 8: Propose Fixes
"Would you like me to apply these fixes?" — wait for confirmation before writing anything.

## Output
Verification report with cell-level findings.
Screenshot of current state.
Optional: apply fixes if user confirms.
