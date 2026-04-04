---
name: excel-format
description: Format an Excel spreadsheet — apply company template, standard header/row styling, number formats
---

# /excel-format

## Purpose
Apply professional formatting to an existing Excel workbook.
Handles header styling, alternating row colors, number formats, and borders.
Uses Python fallback for column widths (not supported by MCP).

## Trigger Conditions
- "format this spreadsheet"
- "apply our template"
- "make it look professional"
- "style this Excel file"
- "the formatting is a mess"
- "apply company colors"

## Agent
Invoke the `spreadsheet-wizard` agent from `~/.claude/agents/spreadsheet-wizard.md`.

## Workflow

### Phase 1: Read Current State
```
excel_describe_sheets → identify sheets and used ranges
excel_read_sheet with showStyle: true → understand current formatting
```
Note: existing colors, fonts, merges, number formats.

### Phase 2: Template Specification
If user provides template file:
- Read it with showStyle:true
- Extract: header color, alternating row colors, font specs, border styles, numFmt strings

If user provides hex colors or description:
- Map to the style objects for excel_format_range

If no template provided, use DEFAULT:
```
Header row:
  font: { bold: true, color: "#FFFFFF", size: 11 }
  fill: { type: "pattern", pattern: "solid", color: ["#1F3864"] }

Even data rows:
  fill: { type: "pattern", pattern: "solid", color: ["#F2F7FF"] }

Odd data rows:
  fill: { type: "pattern", pattern: "solid", color: ["#FFFFFF"] }

Totals/subtotals rows:
  font: { bold: true }
  border: [{ type: "top", style: "continuous", color: "#1F3864" }]

Currency columns: numFmt: "$#,##0.00"
Percentage columns: numFmt: "0.0%"
Integer/count columns: numFmt: "#,##0"
Date columns: numFmt: "mm/dd/yyyy"
```

### Phase 3: Apply Formatting (in this order)
1. Header row
2. Section header rows (if applicable)
3. Data rows (alternating, do even rows in a batch then odd rows)
4. Totals rows
5. Number formats (by column — identify by header label)

Note: styles 2D array must exactly match range size (rows x cols).

### Phase 4: Column Widths (Python required)
If column widths need setting (default Excel columns often too narrow):
```python
from openpyxl import load_workbook
wb = load_workbook("path")
ws = wb["SheetName"]
ws.column_dimensions['A'].width = 24   # Label column
# Data columns: 14 for currency, 10 for counts, 20 for text
wb.save("path")
```

### Phase 5: Verify
```
excel_read_sheet with showStyle: true → confirm styles applied
```
Spot-check header, one odd data row, one even data row, totals row.

### Phase 6: Screenshot
```
excel_screen_capture → describe what you see
```

## Output
Formatted .xlsx file.
Screenshot confirming the result.
Note: any formatting that required Python fallback (column widths, conditional formatting).

## Default Number Format Reference
| Column Type | numFmt |
|-------------|--------|
| USD currency | `$#,##0.00` |
| EUR currency | `€#,##0.00` |
| Percentage | `0.0%` |
| Integer count | `#,##0` |
| Date | `mm/dd/yyyy` |
| Month-Year | `mmm-yy` |
| Positive blue / Negative red | `[Blue]#,##0;[Red]-#,##0;"-"` |
| Thousands (display in K) | `#,##0,"K"` |
| Millions | `#,##0.0,,"M"` |
