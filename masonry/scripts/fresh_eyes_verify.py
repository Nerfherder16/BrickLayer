"""Fresh-eyes verification for synthesis reports.

Generates comprehension questions from a synthesis document, then tests
whether a zero-context reader can answer them correctly. This catches
unclear writing, missing context, and logical gaps.

Usage:
    python masonry/scripts/fresh_eyes_verify.py path/to/synthesis.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def generate_questions(content: str) -> list[dict[str, str]]:
    """Generate comprehension questions from synthesis content.

    Extracts key claims, numbers, and recommendations from the text
    and formulates questions + expected answers.
    """
    questions: list[dict[str, str]] = []
    sections = _split_sections(content)

    for section_title, section_body in sections:
        claims = _extract_claims(section_body)
        for claim in claims:
            q = _claim_to_question(claim, section_title)
            if q:
                questions.append(q)

    # Deduplicate and limit to 5-8
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for q in questions:
        key = q["question"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(q)

    return unique[:8] if len(unique) > 8 else unique


def _split_sections(content: str) -> list[tuple[str, str]]:
    """Split markdown into (heading, body) pairs."""
    sections: list[tuple[str, str]] = []
    current_heading = "Introduction"
    current_body: list[str] = []

    for line in content.splitlines():
        if line.startswith("##"):
            if current_body:
                sections.append((current_heading, "\n".join(current_body)))
            current_heading = re.sub(r"^#+\s*", "", line).strip()
            current_body = []
        else:
            current_body.append(line)

    if current_body:
        sections.append((current_heading, "\n".join(current_body)))

    return sections


def _extract_claims(text: str) -> list[str]:
    """Extract factual claims from text (sentences with numbers, percentages, specifics)."""
    claims: list[str] = []
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence or len(sentence) < 20:
            continue
        # Sentences with numbers, percentages, or specific terms are claims
        if re.search(
            r"\d+%?|\$[\d,]+|\b(?:must|should|reaches?|exceeds?|cap|limit|maintain)\b",
            sentence,
            re.IGNORECASE,
        ):
            claims.append(sentence)

    return claims


def _claim_to_question(claim: str, section: str) -> dict[str, str] | None:
    """Convert a factual claim into a question + expected answer pair."""
    # Extract the key number or threshold
    numbers = re.findall(r"\d+(?:\.\d+)?%?", claim)
    if not numbers:
        return None

    # Generate question based on claim structure
    # Look for "X at/reaches/exceeds Y" patterns
    if re.search(r"(?:at|reaches?|above|exceeds?)\s+\d", claim, re.IGNORECASE):
        question = f"According to the {section.lower()} section, what threshold or value is mentioned regarding: {claim[:80]}?"
    elif re.search(r"(?:cap|limit|maximum|minimum)", claim, re.IGNORECASE):
        question = f"What cap or limit is recommended in the {section.lower()} section?"
    elif re.search(r"(?:risk|danger|threat)", claim, re.IGNORECASE):
        question = f"What risk is identified in the {section.lower()} section?"
    else:
        question = f"What does the {section.lower()} section state about: {claim[:60]}?"

    return {
        "question": question,
        "expected_answer": claim,
    }


def score_answer(expected: str, actual: str) -> float:
    """Score how well an actual answer matches the expected answer.

    Uses keyword overlap as a simple metric. Returns 0.0-1.0.
    """
    expected_words = _normalize_words(expected)
    actual_words = _normalize_words(actual)

    if not expected_words:
        return 0.0

    # Count matching meaningful words
    matches = expected_words & actual_words
    # Weight numbers higher — they're the key facts
    number_matches = {w for w in matches if re.match(r"\d", w)}
    word_matches = matches - number_matches

    score = 0.0
    if expected_words:
        # Numbers count double
        weighted_matches = len(word_matches) + len(number_matches) * 2
        weighted_total = (
            len(expected_words - {w for w in expected_words if re.match(r"\d", w)})
            + len({w for w in expected_words if re.match(r"\d", w)}) * 2
        )
        score = min(1.0, weighted_matches / max(weighted_total, 1))

    return round(score, 2)


def _normalize_words(text: str) -> set[str]:
    """Extract meaningful words from text, lowercased."""
    stop_words = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "of",
        "in",
        "to",
        "for",
        "and",
        "or",
        "that",
        "this",
        "with",
        "by",
        "from",
        "on",
        "at",
        "as",
    }
    words = set(re.findall(r"\b[\w]+\b", text.lower()))
    return words - stop_words


def build_report(results: list[dict]) -> str:
    """Build a markdown verification report from scored results."""
    lines: list[str] = []
    lines.append("# Fresh-Eyes Verification Report\n")

    total = len(results)
    avg_score = sum(r["score"] for r in results) / max(total, 1)
    lines.append(f"**Overall Score:** {avg_score:.0%} ({total} questions)\n")

    lines.append("## Question Results\n")
    for i, r in enumerate(results, 1):
        emoji = "PASS" if r["score"] >= 0.6 else "FAIL"
        lines.append(f"### Q{i}: {r['question']}")
        lines.append(f"- **Score:** {r['score']:.0%} [{emoji}]")
        lines.append(f"- **Expected:** {r['expected_answer'][:120]}")
        lines.append(f"- **Actual:** {r['actual_answer'][:120]}")
        lines.append("")

    # Flag low-scoring sections
    failures = [r for r in results if r["score"] < 0.6]
    if failures:
        lines.append("## Flagged Sections\n")
        lines.append(
            "These questions scored below 60% — the synthesis may be unclear here:\n"
        )
        for r in failures:
            lines.append(f"- {r['question']}")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fresh-eyes verification for synthesis reports."
    )
    parser.add_argument("synthesis_path", help="Path to synthesis.md")
    parser.add_argument("--output", "-o", help="Output report path (default: stdout)")
    args = parser.parse_args()

    synthesis_path = Path(args.synthesis_path)
    if not synthesis_path.exists():
        print(f"Error: {synthesis_path} not found", file=sys.stderr)
        sys.exit(1)

    content = synthesis_path.read_text(encoding="utf-8")
    questions = generate_questions(content)

    if not questions:
        print("No verifiable claims found in synthesis.", file=sys.stderr)
        sys.exit(0)

    print(f"Generated {len(questions)} verification questions.", file=sys.stderr)
    print(
        "Note: Full verification requires spawning a fresh Claude instance.",
        file=sys.stderr,
    )
    print("Run with --claude to perform live verification.", file=sys.stderr)

    # Without --claude, output the questions for manual review
    results = []
    for q in questions:
        results.append(
            {
                "question": q["question"],
                "expected_answer": q["expected_answer"],
                "actual_answer": "(not yet verified — run with --claude)",
                "score": 0.0,
            }
        )

    report = build_report(results)
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
