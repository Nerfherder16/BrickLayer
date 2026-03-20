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

doc = SimpleDocTemplate(
    "docs/ADBP_System_Rules_v3.pdf",
    pagesize=letter,
    rightMargin=0.85 * inch,
    leftMargin=0.85 * inch,
    topMargin=0.9 * inch,
    bottomMargin=0.9 * inch,
    title="ADBP System Rules v3",
    author="American Dream Benefits Program",
)

NAVY = colors.HexColor("#1a2744")
BLUE = colors.HexColor("#2c4a8c")
ACCENT = colors.HexColor("#c8a84b")
LIGHT = colors.HexColor("#f0f4fa")
RULE = colors.HexColor("#d0d8e8")
WHITE = colors.white
BLACK = colors.HexColor("#1a1a1a")
MUTED = colors.HexColor("#555555")
REMOVED_C = colors.HexColor("#cc3333")
ADDED_C = colors.HexColor("#1a7a3a")


def S(name, **kw):
    return ParagraphStyle(name, **kw)


cover_title = S(
    "CT",
    fontSize=26,
    fontName="Helvetica-Bold",
    textColor=WHITE,
    alignment=TA_CENTER,
    leading=32,
)
cover_sub = S(
    "CS",
    fontSize=12,
    fontName="Helvetica",
    textColor=ACCENT,
    alignment=TA_CENTER,
    spaceAfter=4,
)
cover_meta = S(
    "CM",
    fontSize=9,
    fontName="Helvetica",
    textColor=colors.HexColor("#aabbdd"),
    alignment=TA_CENTER,
)
h1 = S(
    "H1",
    fontSize=15,
    fontName="Helvetica-Bold",
    textColor=WHITE,
    spaceBefore=2,
    spaceAfter=2,
    leading=18,
)
h2 = S(
    "H2",
    fontSize=11,
    fontName="Helvetica-Bold",
    textColor=NAVY,
    spaceBefore=14,
    spaceAfter=4,
    leading=14,
)
h3 = S(
    "H3",
    fontSize=10,
    fontName="Helvetica-Bold",
    textColor=BLUE,
    spaceBefore=10,
    spaceAfter=3,
    leading=13,
)
body = S(
    "Body",
    fontSize=9,
    fontName="Helvetica",
    textColor=BLACK,
    leading=14,
    spaceAfter=3,
    alignment=TA_JUSTIFY,
)
bullet = S(
    "Bul",
    fontSize=9,
    fontName="Helvetica",
    textColor=BLACK,
    leading=13,
    spaceAfter=2,
    leftIndent=14,
    bulletIndent=4,
)
note = S(
    "Note",
    fontSize=8.5,
    fontName="Helvetica-Oblique",
    textColor=MUTED,
    leading=12,
    spaceAfter=4,
    leftIndent=14,
)
code = S(
    "Code",
    fontSize=8,
    fontName="Courier",
    textColor=BLUE,
    leading=12,
    spaceAfter=3,
    leftIndent=14,
)
footer_s = S(
    "Ftr", fontSize=7.5, fontName="Helvetica", textColor=MUTED, alignment=TA_CENTER
)


def band(text, style):
    return Table(
        [[Paragraph(text, style)]],
        colWidths=[6.3 * inch],
        style=TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("TOPPADDING", (0, 0), (-1, -1), 14),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
                ("LEFTPADDING", (0, 0), (-1, -1), 20),
                ("RIGHTPADDING", (0, 0), (-1, -1), 20),
            ]
        ),
    )


def sec(text):
    return Table(
        [[Paragraph(text, h1)]],
        colWidths=[6.3 * inch],
        style=TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        ),
    )


def callout(text):
    return Table(
        [[Paragraph(text, note)]],
        colWidths=[6.3 * inch],
        style=TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LINEAFTER", (0, 0), (0, -1), 3, ACCENT),
            ]
        ),
    )


def tbl(headers, rows, widths=None):
    hstyle = S(
        "th", fontSize=8.5, fontName="Helvetica-Bold", textColor=WHITE, leading=11
    )
    dstyle = S("td", fontSize=8.5, fontName="Helvetica", textColor=BLACK, leading=12)
    if widths is None:
        w = 6.3 * inch / len(headers)
        widths = [w] * len(headers)
    data = [[Paragraph(str(c), hstyle) for c in headers]]
    for row in rows:
        data.append([Paragraph(str(c), dstyle) for c in row])
    t = Table(data, colWidths=widths)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
                ("GRID", (0, 0), (-1, -1), 0.4, RULE),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return t


story = []

# Cover
story += [
    Spacer(1, 0.5 * inch),
    band("AMERICAN DREAM BENEFITS PROGRAM", cover_title),
    Spacer(1, 6),
    band("System Rules \u2014 Version 3", cover_sub),
    band("Confidential  |  March 2026  |  Updated model mechanics", cover_meta),
    Spacer(1, 0.3 * inch),
    callout(
        "<b>Summary of changes from v1/v2:</b> Treasury now funded by full $1.00/credit (was $0.50). "
        "Admin fee is 10% pool distributed pro-rata by recirculation share (was flat $0.50 each to vendor + employer). "
        "1.774% per-transaction automatic burn removed. "
        "Discretionary threshold-triggered burns introduced at $2.00/credit with affordability cap."
    ),
    Spacer(1, 0.15 * inch),
]

# Introduction
story += [
    sec("Introduction"),
    Spacer(1, 6),
    Paragraph(
        "<b>Goal:</b> Restore the American Dream \u2014 enable families to thrive on one job / one income again, "
        "without needing two incomes, debt, or constant financial pressure.",
        body,
    ),
    Paragraph(
        "The American Dream Benefits Program is a third-party consumer discount platform with voluntary "
        "payroll facilitation that delivers substantial purchasing power for essentials.",
        body,
    ),
    Spacer(1, 6),
    callout(
        "<b>Core Mechanism:</b> A closed-loop discount-credit system powered by Solana blockchain. "
        "Employees voluntarily purchase Discount Credits (utility tokens) with after-tax dollars.<br/>"
        "<b>$1 = 1 credit = $2 purchasing power at participating essential vendors (50% discount)</b>"
    ),
    Spacer(1, 8),
]

# Participants
story += [
    Paragraph("Program Participants", h2),
    tbl(
        ["Participant", "Role"],
        [
            [
                "Vendors",
                "Essential businesses (groceries, utilities, rent, gas, etc.) that participate, accept & recirculate credits",
            ],
            [
                "Employers",
                "Businesses that participate, employ participating employees, accept & recirculate credits",
            ],
            [
                "Employees",
                "Any person working for a participating employer who voluntarily participates",
            ],
            ["Program", "Operates the Solana smart contracts, treasury, and platform"],
        ],
        [1.5 * inch, 4.8 * inch],
    ),
    Spacer(1, 10),
]

# System Rules
story += [sec("System Rules"), Spacer(1, 6)]

story.append(Paragraph("Credit Purchase", h3))
for b in [
    "$1.00 paid by employee = 1 credit minted = $2.00 purchasing power at vendors (50% discount)",
    "The full <b>$1.00 purchase price flows to the treasury</b> \u2014 this is the primary funding mechanism",
    "Employees are limited to <b>5,000 credits per month</b>",
    "No general cash redemption \u2014 credits are non-redeemable for cash and stay in the closed loop",
    "Fiat on-ramp via embedded bank card, ACH, or Apple Pay (MSB partner handles KYC/AML/MTL)",
]:
    story.append(Paragraph(f"\u2022 {b}", bullet))

story.append(Paragraph("Admin Revenue Pool", h3))
for b in [
    "A <b>10% fee</b> on all credit purchases is collected as admin revenue ($0.10 per credit at $1.00/credit)",
    "This fee does <b>not</b> flow to the treasury \u2014 it is held in escrow and distributed separately",
    "Distribution is <b>pro-rata by recirculation share</b>: the more credits a vendor or employer recirculates, the larger their share",
    "Pool is distributed monthly from the escrow wallet",
]:
    story.append(Paragraph(f"\u2022 {b}", bullet))
story.append(
    callout(
        "<b>Why pro-rata?</b> It directly incentivizes recirculation \u2014 participants who actively move credits "
        "through the network earn proportionally more. A vendor recirculating 10% of total credits earns 10% of the admin pool."
    )
)

story.append(Paragraph("Recirculation Rules", h3))
for b in [
    "Vendors decide the maximum credits they accept in a 12-month period (their recirculation %)",
    "Employers and vendors recirculate credits for any expenses <b>except payroll and taxes</b> \u2014 creating an accounting wash",
    "The <b>recirculation-to-mint ratio is 2:1</b> \u2014 a vendor/employer that can recirculate 100,000 credits allows their employees to mint 50,000 total",
    "Credits are automatically recirculated at month-end on behalf of vendors and employers",
    "Velocity is pegged at <b>12\u00d7 per year</b>",
]:
    story.append(Paragraph(f"\u2022 {b}", bullet))

story.append(Paragraph("Burn Mechanic (Discretionary)", h3))
for b in [
    "Burns are <b>manual and discretionary</b> \u2014 no automatic per-transaction burn",
    "The treasury pays <b>$2.00 per credit burned</b> (the $2 fair market value of the credit)",
    "Burns are threshold-triggered: authorized when the backing ratio (treasury_wallet / total_credits) exceeds a target",
    "<b>Affordability cap:</b> post-burn backing ratio must never fall below the 50% floor",
]:
    story.append(Paragraph(f"\u2022 {b}", bullet))
story.append(
    Paragraph(
        "  Cap formula: max_burnable = (wallet - 0.50 x total_credits) / (2.00 - 0.50)",
        code,
    )
)
story.append(
    callout(
        "<b>MC-optimal burn strategy</b> (confirmed via 20,000-run Monte Carlo):<br/>"
        "Trigger: backing >= 114.6%  |  Size: 30.2% of outstanding credits  |  "
        "Cooldown: 8 months min  |  First eligible: month 13<br/>"
        "Result: 1 burn over 10 years, 30.2% of credits destroyed, 77.7% final backing \u2014 HEALTHY"
    )
)
story.append(
    callout(
        "<b>Why $2/credit?</b> The credit provides $2 of purchasing power. Burning extinguishes a $2 obligation. "
        "The treasury pays $2 to retire $1 of face-value liability \u2014 the amplification cost built into the burn mechanism."
    )
)
story.append(Spacer(1, 4))

story.append(Paragraph("Treasury Mechanics", h3))
story.append(
    tbl(
        ["Cash Flow", "Amount", "Direction"],
        [
            ["Credit purchase", "$1.00 / credit", "-> Treasury"],
            ["Admin fee (10%)", "$0.10 / credit", "-> Escrow (separate)"],
            ["Interest income", "4% APR on wallet balance (monthly)", "-> Treasury"],
            ["Burn event", "$2.00 / credit burned", "<- Treasury (outflow)"],
        ],
        [2.3 * inch, 2.5 * inch, 1.5 * inch],
    )
)
story.append(Spacer(1, 4))
story.append(
    Paragraph(
        "Interest timing:  wallet[t] = wallet[t-1] + interest[t-1] + inflow[t]   then   "
        "interest[t] = wallet[t] x (0.04 / 12)",
        code,
    )
)

story.append(Paragraph("Solvency Thresholds", h3))
story.append(
    tbl(
        ["Status", "Backing Ratio", "Definition"],
        [
            [
                "HEALTHY",
                ">= 75%",
                "Treasury holds >= $0.75 per $1 of credit outstanding",
            ],
            [
                "WARNING",
                "50% - 74%",
                "Solvent but under pressure \u2014 monitor closely",
            ],
            ["FAILURE", "< 50%", "Treasury cannot cover basic obligations"],
        ],
        [1.2 * inch, 1.5 * inch, 3.6 * inch],
    )
)
story.append(Spacer(1, 4))
story.append(
    Paragraph(
        "Primary: backing_ratio = treasury_wallet / total_credits_outstanding", code
    )
)
story.append(
    Paragraph(
        "Secondary: burn_coverage = treasury_wallet / (total_credits x $2.00)", code
    )
)
story.append(Spacer(1, 10))

# Essential Vendors
story += [
    sec("Essential Vendors"),
    Spacer(1, 6),
    tbl(
        ["#", "Business Type"],
        [
            ["1", "Health Insurance Providers"],
            ["2", "Gas Stations"],
            ["3", "Grocery Stores"],
            ["4", "Rental Housing"],
            ["5", "Internet Service Providers"],
            ["6", "Electric & Gas Utilities"],
            ["7", "Water Utilities"],
            ["8", "Childcare Facilities"],
            ["9", "Car Service (Repairs)"],
        ],
        [0.5 * inch, 5.8 * inch],
    ),
    Spacer(1, 10),
]

# Flywheel
story += [
    sec("Recirculation Flywheel"),
    Spacer(1, 6),
    tbl(
        ["Step", "Event", "Detail"],
        [
            [
                "1",
                "Employee buys credits",
                "Smart contract mints tokens -> $1.00/credit to treasury -> $0.10/credit to escrow",
            ],
            [
                "2",
                "Employee spends at vendor",
                "50% discount applied (2x amplification)",
            ],
            [
                "3",
                "Vendor receives tokens",
                "Recirculates to suppliers, utilities, etc.",
            ],
            [
                "4",
                "Loop continues",
                "12x annual velocity \u2014 no credits exit for cash, ever",
            ],
            [
                "5",
                "Month-end settlement",
                "Admin pool distributed pro-rata by recirculation share from escrow",
            ],
        ],
        [0.4 * inch, 1.8 * inch, 4.1 * inch],
    ),
    Spacer(1, 10),
]

# Market scale
story += [
    sec("Market Scale Estimates (2025)"),
    Spacer(1, 6),
    tbl(
        ["Business Type", "Annual Revenue", "Recirc %", "Capacity"],
        [
            ["Multifamily Housing", "$600B", "23%", "$138.0B"],
            ["Food Store (Grocery)", "$1,600B", "86%", "$1,376.0B"],
            ["Electric & Gas Utility", "$550B", "64%", "$352.0B"],
            ["Water Utility", "$72.5B", "57%", "$41.3B"],
            ["Internet Service", "$437B", "45%", "$196.7B"],
            ["Gas Station", "$700B", "94%", "$658.0B"],
            ["Car Service Center", "$199B", "65%", "$129.4B"],
            ["TOTAL", "$4.16T", "\u2014", "$2.90T"],
        ],
        [2.5 * inch, 1.4 * inch, 0.9 * inch, 1.5 * inch],
    ),
    Spacer(1, 4),
    Paragraph(
        "Hard ceiling: $2.9T amplified annual employee purchase capacity. "
        "Realistic scale: several million families.",
        body,
    ),
    Spacer(1, 10),
]

# What changed
story += [sec("What Changed from Prior Version"), Spacer(1, 6)]

chg_hstyle = S(
    "ch", fontSize=8.5, fontName="Helvetica-Bold", textColor=WHITE, leading=11
)
chg_dstyle = S("cd", fontSize=8.5, fontName="Helvetica", textColor=BLACK, leading=12)
rem_style = S(
    "cr", fontSize=8.5, fontName="Helvetica-Bold", textColor=REMOVED_C, leading=12
)
add_style = S(
    "ca", fontSize=8.5, fontName="Helvetica-Bold", textColor=ADDED_C, leading=12
)

changes_data = [
    [Paragraph(c, chg_hstyle) for c in ["Prior Rule", "Status", "Replacement"]]
] + [
    [
        Paragraph(row[0], chg_dstyle),
        Paragraph(row[1], rem_style if row[1] == "REMOVED" else add_style),
        Paragraph(row[2], chg_dstyle),
    ]
    for row in [
        [
            "$0.50 treasury fee per credit",
            "REMOVED",
            "$1.00/credit \u2014 full purchase price to treasury",
        ],
        [
            "$0.50 flat admin fee to vendor",
            "REMOVED",
            "10% pool, pro-rata distribution",
        ],
        [
            "$0.50 flat admin fee to employer",
            "REMOVED",
            "Included in same 10% pool above",
        ],
        [
            "1.774% per-transaction automatic burn",
            "REMOVED",
            "No automatic burns \u2014 discretionary only",
        ],
        [
            "No burn mechanic defined",
            "ADDED",
            "Discretionary, $2.00/credit, threshold-triggered, affordability-capped",
        ],
    ]
]
ct = Table(changes_data, colWidths=[2.4 * inch, 0.85 * inch, 3.05 * inch])
ct.setStyle(
    TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
            ("GRID", (0, 0), (-1, -1), 0.4, RULE),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
    )
)
story += [ct, Spacer(1, 10)]

# Compliance
story += [
    sec("Compliance & Regulatory Posture"),
    Spacer(1, 6),
    tbl(
        ["Risk Area", "Posture"],
        [
            [
                "No private currency risk",
                "Non-custodial utility token on Solana. Decentralized, non-redeemable for cash. 2026 tokenized-asset guidance and GENIUS Act (2025) reinforce exemption under Stamp Payments Act S 486.",
            ],
            [
                "No ERISA risk",
                "Third-party platform, not employer-sponsored. Vendor/employer admin revenue is compensation for recirculation participation, not a welfare benefit.",
            ],
            [
                "No money transmission / CVC",
                "MSB partner handles fiat entry. Closed-loop, non-cash-convertible credits are explicitly distinguished from convertible virtual currency per FinCEN guidance.",
            ],
            [
                "No private scrip risk",
                "Decentralized design, no public circulation, no fiat substitution outside the closed loop.",
            ],
            [
                "Barter tax compliance",
                "Automated 1099-B reporting at $2 FMV per credit.",
            ],
            [
                "Regional launch",
                "New Jersey to start, with regional expansion as the business grows.",
            ],
        ],
        [2.0 * inch, 4.3 * inch],
    ),
    Spacer(1, 12),
]

# Bottom line
story += [
    callout(
        "<b>One job. One family. One future.</b><br/>"
        "A win-win system that can turn a $60,000 salary into a potential $120,000 of essential purchasing power "
        "while financially incentivizing participating vendors and employers through pro-rata recirculation rewards \u2014 "
        "powered by Solana blockchain, modern UX, and built-in compliance. "
        "Ready to launch regionally and scale responsibly."
    ),
    Spacer(1, 0.2 * inch),
    HRFlowable(width="100%", thickness=0.5, color=RULE),
    Spacer(1, 4),
    Paragraph(
        "ADBP System Rules v3  |  Confidential \u2014 Attorney Review Copy  |  March 2026  |  "
        "This document supersedes all prior versions.",
        footer_s,
    ),
]

doc.build(story)
print("PDF written: docs/ADBP_System_Rules_v3.pdf")
