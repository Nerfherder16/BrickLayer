"""bl/scratch.py — Typed signal board management for BrickLayer 2.0 campaigns.

Signals are parsed from finding text, stored in a rolling markdown table,
and trimmed to a cap using priority-based eviction (RESOLVED first, DATA
second; WATCH and BLOCK are never auto-removed).
"""
import re
from pathlib import Path

_VALID_TYPES = {"WATCH", "BLOCK", "DATA", "RESOLVED"}

# Matches: [SIGNAL: TYPE -- message]
# Uses a non-greedy capture on the type and a greedy capture on the message
# so that -- inside the message does not truncate it.
_SIGNAL_RE = re.compile(r"\[SIGNAL:\s*([A-Z]+)\s*--\s*(.*?)\]", re.DOTALL)


def parse_signals(finding_text: str) -> list[dict]:
    """Parse [SIGNAL: TYPE -- message] lines from finding text.

    Returns list of dicts: {signal: str, type: str, source: str, date: str}.
    source and date are always empty strings (not carried in the signal line).
    Unknown types are silently ignored.
    """
    results = []
    for match in _SIGNAL_RE.finditer(finding_text):
        sig_type = match.group(1)
        message = match.group(2).strip()
        if sig_type not in _VALID_TYPES:
            continue
        results.append({"signal": message, "type": sig_type, "source": "", "date": ""})
    return results


# ---------------------------------------------------------------------------
# Markdown table helpers
# ---------------------------------------------------------------------------

_TABLE_HEADER = "| # | Signal | Type | Source | Date |"
_TABLE_SEP = "|---|--------|------|--------|------|"


def _row_to_line(index: int, row: dict) -> str:
    return f"| {index} | {row['signal']} | {row['type']} | {row['source']} | {row['date']} |"


def render_scratch(rows: list[dict]) -> str:
    """Render rows as markdown table string only (no file header).

    Returns the table header + separator + data rows as a single string.
    """
    lines = [_TABLE_HEADER, _TABLE_SEP]
    for i, row in enumerate(rows, start=1):
        lines.append(_row_to_line(i, row))
    return "\n".join(lines)


def save_scratch(path: Path, rows: list[dict]) -> None:
    """Write scratch.md with header and markdown table."""
    table = render_scratch(rows)
    content = f"# Campaign Scratch Pad\n\n{table}\n"
    path.write_text(content, encoding="utf-8")


def load_scratch(path: Path) -> list[dict]:
    """Load scratch.md table rows into list of dicts.

    Returns empty list if file doesn't exist.
    """
    if not path.exists():
        return []

    rows = []
    content = path.read_text(encoding="utf-8")
    in_table = False
    past_separator = False

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("| # |"):
            in_table = True
            past_separator = False
            continue
        if in_table and not past_separator and stripped.startswith("|---"):
            past_separator = True
            continue
        if in_table and past_separator and stripped.startswith("|"):
            # Split into at most 7 parts so a pipe inside the signal field
            # does not split into extra columns.  Format: | idx | signal | type | source | date |
            # maxsplit=6 gives: ['', idx, signal, type, source, 'date |']
            # We strip and strip trailing | from last captured cell.
            parts = [p.strip() for p in stripped.split("|", maxsplit=6)]
            # parts: ['', idx, signal, type, source, date, '']
            if len(parts) >= 6:
                rows.append({
                    "signal": parts[2],
                    "type": parts[3],
                    "source": parts[4],
                    "date": parts[5],
                })

    return rows


# ---------------------------------------------------------------------------
# Trim logic
# ---------------------------------------------------------------------------

def trim_scratch(rows: list[dict], max_entries: int = 15) -> list[dict]:
    """Enforce rolling cap at max_entries.

    Removal priority: oldest RESOLVED first, then oldest DATA.
    WATCH and BLOCK are NEVER auto-removed.
    If only WATCH/BLOCK remain over cap, returns all entries unchanged.
    """
    result = list(rows)
    while len(result) > max_entries:
        # Find the first (oldest) RESOLVED entry
        removed = False
        for i, row in enumerate(result):
            if row["type"] == "RESOLVED":
                result.pop(i)
                removed = True
                break
        if removed:
            continue

        # No RESOLVED found — try oldest DATA
        for i, row in enumerate(result):
            if row["type"] == "DATA":
                result.pop(i)
                removed = True
                break
        if removed:
            continue

        # Nothing removable — preserve all remaining entries
        break

    return result
