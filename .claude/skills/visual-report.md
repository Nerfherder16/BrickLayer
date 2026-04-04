---
name: visual-report
description: Generate a self-contained HTML synthesis report from BrickLayer findings/synthesis.md — verdict badges, confidence indicators, domain sections, and recommendations
user-invocable: true
---

# /visual-report — HTML Synthesis Report Generator

Converts BrickLayer synthesis.md into a navigable HTML report with verdict badges, confidence indicators, and visual hierarchy.

## Trigger

`/visual-report [path/to/synthesis.md]`

If no path given, looks for `findings/synthesis.md` in current directory.

## What It Does

1. **Reads synthesis.md** — extracts title, summary, findings table, domain sections, recommendations
2. **Generates HTML report** at `reports/synthesis-report.html`
3. Prints path to open it

## Output Structure (10 sections)

1. **Executive Summary** — project name, total questions, overall verdict badge (HEALTHY/AT_RISK/CRITICAL), key metrics
2. **Fact Sheet** — tabular summary, color-coded by severity (CRITICAL red / WARNING amber / PASS green), sortable columns
3. **Decision Confidence Tiers** — HIGH (≥80%), MODERATE (60-79%), LOW (<60%) grouped findings
4. **Domain Sections 4-8** — one per research domain, each finding: question → verdict badge → evidence → confidence bar
5. **Section 9 — Failure Boundaries** — visual table showing where the system breaks
6. **Section 10 — Recommendations** — prioritized action list with effort/impact

## HTML Design

- Dark purple-black background (`#0f0d1a`)
- Space Grotesk font (Google Fonts CDN)
- Verdict badges: green PASS / amber WARNING / red CRITICAL / gray UNCERTAIN
- Confidence bars: filled accent-colored bar proportional to value
- Responsive single-column, print-friendly
- Sticky sidebar with section jump links

## Implementation

```python
synthesis = read_file(path)
sections = parse_synthesis_markdown(synthesis)
html = render_html_report(sections)
write_file("reports/synthesis-report.html", html)
print("Report: reports/synthesis-report.html")
```

## Notes
- Self-contained HTML (no external JS — only Google Fonts CDN)
- All charts rendered as inline SVG
- Print-optimized: `@media print` removes sidebar, expands all sections
