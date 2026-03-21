"""
Build ADBP_Research_Findings.docx
"""
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = "docs/ADBP_Research_Findings.docx"

doc = Document()

# --- Margins ---
section = doc.sections[0]
section.top_margin = Inches(1.0)
section.bottom_margin = Inches(1.0)
section.left_margin = Inches(1.25)
section.right_margin = Inches(1.25)

# --- Styles ---
h1 = doc.styles["Heading 1"]
h1.font.size = Pt(14)
h1.font.bold = True
h1.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)

h2 = doc.styles["Heading 2"]
h2.font.size = Pt(12)
h2.font.bold = True
h2.font.color.rgb = RGBColor(0x2E, 0x74, 0xB5)

normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(11)


def add_bullet(doc, text, bold_prefix=None):
    p = doc.add_paragraph(style="List Bullet")
    if bold_prefix:
        run = p.add_run(bold_prefix)
        run.bold = True
        p.add_run(text)
    else:
        p.add_run(text)
    return p


def add_table(doc, headers, rows, col_widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    # Header row
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = h
        for para in hdr[i].paragraphs:
            for run in para.runs:
                run.bold = True
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        hdr[i]._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:fill"), "DCE6F1")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:val"), "clear")
        hdr[i]._tc.get_or_add_tcPr().append(shd)
    # Data rows
    for row_data in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row_data):
            cells[i].text = val
            for para in cells[i].paragraphs:
                para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    # Column widths
    if col_widths:
        for i, width in enumerate(col_widths):
            for row in t.rows:
                row.cells[i].width = Inches(width)
    return t


def add_footer(section, text):
    footer = section.footer
    para = footer.paragraphs[0]
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run(text + "  |  Page ")
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x80, 0x80, 0x80)
    # Page number field
    r = para.add_run()
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(0x80, 0x80, 0x80)
    fldChar = OxmlElement("w:fldChar")
    fldChar.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText")
    instrText.text = "PAGE"
    fldChar2 = OxmlElement("w:fldChar")
    fldChar2.set(qn("w:fldCharType"), "end")
    r._r.append(fldChar)
    r._r.append(instrText)
    r._r.append(fldChar2)


# ── Title block ──────────────────────────────────────────────────────────────
title = doc.add_heading("ADBP Model Research Findings", level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.runs[0].font.color.rgb = RGBColor(0x1F, 0x38, 0x64)

sub = doc.add_paragraph("Monte Carlo Campaign  —  March 2026")
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub.runs[0].font.size = Pt(11)
sub.runs[0].font.color.rgb = RGBColor(0x60, 0x60, 0x60)
sub.runs[0].font.italic = True

doc.add_paragraph()

# ── Section 1: Campaign Overview ─────────────────────────────────────────────
doc.add_heading("1. Campaign Overview", level=1)
add_bullet(doc, "300,000 runs (3 seeds × 100,000 runs × 240 months)", "Simulation: ")
add_bullet(doc, "42, 99, 123", "Seeds: ")
add_bullet(doc, "N(mean=1,000, sigma=300) employees per month (stochastic)", "Growth model: ")
add_bullet(doc, "trigger_ratio [0.9–1.6], burn_pct [2–35%], cooldown [3–24 months], first_eligible [6–24 months]", "Search space: ")

doc.add_paragraph()

# ── Section 2: Outcome Distribution ─────────────────────────────────────────
doc.add_heading("2. Outcome Distribution", level=1)
add_table(
    doc,
    ["Outcome", "Count", "Percentage"],
    [
        ["HEALTHY", "257,034", "85.68%"],
        ["WARNING",  "42,966", "14.32%"],
        ["FAILURE",       "0",  "0.00%"],
    ],
    col_widths=[2.0, 2.0, 2.0],
)
doc.add_paragraph()
p = doc.add_paragraph(
    "Seed stability: 85.63% – 85.75% HEALTHY across all three seeds (0.12 percentage point spread). "
    "The campaign is fully converged."
)
p.runs[0].font.italic = True

doc.add_paragraph()

# ── Section 3: MC-Optimal Strategy ───────────────────────────────────────────
doc.add_heading("3. MC-Optimal Strategy", level=1)
doc.add_paragraph(
    "Best overall score (highest combined HEALTHY rate + burn fraction + stability):"
)
add_table(
    doc,
    ["Parameter", "Value"],
    [
        ["Trigger ratio",       "1.332× (burn when backing ≥ 133.2%)"],
        ["Burn size",           "34.9% of outstanding credits per event"],
        ["Minimum cooldown",    "18 months"],
        ["First eligible",      "Month 20"],
        ["Score",               "3.1388"],
        ["Min backing",         "97.3%"],
        ["Final backing",       "97.3%"],
        ["Burn events",         "1"],
        ["Credits destroyed",   "34.9% of all credits ever minted"],
    ],
    col_widths=[2.5, 4.0],
)

doc.add_paragraph()

# ── Section 4: Structural Solvency Guarantee ─────────────────────────────────
doc.add_heading("4. Structural Solvency Guarantee", level=1)
p = doc.add_paragraph()
r = p.add_run("Finding: ")
r.bold = True
p.add_run("Treasury FAILURE (backing < 50%) is mathematically impossible from market conditions alone.")

p2 = doc.add_paragraph()
r2 = p2.add_run("Proof: ")
r2.bold = True
r2.font.color.rgb = RGBColor(0x2E, 0x74, 0xB5)
p2.add_run(
    "treasury_wallet = \u03a3(inflows) + interest \u2265 \u03a3(credits_minted \u00d7 $1.00) = total_credits_outstanding"
).font.name = "Courier New"

doc.add_paragraph(
    "Because every credit minted adds exactly $1.00 to the treasury, and interest only adds further, "
    "the backing ratio cannot fall below 100% without an explicit burn event."
)

doc.add_paragraph("Stress tests confirming this:")
for line in [
    "Zero interest rate: min backing = 100.0%",
    "75% employee loss (month 6): min backing = 100.0%",
    "Extreme credits per employee (100 CPE): min backing = 100.0%",
    "All adversity combined: min backing = 100.0%",
]:
    add_bullet(doc, line)

doc.add_paragraph(
    "The affordability cap formula (max_burnable = (wallet \u2212 0.50 \u00d7 total_credits) / 1.50) "
    "mathematically prevents post-burn backing from dropping below 50%."
)

p3 = doc.add_paragraph()
r3 = p3.add_run("Implication: ")
r3.bold = True
p3.add_run(
    "The 0.00% FAILURE rate across 300,000 runs is not luck \u2014 "
    "it is guaranteed by the system\u2019s accounting identity."
)

doc.add_paragraph()

# ── Section 5: Burn Frequency Analysis ───────────────────────────────────────
doc.add_heading("5. Burn Frequency Analysis", level=1)
p = doc.add_paragraph()
r = p.add_run("Finding: ")
r.bold = True
p.add_run("Yearly burns are viable and 100% HEALTHY, but not optimal.")

doc.add_paragraph(
    "With trigger=1.0\u00d7 and cooldown=12 months, burns fire annually from first_eligible month onward. "
    "Conservative strategies (2% burn size, many events) achieve 100% HEALTHY rate."
)
doc.add_paragraph("Why the MC-optimal strategy uses one large late burn instead:")
for line in [
    "One large burn at backing ~133% destroys more total obligation than many small burns",
    "Small frequent burns at low trigger ratios produce WARNING states (50\u201374% backing)",
    "The scoring function rewards both burn fraction and minimum backing \u2014 one late large burn maximizes both",
]:
    add_bullet(doc, line)

doc.add_paragraph("HEALTHY rate by trigger ratio band:")
add_table(
    doc,
    ["Trigger Band", "HEALTHY Rate"],
    [
        ["0.9\u00d7 \u2013 1.0\u00d7", "42.49%"],
        ["1.0\u00d7 \u2013 1.1\u00d7", "66.29%"],
        ["1.1\u00d7 \u2013 1.2\u00d7", "90.76%"],
        ["1.2\u00d7 \u2013 1.3\u00d7", "100.00%"],
        ["1.3\u00d7 \u2013 1.6\u00d7", "100.00% (zero burn activity above 1.4\u00d7)"],
    ],
    col_widths=[2.0, 4.5],
)

doc.add_paragraph()

# ── Section 6: Credit Expiry Mechanics ───────────────────────────────────────
doc.add_heading("6. Credit Expiry Mechanics", level=1)
doc.add_paragraph(
    "Research into analogous closed-loop programs (loyalty, commuter benefits, corporate perks, gift cards):"
)
add_table(
    doc,
    ["Program Type", "Typical Window", "Notes"],
    [
        ["Gift cards (CARD Act)",        "5 years minimum",        "Statutory floor for consumer protection"],
        ["Closed-loop corporate perks",  "24\u201336 months",      "Standard practice; legally defensible"],
        ["Loyalty / rewards points",     "12\u201324 months inactivity", "Forfeiture on inactivity, not calendar"],
        ["Commuter / FSA benefits",      "Monthly rolling",         "Strict regulatory use-it-or-lose-it"],
        ["ADBP (recommended)",           "36 months",               "Generous, consumer-friendly"],
    ],
    col_widths=[2.2, 1.8, 2.5],
)

doc.add_paragraph()
doc.add_paragraph(
    "At 12\u00d7 annual velocity, research baseline for annual breakage is 5\u20137%."
)
p = doc.add_paragraph()
r = p.add_run("Expiry economics: ")
r.bold = True
p.add_run(
    "Credits that expire cost $0 to the treasury (the $1.00 inflow was already collected; the $2.00 obligation simply "
    "terminates). This makes expiry strictly more treasury-efficient than burns ($0/credit vs $2/credit)."
)

doc.add_paragraph("Key simulation results from expiry analysis:")
add_table(
    doc,
    ["Scenario", "Burns", "Credits Destroyed", "Final Backing"],
    [
        ["Baseline (burns only)",                 "1", "30.2%", "77.7% HEALTHY"],
        ["36mo expiry + 6% breakage + burns",     "5", "66.4%", "99.1% HEALTHY"],
        ["No-burn + 24mo + 10% breakage",         "0", "67.5%", "352.9% (over-collateralized)"],
        ["No-burn + 36mo + 6% breakage",          "0", "37.1%", "498.2% (over-collateralized)"],
    ],
    col_widths=[2.8, 0.7, 1.5, 1.5],
)

doc.add_paragraph()
doc.add_paragraph(
    "Note: No-burn + expiry produces extreme over-collateralization. Expiry alone is not a substitute for burns \u2014 "
    "it accelerates backing ratio growth, which then requires burns to rebalance."
).runs[0].font.italic = True

doc.add_paragraph()

# ── Section 7: CPE Invariance ─────────────────────────────────────────────────
doc.add_heading("7. CPE Invariance", level=1)
p = doc.add_paragraph()
r = p.add_run("Finding: ")
r.bold = True
p.add_run("Credits-per-employee (CPE) does not affect the backing ratio.")
doc.add_paragraph(
    "Both treasury_wallet and total_credits scale linearly with CPE, so the ratio is CPE-invariant. "
    "A program with 10 CPE and a program with 5,000 CPE produce identical backing ratios under identical burn strategies."
)

doc.add_paragraph()

# ── Section 8: Post-Burn Adversity ───────────────────────────────────────────
doc.add_heading("8. Post-Burn Adversity", level=1)
p = doc.add_paragraph()
r = p.add_run("Finding: ")
r.bold = True
p.add_run(
    "The burn event itself is always the minimum backing point. "
    "Subsequent adverse conditions cannot reduce backing further."
)
doc.add_paragraph(
    "After a burn, any new credit minted adds $1.00 to the wallet and $1.00 to outstanding credits. "
    "The structural solvency guarantee applies from that point forward. Post-burn conditions "
    "(zero interest, negative growth) cannot push backing lower."
)

doc.add_paragraph()

# ── Section 9: Recommended Parameters ────────────────────────────────────────
doc.add_heading("9. Recommended Parameters", level=1)
doc.add_paragraph("Based on 300,000-run MC campaign over 240 months:")
for line in [
    "Trigger: backing \u2265 133.2%",
    "Burn size: 34.9% of outstanding credits",
    "Cooldown: 18 months minimum between burns",
    "First eligible: Month 20 (ramp-up protection)",
    "Credit expiry window: 36 months",
    "Annual breakage target: 5\u20137%",
]:
    add_bullet(doc, line)

# ── Footer ────────────────────────────────────────────────────────────────────
add_footer(section, "American Dream Benefits Program  |  Research Findings  |  Confidential \u2014 March 2026")

doc.save(OUT)
print(f"Saved: {OUT}")
