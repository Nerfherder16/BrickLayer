"""
bl/question_sharpener.py — Question sharpening feedback loop.

Reads INCONCLUSIVE findings and narrows PENDING questions in the same mode/domain.
Called by synthesizer-bl2 at wave end, before writing synthesis.md.
"""

import os
import re
import tempfile
from pathlib import Path


def _extract_finding_mode(content: str) -> str | None:
    """
    Extract the mode from a finding file's content.

    Searches for **Mode**: <value> and returns the value, or None if absent.
    """
    match = re.search(r"\*\*Mode\*\*:\s*(\S+)", content)
    if match:
        return match.group(1).strip()
    return None


def _finding_keyword(content: str) -> str:
    """
    Extract a short keyword slug from the ## Summary section of a finding.

    Returns the first 3 non-empty words joined with '-', lowercased.
    Falls back to 'inconclusive' if the section is missing or empty.
    """
    summary_match = re.search(
        r"^##\s+Summary\s*\n(.*?)(?=^##|\Z)", content, re.MULTILINE | re.DOTALL
    )
    if not summary_match:
        return "inconclusive"

    summary_text = summary_match.group(1).strip()
    words = [w for w in re.split(r"\s+", summary_text) if w]
    if not words:
        return "inconclusive"

    slug_words = [w.lower() for w in words[:3]]
    return "-".join(slug_words)


def sharpen_pending_questions(
    project_dir,
    max_sharpen: int = 5,
    dry_run: bool = False,
) -> list[str]:
    """
    Read INCONCLUSIVE findings and narrow matching PENDING questions.

    Algorithm:
    1. Find all findings/*.md where content contains **Verdict**: INCONCLUSIVE
    2. For each INCONCLUSIVE finding, extract its mode
    3. Find PENDING question blocks matching that mode (case-insensitive)
       that do NOT already have **Sharpened**: true
    4. Append [narrowed: {keyword}] to the title line and insert **Sharpened**: true
       after the **Status**: line
    5. Write questions.md atomically unless dry_run=True
    6. Return list of question IDs that were modified

    Args:
        project_dir: Path (or str) to the project root containing questions.md
                     and findings/
        max_sharpen: Maximum number of questions to sharpen in one call
        dry_run:     If True, compute changes but do not write questions.md

    Returns:
        List of question IDs (e.g. ["Q1.1", "Q2.3"]) that were (or would be)
        sharpened.
    """
    project_dir = Path(project_dir)
    questions_path = project_dir / "questions.md"
    findings_dir = project_dir / "findings"

    # Guard: no questions.md → nothing to do
    if not questions_path.exists():
        return []

    # Guard: no findings directory → nothing to do
    if not findings_dir.exists() or not findings_dir.is_dir():
        return []

    # Step 1: collect INCONCLUSIVE findings and their modes
    inconclusive_modes: list[str] = []
    inconclusive_keywords: list[str] = []

    for finding_file in sorted(findings_dir.glob("*.md")):
        content = finding_file.read_text(encoding="utf-8", errors="replace")
        if "**Verdict**: INCONCLUSIVE" not in content:
            continue
        mode = _extract_finding_mode(content)
        if mode:
            inconclusive_modes.append(mode.lower())
            inconclusive_keywords.append(_finding_keyword(content))

    if not inconclusive_modes:
        return []

    # Step 2: read questions.md and find PENDING question blocks to sharpen
    text = questions_path.read_text(encoding="utf-8")

    # Split into question blocks by the ### QID — Title header pattern
    # Each block starts with ### and ends just before the next ### or EOF
    block_pattern = re.compile(r"^(###\s+(\S+)\s+—\s+.+)$", re.MULTILINE)
    block_starts = [
        (m.start(), m.end(), m.group(1), m.group(2))
        for m in block_pattern.finditer(text)
    ]

    modified_ids: list[str] = []
    # We'll build the new text by splicing replacements
    # Work from end to start to preserve offsets
    replacements: list[tuple[int, int, str]] = []  # (start, end, new_text)

    for i, (block_start, header_end, header_line, qid) in enumerate(block_starts):
        if len(modified_ids) >= max_sharpen:
            break

        # Determine block body extent
        next_block_start = (
            block_starts[i + 1][0] if i + 1 < len(block_starts) else len(text)
        )
        block_body = text[header_end:next_block_start]

        # Must be PENDING
        if "**Status**: PENDING" not in block_body:
            continue

        # Must not already be sharpened
        if "**Sharpened**: true" in block_body:
            continue

        # Extract this question's mode (case-insensitive match)
        mode_match = re.search(r"\*\*Mode\*\*:\s*(\S+)", block_body)
        if not mode_match:
            continue
        question_mode = mode_match.group(1).strip().lower()

        # Check if any INCONCLUSIVE finding matches this mode
        keyword = None
        for inc_mode, inc_kw in zip(inconclusive_modes, inconclusive_keywords):
            if inc_mode == question_mode:
                keyword = inc_kw
                break

        if keyword is None:
            continue

        # Build the replacement: modify header + insert Sharpened flag after Status line
        new_header = header_line + f" [narrowed: {keyword}]"

        # Insert **Sharpened**: true after **Status**: PENDING in the block body
        new_block_body = block_body.replace(
            "**Status**: PENDING",
            "**Status**: PENDING\n**Sharpened**: true",
            1,
        )

        replacements.append(
            (block_start, next_block_start, new_header + new_block_body)
        )
        modified_ids.append(qid)

    if not modified_ids or dry_run:
        return modified_ids

    # Apply replacements from end to start (preserves offsets)
    for start, end, new_text in reversed(replacements):
        text = text[:start] + new_text + text[end:]

    # Atomic write: temp file then os.replace
    dir_ = questions_path.parent
    fd, tmp_path = tempfile.mkstemp(dir=dir_, suffix=".tmp", prefix="questions_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp_path, questions_path)
    except Exception:
        # Clean up temp file if replace fails
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    return modified_ids
