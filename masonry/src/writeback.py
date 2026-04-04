"""masonry/src/writeback.py

Helpers for writing optimized agent instructions back to .md files
and updating agent_registry.yml. No DSPy dependency.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

_SECTION_HEADER = "## DSPy Optimized Instructions"
_SECTION_END = "<!-- /DSPy Optimized Instructions -->"
_SECTION_PATTERN = re.compile(
    rf"{re.escape(_SECTION_HEADER)}.*?{re.escape(_SECTION_END)}\n?",
    re.DOTALL,
)

# Safe placeholder substituted when LLM-generated content contains a delimiter.
_DELIMITER_PLACEHOLDER = "<!-- DSPy-section-marker -->"


def _sanitize_instructions(instructions: str) -> str:
    """Replace delimiter strings embedded in LLM-generated instructions.

    If either ``_SECTION_HEADER`` or ``_SECTION_END`` appears verbatim inside
    the instruction text, the writeback regex would mis-parse the section
    boundaries.  This replaces any occurrences with ``_DELIMITER_PLACEHOLDER``
    and logs a warning so the problem is visible without silently corrupting
    agent files.

    The substitution is lossless in the sense that the instruction content is
    fully preserved — only the two forbidden delimiter strings are replaced.
    """
    sanitized = instructions
    if _SECTION_HEADER in sanitized:
        logger.warning(
            "writeback: _SECTION_HEADER found in LLM-generated instructions for "
            "agent — replacing with placeholder to prevent section corruption.  "
            "Review the optimized prompt output."
        )
        sanitized = sanitized.replace(_SECTION_HEADER, _DELIMITER_PLACEHOLDER)
    if _SECTION_END in sanitized:
        logger.warning(
            "writeback: _SECTION_END found in LLM-generated instructions for "
            "agent — replacing with placeholder to prevent section corruption.  "
            "Review the optimized prompt output."
        )
        sanitized = sanitized.replace(_SECTION_END, _DELIMITER_PLACEHOLDER)
    return sanitized


def _validate_writeback(md_path: Path, expected_instructions: str) -> None:
    """Confirm the written section can be round-tripped without corruption.

    Reads the file that was just written, extracts the DSPy section using the
    same regex used during writeback, and verifies that the embedded
    instructions match *expected_instructions* exactly.  Raises ``ValueError``
    if the content does not match (e.g., because a residual delimiter caused
    the regex to collapse two sections into one).

    The caller is responsible for restoring a backup when this raises.
    """
    written = md_path.read_text(encoding="utf-8")
    match = _SECTION_PATTERN.search(written)
    if match is None:
        raise ValueError(
            f"writeback validation failed for {md_path}: DSPy section not found "
            "after write — the file may be corrupt."
        )
    # Extract the body between the header line and the end marker.
    section_body = match.group(0)
    # Strip the surrounding header/end lines to recover only the instructions.
    body_only = section_body
    body_only = re.sub(rf"^{re.escape(_SECTION_HEADER)}\n?", "", body_only)
    body_only = re.sub(rf"\n?{re.escape(_SECTION_END)}\n?$", "", body_only)
    # Normalise trailing whitespace the same way writeback does.
    body_only = body_only.strip("\n")
    expected_stripped = expected_instructions.strip("\n")
    if body_only != expected_stripped:
        raise ValueError(
            f"writeback validation failed for {md_path}: extracted instructions "
            f"do not match what was written.\n"
            f"  expected ({len(expected_stripped)} chars): {expected_stripped[:120]!r}...\n"
            f"  got      ({len(body_only)} chars):     {body_only[:120]!r}..."
        )


def writeback_optimized_instructions(
    base_dir: Path,
    agent_name: str,
    instructions: str,
    optimized_at: str,
    target_paths: "list[Path] | None" = None,
) -> list[Path]:
    """Inject optimized instructions into agent .md file(s).

    If target_paths is provided, only those files are updated (scope guard —
    prevents unintended cross-file contamination when variants exist).
    Otherwise, searches all copies:
      - base_dir/.claude/agents/{agent}.md
      - base_dir/{project}/.claude/agents/{agent}.md  (one level deep)
      - ~/.claude/agents/{agent}.md

    Replaces existing section in-place, or appends if not present.
    Returns list of updated file paths.

    The *instructions* string is sanitized before writing: any occurrence of
    the section delimiter strings is replaced with ``_DELIMITER_PLACEHOLDER``
    so that round-trip parsing remains unambiguous.  After each write a
    validation step re-reads the file and confirms the section was stored
    correctly; if validation fails the original content is restored and an
    error is raised.
    """
    # Sanitize before building section_text so the placeholder is embedded.
    safe_instructions = _sanitize_instructions(instructions)

    section_text = (
        f"\n{_SECTION_HEADER}\n"
        f"{safe_instructions}\n\n"
        f"{_SECTION_END}\n"
    )

    if target_paths is not None:
        # Scope guard: only write to the explicitly specified files
        candidates = list(target_paths)
    else:
        candidates = [
            base_dir / ".claude" / "agents" / f"{agent_name}.md",
        ]
        for child in base_dir.iterdir():
            if child.is_dir() and not child.name.startswith("."):
                p = child / ".claude" / "agents" / f"{agent_name}.md"
                if p.exists():
                    candidates.append(p)
        candidates.append(Path.home() / ".claude" / "agents" / f"{agent_name}.md")

    seen: set[Path] = set()
    unique: list[Path] = []
    for c in candidates:
        resolved = c.resolve() if c.exists() else c
        if resolved not in seen:
            seen.add(resolved)
            unique.append(c)

    updated: list[Path] = []
    for md_path in unique:
        if not md_path.exists():
            continue
        original_content = md_path.read_text(encoding="utf-8")
        if _SECTION_PATTERN.search(original_content):
            new_content = _SECTION_PATTERN.sub(section_text.lstrip("\n"), original_content)
        else:
            new_content = original_content.rstrip("\n") + "\n" + section_text
        md_path.write_text(new_content, encoding="utf-8")

        # Post-write validation: confirm the section round-trips cleanly.
        try:
            _validate_writeback(md_path, safe_instructions)
        except ValueError:
            # Restore original content before re-raising so the file is not
            # left in a corrupt or partially-written state.
            md_path.write_text(original_content, encoding="utf-8")
            raise

        updated.append(md_path)

    return updated


def strip_optimized_instructions(md_path: Path) -> bool:
    """Remove the optimized instructions section from an agent .md file.

    Returns True if a section was found and removed, False if nothing changed.
    """
    if not md_path.exists():
        return False
    content = md_path.read_text(encoding="utf-8")
    if not _SECTION_PATTERN.search(content):
        return False
    new_content = _SECTION_PATTERN.sub("", content).rstrip("\n") + "\n"
    md_path.write_text(new_content, encoding="utf-8")
    return True


def update_registry_dspy_status(
    registry_path: Path,
    agent_name: str,
    optimized_at: str,
) -> None:
    """Update dspy_status and last_optimized fields in agent_registry.yml."""
    if not registry_path.exists():
        return
    content = registry_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    in_target = False
    updated = []
    for line in lines:
        name_match = line.strip().startswith("- name:") or (
            line.strip().startswith("name:") and not line.strip().startswith("name: #")
        )
        if name_match and agent_name in line:
            in_target = True
        elif name_match:
            in_target = False
        if in_target and "dspy_status:" in line:
            indent = len(line) - len(line.lstrip())
            line = " " * indent + "dspy_status: optimized"
        elif in_target and "last_optimized:" in line:
            indent = len(line) - len(line.lstrip())
            line = " " * indent + f"last_optimized: {optimized_at}"
        updated.append(line)
    registry_path.write_text("\n".join(updated), encoding="utf-8")
