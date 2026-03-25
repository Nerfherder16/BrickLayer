"""
bl/peer_review_watcher.py — Process peer-reviewer results and requeue low-quality INCONCLUSIVEs.

Scans findings/ for findings that have:
  - Primary verdict INCONCLUSIVE
  - A ## Peer Review section with Quality Score < 0.4

For each match:
  - Calls record_result() to update .bl-weights.json
  - Appends a REQUEUE block to questions.md (as {qid}-RQ1 if not already present)

Usage:
    python -m bl.peer_review_watcher --project-root /path/to/project
    # or called inline by Trowel after peer-reviewer background jobs complete
"""

from __future__ import annotations

import argparse
import re
import tempfile
import os
from datetime import datetime, timezone
from pathlib import Path

from bl.question_weights import record_result

# Quality score below this threshold triggers requeue
REQUEUE_THRESHOLD = 0.4

_PRIMARY_VERDICT_RE = re.compile(r"^\*\*Verdict\*\*:\s*(\w+)", re.MULTILINE)
_PEER_VERDICT_RE = re.compile(r"## Peer Review.*?\*\*Verdict\*\*:\s*(\w+)", re.DOTALL)
_PEER_QUALITY_RE = re.compile(
    r"## Peer Review.*?\*\*Quality Score\*\*:\s*([0-9.]+)", re.DOTALL
)
_PEER_SECTION_RE = re.compile(r"## Peer Review", re.MULTILINE)
_QID_RE = re.compile(r"^## ([A-Za-z0-9_.:\-]+)\s*\[", re.MULTILINE)


def _parse_finding(path: Path) -> dict | None:
    """Extract primary verdict, peer review verdict, and quality score from a finding."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    # Must have a peer review section
    if not _PEER_SECTION_RE.search(text):
        return None

    primary_m = _PRIMARY_VERDICT_RE.search(text)
    peer_verdict_m = _PEER_VERDICT_RE.search(text)
    quality_m = _PEER_QUALITY_RE.search(text)

    primary_verdict = primary_m.group(1).upper() if primary_m else "UNKNOWN"
    peer_verdict = peer_verdict_m.group(1).upper() if peer_verdict_m else None
    quality_score = float(quality_m.group(1)) if quality_m else None

    return {
        "qid": path.stem,
        "primary_verdict": primary_verdict,
        "peer_verdict": peer_verdict,
        "quality_score": quality_score,
    }


def _already_requeued(questions_text: str, rq_id: str) -> bool:
    """Return True if {rq_id} already appears in questions.md."""
    return f"## {rq_id}" in questions_text or f"## {rq_id} [" in questions_text


def _original_question_text(questions_text: str, qid: str) -> str:
    """Extract the hypothesis/question text for a given qid from questions.md."""
    # Find the block for this question
    block_start = questions_text.find(f"## {qid} [")
    if block_start == -1:
        block_start = questions_text.find(f"## {qid}\n")
    if block_start == -1:
        return f"Original question {qid} (text not found)"
    next_block = questions_text.find("\n## ", block_start + 1)
    block = questions_text[
        block_start : next_block if next_block != -1 else len(questions_text)
    ]
    hyp_m = re.search(r"\*\*Hypothesis\*\*:\s*(.+)", block)
    q_m = re.search(r"\*\*Question\*\*:\s*(.+)", block)
    if hyp_m:
        return hyp_m.group(1).strip()
    if q_m:
        return q_m.group(1).strip()
    return f"Original question {qid}"


def _append_requeue(
    questions_path: Path, qid: str, rq_id: str, quality_score: float
) -> None:
    """Append a REQUEUE question block to questions.md."""
    text = questions_path.read_text(encoding="utf-8", errors="replace")

    orig_hypothesis = _original_question_text(text, qid)
    # Truncate hypothesis to keep it readable
    if len(orig_hypothesis) > 200:
        orig_hypothesis = orig_hypothesis[:197] + "..."

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Infer mode from original block
    block_start = text.find(f"## {qid}")
    mode = "research"
    if block_start != -1:
        next_block = text.find("\n## ", block_start + 1)
        block = text[block_start : next_block if next_block != -1 else len(text)]
        mode_m = re.search(r"\*\*Mode\*\*:\s*(\w+)", block)
        if mode_m:
            mode = mode_m.group(1)

    requeue_block = f"""
## {rq_id} [PENDING]

**Question**: {orig_hypothesis} — REQUEUE: prior finding INCONCLUSIVE with low quality score ({quality_score:.2f} < {REQUEUE_THRESHOLD}). Narrow scope and focus on the most specific claim.
**Hypothesis**: {orig_hypothesis}
**Mode**: {mode}
**Status**: PENDING
**Priority**: high
**Added**: {timestamp}
**Source**: peer_review_watcher (requeue of {qid})

"""

    new_text = text.rstrip() + "\n" + requeue_block
    fd, tmp = tempfile.mkstemp(dir=questions_path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(new_text)
        os.replace(tmp, questions_path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def process(project_root: Path) -> list[str]:
    """
    Scan findings/ and process low-quality INCONCLUSIVEs.
    Returns list of requeued qids.
    """
    project_root = Path(project_root).resolve()
    findings_dir = project_root / "findings"
    questions_path = project_root / "questions.md"

    if not findings_dir.exists():
        return []

    requeued: list[str] = []

    for md in sorted(findings_dir.glob("*.md")):
        if md.stem == "synthesis":
            continue

        info = _parse_finding(md)
        if not info:
            continue

        # Only act on INCONCLUSIVE primary verdicts with low quality score
        if info["primary_verdict"] != "INCONCLUSIVE":
            continue
        if info["quality_score"] is None or info["quality_score"] >= REQUEUE_THRESHOLD:
            continue

        qid = info["qid"]
        quality_score = info["quality_score"]

        # Update weights
        record_result(
            str(project_root), qid, "INCONCLUSIVE", quality_score=quality_score
        )

        # Requeue in questions.md if it exists and the requeue isn't already there
        if questions_path.exists():
            questions_text = questions_path.read_text(
                encoding="utf-8", errors="replace"
            )
            rq_id = f"{qid}-RQ1"
            if not _already_requeued(questions_text, rq_id):
                _append_requeue(questions_path, qid, rq_id, quality_score)
                print(
                    f"[peer_review_watcher] Requeued {qid} → {rq_id} (quality_score={quality_score:.2f})"
                )
                requeued.append(qid)
            else:
                print(f"[peer_review_watcher] {rq_id} already in questions.md — skip")
        else:
            print(
                f"[peer_review_watcher] Updated weights for {qid} (no questions.md to requeue)"
            )
            requeued.append(qid)

    return requeued


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Process peer-reviewer results and requeue low-quality INCONCLUSIVEs"
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Path to the BrickLayer project directory (default: cwd)",
    )
    args = parser.parse_args()
    requeued = process(Path(args.project_root))
    if requeued:
        print(
            f"[peer_review_watcher] Done — requeued {len(requeued)} finding(s): {', '.join(requeued)}"
        )
    else:
        print("[peer_review_watcher] Done — no low-quality INCONCLUSIVEs found")


if __name__ == "__main__":
    main()
