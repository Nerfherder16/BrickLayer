"""Utility for reading and appending to model_assumptions.md."""
from pathlib import Path
from datetime import date

TEMPLATE = """# Model Assumptions Log

This file tracks design decisions about `simulate.py` and `constants.py`.
Trowel and specialist agents append here when they change model logic or discover important invariants.

## Format

Each entry:

```
## [YYYY-MM-DD] <agent> — <one-line summary>
**Changed**: <what was modified>
**Why**: <reasoning>
**Impact**: <what findings this affects>
```

## Entries

<!-- Trowel appends below -->
"""


def ensure_exists(project_root) -> Path:
    root = Path(project_root)
    p = root / "model_assumptions.md"
    if not p.exists():
        p.write_text(TEMPLATE, encoding="utf-8")
    return p


def append_entry(project_root, agent: str, summary: str, changed: str, why: str, impact: str) -> None:
    p = ensure_exists(project_root)
    today = date.today().isoformat()
    entry = f"\n## [{today}] {agent} — {summary}\n**Changed**: {changed}\n**Why**: {why}\n**Impact**: {impact}\n"
    p.write_text(p.read_text(encoding="utf-8") + entry, encoding="utf-8")
