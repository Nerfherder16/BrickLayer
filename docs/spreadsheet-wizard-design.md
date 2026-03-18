# Spreadsheet-Wizard Agent — Design Document

**Date:** 2026-03-18
**Status:** Design complete — agent file at `~/.claude/agents/spreadsheet-wizard.md`

---

## Executive Summary

The spreadsheet-wizard is a domain-specialist Claude agent that autonomously builds,
edits, formats, verifies, and delivers production-quality Excel workbooks. It operates
primarily through 7 MCP excel tools, falling back to openpyxl/pandas via Bash when
those tools hit structural limits. The agent follows a strict Plan → Write → Verify →
Format → Visual QA workflow and never marks work done without evidence.

---

## 1. Formula Knowledge Required

### Coverage Map

A world-class spreadsheet agent needs mastery across 10 formula categories. These are
ordered by frequency of use in real-world business spreadsheets:

| Rank | Category | Key Formulas | Why |
|------|----------|-------------|-----|
| 1 | Aggregation (Conditional) | SUMIFS, COUNTIFS, AVERAGEIFS, SUMPRODUCT | Every analytical model uses these |
| 2 | Lookup & Reference | XLOOKUP, INDEX/MATCH, VLOOKUP (legacy) | Data joining is universal |
| 3 | Logical | IF, IFS, IFERROR, IFNA, AND, OR | Error handling + branching everywhere |
| 4 | Financial | NPV, IRR, PMT, FV, PV, XIRR | P&L, DCF, loan models |
| 5 | Dynamic Array | FILTER, SORT, UNIQUE, SEQUENCE, VSTACK | Modern Excel — dashboards, reports |
| 6 | Text | TEXT, TEXTJOIN, SUBSTITUTE, LEFT/MID/RIGHT | Data cleaning, display formatting |
| 7 | Date & Time | EOMONTH, EDATE, NETWORKDAYS, DATEDIF | Financial calendars, aging reports |
| 8 | Statistical | PERCENTILE, STDEV, CORREL, FORECAST.ETS | Analytical dashboards |
| 9 | Table Structured Refs | Table[Column], [@Field] syntax | Self-documenting, auto-expanding |
| 10 | Advanced Patterns | Running totals, cumulative %, YoY growth | Analyst staples |

### Most Complex Formula Patterns

These are the patterns that separate a basic agent from a world-class one:

**Pattern 1: Cascading error-handled lookup**
```excel
=IFERROR(
  XLOOKUP([@SKU], Products[SKU], Products[Price]),
  IFERROR(
    XLOOKUP([@SKU], LegacyProducts[OldSKU], LegacyProducts[Price]),
    0
  )
)
```
Uses: Try primary table, fall back to legacy table, default to 0. Prevents #N/A
bubbling through a model.

**Pattern 2: Dynamic filtered aggregation**
```excel
=SUMPRODUCT(
  (Sales[Region]=DashboardFilter!$B$2) *
  (YEAR(Sales[Date])=DashboardFilter!$B$3) *
  Sales[Revenue]
)
```
Uses: Multi-condition sum without SUMIFS, works in any Excel version, supports
cell-reference criteria.

**Pattern 3: Running balance with gap protection**
```excel
=IF(
  ISBLANK(C2),
  "",
  SUM($C$2:C2)
)
```
Uses: Cumulative sum that skips blank rows cleanly.

**Pattern 4: Fiscal quarter derivation**
```excel
=CHOOSE(MONTH(A2), 1,1,1,2,2,2,3,3,3,4,4,4)
```
Uses: Convert any date to Q1-Q4. Faster and clearer than nested IFs.

**Pattern 5: Non-volatile dynamic range (replaces OFFSET)**
```excel
=XLOOKUP(MAX(A:A), A:A, B:B)   # Last value in a growing list
=INDEX(B:B, MATCH(MAX(A:A), A:A, 0))   # Same, legacy
```
Uses: Avoids volatile OFFSET while getting dynamic last-value behavior.

**Pattern 6: Tiered pricing / tax brackets**
```excel
=VLOOKUP(Income, TaxTable, 2, TRUE)   # TRUE = approximate match (must sort ascending)
```
The only legitimate use of `TRUE` match mode. The table must be sorted. Use for
commission tiers, tax brackets, discount schedules.

**Pattern 7: Two-dimensional lookup**
```excel
=INDEX(DataMatrix, MATCH(RowKey, RowHeaders, 0), MATCH(ColKey, ColHeaders, 0))
```
Most flexible matrix lookup. Works where XLOOKUP can only return 1D.

**Pattern 8: Array formula for unique count (pre-365)**
```excel
=SUMPRODUCT(1/COUNTIF(A2:A100, A2:A100))
```
Counts distinct values without UNIQUE(). The COUNTIF returns a frequency for
each value; 1/frequency summed = count of unique groups.

---

## 2. Verification Approach

### Layer 1: Structural Verification

Run immediately after any write operation:

```
excel_describe_sheets
  → Confirm: sheet name exists
  → Confirm: used range dimensions match expectation
  → Confirm: no unexpected sheets were created or deleted

excel_read_sheet (first 20 rows, no flags)
  → Confirm: data is in correct cells
  → Confirm: row/column count matches input
  → Confirm: no data spilled into wrong cells
```

### Layer 2: Formula Text Verification

For every cell containing a formula:

```
excel_read_sheet with showFormula: true
  → Compare returned formula text to intended formula string
  → Check: absolute/relative references are correct ($ signs present where needed)
  → Check: range bounds are correct (SUM(B2:B13) not SUM(B2:B12))
  → Check: function name is spelled correctly (no #NAME? waiting to happen)
  → Check: no extra spaces, stray characters
```

This catches: wrong range bounds, missing $ signs that will break when copied,
function name typos that won't error until a specific value triggers them.

### Layer 3: Computed Value Verification

```
excel_read_sheet with showFormula: false
  → For aggregations (SUM, COUNT, AVERAGE):
      Read the source range values
      Compute the expected result independently
      Compare — flag if difference > 0.01 (floating point tolerance)

  → For lookups (XLOOKUP, VLOOKUP):
      Read 3 test cases: one match, one non-match, one edge case
      Confirm: match returns correct value
      Confirm: non-match returns the specified fallback (not #N/A)
      Confirm: edge cases (blank, zero, max value) don't produce errors

  → For financial formulas (NPV, IRR):
      Use a known reference: e.g., NPV at 10% of {100, 100, 100} = 248.69
      If numbers deviate from hand-calculation by >0.5%, flag for review

  → For date formulas:
      Test boundary months: EOMONTH on Dec 31 returns Jan 31 of next year
      Test leap years: Feb 28 vs Feb 29
```

### Layer 4: Formatting Verification

```
excel_read_sheet with showStyle: true
  → Header row: confirm bold: true, fill color matches spec, font color white/dark
  → Data rows 2 and 3: confirm alternating fill colors differ
  → Totals row: confirm bold: true, border present at top
  → Number cells: confirm numFmt string contains "$", "%", or "," as appropriate
  → Confirm: no accidental merges in data rows (merges destroy sort/filter)
```

### Layer 5: Visual QA

```
excel_screen_capture of each major section:
  → Header + first 10 rows: column labels readable, widths not truncating data
  → Totals section: subtotals visible, formatting distinct from data rows
  → Full dashboard view (if applicable)

Report findings: describe what the screenshot shows — don't just say "screenshot taken"
  Example: "Screenshot shows a 13-column P&L with dark blue header, monthly columns Jan-Dec
            plus a Total column. Revenue $12.4M, Gross Profit $5.1M (41.2%), EBITDA $2.8M.
            All numbers formatted with $ and comma separator. No obvious truncation."
```

### Layer 6: Named Range and Conditional Formatting (Python audit)

These are invisible to MCP tools. If the workbook should have:
- Named ranges: verify with Python `wb.defined_names`
- Conditional formatting: verify with Python `ws.conditional_formatting`
- Data validation: verify with Python `ws.data_validations`

```python
wb = load_workbook(path)
print("Named ranges:", list(wb.defined_names.keys()))
ws = wb.active
print("CF rules:", len(ws.conditional_formatting._cf_rules))
print("DV:", [str(dv) for dv in ws.data_validations.dataValidation])
```

---

## 3. Python Fallback Decision Tree

```
Task requested
    │
    ├── Need conditional formatting? ─────────────────────────→ Python (openpyxl)
    ├── Need data validation? ────────────────────────────────→ Python (openpyxl)
    ├── Need charts? ─────────────────────────────────────────→ Python (openpyxl.chart)
    ├── Need named ranges? ───────────────────────────────────→ Python (openpyxl)
    ├── Need freeze panes? ───────────────────────────────────→ Python (openpyxl)
    ├── Need column/row width? ───────────────────────────────→ Python (openpyxl)
    ├── Need row/col hide or group? ──────────────────────────→ Python (openpyxl)
    ├── Need pivot tables? ───────────────────────────────────→ Python (xlwings or pandas groupby)
    ├── Need VBA macros? ─────────────────────────────────────→ Python (xlwings)
    ├── Bulk import >200 rows from CSV/database? ─────────────→ Python (pandas)
    ├── Need to unmerge cells? ───────────────────────────────→ Python (openpyxl)
    ├── Sheet is protected? ──────────────────────────────────→ Python (unprotect first)
    └── Everything else → MCP tools
```

### Hybrid Pattern (Best for Complex Workbooks)

For workbooks that need both bulk data AND MCP-supported formatting:

1. Python phase: import bulk data, create tables, add named ranges, conditional
   formatting, data validation, set column widths, freeze panes, save file
2. MCP phase: verify structure, add/edit formulas incrementally, apply
   remaining formatting, visual QA

Python handles the structural work; MCP handles the interactive editing and
verification loop.

### When NOT to Use Python

- When the task is 10 cells or fewer (MCP call is faster than starting a Python script)
- When you need to read back and verify immediately (MCP gives parsed JSON, Python requires
  save+reload)
- When the file is locked by Excel (MCP handles this more gracefully)

---

## 4. Workflow Design

### A. "Build me a P&L from scratch"

```
Phase 1: Requirements Clarification (before any tool call)
  Questions to ask/infer:
  - Company name, fiscal year (calendar or custom)
  - Granularity: monthly, quarterly, or annual columns
  - Revenue lines (products, services, segments)
  - COGS items
  - Operating expense categories
  - Below-the-line items (D&A, interest, taxes)
  - Output: summary only, full detail, or both sheets

Phase 2: File Creation
  If file doesn't exist: use Bash to touch it, or write first cell to create it
  excel_write_to_sheet (newSheet: true, sheetName: "P&L")

Phase 3: Header and Structure
  Write row 1: ["", "Jan", "Feb", ..., "Dec", "FY Total"]
  Write labels in column A:
    - "Revenue" section header
    - Each revenue line item
    - "Total Revenue" subtotal
    - "Cost of Revenue" section header
    - Each COGS item
    - "Total COGS" subtotal
    - "GROSS PROFIT" key metric
    - "Gross Margin %" key metric
    - "Operating Expenses" section header
    - Each OpEx line
    - "Total OpEx" subtotal
    - "EBITDA" key metric
    - "D&A"
    - "EBIT" key metric
    - "Interest Expense"
    - "EBT" key metric
    - "Income Tax"
    - "NET INCOME" key metric
    - "Net Margin %" key metric

Phase 4: Write Input Data
  Write hardcoded assumption values first (revenue, costs)
  Leave formula rows blank

Phase 5: Write Formulas
  Total Revenue: =SUM(B3:B5)   (adjust range to actual revenue rows)
  Total COGS: =SUM(B8:B9)
  Gross Profit: =B6-B10        (Total Revenue - Total COGS)
  Gross Margin: =B11/B6        (format as %)
  Total OpEx: =SUM(B14:B17)
  EBITDA: =B11-B18             (Gross Profit - Total OpEx)
  EBIT: =B19-B20               (EBITDA - D&A)
  EBT: =B21-B22                (EBIT - Interest)
  Net Income: =B23-B24         (EBT - Tax)
  Net Margin: =B25/B6          (format as %)
  FY Total column: =SUM(B6:M6) for each row

Phase 6: Verify (see Verification Protocol above)

Phase 7: Format
  Header row: dark blue fill, white bold font
  Section headers: medium blue fill, dark blue bold font
  Key metric rows (Gross Profit, EBITDA, Net Income): bold, top border
  Percentage rows: "0.0%" numFmt
  Currency rows: "$#,##0" numFmt
  Alternating data rows: white / very light blue

Phase 8: Visual QA
  Screenshot entire model
  Confirm: all numbers visible (not ######), structure clear, metrics bold and distinct
```

### B. "Add a dashboard sheet to this existing workbook"

```
Phase 1: Workbook Audit
  excel_describe_sheets → inventory all sheets and their sizes
  For each data sheet:
    excel_read_sheet (first 50 rows) → understand column structure
    Note: column names, data types, row counts, any existing tables

Phase 2: Source Analysis
  Identify: which sheet has the primary data (sales, transactions, etc.)
  Identify: existing tables (structured references are better than cell refs)
  Note: any cross-sheet linking already present (don't break it)

Phase 3: Safety Backup
  excel_copy_sheet for each source sheet (srcSheet → srcSheet_backup)

Phase 4: Define KPIs
  Based on data structure, propose 4-6 KPIs:
  - If sales data: Total Revenue, Unit Count, Avg Deal Size, Win Rate, Top Region
  - If financial: Total Revenue, Gross Profit, EBITDA, YTD Budget vs Actual
  - If operational: Volume processed, Error rate, SLA compliance, Throughput

Phase 5: Dashboard Scaffold
  excel_write_to_sheet (newSheet: true, sheetName: "Dashboard")
  Layout rows:
    Row 1: Dashboard title
    Row 2: blank (breathing room)
    Rows 3-6: KPI hero numbers (one per pair of rows: label + number)
    Row 7: blank
    Rows 8+: summary table or chart placeholder
    Bottom: "Data as of: " + formula referencing source data update date

Phase 6: Write KPI Formulas
  All formulas reference source sheets/tables:
  =SUM(Sales[Revenue])
  =COUNTIFS(Sales[Status],"Won",Sales[Year],2025)
  =AVERAGEIF(Sales[Rep],DashFilter,$B$4,Sales[Revenue])

Phase 7: Format KPI Display
  Metric labels: 10pt, uppercase, gray (#666666)
  Metric values: 32pt, bold, accent color (#1F3864 or custom)
  Section borders: light bottom border separating sections

Phase 8: Verify + Screenshot
  Read back all formulas with showFormula: true
  Cross-check totals against source data
  Screenshot full dashboard
```

### C. "Fix the formula errors in column D"

```
Phase 1: Full Audit
  excel_read_sheet with showFormula: true for the full sheet (or column D range)
  Identify every cell showing an error value in the formula text or computed value

Phase 2: Error Classification
  Map each error to its cause:
  - #REF! → a reference is pointing to a deleted row/column or out-of-bounds
  - #NAME? → function name typo, or named range that no longer exists
  - #VALUE! → a non-numeric value (text, date, blank) where a number is required
  - #DIV/0! → division by zero or blank — wrap with IFERROR or add IF guard
  - #N/A → XLOOKUP/VLOOKUP couldn't find the lookup value
  - #NULL! → incorrect use of intersection operator (space instead of :)
  - #NUM! → invalid numeric argument (e.g., SQRT of negative)
  - #SPILL! → dynamic array formula's spill zone has non-empty cells

Phase 3: Root Cause Diagnosis (per error)
  #REF!: read the broken formula → trace which reference is invalid → check if rows/cols were deleted
  #N/A: read the lookup value in the source row → read 5 values in the lookup table →
        check type mismatch (text vs number) or leading/trailing spaces
  #VALUE!: read the referenced cell → check if it contains text or a non-numeric

Phase 4: Fixes
  Write the corrected formula for each broken cell
  Strategy per error type:
  - #REF!: rebuild the reference from scratch using current cell addresses
  - #NAME?: fix the function name spelling, or create the missing named range
  - #VALUE!: wrap input with VALUE() or TEXT() to coerce the type
  - #DIV/0!: =IFERROR(numerator/denominator, 0) or =IF(denominator=0,"",numerator/denominator)
  - #N/A: =IFERROR(XLOOKUP(...),"Not found") — don't just suppress, use meaningful fallback
  - #SPILL!: clear the cells in the spill zone, or move the formula

Phase 5: Verification
  Re-read all previously-errored cells with showFormula: false
  Confirm: all return values, no error strings remain
  Spot-check 3 non-error rows to confirm existing logic wasn't accidentally changed
  Screenshot before/after comparison range
```

### D. "Format this data to match our company template"

```
Phase 1: Read Current State
  excel_read_sheet with showStyle: true → understand what formatting already exists
  Note: header row, data row patterns, any existing number formats
  Note: if merged cells exist (these need special handling)

Phase 2: Get Template Requirements
  If template is provided as reference file:
    excel_read_sheet with showStyle: true on template
    Extract: exact hex colors, font sizes, border styles, number formats

  If no template provided, ask for:
    - Header color (or use default dark blue #1F3864)
    - Accent/alternating row color (or use default light blue #F2F7FF)
    - Number format preference ($, €, £; decimal places; thousands separator)
    - Font preference (or default to Calibri 11pt)

Phase 3: Apply Formatting (in this exact order)
  1. Header row:
     excel_format_range (row 1 or identified header row)
     font: bold, white, 11pt
     fill: solid, #1F3864

  2. Section header rows (if applicable):
     excel_format_range
     font: bold, dark blue #1F3864, 10pt
     fill: solid, #D6E4F7

  3. Data rows (alternating pattern):
     Odd rows: fill solid white #FFFFFF
     Even rows: fill solid #F2F7FF
     (write as a loop: for each even row, call excel_format_range)
     Caveat: this is expensive for large sheets — use Python for >50 rows

  4. Totals/subtotals rows:
     excel_format_range
     font: bold
     border: top, continuous, #1F3864

  5. Number formats:
     Identify columns by header (Revenue, Amount, Cost → currency)
     excel_format_range with numFmt: "$#,##0.00"
     Identify percentage columns (Margin %, Growth %) → numFmt: "0.0%"
     Identify count columns (Units, Count) → numFmt: "#,##0"
     Identify date columns → numFmt: "mm/dd/yyyy"

Phase 4: Column Widths (Python required)
  ws.column_dimensions['A'].width = 24
  For data columns, set based on content: 12-16 for numbers, 20+ for text

Phase 5: Verify
  excel_read_sheet with showStyle: true → confirm styles applied as expected
  Screenshot for visual confirmation + deliver to user
```

---

## 5. System Prompt Engineering

### Core Identity Statement
```
You are a world-class Excel automation specialist with 20 years of financial modeling
experience. You build production-quality spreadsheets that are correct, robust, and
visually professional. You never guess — you verify. You never mark work done until
you have read back what you wrote and confirmed it is correct.
```

### Formula Discipline Rules (bake into system prompt)

```
FORMULA RULES:
1. All formulas start with = in the values array
2. Use absolute references ($A$1) for any cell referenced from multiple places (rates, assumptions)
3. Use TABLE STRUCTURED REFERENCES (Table[Column]) whenever data is in an Excel Table
4. Prefer XLOOKUP over VLOOKUP — VLOOKUP's column index breaks when columns are inserted
5. Always wrap XLOOKUP/VLOOKUP with IFERROR or IFNA — never leave a raw #N/A
6. Never use volatile functions (NOW, RAND, INDIRECT, OFFSET) unless specifically required
7. Use regional US syntax (comma separators): =IF(A1>0, "Yes", "No") NOT semicolons
8. Use IFERROR for trapping all errors; use IFNA for trapping #N/A only (safer — doesn't hide real errors)
9. For financial P&L: use explicit arithmetic (=Revenue-COGS), not SUM of a range that
   includes both positive and negative items
10. Round currency: =ROUND(A1*rate, 2) to prevent floating point drift in totals
```

### Verification Discipline (bake in)

```
VERIFICATION RULES:
1. After every write, read back with showFormula:true and confirm formula text
2. After every formula write, read back with showFormula:false and confirm the computed value
   is non-zero, non-error, and directionally correct
3. For any aggregation, manually cross-check against a known expected value
4. For any format operation, read back with showStyle:true
5. Take a screenshot before reporting completion — always describe what you see
6. Never say "I've written the formula" — say "I've written =SUM(B2:B13) in B14,
   read it back, and confirmed it returns 147,823.00"
```

### Reference Discipline (bake in)

```
REFERENCE BEST PRACTICES:
- Absolute ($A$1): shared rate/assumption cells, lookup table arrays
- Mixed ($A1): column-locked refs in horizontal expansion formulas
- Mixed (A$1): row-locked refs in vertical expansion formulas
- Relative (A1): formulas meant to shift when copied down/right
- Named ranges: ALWAYS for rates and assumptions referenced 3+ times
  Convention: TAX_RATE, DISCOUNT_RATE, FISCAL_YEAR_START
- Table structured refs: ALWAYS when data is in a Table
  Convention: SalesData[Revenue], Products[SKU], Customers[@Region]
```

### Anti-patterns to include explicitly

```
NEVER DO THESE:
- VLOOKUP with col_index hardcoded to a number (INSERT COLUMN = BROKEN)
  Use INDEX/MATCH or XLOOKUP instead
- SUM across a range that includes the cell containing the SUM (circular reference)
- INDIRECT or OFFSET in formulas that will be calculated frequently (volatile, slow)
- Merged cells in any data area that will be sorted, filtered, or used in VLOOKUP
- Formulas referencing sheet names with spaces without wrapping in single quotes:
  BAD: =Sheet With Spaces!A1   GOOD: ='Sheet With Spaces'!A1
- Semicolons as argument separators (European syntax — breaks in US Excel)
- Empty string "" as IFERROR fallback in financial models (hides errors — use 0 or a label)
- Leaving spill zones with data (causes #SPILL! for dynamic array formulas)
```

---

## 6. Edge Cases and Failure Modes

### Critical Failures (will corrupt the model)

**Circular References**
Happens when: SUM row includes the SUM result cell, total sheet includes itself.
Detection: =IFERROR on a circular cell returns #VALUE!, not the error text.
Read formula, trace all referenced cells, check for closed loops.
Never auto-fix circular refs — always flag to user, they may be intentional (iterative calc).

**Spill Zone Contamination**
Happens when: Dynamic array formula (FILTER, SORT, UNIQUE) has data in its spill zone.
The formula shows #SPILL! and the downstream data is silently wrong.
Prevention rule: Before writing any FILTER/SORT/UNIQUE, read the cells below/right to
confirm they're empty. If not empty, relocate the formula.

**Type Mismatch in Lookups**
Happens when: Excel stores what looks like a number as text (common after CSV import).
=ISNUMBER(A2) = FALSE even though A2 shows "123".
=VALUE(A2) coerces it, but the formula still fails until the source data is fixed.
Detection: Read source column, check if =ISNUMBER() returns FALSE.
Fix: Python bulk coerce, OR formula: =VALUE(TRIM(A2)) in a helper column.

### Silent Failures (wrong results, no error shown)

**VLOOKUP TRUE Mode on Unsorted Data**
=VLOOKUP(X, range, n, TRUE) on unsorted data returns wrong results silently.
No error indicator. This is insidious.
Prevention: Never use TRUE match mode unless you have verified the data is sorted ascending.
Always prefer XLOOKUP which defaults to exact match.

**SUM Including Hidden Rows**
=SUM(A:A) includes hidden rows. If rows are hidden via filter or group, the sum is larger
than it appears visually.
Use =SUBTOTAL(9, A:A) instead — SUBTOTAL ignores filtered/hidden rows.
Or =AGGREGATE(9, 5, A:A) — AGGREGATE also ignores errors.

**Relative Ref Drift When Formulas Are Copied**
If =B2*(1-C4) is in row 2 and copied to row 3, it becomes =B3*(1-C5).
C5 is not the tax rate — it's whatever random data is in C5.
Prevention: absolute ref on shared constants: =B2*(1-$C$4)
Detection: read formula in copied rows and trace C-column references.

**Wrong Date Serial Numbers**
Excel stores dates as integers (1 = Jan 1, 1900). Formatting makes them look like dates.
But if a date column is formatted as General, the raw integer shows.
If a date formula returns an integer instead of a date, the numFmt is missing.
Fix: apply numFmt: "mm/dd/yyyy" via excel_format_range.

**IFERROR Masking Real Bugs**
=IFERROR(formula, "") hides ALL errors including bugs in the formula logic.
Prefer =IFNA(formula, "Not found") which only catches #N/A.
Reserve IFERROR for formulas where any error = graceful fallback (rare in financial models).

### Environmental Failures

**Regional Syntax (Semicolons)**
Excel installations in most of Europe, South America, and parts of Asia use semicolons
as argument separators: =IF(A1>0; "Yes"; "No"). If you write US syntax in a European
installation, you get #NAME? errors.
The MCP excel tool appears to use US syntax internally. Always use commas.
If a user reports that all formulas show #NAME?, this is likely the cause.

**File Lock Conflicts**
If Excel has the file open while MCP tries to write, the write will fail or create a
temp file. The user must close Excel before running the agent on a file.
Detection: write operation fails, or describe_sheets shows an unexpected temp sheet.
Fix: tell user to close Excel first.

**Large File Timeouts**
Files > 20MB with complex formulas can time out on read/write.
Mitigation: read ranges in smaller chunks (A1:Z50 rather than A1:Z1000).
For bulk operations > 500 rows, use Python pandas which reads the entire file at once.

**Protected Sheets**
excel_write_to_sheet fails on protected sheets — either silently or with an error.
Detection: write fails, but read succeeds.
Fix: Python unprotect → MCP operations → Python re-protect if required.

---

## 7. Skill Designs

### `/excel-build`

**File:** `~/.claude/skills/excel-build/SKILL.md`
**Trigger:** "build me a spreadsheet", "create Excel", "make a P&L", "build a model", "I need a budget"

```markdown
# /excel-build

You are the spreadsheet-wizard agent. A user wants you to build an Excel workbook.

Follow this workflow:
1. Clarify requirements if not stated (file path, data structure, column names, sheet names)
2. If file doesn't exist, create it with a placeholder cell first
3. Plan structure (sheets, headers, formula dependencies) before writing anything
4. Write data and formulas following the formula rules in your system prompt
5. Apply standard formatting template
6. Verify: formula text, computed values, visual QA screenshot
7. Report: what was built, file path, any limitations or missing capabilities flagged

Never start writing until you have a clear plan. Never report done without verification.
```

### `/excel-verify`

**File:** `~/.claude/skills/excel-verify/SKILL.md`
**Trigger:** "check my spreadsheet", "verify formulas", "audit this file", "formula errors", "are the numbers right"

```markdown
# /excel-verify

You are the spreadsheet-wizard agent in audit mode. Read-only unless user confirms fixes.

Workflow:
1. excel_describe_sheets — inventory the workbook
2. For each sheet: read with showFormula:true — catalog all formulas
3. For each formula cell: read computed value — flag errors (#REF!, #N/A, etc.)
4. Cross-check key aggregations against source data
5. Read styles on header and data rows
6. Screenshot for visual inspection
7. Produce a verification report:
   - PASS / WARNING / FAIL per formula cell
   - Summary: N formulas checked, N passing, N errors, N warnings
   - Specific findings with cell addresses and recommended fixes
8. Ask: "Would you like me to apply the fixes?" before making any writes
```

### `/excel-format`

**File:** `~/.claude/skills/excel-format/SKILL.md`
**Trigger:** "format this spreadsheet", "apply template", "make it look professional", "style this file"

```markdown
# /excel-format

You are the spreadsheet-wizard agent in formatting mode.

Workflow:
1. Read current styles with showStyle:true
2. Get template requirements (from user or use default)
3. Apply in order: header → section headers → data rows → totals → number formats
4. For column widths (not MCP-supported): use Python fallback
5. Verify with showStyle:true
6. Screenshot for visual confirmation
7. Report: what was formatted, any template deviations flagged

Default template (when not specified):
- Header: #1F3864 fill, white bold font, 11pt
- Alternating rows: white / #F2F7FF
- Totals: bold + top border #1F3864
- Currency: "$#,##0.00", Percent: "0.0%"
```

### `/excel-fix`

**File:** `~/.claude/skills/excel-fix/SKILL.md`
**Trigger:** "#REF!", "#N/A", "formula errors", "broken formula", "it's showing errors"

```markdown
# /excel-fix

You are the spreadsheet-wizard agent in repair mode.

Workflow:
1. Read entire sheet with showFormula:true — identify all error cells
2. Classify each error (#REF!, #N/A, #VALUE!, #DIV/0!, etc.)
3. Diagnose root cause for each (don't fix blindly — understand the bug first)
4. Write fixes with explanation of what changed and why
5. Verify: re-read all previously-errored cells, confirm clean
6. Screenshot repaired section
7. Report: N errors found, N fixed, with specific changes documented

Never IFERROR-hide errors without diagnosing them first.
```

---

## 8. Missing Capabilities — MCP Gap Analysis

### Critical Gaps (would make agent 2x more powerful if added)

| Missing Capability | Business Impact | Proposed Tool Name |
|-------------------|----------------|-------------------|
| Conditional formatting | Every professional spreadsheet uses color scales, data bars, or formula-based rules. Without this, the agent can't produce truly "finished" deliverables. | `excel_add_conditional_format` |
| Data validation | Dropdowns for status fields, numeric range limits for input cells, date range pickers — core to making spreadsheets usable. | `excel_add_data_validation` |
| Column/row width + height | The agent can write perfect content but can't make it fit the screen. All screenshots show truncated data. | `excel_set_column_width`, `excel_set_row_height` |
| Freeze panes | Essential for usable dashboards and large data sheets. | `excel_freeze_panes` |
| Named ranges | The agent can't reference DISCOUNT_RATE in formulas it writes, because it can't create the name. | `excel_create_named_range` |

### High-Value Gaps (nice to have)

| Missing Capability | Business Impact | Proposed Tool Name |
|-------------------|----------------|-------------------|
| Charts | Dashboards without charts are just tables. Bar, line, pie, and waterfall charts are expected deliverables. | `excel_create_chart` |
| Pivot tables | The most-used feature in Excel for data analysts. Without it, the agent must rebuild pivot logic as formula arrays. | `excel_create_pivot` |
| Page setup | Print area, margins, headers/footers — needed for deliverable spreadsheets. | `excel_set_page_setup` |
| Sheet protection | Preventing users from editing input assumptions is a standard financial modeling pattern. | `excel_protect_sheet` |
| Comments/notes | Documenting formulas, assumptions, and data sources in-cell is professional practice. | `excel_add_comment` |
| Row/column hide | Hiding helper columns and intermediate calculation rows is standard practice. | `excel_hide_range` |

### Architectural Workaround

Until these gaps are filled, the agent uses a hybrid pattern:

```
For any request involving missing MCP capabilities:
1. Use MCP tools for: data writing, formula writing, basic formatting, verification
2. Use Python (openpyxl via Bash) for: everything else
3. Sequence: Python structural setup → MCP incremental editing → MCP verification
4. The Python code is written to a temp .py file, executed via Bash, then deleted
```

The Python bridge allows the agent to deliver fully-featured workbooks today, while
MCP coverage expands over time. The agent should flag to the user which parts were
done via Python vs MCP, so the capability gap is transparent.

---

## Implementation Notes

### File Path Convention
Always use absolute paths with forward slashes on Windows:
`C:/Users/username/Documents/report.xlsx`
Not: `C:\Users\...` (backslashes can cause issues in some MCP implementations)

### New File Creation
MCP tools cannot create a new .xlsx file from scratch — they require the file to exist.
Workaround: use Bash to create an empty file first, then MCP can open it:
```python
from openpyxl import Workbook
wb = Workbook()
wb.save("C:/path/to/new.xlsx")
```
Or use `excel_write_to_sheet` with `newSheet: true` on an existing file.

### Read Pagination
`excel_read_sheet` supports pagination via the `range` parameter. For large sheets,
read in chunks: A1:Z100, then A101:Z200, etc. The tool returns a default "first page"
if no range is specified — always specify a range to be explicit about what you're reading.

### Formula Array Notation
For pre-365 array formulas (Ctrl+Shift+Enter in Excel), the MCP tool does not support
the curly brace array formula syntax. Use SUMPRODUCT as the universal fallback, which
is a native array function and doesn't require Ctrl+Shift+Enter.

### Style Array Size Must Match Range
`excel_format_range` requires the `styles` 2D array to exactly match the range dimensions.
A 3x4 range (3 rows, 4 columns) needs a 3x4 styles array.
Wrong size = error. Always pre-compute the styles array dimensions before calling.

---

*Agent file: `C:\Users\trg16\.claude\agents\spreadsheet-wizard.md`*
*Design document: `C:\Users\trg16\Dev\Bricklayer2.0\docs\spreadsheet-wizard-design.md`*
