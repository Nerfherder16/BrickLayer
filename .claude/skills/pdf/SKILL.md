---
name: pdf
description: Create a professional PDF — reports, invoices, research summaries, data exports. HTML→PDF via WeasyPrint (richest layout) or FPDF2 (programmatic). Auto-selects best engine.
---

# /pdf — Build a PDF Document

## Purpose
Autonomously produce a production-quality `.pdf` file. Two engines available:
- **WeasyPrint** — HTML/CSS → PDF. Best for rich layouts, charts, styled reports.
- **FPDF2** — Pure Python programmatic PDF. Best for data-heavy tables, invoices, dynamic content.

Auto-selects engine based on the task. User can override.

## Trigger Conditions
- "create a PDF report"
- "export this as PDF"
- "make me a PDF of..."
- "generate an invoice / summary / analysis as PDF"
- "I need a formatted PDF"

---

## Engine Selection Guide

| Use WeasyPrint when... | Use FPDF2 when... |
|------------------------|-------------------|
| Rich typography / branding | Programmatic row generation |
| Multi-column layouts | Dynamic page breaks needed |
| CSS styling control | Invoice / receipt format |
| HTML source already exists | Simple tabular data |
| Charts via `<img>` embed | Minimal dependencies needed |

---

## Workflow

### Phase 1: Requirements Clarification

Before any tool calls, confirm:
- **Output path** — where to save the `.pdf`
- **Content** — text, tables, charts, data?
- **Layout** — single column, two-column, executive report, invoice?
- **Engine preference** — or let Claude choose

---

### Phase 2: Dependency Check

```bash
# WeasyPrint
python -c "import weasyprint; print('OK')" 2>/dev/null || pip install weasyprint -q

# FPDF2
python -c "import fpdf; print('OK')" 2>/dev/null || pip install fpdf2 -q
```

---

### Phase 3a: WeasyPrint Path (Recommended for Reports)

Write HTML with embedded CSS, then convert to PDF.

```python
from weasyprint import HTML, CSS
import os

html_content = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page {
    size: letter;
    margin: 1in 1.25in;
    @bottom-center {
      content: "Page " counter(page) " of " counter(pages);
      font-size: 9pt;
      color: #666;
    }
  }

  body {
    font-family: 'Calibri', 'Segoe UI', Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.5;
    color: #222;
  }

  h1 {
    font-size: 18pt;
    color: #1F3864;
    border-bottom: 2px solid #1F3864;
    padding-bottom: 6pt;
    margin-top: 0;
  }

  h2 {
    font-size: 13pt;
    color: #2E74B5;
    margin-top: 18pt;
  }

  h3 {
    font-size: 11pt;
    font-weight: bold;
    color: #333;
  }

  .cover {
    text-align: center;
    padding-top: 2in;
    page-break-after: always;
  }

  .cover h1 {
    font-size: 28pt;
    border: none;
  }

  .cover .subtitle {
    font-size: 14pt;
    color: #555;
    margin-top: 12pt;
  }

  .cover .date {
    font-size: 10pt;
    color: #888;
    margin-top: 8pt;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    margin: 12pt 0;
    font-size: 10pt;
  }

  th {
    background-color: #1F3864;
    color: white;
    padding: 8pt 10pt;
    text-align: left;
    font-weight: bold;
  }

  td {
    padding: 6pt 10pt;
    border-bottom: 1px solid #E0E0E0;
  }

  tr:nth-child(even) td {
    background-color: #F5F8FF;
  }

  .callout {
    background: #EEF4FF;
    border-left: 4px solid #2E74B5;
    padding: 10pt 14pt;
    margin: 12pt 0;
    font-size: 10pt;
  }

  .highlight {
    background: #FFF9E6;
    border-left: 4px solid #F59E0B;
    padding: 10pt 14pt;
    margin: 12pt 0;
    font-size: 10pt;
  }

  .metric-row {
    display: flex;
    gap: 20pt;
    margin: 12pt 0;
  }

  .metric-box {
    flex: 1;
    border: 1px solid #DDD;
    border-radius: 4pt;
    padding: 10pt;
    text-align: center;
  }

  .metric-value {
    font-size: 22pt;
    font-weight: 300;
    color: #1F3864;
  }

  .metric-label {
    font-size: 8pt;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.5pt;
    margin-top: 4pt;
  }

  ul, ol {
    margin: 6pt 0;
    padding-left: 18pt;
  }

  li {
    margin-bottom: 4pt;
  }

  .page-break {
    page-break-before: always;
  }

  footer-note {
    font-size: 8pt;
    color: #888;
    border-top: 1px solid #DDD;
    padding-top: 6pt;
    margin-top: 24pt;
  }
</style>
</head>
<body>

<!-- COVER PAGE -->
<div class="cover">
  <h1>Report Title</h1>
  <div class="subtitle">Subtitle or Organization Name</div>
  <div class="date">March 20, 2026 · Prepared by: [Name]</div>
</div>

<!-- SECTION 1 -->
<h1>Section Heading</h1>
<p>Body text here. Professional, clear, concise.</p>

<!-- CALLOUT BOX -->
<div class="callout">
  <strong>Key insight:</strong> Important finding or note displayed prominently.
</div>

<!-- TABLE -->
<h2>Data Summary</h2>
<table>
  <tr><th>Column A</th><th>Column B</th><th>Column C</th></tr>
  <tr><td>Value 1</td><td>Value 2</td><td>Value 3</td></tr>
  <tr><td>Value 4</td><td>Value 5</td><td>Value 6</td></tr>
</table>

</body>
</html>
"""

output_path = 'output.pdf'
HTML(string=html_content).write_pdf(output_path)
print(f'Saved: {os.path.abspath(output_path)}')
```

---

### Phase 3b: FPDF2 Path (Programmatic / Data-Dense)

```python
from fpdf import FPDF
import os

class ReportPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(31, 56, 100)
        self.cell(0, 8, 'REPORT TITLE', align='L')
        self.ln(4)
        self.set_draw_color(31, 56, 100)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

pdf = ReportPDF()
pdf.alias_nb_pages()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=15)

# Title
pdf.set_font('Helvetica', 'B', 18)
pdf.set_text_color(31, 56, 100)
pdf.cell(0, 12, 'Document Title', ln=True)
pdf.ln(4)

# Body text
pdf.set_font('Helvetica', '', 11)
pdf.set_text_color(34, 34, 34)
pdf.multi_cell(0, 6, 'Body paragraph text. Wraps automatically to page width.')
pdf.ln(4)

# Section heading
pdf.set_font('Helvetica', 'B', 13)
pdf.set_text_color(46, 116, 181)
pdf.cell(0, 8, 'Section Heading', ln=True)
pdf.ln(2)

# Table
pdf.set_font('Helvetica', 'B', 10)
pdf.set_fill_color(31, 56, 100)
pdf.set_text_color(255, 255, 255)
col_widths = [60, 60, 70]
headers = ['Column A', 'Column B', 'Column C']
for w, h in zip(col_widths, headers):
    pdf.cell(w, 8, h, border=1, fill=True)
pdf.ln()

pdf.set_font('Helvetica', '', 10)
pdf.set_text_color(34, 34, 34)
rows = [('Value 1', 'Value 2', 'Value 3'), ('Value 4', 'Value 5', 'Value 6')]
for i, row in enumerate(rows):
    pdf.set_fill_color(245, 248, 255) if i % 2 else pdf.set_fill_color(255, 255, 255)
    for w, val in zip(col_widths, row):
        pdf.cell(w, 7, val, border=1, fill=True)
    pdf.ln()

output_path = 'output.pdf'
pdf.output(output_path)
print(f'Saved: {os.path.abspath(output_path)}')
```

---

### Phase 4: Formatting Standards

| Element | Standard |
|---------|----------|
| Page size | US Letter (8.5" × 11") |
| Margins | 1" top/bottom, 1.25" left/right |
| Body font | Calibri / Helvetica 11pt |
| Heading 1 | 18pt bold, dark blue `#1F3864` |
| Heading 2 | 13pt bold, medium blue `#2E74B5` |
| Table header | `#1F3864` fill, white bold text |
| Table rows | Alternating white / `#F5F8FF` |
| Footer | Page N of M, centered, 8pt gray |
| Callout boxes | Left border accent, light background |

---

### Phase 5: Verification

```bash
python -c "
import os
path = 'output.pdf'
size = os.path.getsize(path)
print(f'File: {path}')
print(f'Size: {size:,} bytes ({size/1024:.1f} KB)')
print('Status: OK' if size > 1000 else 'WARNING: file may be empty')
"
```

Also open and describe: `start output.pdf` (Windows)

---

### Phase 6: Delivery

Report:
- Full output path
- Engine used (WeasyPrint / FPDF2) and why
- Page count (if detectable)
- Sections created
- Tables: count × dimensions
- Any embedded images or charts

---

## Quality Rules

- **Always include page numbers** — footer with page N of M
- **Cover page for reports > 3 pages** — title, subtitle, date, author
- **No orphan headings** — heading must not appear alone at bottom of page (`page-break-inside: avoid`)
- **Table headers repeat on new pages** — for multi-page tables
- **Date is explicit** — never leave placeholder dates
- **File size sanity check** — warn if < 5KB (likely empty)

---

## Python Library Reference

```bash
# WeasyPrint (recommended for rich reports)
pip install weasyprint

# FPDF2 (recommended for data / invoices)
pip install fpdf2

# Key WeasyPrint imports
from weasyprint import HTML, CSS

# Key FPDF2 imports
from fpdf import FPDF
```

### WeasyPrint Notes
- Requires system fonts — uses Calibri on Windows, falls back to Arial/Helvetica
- On headless servers: `pip install weasyprint[all]` + `apt install libpango-1.0-0`
- No JavaScript execution — pure HTML/CSS only
- CSS `@page` controls margins, page size, headers/footers

### FPDF2 Notes
- Pure Python, no system dependencies
- `alias_nb_pages()` enables total page count in footer
- `multi_cell()` for wrapping text, `cell()` for fixed-width
- Fonts: built-in Helvetica/Times/Courier, or load TTF with `add_font()`
