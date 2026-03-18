"""
bl/synthesizer.py — Campaign synthesizer.

Reads all findings/*.md + results.tsv after each wave and calls Claude
to produce synthesis.md: validated bets, dead ends, unvalidated bets,
and a CONTINUE|STOP|PIVOT recommendation.
"""

import shutil
import subprocess
import sys
from pathlib import Path


_MAX_CORPUS_CHARS = 12000


def _build_findings_corpus(findings_dir: Path, results_tsv: Path) -> str:
    """
    Reads all findings/*.md files (sorted by name) and results.tsv.
    Returns a combined text corpus for the LLM prompt.
    Cap total size at 12000 chars (truncate oldest findings first if over limit).
    """
    # Results TSV first (always include)
    tsv_section = ""
    if results_tsv.exists():
        tsv_content = results_tsv.read_text(encoding="utf-8").strip()
        if tsv_content:
            tsv_section = f"## Results Summary\n\n{tsv_content}\n"

    # Findings files sorted by name
    finding_sections: list[str] = []
    if findings_dir.exists():
        for finding_file in sorted(findings_dir.glob("*.md")):
            content = finding_file.read_text(encoding="utf-8").strip()
            if content:
                finding_sections.append(f"### {finding_file.stem}\n\n{content}\n")

    # Build corpus: TSV always included, truncate low-severity findings first if over limit
    tsv_chars = len(tsv_section)
    budget = _MAX_CORPUS_CHARS - tsv_chars

    # F11.3: severity-aware truncation — drop COMPLIANT/FIXED findings before FAILURE/NON_COMPLIANT
    # Sort: high-severity (FAILURE, NON_COMPLIANT) first, low-severity (COMPLIANT, FIXED) last
    _HIGH_SEVERITY = frozenset(
        {
            "FAILURE",
            "NON_COMPLIANT",
            "WARNING",
            "REGRESSION",
            "ALERT",
            "DIAGNOSIS_COMPLETE",
            "FIX_FAILED",
        }
    )

    def _finding_priority(section: str) -> int:
        """Lower number = higher priority = kept longer under budget pressure."""
        for verdict in _HIGH_SEVERITY:
            if f"**Verdict**: {verdict}" in section or f": {verdict}" in section:
                return 0  # high severity — keep
        return 1  # low severity (COMPLIANT, FIXED, etc.) — drop first

    finding_sections.sort(key=_finding_priority)  # high-severity first
    while finding_sections and budget < sum(len(s) for s in finding_sections):
        finding_sections.pop()  # drop from tail (low-severity last)

    corpus_parts = []
    if tsv_section:
        corpus_parts.append(tsv_section)
    if finding_sections:
        corpus_parts.append("## Findings\n\n" + "\n".join(finding_sections))

    if not corpus_parts:
        return "No findings or results available yet."

    return "\n".join(corpus_parts)


def _read_doctrine(project_dir: Path) -> str:
    """
    Reads doctrine.md from project_dir if it exists.
    Returns content, or empty string if not found.
    """
    doctrine_path = project_dir / "doctrine.md"
    if not doctrine_path.exists():
        return ""
    return doctrine_path.read_text(encoding="utf-8").strip()


def _call_claude(prompt: str) -> str | None:
    """
    Calls Claude via subprocess: claude -p "{prompt}" --output-format text
    Returns stdout stripped, or None on failure.
    """
    claude_bin = shutil.which("claude") or "claude"
    try:
        result = subprocess.run(
            [claude_bin, "-p", prompt, "--output-format", "text"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
        if result.stderr.strip():
            print(result.stderr.strip(), file=sys.stderr)
        if result.returncode != 0:
            print(
                f"[synthesizer] Claude exited with code {result.returncode}",
                file=sys.stderr,
            )
            return None
        return result.stdout.strip() or None
    except FileNotFoundError:
        print("[synthesizer] claude CLI not found", file=sys.stderr)
        return None
    except subprocess.TimeoutExpired:
        print("[synthesizer] Claude timed out after 120s", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[synthesizer] Unexpected error calling Claude: {e}", file=sys.stderr)
        return None


def parse_recommendation(synthesis_text: str) -> str:
    """
    Extracts the recommendation from synthesis output.
    Scans lines after the '## Recommended Next Action' section header.
    Falls back to full-text scan if the section header is absent.
    Returns "CONTINUE" as default if not found.
    """
    lines = synthesis_text.splitlines()

    # F10.2: locate the Recommended Next Action section, scan only lines after it
    section_start = None
    for i, line in enumerate(lines):
        if "recommended next action" in line.lower():
            section_start = i + 1
            break

    scan_lines = lines[section_start:] if section_start is not None else lines

    for line in scan_lines:
        upper = line.upper()
        if "STOP" in upper:
            return "STOP"
        if "PIVOT" in upper:
            return "PIVOT"
        if "CONTINUE" in upper:
            return "CONTINUE"
    return "CONTINUE"


def synthesize(
    project_dir: Path,
    wave: int | None = None,
    dry_run: bool = False,
) -> Path | None:
    """
    Main entry point. Builds corpus, reads doctrine, calls Claude,
    writes synthesis.md (or prints on dry_run).

    Returns path to synthesis.md, or None on dry_run or failure.
    """
    findings_dir = project_dir / "findings"
    results_tsv = project_dir / "results.tsv"

    corpus = _build_findings_corpus(findings_dir, results_tsv)
    doctrine = _read_doctrine(project_dir)

    # Detect wave from corpus if not supplied
    wave_label = wave if wave is not None else "?"

    doctrine_section = ""
    if doctrine:
        doctrine_section = f"## Project Doctrine\n\n{doctrine}\n\n"

    prompt = f"""You are a research campaign director reviewing findings from a BrickLayer autonomous research campaign.

Your job: synthesize the accumulated evidence and produce a structured campaign status report.

{doctrine_section}CAMPAIGN FINDINGS:
{corpus}

Produce a synthesis report in this EXACT format:

# Campaign Synthesis — Wave {wave_label}

## Core Hypothesis Verdict
[CONFIRMED | UNCONFIRMED | PARTIALLY CONFIRMED | REFUTED] — one paragraph explaining why.

## Validated Bets
List each thing the campaign has confirmed with evidence. Format:
- [what was confirmed]: evidence from [Q IDs] — confidence [high/medium/low]

If nothing validated yet: "None confirmed yet."

## Dead Ends
List paths that have been exhausted with no findings worth pursuing further:
- [what was tested]: [Q IDs] found nothing actionable — stop probing here

If none: "None identified."

## Unvalidated Bets
List key questions or assumptions that have NOT been tested yet:
- [what is unvalidated]: [why it matters]

If all bets validated: "None remaining."

## Recommended Next Action
State exactly one of: CONTINUE, STOP, or PIVOT

CONTINUE — more questions needed, campaign is making progress
STOP — core hypothesis confirmed or refuted with sufficient confidence; no unvalidated bets remain
PIVOT — a new direction has emerged that the current question bank doesn't cover; describe the pivot

Then one paragraph of specific reasoning for the recommendation."""

    output = _call_claude(prompt)

    if output is None:
        print(
            "[synthesizer] Claude call failed — no synthesis written", file=sys.stderr
        )
        return None

    recommendation = parse_recommendation(output)
    print(f"[synthesizer] Recommendation: {recommendation}", file=sys.stderr)

    if dry_run:
        print(output)
        return None

    synthesis_path = project_dir / "synthesis.md"
    synthesis_path.write_text(output, encoding="utf-8")
    return synthesis_path
