"""
bl/runners/document.py — Documentation completeness and accuracy runner (C-doc).

Checks whether documentation matches the codebase: endpoint coverage, function
coverage, example syntax validity, dead local links, keyword presence, and
doc freshness relative to code.

Handles questions with mode: document

Spec format (parsed from question['spec']):
    mode: document
    spec:
      code_path: "src/"
      doc_path: "README.md"          # or list of paths
      checks:
        - type: endpoint_coverage
          pattern: "@(app|router)\\.(get|post|put|delete|patch)"
        - type: function_coverage
        - type: example_syntax
          languages: ["python", "json"]
        - type: dead_links
        - type: keyword_presence
          keywords: ["installation", "usage", "configuration"]
        - type: freshness
          max_staleness_days: 30
      min_coverage: 0.8
      exclude_patterns: ["test_*", "_*"]
"""

import ast
import fnmatch
import json
import re
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Check helpers
# ---------------------------------------------------------------------------

_DEFAULT_ENDPOINT_PATTERN = r"@(app|router)\.(get|post|put|delete|patch)"
_ROUTE_CAPTURE_RE = re.compile(
    r"""@(?:app|router)\.(?:get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]""",
    re.IGNORECASE,
)
_FUNC_DEF_RE = re.compile(r"^\s*def ([a-zA-Z][a-zA-Z0-9_]*)\s*\(", re.MULTILINE)
_CODE_BLOCK_RE = re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL)
_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_MARKDOWN_REF_LINK_RE = re.compile(r"\[([^\]]+)\]\[([^\]]*)\]")
_MARKDOWN_REF_DEF_RE = re.compile(r"^\[([^\]]+)\]:\s*(\S+)", re.MULTILINE)


def _collect_source_files(code_path: Path, exclude_patterns: list[str]) -> list[Path]:
    """Return all Python source files under code_path, respecting excludes."""
    if code_path.is_file():
        return [code_path]

    files = []
    for f in code_path.rglob("*.py"):
        name = f.name
        excluded = any(fnmatch.fnmatch(name, pat) for pat in exclude_patterns)
        if not excluded:
            files.append(f)
    return sorted(files)


def _collect_doc_files(doc_path_spec) -> list[Path]:
    """Resolve doc_path to a list of Path objects."""
    if isinstance(doc_path_spec, str):
        return [Path(doc_path_spec)]
    if isinstance(doc_path_spec, list):
        return [Path(p) for p in doc_path_spec]
    return []


def _read_doc_text(doc_paths: list[Path]) -> str:
    """Read and concatenate all doc files into one string."""
    parts = []
    for dp in doc_paths:
        if dp.exists() and dp.is_file():
            parts.append(dp.read_text(encoding="utf-8", errors="replace"))
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Check: endpoint_coverage
# ---------------------------------------------------------------------------


def _check_endpoint_coverage(
    source_files: list[Path],
    doc_text: str,
    pattern: str,
    min_coverage: float,
) -> dict:
    """Find all API routes in source and check they appear in docs."""
    route_re = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
    found_routes = []

    for sf in source_files:
        try:
            src = sf.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Only scan files that actually have the decorator pattern
        if not route_re.search(src):
            continue

        # Extract the path string from each decorator
        for m in _ROUTE_CAPTURE_RE.finditer(src):
            route_path = m.group(1)
            found_routes.append(route_path)

    if not found_routes:
        return {
            "passed": True,
            "coverage": None,
            "issues": [],
            "count": 0,
            "note": "No routes found in source — check that code_path points to API files",
        }

    documented = []
    missing = []
    for route in found_routes:
        if route in doc_text:
            documented.append(route)
        else:
            missing.append(route)

    coverage = len(documented) / len(found_routes)
    passed = coverage >= min_coverage

    issues = [f"Missing: {r}" for r in missing]
    return {
        "passed": passed,
        "coverage": round(coverage, 3),
        "issues": issues,
        "count": len(found_routes),
    }


# ---------------------------------------------------------------------------
# Check: function_coverage
# ---------------------------------------------------------------------------


def _check_function_coverage(
    source_files: list[Path],
    doc_text: str,
    min_coverage: float,
) -> dict:
    """Find all public functions in source and check they appear in docs."""
    public_funcs = []

    for sf in source_files:
        try:
            src = sf.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in _FUNC_DEF_RE.finditer(src):
            name = m.group(1)
            # Public = no leading underscore
            if not name.startswith("_"):
                public_funcs.append(name)

    # Deduplicate while preserving order
    seen = set()
    unique_funcs = []
    for fn in public_funcs:
        if fn not in seen:
            seen.add(fn)
            unique_funcs.append(fn)

    if not unique_funcs:
        return {
            "passed": True,
            "coverage": None,
            "issues": [],
            "count": 0,
            "note": "No public functions found in source",
        }

    documented = [fn for fn in unique_funcs if fn in doc_text]
    missing = [fn for fn in unique_funcs if fn not in doc_text]

    coverage = len(documented) / len(unique_funcs)
    passed = coverage >= min_coverage

    issues = [f"Undocumented function: {fn}" for fn in missing]
    return {
        "passed": passed,
        "coverage": round(coverage, 3),
        "issues": issues,
        "count": len(unique_funcs),
    }


# ---------------------------------------------------------------------------
# Check: example_syntax
# ---------------------------------------------------------------------------


def _try_parse_python(code: str) -> str | None:
    """Return an error message if code is not valid Python, else None."""
    try:
        ast.parse(code)
        return None
    except SyntaxError as e:
        return str(e)


def _try_parse_json(code: str) -> str | None:
    """Return an error message if code is not valid JSON, else None."""
    try:
        json.loads(code)
        return None
    except json.JSONDecodeError as e:
        return str(e)


_SYNTAX_PARSERS = {
    "python": _try_parse_python,
    "py": _try_parse_python,
    "json": _try_parse_json,
}


def _check_example_syntax(doc_text: str, languages: list[str]) -> dict:
    """Parse code blocks in doc_text and report which fail to parse."""
    lang_set = {lang.lower() for lang in (languages or [])}
    total = 0
    failed_blocks = []

    for m in _CODE_BLOCK_RE.finditer(doc_text):
        lang = (m.group(1) or "").lower().strip()
        code = m.group(2)

        if lang_set and lang not in lang_set:
            continue

        parser = _SYNTAX_PARSERS.get(lang)
        if parser is None:
            continue

        total += 1
        error = parser(code)
        if error is not None:
            # Truncate code snippet to first 60 chars for the issue message
            snippet = code[:60].replace("\n", " ").strip()
            failed_blocks.append(f"Invalid {lang} block: {error} — `{snippet}...`")

    if total == 0:
        return {
            "passed": True,
            "coverage": None,
            "issues": [],
            "count": 0,
            "note": "No parseable code blocks found",
        }

    fail_rate = len(failed_blocks) / total
    # FAILURE threshold: >20% of syntax examples fail
    passed = fail_rate <= 0.20

    return {
        "passed": passed,
        "coverage": round(1.0 - fail_rate, 3),
        "issues": failed_blocks,
        "count": total,
    }


# ---------------------------------------------------------------------------
# Check: dead_links
# ---------------------------------------------------------------------------


def _check_dead_links(doc_paths: list[Path], doc_text: str) -> dict:
    """Find local file links in docs that don't exist on disk."""
    # Use the directory of the first doc as base for resolving relative links
    base_dirs = [dp.parent for dp in doc_paths if dp.exists()]
    base_dir = base_dirs[0] if base_dirs else Path(".")

    # Collect all inline links
    all_links = []
    for m in _MARKDOWN_LINK_RE.finditer(doc_text):
        all_links.append((m.group(1), m.group(2)))

    # Collect reference-style links: [text][ref] with [ref]: url definitions
    ref_defs: dict[str, str] = {}
    for m in _MARKDOWN_REF_DEF_RE.finditer(doc_text):
        ref_defs[m.group(1).lower()] = m.group(2)

    for m in _MARKDOWN_REF_LINK_RE.finditer(doc_text):
        text = m.group(1)
        ref_key = (m.group(2) or text).lower()
        url = ref_defs.get(ref_key)
        if url:
            all_links.append((text, url))

    dead = []
    checked = 0

    for text, url in all_links:
        # Skip external links
        if url.startswith(("http://", "https://", "ftp://", "mailto:", "#")):
            continue

        # Strip fragment from local path
        local_path = url.split("#")[0]
        if not local_path:
            continue

        checked += 1
        resolved = (base_dir / local_path).resolve()
        if not resolved.exists():
            dead.append(f"Dead link: [{text}]({url})")

    return {
        "passed": len(dead) == 0,
        "coverage": None,
        "issues": dead,
        "count": checked,
    }


# ---------------------------------------------------------------------------
# Check: keyword_presence
# ---------------------------------------------------------------------------


def _check_keyword_presence(doc_text: str, keywords: list[str]) -> dict:
    """Check that all required keywords appear in doc_text (case-insensitive)."""
    doc_lower = doc_text.lower()
    missing = []
    for kw in keywords:
        if kw.lower() not in doc_lower:
            missing.append(f"Missing keyword: '{kw}'")

    total = len(keywords)
    present = total - len(missing)
    coverage = present / total if total > 0 else 1.0

    return {
        "passed": len(missing) == 0,
        "coverage": round(coverage, 3),
        "issues": missing,
        "count": total,
    }


# ---------------------------------------------------------------------------
# Check: freshness
# ---------------------------------------------------------------------------


def _check_freshness(
    source_files: list[Path],
    doc_paths: list[Path],
    max_staleness_days: int,
) -> dict:
    """Fail if docs are older than code by more than max_staleness_days."""
    existing_docs = [dp for dp in doc_paths if dp.exists()]
    existing_src = [sf for sf in source_files if sf.exists()]

    if not existing_docs:
        return {
            "passed": False,
            "coverage": None,
            "issues": ["Doc files not found — cannot check freshness"],
            "count": 0,
        }
    if not existing_src:
        return {
            "passed": True,
            "coverage": None,
            "issues": [],
            "count": 0,
            "note": "No source files found — freshness check skipped",
        }

    doc_mtime = max(dp.stat().st_mtime for dp in existing_docs)
    src_mtime = max(sf.stat().st_mtime for sf in existing_src)

    staleness_seconds = src_mtime - doc_mtime
    staleness_days = staleness_seconds / 86400.0

    if staleness_days <= 0:
        # Docs are newer than or same age as code
        return {
            "passed": True,
            "coverage": None,
            "issues": [],
            "count": 1,
        }

    doc_dt = datetime.fromtimestamp(doc_mtime, tz=timezone.utc).strftime("%Y-%m-%d")
    src_dt = datetime.fromtimestamp(src_mtime, tz=timezone.utc).strftime("%Y-%m-%d")
    passed = staleness_days <= max_staleness_days

    issues = []
    if not passed:
        issues.append(
            f"Docs last updated {doc_dt}, code last updated {src_dt} "
            f"({staleness_days:.1f} days stale, threshold: {max_staleness_days}d)"
        )

    return {
        "passed": passed,
        "coverage": None,
        "issues": issues,
        "count": 1,
        "staleness_days": round(staleness_days, 1),
    }


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def run_document(question: dict) -> dict:
    """Run documentation checks and return a verdict envelope."""
    spec = question.get("spec") or {}

    if not spec:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "document runner: no spec provided",
            "data": {"error": "missing_spec"},
            "details": "question['spec'] is empty. Provide code_path, doc_path, and checks.",
        }

    # Resolve paths
    code_path_raw = spec.get("code_path")
    doc_path_raw = spec.get("doc_path")

    if not code_path_raw or not doc_path_raw:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "document runner: spec missing code_path or doc_path",
            "data": {"error": "missing_paths"},
            "details": "spec must include both 'code_path' and 'doc_path'.",
        }

    code_path = Path(code_path_raw)
    doc_paths = _collect_doc_files(doc_path_raw)

    # Verify at least one doc file exists
    existing_docs = [dp for dp in doc_paths if dp.exists()]
    if not existing_docs:
        missing_paths = [str(dp) for dp in doc_paths]
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"document runner: doc file(s) not found: {', '.join(missing_paths)}",
            "data": {"error": "doc_not_found", "paths": missing_paths},
            "details": f"Could not read doc file(s): {', '.join(missing_paths)}",
        }

    if not code_path.exists():
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"document runner: code_path not found: {code_path}",
            "data": {"error": "code_not_found", "path": str(code_path)},
            "details": f"code_path does not exist: {code_path}",
        }

    # Common inputs
    checks_spec = spec.get("checks") or []
    min_coverage = float(spec.get("min_coverage", 0.8))
    exclude_patterns = list(spec.get("exclude_patterns") or [])
    doc_text = _read_doc_text(doc_paths)
    source_files = _collect_source_files(code_path, exclude_patterns)

    if not checks_spec:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "document runner: no checks specified in spec",
            "data": {"error": "no_checks"},
            "details": "spec.checks is empty. Add at least one check type.",
        }

    # Run each check
    check_results: dict[str, dict] = {}
    all_issues: list[str] = []
    coverage_values: list[float] = []

    checks_run = 0
    checks_passed = 0

    for check in checks_spec:
        check_type = check.get("type", "")
        result: dict = {}

        if check_type == "endpoint_coverage":
            pattern = check.get("pattern", _DEFAULT_ENDPOINT_PATTERN)
            result = _check_endpoint_coverage(
                source_files, doc_text, pattern, min_coverage
            )

        elif check_type == "function_coverage":
            result = _check_function_coverage(source_files, doc_text, min_coverage)

        elif check_type == "example_syntax":
            languages = check.get("languages") or []
            result = _check_example_syntax(doc_text, languages)

        elif check_type == "dead_links":
            result = _check_dead_links(doc_paths, doc_text)

        elif check_type == "keyword_presence":
            keywords = check.get("keywords") or []
            if not keywords:
                result = {
                    "passed": True,
                    "coverage": None,
                    "issues": [],
                    "count": 0,
                    "note": "No keywords specified",
                }
            else:
                result = _check_keyword_presence(doc_text, keywords)

        elif check_type == "freshness":
            max_staleness = int(check.get("max_staleness_days", 30))
            result = _check_freshness(source_files, doc_paths, max_staleness)

        else:
            result = {
                "passed": False,
                "coverage": None,
                "issues": [f"Unknown check type: '{check_type}'"],
                "count": 0,
            }

        check_results[check_type] = result
        checks_run += 1
        if result.get("passed"):
            checks_passed += 1
        all_issues.extend(result.get("issues") or [])
        if result.get("coverage") is not None:
            coverage_values.append(result["coverage"])

    # Aggregate coverage
    agg_coverage = (
        round(sum(coverage_values) / len(coverage_values), 3)
        if coverage_values
        else None
    )

    # Determine overall verdict
    verdict = _determine_verdict(check_results, min_coverage)

    # Build summary
    issue_count = len(all_issues)
    summary_parts = [f"{checks_passed}/{checks_run} checks passed"]
    if agg_coverage is not None:
        summary_parts.append(f"coverage {agg_coverage:.0%}")
    if issue_count > 0:
        summary_parts.append(f"{issue_count} issue(s) found")
    summary = ", ".join(summary_parts)

    # Build details
    detail_lines = [
        "Document runner results",
        f"  code_path: {code_path}",
        f"  doc_path:  {', '.join(str(dp) for dp in doc_paths)}",
        f"  source files scanned: {len(source_files)}",
        "",
    ]
    for ctype, cr in check_results.items():
        status = "PASS" if cr.get("passed") else "FAIL"
        cov = cr.get("coverage")
        cov_str = f" (coverage: {cov:.0%})" if cov is not None else ""
        count = cr.get("count", 0)
        detail_lines.append(f"[{status}] {ctype}{cov_str} — {count} item(s) checked")
        for issue in (cr.get("issues") or [])[:10]:
            detail_lines.append(f"       • {issue}")
        if len(cr.get("issues") or []) > 10:
            detail_lines.append(f"       … and {len(cr['issues']) - 10} more")
        if cr.get("note"):
            detail_lines.append(f"       note: {cr['note']}")

    if all_issues:
        detail_lines.append("")
        detail_lines.append(f"All issues ({len(all_issues)}):")
        for issue in all_issues:
            detail_lines.append(f"  • {issue}")

    return {
        "verdict": verdict,
        "summary": summary,
        "data": {
            "checks_run": checks_run,
            "checks_passed": checks_passed,
            "coverage": agg_coverage,
            "issues": all_issues,
            "check_results": check_results,
        },
        "details": "\n".join(detail_lines),
    }


# ---------------------------------------------------------------------------
# Verdict logic
# ---------------------------------------------------------------------------

_COVERAGE_CHECK_TYPES = {"endpoint_coverage", "function_coverage"}


def _determine_verdict(check_results: dict[str, dict], min_coverage: float) -> str:
    """Determine the overall verdict from all check results."""
    has_failure = False
    has_warning = False

    for check_type, result in check_results.items():
        passed = result.get("passed", False)
        coverage = result.get("coverage")

        if not passed:
            if check_type in _COVERAGE_CHECK_TYPES and coverage is not None:
                if coverage < min_coverage:
                    has_failure = True
                else:
                    # Coverage present but below 1.0 — warning
                    has_warning = True

            elif check_type == "example_syntax":
                # >20% failure rate triggers FAILURE (set by _check_example_syntax)
                has_failure = True

            elif check_type == "freshness":
                has_failure = True

            elif check_type == "dead_links":
                # Dead links are a warning by default, not hard failure
                has_warning = True

            elif check_type == "keyword_presence":
                has_warning = True

            else:
                has_failure = True

        else:
            # Passed but coverage < 1.0 → warning
            if coverage is not None and coverage < 1.0:
                has_warning = True

    if has_failure:
        return "FAILURE"
    if has_warning:
        return "WARNING"
    return "HEALTHY"
