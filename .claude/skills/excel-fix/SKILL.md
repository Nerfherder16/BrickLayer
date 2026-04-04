---
name: excel-fix
description: Fix Excel formula errors — diagnose and repair #REF!, #N/A, #VALUE!, #DIV/0!, #NAME?, circular refs
---

# /excel-fix

## Purpose
Diagnose and repair formula errors in an existing workbook.
Never blindly suppress errors with IFERROR — always diagnose root cause first.

## Trigger Conditions
- "#REF! error"
- "#N/A in my formulas"
- "formula errors in column D"
- "something is broken"
- "it's showing errors all over"
- "circular reference warning"

## Agent
Invoke the `spreadsheet-wizard` agent from `~/.claude/agents/spreadsheet-wizard.md`.

## Error Reference

| Error | Typical Cause | Fix Strategy |
|-------|---------------|-------------|
| `#REF!` | Row/column deleted that was referenced | Rebuild the reference from scratch |
| `#NAME?` | Function name typo, missing named range | Fix spelling or create the named range |
| `#VALUE!` | Wrong data type (text where number expected) | VALUE() coerce, or check source cell type |
| `#DIV/0!` | Division by zero or blank denominator | `=IF(denom=0, "", numer/denom)` or IFERROR |
| `#N/A` | Lookup value not found | IFERROR/IFNA + check type match (text vs number) |
| `#NULL!` | Space instead of : in range, or incorrect intersection | Fix the range syntax |
| `#NUM!` | Invalid numeric arg (SQRT of negative, IRR no convergence) | Check input data validity |
| `#SPILL!` | Dynamic array formula's output zone has data in it | Clear spill zone or move formula |
| `######` | Column too narrow for the value | Formatting issue — not formula error |

## Workflow

### Phase 1: Full Error Audit
```
excel_read_sheet with showFormula: true
```
Read the entire sheet (or specific range if user indicated location).
List every cell containing an error value.

### Phase 2: Classify Each Error
For each error cell, determine the error type from the computed value.
Note the formula text.

### Phase 3: Diagnose Root Cause
For each error:

**#REF!**
- Read the formula text — identify which reference shows `#REF!`
- Ask: were rows or columns recently deleted? Check the surrounding cells for gaps
- Rebuild the reference to point to the correct current cells

**#N/A**
- Read the lookup value in the source row
- Read the first 10 values in the lookup table key column
- Check: are they the same data type? (=ISNUMBER vs text representation of number)
- Check: any leading/trailing spaces? (=TRIM(A2) to test)
- Check: is the lookup value actually in the table?

**#VALUE!**
- Read the cell being referenced
- Confirm it's text: `=ISNUMBER(the_cell)` returns FALSE
- If text-disguised-number: use VALUE() wrapper in the formula

**#DIV/0!**
- Read the denominator cell — confirm it's 0 or blank
- Decide: should 0 denominator return 0, blank, or "N/A"?

**#SPILL!**
- Read the cells in the spill zone (below and right of the formula)
- Identify which cell has data blocking the spill
- Options: clear the blocking cell, or move the formula to a new location

### Phase 4: Write Fixes
Apply fixes one by one. For each fix, log:
- Cell address
- Original (broken) formula
- Fixed formula
- Why the fix works

Do NOT use blanket IFERROR to suppress errors without diagnosing them first.
If IFERROR is the right fix (e.g., truly optional lookup), the fallback value
must be meaningful (0, "N/A", "Not assigned") — not empty string "" (hides bugs).

### Phase 5: Verify
```
excel_read_sheet with showFormula: false
```
Re-read all previously-errored cells.
Confirm: all return values, no error strings remain.
Spot-check 3 adjacent non-error rows to confirm formula logic wasn't accidentally changed.

### Phase 6: Screenshot
```
excel_screen_capture → describe repaired section
```

## Output
Fix report:
- N errors found by type
- N fixed
- For each fix: cell, original formula, fixed formula, explanation
- Screenshot of clean state

## What NOT to Do
- Do NOT =IFERROR(broken_formula, "") blindly — this hides bugs
- Do NOT guess at the intended formula — trace the data to understand intent
- Do NOT fix #REF! by extending ranges blindly — confirm the correct range first
- Do NOT report done until all error cells return values
