---
name: docx
description: Create a professional Word document (.docx) — reports, proposals, SOPs, memos, structured docs with headings, tables, and proper formatting
---

# /docx — Build a Word Document

## Purpose
Autonomously produce a production-quality `.docx` file using `python-docx`.
Handles structure, styles, tables, headers/footers, and formatting in one pass.

## Trigger Conditions
- "write me a Word doc"
- "create a report / proposal / SOP / memo"
- "make a DOCX file"
- "I need a document for..."
- "draft this as a Word document"

---

## Workflow

### Phase 1: Requirements Clarification

Before any tool calls, confirm:
- **Output path** — where to save the `.docx`
- **Document type** — report, proposal, SOP, memo, contract, letter, analysis
- **Content** — user provides text, or Claude drafts from context
- **Structure** — sections, tables, numbered lists, appendices

If partially specified, infer reasonable defaults and state them.

---

### Phase 2: Dependency Check

```bash
python -c "import docx; print('OK')" 2>/dev/null || pip install python-docx -q
```

---

### Phase 3: Build the Document

Always use a Python script (write to a temp file, then run via Bash).

#### Standard Structure Template

```python
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import datetime

doc = Document()

# --- Page margins ---
section = doc.sections[0]
section.top_margin = Inches(1.0)
section.bottom_margin = Inches(1.0)
section.left_margin = Inches(1.25)
section.right_margin = Inches(1.25)

# --- Document styles ---
# Heading 1
h1 = doc.styles['Heading 1']
h1.font.size = Pt(16)
h1.font.bold = True
h1.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)  # Dark blue

# Heading 2
h2 = doc.styles['Heading 2']
h2.font.size = Pt(13)
h2.font.bold = True
h2.font.color.rgb = RGBColor(0x2E, 0x74, 0xB5)

# Normal text
normal = doc.styles['Normal']
normal.font.name = 'Calibri'
normal.font.size = Pt(11)

# --- Title block ---
title = doc.add_heading('Document Title Here', level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

subtitle = doc.add_paragraph('Subtitle or Author • Date')
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
subtitle.runs[0].font.size = Pt(10)
subtitle.runs[0].font.color.rgb = RGBColor(0x60, 0x60, 0x60)

doc.add_paragraph()  # Spacer

# --- Section 1 ---
doc.add_heading('Section Heading', level=1)
doc.add_paragraph(
    'Body text goes here. Use clear, professional language. '
    'Keep paragraphs focused on a single idea.'
)

# --- Table example ---
table = doc.add_table(rows=1, cols=3)
table.style = 'Table Grid'
hdr_cells = table.rows[0].cells
hdr_cells[0].text = 'Column A'
hdr_cells[1].text = 'Column B'
hdr_cells[2].text = 'Column C'
# Bold header row
for cell in hdr_cells:
    for para in cell.paragraphs:
        for run in para.runs:
            run.bold = True

# Add data rows
row_data = [('Val 1', 'Val 2', 'Val 3')]
for a, b, c in row_data:
    row_cells = table.add_row().cells
    row_cells[0].text = a
    row_cells[1].text = b
    row_cells[2].text = c

doc.add_paragraph()  # Spacer after table

# --- Footer with page numbers ---
footer = section.footer
footer_para = footer.paragraphs[0]
footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
footer_para.text = 'Confidential  •  Page '
run = footer_para.add_run()
fldChar = OxmlElement('w:fldChar')
fldChar.set(qn('w:fldCharType'), 'begin')
instrText = OxmlElement('w:instrText')
instrText.text = 'PAGE'
fldChar2 = OxmlElement('w:fldChar')
fldChar2.set(qn('w:fldCharType'), 'end')
run._r.append(fldChar)
run._r.append(instrText)
run._r.append(fldChar2)

doc.save('output.docx')
print('Saved: output.docx')
```

---

### Phase 4: Formatting Standards

| Element | Standard |
|---------|----------|
| Body font | Calibri 11pt |
| Heading 1 | Bold 16pt, dark blue `#1F3864` |
| Heading 2 | Bold 13pt, medium blue `#2E74B5` |
| Margins | 1.0" top/bottom, 1.25" left/right |
| Line spacing | 1.15 (Word default) |
| Table header | Bold, `Table Grid` style |
| Footer | Page number centered |
| Date format | Month D, YYYY (e.g., March 20, 2026) |

---

### Phase 5: Verification

After saving, read back to confirm structure:

```python
from docx import Document
doc = Document('output.docx')
print(f"Paragraphs: {len(doc.paragraphs)}")
print(f"Tables: {len(doc.tables)}")
for i, para in enumerate(doc.paragraphs[:10]):
    print(f"  [{para.style.name}] {para.text[:60]}")
```

Report: paragraph count, table count, heading hierarchy, any warnings.

---

### Phase 6: Delivery

Report:
- Full output path
- Sections created (with heading names)
- Tables: count × dimensions
- Any non-standard features used (TOC, images, footnotes)
- How to open: `start output.docx` (Windows)

---

## Quality Rules

- **No empty headings** — every heading has content below it
- **No orphaned tables** — every table has a heading or caption
- **Page numbers always** — include footer with page number
- **Date is explicit** — never leave placeholder dates
- **Consistent heading hierarchy** — H1 → H2 → H3, no skipping levels
- **Spell-check reminder** — note in delivery that spell check should be run in Word

---

## Common Document Types

### Executive Summary / Report
Title block → Executive Summary (H1) → Background (H1) → Findings (H1 with H2 subsections) → Recommendations (H1) → Appendix (H1)

### Standard Operating Procedure (SOP)
Title → Purpose → Scope → Responsibilities → Procedure (numbered steps) → References → Revision History (table)

### Business Proposal
Cover page → Problem Statement → Proposed Solution → Timeline (table) → Budget (table) → Terms → Signature Block

### Memo
Header table (TO/FROM/DATE/RE) → Body paragraphs → Action Items (bullet list)

---

## Python Library Reference

```bash
# Install
pip install python-docx

# Key imports
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
```
