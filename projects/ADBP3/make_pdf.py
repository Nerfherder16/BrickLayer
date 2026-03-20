"""
Generate ADBP_System_Rules_v3.pdf from the markdown file.
Matches the clean, simple style of ADBP_Final_Model_Legal.pdf.
Content is taken verbatim from the markdown — no additions.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

PAGE_W, PAGE_H = letter
LM = RM = 1.0 * inch
TM = BM = 0.9 * inch
COL = PAGE_W - LM - RM  # 6.5 inches

BLACK = colors.HexColor("#000000")
DGRAY = colors.HexColor("#333333")
MGRAY = colors.HexColor("#666666")
LGRAY = colors.HexColor("#f5f5f5")
RULE = colors.HexColor("#cccccc")
WHITE = colors.white


def S(name, **kw):
    return ParagraphStyle(name, **kw)


# Styles — plain, matching original document aesthetic
title = S(
    "title",
    fontSize=16,
    fontName="Helvetica-Bold",
    textColor=BLACK,
    alignment=TA_CENTER,
    leading=22,
    spaceAfter=4,
)
meta = S(
    "meta",
    fontSize=9,
    fontName="Helvetica",
    textColor=MGRAY,
    alignment=TA_CENTER,
    leading=13,
    spaceAfter=2,
)
h2 = S(
    "h2",
    fontSize=12,
    fontName="Helvetica-Bold",
    textColor=BLACK,
    spaceBefore=16,
    spaceAfter=4,
    leading=16,
)
h3 = S(
    "h3",
    fontSize=10,
    fontName="Helvetica-Bold",
    textColor=BLACK,
    spaceBefore=10,
    spaceAfter=3,
    leading=14,
)
body = S(
    "body",
    fontSize=9.5,
    fontName="Helvetica",
    textColor=DGRAY,
    leading=14,
    spaceAfter=3,
)
bul = S(
    "bul",
    fontSize=9.5,
    fontName="Helvetica",
    textColor=DGRAY,
    leading=14,
    spaceAfter=2,
    leftIndent=16,
    firstLineIndent=0,
)
bul2 = S(
    "bul2",
    fontSize=9.5,
    fontName="Helvetica",
    textColor=DGRAY,
    leading=14,
    spaceAfter=2,
    leftIndent=32,
    firstLineIndent=0,
)
blockq = S(
    "blockq",
    fontSize=9.5,
    fontName="Helvetica-Oblique",
    textColor=DGRAY,
    leading=14,
    spaceAfter=4,
    leftIndent=20,
)
code_s = S(
    "code",
    fontSize=8.5,
    fontName="Courier",
    textColor=DGRAY,
    leading=13,
    spaceAfter=2,
    leftIndent=16,
)
num_bul = S(
    "num",
    fontSize=9.5,
    fontName="Helvetica",
    textColor=DGRAY,
    leading=14,
    spaceAfter=2,
    leftIndent=16,
)
footer_s = S(
    "ftr", fontSize=8, fontName="Helvetica", textColor=MGRAY, alignment=TA_CENTER
)


def hr():
    return HRFlowable(
        width="100%", thickness=0.5, color=RULE, spaceAfter=6, spaceBefore=6
    )


def simple_table(headers, rows, col_widths):
    hs = S("th", fontSize=9, fontName="Helvetica-Bold", textColor=BLACK, leading=12)
    ds = S("td", fontSize=9, fontName="Helvetica", textColor=DGRAY, leading=12)
    data = [[Paragraph(c, hs) for c in headers]]
    for row in rows:
        data.append([Paragraph(c, ds) for c in row])
    t = Table(data, colWidths=col_widths)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), LGRAY),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, RULE),
                ("GRID", (0, 0), (-1, -1), 0.4, RULE),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return t


doc = SimpleDocTemplate(
    "docs/ADBP_System_Rules_v3.pdf",
    pagesize=letter,
    leftMargin=LM,
    rightMargin=RM,
    topMargin=TM,
    bottomMargin=BM,
    title="ADBP System Rules v3",
    author="American Dream Benefits Program",
)

story = []

# ── Header ────────────────────────────────────────────────────────────────────
story.append(Paragraph("American Dream Benefits Program | System Rules v3", title))
story.append(Paragraph("Confidential | March 2026", meta))
story.append(Paragraph("Status: Updated to reflect confirmed model mechanics", meta))
story.append(Spacer(1, 6))
story.append(hr())

# ── Introduction ──────────────────────────────────────────────────────────────
story.append(Paragraph("Introduction", h2))
story.append(
    Paragraph(
        "<b>Goal</b> Restore the American Dream — enable families to thrive on one job / one income again, "
        "without needing two incomes, debt, or constant financial pressure.",
        body,
    )
)
story.append(
    Paragraph(
        "The American Dream Benefits Program is a third-party consumer discount platform with voluntary "
        "payroll facilitation that delivers substantial purchasing power for essentials.",
        body,
    )
)
story.append(
    Paragraph(
        "<b>Core Mechanism</b> A closed-loop discount-credit system powered by Solana blockchain. "
        "Employees voluntarily purchase Discount Credits (utility tokens) with after-tax dollars.",
        body,
    )
)
story.append(
    Paragraph(
        "$1 = 1 credit = $2 in purchasing power at participating essential vendors (50% discount)",
        blockq,
    )
)
story.append(hr())

# ── Program Participants ──────────────────────────────────────────────────────
story.append(Paragraph("Program Participants", h2))
for line in [
    "<b>Vendors</b> — essential businesses (groceries, utilities, rent, gas, etc.) that participate, employ participating employees, accept & recirculate credits",
    "<b>Employers</b> — businesses that participate, employ participating employees, accept & recirculate credits",
    "<b>Employees</b> — any person working for a participating employer who voluntarily participates",
    "<b>Program</b> — operates the Solana smart contracts, treasury, and platform",
]:
    story.append(Paragraph(f"\u2022  {line}", bul))
story.append(hr())

# ── System Rules ──────────────────────────────────────────────────────────────
story.append(Paragraph("System Rules", h2))

story.append(Paragraph("Credit Purchase", h3))
for line in [
    "Employees purchase credits post-tax via embedded fiat on-ramp (bank card, ACH, Apple Pay)",
    "<b>$1.00 paid by employee = 1 credit minted = $2.00 purchasing power at vendors</b>",
    "The full <b>$1.00 purchase price flows to the treasury</b> — this is the primary funding mechanism",
    "Employees are limited to <b>5,000 credits per month</b>",
    "No general cash redemption — credits are non-redeemable for cash and stay in the closed loop",
]:
    story.append(Paragraph(f"\u2022  {line}", bul))

story.append(Paragraph("Admin Revenue Pool", h3))
for line in [
    "A <b>10% fee</b> on all credit purchases is collected as admin revenue",
    "At $1.00/credit, this equals $0.10 per credit minted",
    "This fee does <b>not</b> flow to the treasury — it is tracked and distributed separately",
    "Distribution is <b>pro-rata by recirculation share</b>: the more credits a vendor or employer recirculates within the network, the larger their share of the admin revenue pool",
]:
    story.append(Paragraph(f"\u2022  {line}", bul))
story.append(
    Paragraph(
        "<b>Why pro-rata?</b> It directly incentivizes recirculation — participants who actively move credits "
        "through the network earn proportionally more. A vendor recirculating 10% of total credits earns 10% of the admin pool.",
        blockq,
    )
)

story.append(Paragraph("Recirculation Rules", h3))
for line in [
    "Vendors decide the maximum credits they accept in a 12-month period (their recirculation %)",
    "Employers and vendors recirculate credits for any of their expenses <b>except</b> payroll and taxes — creating an accounting wash ($X foregone income offset by $X saved)",
    "The <b>recirculation-to-mint ratio is 2:1</b> — a vendor/employer that can recirculate 100,000 credits allows their employees to mint 50,000 total",
    "Credits are automatically recirculated at month-end on behalf of vendors and employers",
    "Velocity is pegged at <b>12\u00d7 per year</b>",
]:
    story.append(Paragraph(f"\u2022  {line}", bul))

story.append(Paragraph("Burn Mechanic (Discretionary)", h3))
for line in [
    "Burns are <b>manual and discretionary</b> — no automatic per-transaction burn",
    "The treasury pays <b>$2.00 per credit burned</b> (the $2 fair market value of the credit)",
    "Burns are threshold-triggered: a burn is authorized when the backing ratio (treasury_wallet / total_credits) exceeds a target threshold",
    "<b>Affordability cap:</b> post-burn backing ratio must never fall below the 50% floor",
]:
    story.append(Paragraph(f"\u2022  {line}", bul))
story.append(
    Paragraph(
        "Cap formula: max_burnable = (wallet \u2212 0.50 \u00d7 total_credits) / (2.00 \u2212 0.50)",
        code_s,
    )
)

story.append(
    Paragraph(
        f"\u2022  <b>MC-optimal strategy</b> (confirmed via 20,000-run Monte Carlo):",
        bul,
    )
)
for sub in [
    "Trigger: backing \u2265 114.6%",
    "Size: 30.2% of outstanding credits per event",
    "Cooldown: 8 months minimum between burns",
    "First eligible: month 13 (ramp-up protection)",
    "Result: 1 burn event over 10 years, 30.2% of credits destroyed, 77.7% final backing (HEALTHY)",
]:
    story.append(Paragraph(f"\u2022  {sub}", bul2))
story.append(
    Paragraph(
        "<b>Why $2/credit?</b> The credit provides $2 of purchasing power. Burning a credit extinguishes a $2 obligation. "
        "The treasury pays $2 to retire $1 of face-value liability — the difference is the amplification cost built into the burn mechanism.",
        blockq,
    )
)

story.append(Paragraph("Treasury Mechanics", h3))
story.append(
    simple_table(
        ["Flow", "Amount", "Direction"],
        [
            ["Credit purchase", "$1.00/credit", "\u2192 Treasury"],
            [
                "Interest income",
                "4% APR on wallet balance (monthly)",
                "\u2192 Treasury",
            ],
            ["Burn event", "$2.00/credit burned", "\u2190 Treasury"],
            ["Admin fee", "$0.10/credit (10%)", "\u2192 Admin pool (separate)"],
        ],
        [2.5 * inch, 2.5 * inch, 1.5 * inch],
    )
)
story.append(Spacer(1, 4))
story.append(
    Paragraph(
        "Interest timing: wallet[t] = wallet[t-1] + interest[t-1] + inflow[t]", code_s
    )
)
story.append(Paragraph("Then: interest[t] = wallet[t] \u00d7 (0.04 / 12)", code_s))

story.append(Paragraph("Solvency Thresholds", h3))
story.append(
    simple_table(
        ["Status", "Backing Ratio", "Definition"],
        [
            [
                "HEALTHY",
                "\u2265 75%",
                "Treasury holds \u2265 $0.75 per $1 of credit outstanding",
            ],
            ["WARNING", "50% \u2013 74%", "Solvent but under pressure"],
            ["FAILURE", "< 50%", "Treasury cannot cover basic obligations"],
        ],
        [1.2 * inch, 1.5 * inch, 3.8 * inch],
    )
)
story.append(Spacer(1, 4))
story.append(
    Paragraph(
        "Primary metric: backing_ratio = treasury_wallet / total_credits_outstanding",
        code_s,
    )
)
story.append(
    Paragraph(
        "Secondary metric: burn_coverage = treasury_wallet / (total_credits \u00d7 $2.00)",
        code_s,
    )
)
story.append(hr())

# ── Recirculation Flywheel ────────────────────────────────────────────────────
story.append(Paragraph("Recirculation Flywheel", h2))
for i, line in enumerate(
    [
        "Employee buys credits \u2192 smart contract mints tokens \u2192 $1/credit to treasury \u2192 $0.10/credit to escrow",
        "Employee spends at vendors \u2192 50% discount applied (2\u00d7 amplification)",
        "Vendor receives tokens \u2192 recirculates to suppliers, utilities, etc.",
        "Loop continues at 12\u00d7 annual velocity",
        "No credits exit for cash, ever",
        "Admin revenue pool distributed monthly pro-rata by recirculation share from escrow wallet",
    ],
    1,
):
    story.append(Paragraph(f"{i}.  {line}", num_bul))

# ── Essential Businesses ──────────────────────────────────────────────────────
story.append(Paragraph("Essential Businesses (Vendors)", h2))
for i, vendor in enumerate(
    [
        "Health Insurance Providers",
        "Gas Stations",
        "Grocery Stores",
        "Rental Housing",
        "Internet Service Provider",
        "Electric and Gas Utilities",
        "Water Utilities",
        "Childcare Facilities",
        "Car Service (Repairs)",
    ],
    1,
):
    story.append(Paragraph(f"{i}.  {vendor}", num_bul))
story.append(hr())

# ── Compliance ────────────────────────────────────────────────────────────────
story.append(Paragraph("Compliance & Regulatory Posture", h2))
for line in [
    "Non-custodial utility token on Solana (closed-loop discount access).",
    "No private currency risk under Stamp Payments Act (\u00a7 486) - decentralized, no centralized issuer. Credits are utility tokens in a closed-loop system, non-redeemable for cash, decentralized on Solana, and not intended as general currency. 2026 guidance on tokenized assets distinguishes utility tokens from scrip if they are platform-specific and non-convertible. The GENIUS Act (2025) for stable coins explicitly exempts non-currency digital assets, reinforcing this.",
    "No ERISA risk - third-party platform, not employer-sponsored. No welfare benefit triggers like health insurance or childcare. Vendors and employers earn a fair market value fixed admin fee for offering a discount and recirculating credits.",
    "No money transmission / CVC risk - MSB partner handles fiat entry. Per FinCEN\u2019s longstanding guidance, convertible virtual currency (CVC) is virtual currency that either has an equivalent value in real currency or acts as a substitute for it. Closed-loop systems where credits cannot exit for cash are explicitly distinguished from CVC.",
    "No private scrip risk - the Stamp Payments Act targets private currencies that compete with fiat, not closed-loop discounts. Decentralized, blockchain-based utility tokens without cash equivalence or broad circulation are generally exempt. Credits recirculate indefinitely but only for essentials among participants - no public circulation or fiat substitution outside the loop. The decentralized design (no central issuer) further reduces risk.",
    "Barter tax compliance - automated 1099-B reporting at $2 FMV per credit.",
    "Regional launch - NJ to start with regional expansion as the business grows.",
]:
    story.append(Paragraph(f"\u2022  {line}", bul))

# ── Bottom Line ───────────────────────────────────────────────────────────────
story.append(Paragraph("Bottom Line", h2))
story.append(
    Paragraph(
        "One job. One family. One future. A win-win system that can turn a $60,000 salary into a potential "
        "$120,000 of essential purchasing power while financially incentivizing the vendor or employer - "
        "powered by Solana blockchain, modern UX, and built-in compliance.",
        body,
    )
)
story.append(Paragraph("Ready to launch regionally and scale responsibly.", body))

story.append(Spacer(1, 0.3 * inch))
story.append(hr())
story.append(
    Paragraph(
        "American Dream Benefits Program  |  Confidential \u2014 Attorney Review Copy  |  March 2026",
        footer_s,
    )
)

doc.build(story)
print("PDF written: docs/ADBP_System_Rules_v3.pdf")
