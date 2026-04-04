"""bl/tmux/stream_format.py — Format claude stream-json for human-readable pane output.

Standalone script (stdlib only). Reads stream-json lines from stdin,
writes formatted text to stdout. Designed to be piped:

    claude -p - --output-format stream-json < prompt | python3 -u stream_format.py
"""

from __future__ import annotations

import json
import sys


def _truncate(text: str, limit: int = 200) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def _format_tool_use(block: dict) -> str:
    name = block.get("name", "?")
    inp = block.get("input", {})
    if name == "Bash":
        return f"  $ {inp.get('command', '')[:120]}"
    if name in ("Read", "Glob"):
        return f"  {name}: {inp.get('file_path', inp.get('pattern', ''))[:120]}"
    if name == "Grep":
        return f"  {name}: /{inp.get('pattern', '')[:60]}/ {inp.get('path', '')[:60]}"
    if name in ("Edit", "Write"):
        return f"  {name}: {inp.get('file_path', '')[:120]}"
    return f"  {name}"


def format_event(event: dict) -> str | None:
    etype = event.get("type", "")

    if etype == "assistant":
        lines: list[str] = []
        msg = event.get("message", {})
        for block in msg.get("content", []):
            btype = block.get("type", "")
            if btype == "thinking":
                thought = block.get("thinking", "")
                if thought:
                    preview = thought[:300].replace("\n", " ")
                    if len(thought) > 300:
                        preview += "..."
                    lines.append(f"  [thinking] {preview}")
            elif btype == "text":
                text = block.get("text", "")
                if text:
                    lines.append(text)
            elif btype == "tool_use":
                lines.append(_format_tool_use(block))
        return "\n".join(lines) if lines else None

    if etype == "tool_result":
        content = event.get("content", "")
        if isinstance(content, list):
            parts = [c.get("text", "") for c in content if isinstance(c, dict)]
            content = "\n".join(parts)
        if content:
            preview = content.strip().split("\n")
            if len(preview) > 5:
                shown = "\n    ".join(preview[:5])
                return f"    {shown}\n    ... (+{len(preview) - 5} lines)"
            return "    " + "\n    ".join(preview)
        return None

    if etype == "result":
        cost = event.get("total_cost_usd", 0)
        turns = event.get("num_turns", 0)
        subtype = event.get("subtype", "")
        if subtype == "success":
            return f"\n  Done ({turns} turns, ${cost:.4f})"
        error = event.get("error", subtype)
        return f"\n  Error: {error}"

    return None


def main() -> None:
    for line in iter(sys.stdin.readline, ""):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        output = format_event(event)
        if output is not None:
            print(output, flush=True)


if __name__ == "__main__":
    main()
