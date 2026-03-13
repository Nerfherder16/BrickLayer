"""
bl/runners/quality.py — Static quality analysis runner.

Reads source files specified in the Target field and applies pattern-based
analysis to produce a BrickLayer verdict envelope.
"""

import re
import sys

from bl.config import cfg


def run_quality(question: dict) -> dict:
    """Read source files specified in the Target field and emit contents."""
    target = question.get("target", "")

    src_files = []
    target_segments = [s.strip() for s in target.split("+")]

    for segment in target_segments:
        segment = segment.strip()

        file_matches = re.findall(r"(?:src|tests)/[\w/]+\.py", segment)
        for fpath in file_matches:
            full = cfg.recall_src / fpath
            src_files.append(full)

        dir_matches = re.findall(r"(?:src|tests)(?:/[\w/]*)?/?(?=\s|$)", segment)
        for dpath in dir_matches:
            if file_matches:
                continue
            dpath = dpath.strip().rstrip("/")
            full_dir = cfg.recall_src / dpath
            if full_dir.is_dir():
                src_files.extend(sorted(full_dir.rglob("*.py")))

    if "src/api/routes/" in target and not src_files:
        routes_dir = cfg.recall_src / "src" / "api" / "routes"
        if routes_dir.exists():
            src_files.extend(sorted(routes_dir.glob("*.py")))

    seen: set = set()
    unique_files = []
    for f in src_files:
        if str(f) not in seen:
            seen.add(str(f))
            unique_files.append(f)

    if not unique_files:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"No source files found from target: {target}",
            "data": {"target": target},
            "details": "Check target field in questions.md — paths must match actual Recall source layout",
        }

    output_parts = []
    missing = []
    total_lines = 0

    for fpath in unique_files:
        if not fpath.exists():
            missing.append(str(fpath))
            output_parts.append(f"\n=== MISSING: {fpath} ===\n")
            continue
        try:
            content = fpath.read_text(encoding="utf-8")
            lines = content.splitlines()
            total_lines += len(lines)
            output_parts.append(f"\n=== {fpath} ({len(lines)} lines) ===\n{content}\n")
        except Exception as exc:
            output_parts.append(f"\n=== ERROR reading {fpath}: {exc} ===\n")

    full_output = "".join(output_parts)

    verdict, summary = _analyze_quality_patterns(
        question, unique_files, full_output, missing, total_lines
    )

    return {
        "verdict": verdict,
        "summary": summary,
        "data": {
            "files_read": [str(f) for f in unique_files if f.exists()],
            "files_missing": missing,
            "total_lines": total_lines,
        },
        "details": full_output,
    }


def _analyze_quality_patterns(
    question: dict, files: list, content: str, missing: list, total_lines: int
) -> tuple[str, str]:
    """
    Apply pattern-based analysis to quality question file content.
    Returns (verdict, summary). Falls back to INCONCLUSIVE when no pattern matches.
    """
    hypothesis = question.get("hypothesis", "").lower()

    # --- Logger mismatch detection ---
    if "structlog" in hypothesis and (
        "stdlib" in hypothesis
        or "logging.getlogger" in hypothesis
        or "mismatch" in hypothesis
    ):
        failures = []
        warnings = []
        for fpath in files:
            if not fpath.exists():
                continue
            try:
                src = fpath.read_text(encoding="utf-8", errors="replace")
            except Exception as exc:  # noqa: BLE001
                print(f"[quality] skipping {fpath.name}: {exc}", file=sys.stderr)
                continue
            has_stdlib = bool(re.search(r"^import logging\b", src, re.MULTILINE))
            has_structlog = bool(re.search(r"import structlog", src))
            stdlib_kwarg_calls = re.findall(
                r"(?:logging\.\w+|logger\.\w+)\([^)]*,\s*\w+=",
                src,
            )
            uses_stdlib_logger = bool(re.search(r"logging\.getLogger\(\)", src))
            if has_stdlib and has_structlog:
                if stdlib_kwarg_calls and uses_stdlib_logger:
                    failures.append(
                        f"{fpath.name}: stdlib logger called with kwargs — TypeError in except blocks"
                    )
                else:
                    warnings.append(
                        f"{fpath.name}: mixed imports (stdlib + structlog) but no kwarg-passing found"
                    )
        if failures:
            return "FAILURE", f"Logger mismatch: {'; '.join(failures)}"
        if warnings:
            return "WARNING", f"Mixed logger imports: {'; '.join(warnings)}"
        return (
            "HEALTHY",
            f"Checked {len(files)} files — all consistently use structlog; no stdlib/structlog mixing detected",
        )

    # --- Unguarded mutable module-level state ---
    if "mutable" in hypothesis and ("lock" in hypothesis or "async" in hypothesis):
        failures = []
        warnings = []
        for fpath in files:
            if not fpath.exists():
                continue
            try:
                src = fpath.read_text(encoding="utf-8", errors="replace")
            except Exception as exc:  # noqa: BLE001
                print(f"[quality] skipping {fpath.name}: {exc}", file=sys.stderr)
                continue
            module_dicts = re.findall(
                r"^(\w+)\s*(?::\s*\S+)?\s*=\s*(?:\{\}|\[\]|dict\(\)|list\(\))",
                src,
                re.MULTILINE,
            )
            for var in module_dicts:
                lock_nearby = bool(
                    re.search(rf"{var}_lock|_{var}_lock|asyncio\.Lock", src)
                )
                written_in_async = bool(
                    re.search(rf"async def[^{{]+\n(?:.*\n){{0,30}}.*{var}\s*[=\[]", src)
                )
                if written_in_async and not lock_nearby:
                    failures.append(
                        f"{fpath.name}: `{var}` written from async path without asyncio.Lock"
                    )
                elif not lock_nearby and module_dicts:
                    warnings.append(f"{fpath.name}: `{var}` has no apparent lock guard")
        if failures:
            return (
                "FAILURE",
                f"Unguarded async-written state: {'; '.join(failures[:3])}",
            )
        if warnings:
            return (
                "WARNING",
                f"Potentially unguarded module-level state: {'; '.join(warnings[:3])}",
            )
        return (
            "HEALTHY",
            f"Checked {len(files)} files — no unguarded async-written module-level state detected",
        )

    # --- datetime.utcnow() deprecation ---
    if "utcnow" in hypothesis:
        hits = re.findall(r"datetime\.utcnow\(\)", content)
        file_hits = [
            str(f.name)
            for f in files
            if f.exists()
            and "datetime.utcnow()" in f.read_text(encoding="utf-8", errors="replace")
        ]
        if hits:
            return (
                "FAILURE",
                f"Found {len(hits)} datetime.utcnow() calls in {len(file_hits)} files: {', '.join(file_hits[:5])}",
            )
        return "HEALTHY", f"No datetime.utcnow() calls found in {len(files)} files"

    # --- N+1 query pattern detection ---
    if "n+1" in hypothesis or ("loop" in hypothesis and "db" in hypothesis):
        loop_db_pattern = re.findall(
            r"for\s+\w+\s+in\s+\w+[^:]+:\s*\n(?:.*\n){0,5}.*(?:session\.|qdrant\.|redis\.)",
            content,
        )
        if loop_db_pattern:
            return (
                "FAILURE",
                f"Potential N+1 pattern: DB call inside result loop ({len(loop_db_pattern)} instances)",
            )
        return "HEALTHY", "No N+1 DB-inside-loop patterns detected"

    # --- Fallback ---
    if missing:
        return (
            "INCONCLUSIVE",
            f"Read {len(files) - len(missing)}/{len(files)} files ({total_lines} lines). Missing: {', '.join(missing)}",
        )
    return (
        "INCONCLUSIVE",
        f"Read {len(files)} source files ({total_lines} lines) — requires agent analysis for verdict",
    )
