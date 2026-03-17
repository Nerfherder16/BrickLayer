"""
analyze.py — End-of-run analysis report generator.

Reads results.tsv and findings/*.md, then produces a comprehensive PDF report
including executive summary, failure boundary map, per-domain findings,
best-way-forward recommendations, and raw data appendix.

Customize the REPORT_CONFIG section for your project before running.

Usage:
    python analyze.py
    python analyze.py --output reports/analysis_v1.pdf
"""

import argparse
import csv
import re
import sys
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# =============================================================================
# REPORT CONFIG — Customize for your project
# =============================================================================

PROJECT_NAME = "My Project"  # Replace with your project name
PRIMARY_METRIC_LABEL = "Primary Metric"  # e.g., "Treasury Runway (mo)"

DOMAIN_MAP = {
    "1": "Domain 1 — Model Integrity",
    "2": "Domain 2 — Regulatory & Legal",
    "3": "Domain 3 — Economic & Competitive",
    "4": "Domain 4 — Technical Risk",
    "5": "Domain 5 — Transition Risk",
    "6": "Domain 6 — Adversarial & Stress",
}

# =============================================================================
# ENGINE — No modifications needed below
# =============================================================================

BASE_DIR = Path(__file__).parent
RESULTS_TSV = BASE_DIR / "results.tsv"
FINDINGS_DIR = BASE_DIR / "findings"
REPORTS_DIR = BASE_DIR / "reports"

RED = colors.HexColor("#C0392B")
ORANGE = colors.HexColor("#E67E22")
GREEN = colors.HexColor("#27AE60")
BLUE = colors.HexColor("#2980B9")
DARK = colors.HexColor("#1A1A2E")
LIGHT_GRAY = colors.HexColor("#F4F6F9")
MID_GRAY = colors.HexColor("#BDC3C7")
WHITE = colors.white

VERDICT_COLOR = {
    "FAILURE": RED,
    "WARNING": ORANGE,
    "HEALTHY": GREEN,
    "INCONCLUSIVE": BLUE,
}
SEVERITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Info": 4}


def parse_results_tsv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def parse_finding(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    f = {
        "id": path.stem,
        "title": "",
        "question": "",
        "verdict": "",
        "severity": "",
        "evidence": "",
        "mitigation": "",
    }

    m = re.search(r"^# Finding: (.+)$", text, re.MULTILINE)
    if m:
        f["title"] = m.group(1).strip()

    m = re.search(r"\*\*Question\*\*:\s*(.+?)(?=\n\n|\*\*)", text, re.DOTALL)
    if m:
        f["question"] = m.group(1).strip()

    m = re.search(r"\*\*Verdict\*\*:\s*(.+)", text)
    if m:
        f["verdict"] = m.group(1).strip()

    m = re.search(r"\*\*Severity\*\*:\s*(.+)", text)
    if m:
        raw = m.group(1).strip()
        f["severity"] = next(
            (s for s in SEVERITY_ORDER if raw.startswith(s)),
            raw.split()[0] if raw else "Info",
        )

    m = re.search(r"## Evidence(.+?)(?=## |\Z)", text, re.DOTALL)
    if m:
        f["evidence"] = m.group(1).strip()[:600]

    m = re.search(r"## Mitigation Recommendation(.+?)(?=## |\Z)", text, re.DOTALL)
    if m:
        f["mitigation"] = m.group(1).strip()[:800]

    return f


def domain_of(qid: str) -> str:
    if not qid or qid == "N/A":
        return "Unknown"
    return DOMAIN_MAP.get(qid.split(".")[0], f"Domain {qid.split('.')[0]}")


def make_styles() -> dict:
    return {
        "cover_title": ParagraphStyle(
            "cover_title",
            fontSize=26,
            leading=32,
            textColor=DARK,
            fontName="Helvetica-Bold",
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub",
            fontSize=13,
            textColor=colors.HexColor("#555555"),
            fontName="Helvetica",
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "cover_date": ParagraphStyle(
            "cover_date",
            fontSize=10,
            textColor=MID_GRAY,
            fontName="Helvetica",
            alignment=TA_CENTER,
        ),
        "h1": ParagraphStyle(
            "h1",
            fontSize=17,
            leading=21,
            textColor=DARK,
            fontName="Helvetica-Bold",
            spaceBefore=14,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2",
            fontSize=13,
            leading=17,
            textColor=DARK,
            fontName="Helvetica-Bold",
            spaceBefore=10,
            spaceAfter=5,
        ),
        "h3": ParagraphStyle(
            "h3",
            fontSize=10,
            leading=13,
            textColor=DARK,
            fontName="Helvetica-Bold",
            spaceBefore=6,
            spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "body",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#333333"),
            fontName="Helvetica",
            spaceAfter=4,
        ),
        "small": ParagraphStyle(
            "small",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#666666"),
            fontName="Helvetica",
            spaceAfter=2,
        ),
        "label": ParagraphStyle(
            "label",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#888888"),
            fontName="Helvetica-Oblique",
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#333333"),
            fontName="Helvetica",
            leftIndent=14,
            spaceAfter=2,
        ),
    }


def section_header(styles, title: str) -> list:
    return [
        Paragraph(title, styles["h1"]),
        HRFlowable(width="100%", thickness=1, color=MID_GRAY),
        Spacer(1, 0.1 * inch),
    ]


def build_cover(styles, run_date: str) -> list:
    elems = [Spacer(1, 2 * inch)]
    elems.append(Paragraph("Autoresearch Report", styles["cover_title"]))
    elems.append(Paragraph(f"Project: {PROJECT_NAME}", styles["cover_sub"]))
    elems.append(Spacer(1, 0.2 * inch))
    elems.append(HRFlowable(width="80%", thickness=2, color=DARK, hAlign="CENTER"))
    elems.append(Spacer(1, 0.2 * inch))
    elems.append(Paragraph(f"Generated: {run_date}", styles["cover_date"]))
    elems.append(
        Paragraph(
            "Autonomous simulation research -- failure boundary mapping",
            styles["cover_date"],
        )
    )
    elems.append(PageBreak())
    return elems


def build_summary(styles, results: list[dict], findings: list[dict]) -> list:
    elems = section_header(styles, "Executive Summary")
    verdicts = [r.get("verdict", "") for r in results]
    sev_counts: dict[str, int] = {}
    for f in findings:
        sev = f["severity"] or "Info"
        sev_counts[sev] = sev_counts.get(sev, 0) + 1

    elems.append(
        Paragraph(
            f"This report covers <b>{len(results)}</b> research scenarios across {len(DOMAIN_MAP)} domains. "
            "The autoresearch loop ran simulations and qualitative analysis to map system failure boundaries.",
            styles["body"],
        )
    )
    elems.append(Spacer(1, 0.1 * inch))

    stats = [
        ["Verdict", "Count", "Interpretation"],
        [
            "FAILURE",
            str(verdicts.count("FAILURE")),
            "System collapses — requires architecture change",
        ],
        [
            "WARNING",
            str(verdicts.count("WARNING")),
            "Degraded but surviving — mitigation required",
        ],
        ["HEALTHY", str(verdicts.count("HEALTHY")), "System behaves as expected"],
        [
            "INCONCLUSIVE",
            str(verdicts.count("INCONCLUSIVE")),
            "Insufficient evidence — needs external validation",
        ],
    ]
    t = Table(stats, colWidths=[1.1 * inch, 0.65 * inch, 4.25 * inch])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
                ("BACKGROUND", (0, 1), (0, 1), colors.HexColor("#FADBD8")),
                ("BACKGROUND", (0, 2), (0, 2), colors.HexColor("#FDEBD0")),
                ("BACKGROUND", (0, 3), (0, 3), colors.HexColor("#D5F5E3")),
                ("BACKGROUND", (0, 4), (0, 4), colors.HexColor("#D6EAF8")),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, MID_GRAY),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elems.append(t)
    elems.append(Spacer(1, 0.1 * inch))

    if sev_counts:
        elems.append(Paragraph("Findings by Severity:", styles["h3"]))
        for sev in ["Critical", "High", "Medium", "Low", "Info"]:
            cnt = sev_counts.get(sev, 0)
            if cnt:
                elems.append(
                    Paragraph(f"* <b>{sev}</b>: {cnt} finding(s)", styles["bullet"])
                )

    critical_high = sorted(
        [f for f in findings if f["severity"] in ("Critical", "High")],
        key=lambda x: SEVERITY_ORDER.get(x["severity"], 99),
    )
    if critical_high:
        elems.append(Spacer(1, 0.08 * inch))
        elems.append(Paragraph("Critical & High Severity Findings:", styles["h3"]))
        for f in critical_high[:8]:
            elems.append(
                Paragraph(
                    f"* <b>[{f['id']}] {f['severity']}</b>: {f['title']}",
                    styles["bullet"],
                )
            )

    elems.append(PageBreak())
    return elems


def build_boundary_map(styles, results: list[dict]) -> list:
    elems = section_header(styles, "Failure Boundary Map")
    elems.append(
        Paragraph(
            "All WARNING and FAILURE scenarios. These are the boundaries where the system degrades or collapses.",
            styles["body"],
        )
    )
    elems.append(Spacer(1, 0.1 * inch))

    stressed = [r for r in results if r.get("verdict") in ("FAILURE", "WARNING")]
    if not stressed:
        elems.append(
            Paragraph("No FAILURE or WARNING scenarios recorded.", styles["body"])
        )
        elems.append(PageBreak())
        return elems

    table_data = [["ID", "Verdict", "Domain", PRIMARY_METRIC_LABEL, "Key Finding"]]
    for r in stressed:
        qid = r.get("question_id", "")
        dom = domain_of(qid).split("--")[-1].strip()[:20]
        finding = r.get("key_finding", "")
        if len(finding) > 75:
            finding = finding[:75] + "..."
        table_data.append(
            [qid, r.get("verdict", ""), dom, r.get("primary_metric", "N/A"), finding]
        )

    t = Table(
        table_data,
        colWidths=[0.45 * inch, 0.75 * inch, 1.4 * inch, 0.8 * inch, 3.05 * inch],
        repeatRows=1,
    )
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.5, MID_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]
    for i, row in enumerate(table_data[1:], 1):
        c = VERDICT_COLOR.get(row[1], MID_GRAY)
        style_cmds += [
            ("BACKGROUND", (1, i), (1, i), c),
            ("TEXTCOLOR", (1, i), (1, i), WHITE),
            ("FONTNAME", (1, i), (1, i), "Helvetica-Bold"),
        ]
    t.setStyle(TableStyle(style_cmds))
    elems.append(t)
    elems.append(PageBreak())
    return elems


def build_domain_findings(styles, findings: list[dict]) -> list:
    elems = section_header(styles, "Per-Domain Findings")
    by_domain: dict[str, list[dict]] = {}
    for f in findings:
        by_domain.setdefault(domain_of(f["id"]), []).append(f)

    for dom in sorted(by_domain.keys()):
        elems.append(Paragraph(dom, styles["h2"]))
        elems.append(HRFlowable(width="100%", thickness=0.5, color=MID_GRAY))
        elems.append(Spacer(1, 0.05 * inch))

        for f in sorted(by_domain[dom], key=lambda x: x["id"]):
            verdict_parts = f["verdict"].split()
            verdict_word = verdict_parts[0] if verdict_parts else "INFO"
            vc = VERDICT_COLOR.get(verdict_word, BLUE)
            elems.append(
                Paragraph(
                    f'<font color="#{vc.hexval()[2:]}"><b>[{verdict_word}]</b></font> '
                    f"<b>{f['id']}</b> -- {f['title']}",
                    styles["h3"],
                )
            )
            if f["question"]:
                elems.append(
                    Paragraph(f"<i>Q: {f['question'][:180]}</i>", styles["label"])
                )
            elems.append(
                Paragraph(
                    f"Severity: <b>{f['severity'] or 'Info'}</b>", styles["small"]
                )
            )

            if f["evidence"]:
                for ln in [x for x in f["evidence"].split("\n") if x.strip()][:4]:
                    clean = re.sub(r"[*`#]", "", ln).strip()
                    if clean:
                        elems.append(Paragraph(clean, styles["small"]))

            if f["mitigation"]:
                elems.append(Paragraph("<b>Mitigation:</b>", styles["body"]))
                for ln in [
                    x.strip()
                    for x in f["mitigation"].split("\n")
                    if x.strip().startswith(("1.", "2.", "3.", "-", "*"))
                ][:2]:
                    clean = re.sub(r"[*`]", "", ln).strip()
                    if clean:
                        elems.append(Paragraph(f"  {clean}", styles["bullet"]))

            elems.append(Spacer(1, 0.07 * inch))
        elems.append(Spacer(1, 0.08 * inch))

    elems.append(PageBreak())
    return elems


def build_best_way_forward(styles, findings: list[dict]) -> list:
    elems = section_header(styles, "Best Way Forward")
    elems.append(
        Paragraph(
            "Consolidated recommendations from Critical and High severity findings. "
            "These represent the minimum changes to make the system resilient.",
            styles["body"],
        )
    )
    elems.append(Spacer(1, 0.1 * inch))

    priority = sorted(
        [f for f in findings if f["severity"] in ("Critical", "High")],
        key=lambda x: (SEVERITY_ORDER.get(x["severity"], 99), x["id"]),
    )

    if not priority:
        elems.append(
            Paragraph(
                "No Critical or High severity findings. System appears resilient.",
                styles["body"],
            )
        )
    else:
        elems.append(
            Paragraph(
                f"<b>{len(priority)} Critical/High findings requiring action:</b>",
                styles["body"],
            )
        )
        elems.append(Spacer(1, 0.05 * inch))
        for i, f in enumerate(priority, 1):
            sev_color = RED if f["severity"] == "Critical" else ORANGE
            elems.append(
                Paragraph(
                    f'<font color="#{sev_color.hexval()[2:]}">&#9632;</font> '
                    f"<b>{i}. [{f['severity']}] {f['id']}</b>: {f['title']}",
                    styles["h3"],
                )
            )
            if f["mitigation"]:
                bullets = [
                    x.strip()
                    for x in f["mitigation"].split("\n")
                    if x.strip().startswith(("1.", "2.", "3.", "-", "*"))
                ][:2]
                for b in bullets:
                    clean = re.sub(r"[*`]", "", b).strip()
                    if clean:
                        elems.append(Paragraph(f"  {clean}", styles["bullet"]))
            elems.append(Spacer(1, 0.06 * inch))

    medium = [f for f in findings if f["severity"] == "Medium"]
    if medium:
        elems.append(Spacer(1, 0.08 * inch))
        elems.append(Paragraph("Monitor (Medium Severity):", styles["h2"]))
        for f in medium:
            elems.append(
                Paragraph(f"* <b>{f['id']}</b>: {f['title']}", styles["bullet"])
            )

    elems.append(PageBreak())
    return elems


def build_raw_data(styles, results: list[dict]) -> list:
    elems = section_header(styles, "Raw Data Appendix")
    table_data = [["Commit", "ID", "Verdict", PRIMARY_METRIC_LABEL, "Scenario"]]
    for r in results:
        commit = (r.get("commit") or "N/A")[:7]
        scenario = r.get("scenario_name", "")[:45]
        table_data.append(
            [
                commit,
                r.get("question_id", ""),
                r.get("verdict", ""),
                r.get("primary_metric", "N/A"),
                scenario,
            ]
        )

    t = Table(
        table_data,
        colWidths=[0.6 * inch, 0.5 * inch, 0.75 * inch, 0.75 * inch, 3.85 * inch],
        repeatRows=1,
    )
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.5, MID_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]
    for i, row in enumerate(table_data[1:], 1):
        c = VERDICT_COLOR.get(row[2], MID_GRAY)
        style_cmds += [
            ("BACKGROUND", (2, i), (2, i), c),
            ("TEXTCOLOR", (2, i), (2, i), WHITE),
            ("FONTNAME", (2, i), (2, i), "Helvetica-Bold"),
        ]
    t.setStyle(TableStyle(style_cmds))
    elems.append(t)
    return elems


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate autoresearch PDF report")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    REPORTS_DIR.mkdir(exist_ok=True)
    run_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    out_path = args.output or str(
        REPORTS_DIR / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    )

    if not RESULTS_TSV.exists():
        print("ERROR: results.tsv not found.", file=sys.stderr)
        sys.exit(1)

    results = parse_results_tsv(RESULTS_TSV)
    findings = (
        [parse_finding(md) for md in sorted(FINDINGS_DIR.glob("*.md"))]
        if FINDINGS_DIR.exists()
        else []
    )
    print(f"{len(results)} results, {len(findings)} findings -> {out_path}")

    styles = make_styles()
    doc = SimpleDocTemplate(
        out_path,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    story = (
        build_cover(styles, run_date)
        + build_summary(styles, results, findings)
        + build_boundary_map(styles, results)
        + build_domain_findings(styles, findings)
        + build_best_way_forward(styles, findings)
        + build_raw_data(styles, results)
    )
    doc.build(story)
    print(f"Done. Report saved to: {out_path}")


if __name__ == "__main__":
    main()
