"""
bl/runners/contract.py — Static analysis runner for Solana/Anchor smart contracts.

Identifies common vulnerability patterns, missing invariants, and dangerous patterns
in Rust smart contract code without requiring a running chain.

Handles questions with mode: contract

Spec format (parsed from question['spec']):
    mode: contract
    spec:
      path: "programs/my-program/src/"   # dir or file (.rs / .sol)
      framework: "anchor"                 # "anchor" | "raw_solana" | "generic"

      checks:
        - type: invariant_coverage
          # Anchor: every #[account] struct field should have a constraint
        - type: signer_checks
          # Every instruction handler must validate at least one signer
        - type: owner_checks
          # Account owner must be validated
        - type: overflow_patterns
          # Flag unchecked arithmetic (a + b, a * b) without checked_ / saturating_
        - type: reentrancy_patterns
          # State mutation before CPI call (invoke / invoke_signed)
        - type: seed_canonicalization
          # create_program_address preferred to find_program_address — flag usages
        - type: pattern_search
          patterns:
            - pattern: "unsafe"
              severity: "warning"
              message: "Unsafe block detected"

      max_unchecked_fields: 0     # FAILURE if invariant_coverage exceeds this
      max_overflow_sites: 5       # WARNING threshold for overflow patterns
      exclude: ["tests/", "migrations/"]
"""

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Source file collection
# ---------------------------------------------------------------------------

_RS_EXTENSIONS = {".rs"}
_SOL_EXTENSIONS = {".sol"}


def _collect_source_files(
    path: Path,
    framework: str,
    exclude_dirs: list[str],
) -> list[Path]:
    """Walk path and return all relevant source files (filtered by framework)."""
    extensions = _SOL_EXTENSIONS if framework == "generic_sol" else _RS_EXTENSIONS

    if path.is_file():
        return [path] if path.suffix in extensions else []

    files: list[Path] = []
    for f in path.rglob("*"):
        if f.suffix not in extensions:
            continue
        # Exclude specified dirs — check each path component
        rel_parts = f.parts
        excluded = any(
            any(excl.strip("/") in part for part in rel_parts) for excl in exclude_dirs
        )
        if not excluded:
            files.append(f)
    return sorted(files)


def _read_file(path: Path) -> str:
    """Read a source file; return empty string on error."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Finding helpers
# ---------------------------------------------------------------------------

Finding = dict  # {file, line, snippet, severity, message}


def _make_finding(
    path: Path,
    line_no: int,
    snippet: str,
    severity: str,
    message: str,
) -> Finding:
    return {
        "file": str(path),
        "line": line_no,
        "snippet": snippet.strip()[:120],
        "severity": severity,
        "message": message,
    }


def _lines_with_numbers(src: str) -> list[tuple[int, str]]:
    """Return [(1-based line number, line text), ...]."""
    return list(enumerate(src.splitlines(), start=1))


# ---------------------------------------------------------------------------
# Check: invariant_coverage
# ---------------------------------------------------------------------------

# Matches Anchor #[account(...)] attribute lines that have at least one constraint
_ACCOUNT_ATTR_RE = re.compile(r"#\[account\(([^)]*)\)\]", re.MULTILINE)
# Matches a struct field declaration inside an Accounts struct context
_STRUCT_FIELD_RE = re.compile(r"^\s+pub\s+\w+\s*:\s*.+,?\s*$", re.MULTILINE)
# An Anchor Accounts derive struct
_ACCOUNTS_STRUCT_RE = re.compile(
    r"#\[derive\([^)]*Accounts[^)]*\)\].*?pub\s+struct\s+\w+\s*<[^>]*>\s*\{([^}]+)\}",
    re.DOTALL,
)
# Individual field inside struct with optional preceding attribute
_FIELD_WITH_ATTR_RE = re.compile(
    r"((?:#\[[^\]]*\]\s*)*)\s*pub\s+(\w+)\s*:\s*([^,\n]+)",
    re.MULTILINE,
)


def _check_invariant_coverage(files: list[Path]) -> list[Finding]:
    """
    For Anchor programs: each field in an Accounts struct should have at least
    one #[account(...)] constraint. Report fields with no constraints.
    """
    findings: list[Finding] = []

    for path in files:
        src = _read_file(path)
        if not src:
            continue

        # Find all Accounts derive structs
        for struct_match in _ACCOUNTS_STRUCT_RE.finditer(src):
            struct_body = struct_match.group(1)
            # Walk field declarations; check for preceding #[account(...)]
            for field_match in _FIELD_WITH_ATTR_RE.finditer(struct_body):
                attrs_block = field_match.group(1)
                field_name = field_match.group(2)

                # Skip special fields: bump, authority, system_program, etc.
                # (they rarely need explicit constraints)
                if field_name in {
                    "bump",
                    "authority",
                    "system_program",
                    "token_program",
                    "rent",
                }:
                    continue

                has_account_attr = bool(re.search(r"#\[account\(", attrs_block))
                if not has_account_attr:
                    # Compute approximate line number
                    offset = struct_match.start() + struct_body.find(
                        field_match.group(0)
                    )
                    line_no = src[:offset].count("\n") + 1
                    findings.append(
                        _make_finding(
                            path,
                            line_no,
                            f"pub {field_name}: ...",
                            "warning",
                            f"Field '{field_name}' in Accounts struct has no #[account(...)] constraint",
                        )
                    )

    return findings


# ---------------------------------------------------------------------------
# Check: signer_checks
# ---------------------------------------------------------------------------

# Anchor signer type patterns
_SIGNER_PATTERNS = [
    re.compile(r"\bSigner\b"),
    re.compile(r"#\[account\([^)]*signer[^)]*\)\]"),
    re.compile(r"\bhas_one\s*=\s*\w*signer\w*"),
    re.compile(r"\.is_signer\b"),
    re.compile(r"require!\s*\([^,)]*\.is_signer"),
]

# Instruction handler: public async/non-async fn taking Context<...>
_HANDLER_RE = re.compile(
    r"pub\s+(?:async\s+)?fn\s+(\w+)\s*\(\s*ctx\s*:\s*Context\s*<\s*(\w+)\s*>",
    re.MULTILINE,
)


def _accounts_struct_has_signer(struct_name: str, src: str) -> bool:
    """Check if the named Accounts struct contains any signer validation."""
    # Find the struct definition
    struct_def_re = re.compile(
        rf"pub\s+struct\s+{re.escape(struct_name)}\s*(?:<[^>]*>)?\s*\{{([^}}]+)\}}",
        re.DOTALL,
    )
    m = struct_def_re.search(src)
    if not m:
        return False
    body = m.group(1)
    return any(pat.search(body) for pat in _SIGNER_PATTERNS)


def _check_signer_checks(files: list[Path]) -> list[Finding]:
    """
    Each instruction handler (pub fn taking Context<T>) should validate at least
    one signer — either via the Signer type, is_signer, or a require! check.
    """
    findings: list[Finding] = []

    for path in files:
        src = _read_file(path)
        if not src:
            continue

        lines = _lines_with_numbers(src)

        for m in _HANDLER_RE.finditer(src):
            fn_name = m.group(1)
            ctx_type = m.group(2)
            line_no = src[: m.start()].count("\n") + 1

            # Check whether the Accounts struct references a signer
            has_signer = _accounts_struct_has_signer(ctx_type, src)

            # Also scan the function body for explicit .is_signer / require! checks
            # Find the function body by locating the opening brace after the signature
            fn_start = m.end()
            brace_depth = 0
            fn_body_start = None
            for i, ch in enumerate(src[fn_start:], fn_start):
                if ch == "{":
                    if fn_body_start is None:
                        fn_body_start = i
                    brace_depth += 1
                elif ch == "}":
                    brace_depth -= 1
                    if brace_depth == 0:
                        fn_body = src[fn_body_start : i + 1] if fn_body_start else ""
                        has_signer = has_signer or any(
                            pat.search(fn_body) for pat in _SIGNER_PATTERNS
                        )
                        break

            if not has_signer:
                snippet = lines[line_no - 1][1] if line_no <= len(lines) else ""
                findings.append(
                    _make_finding(
                        path,
                        line_no,
                        snippet,
                        "critical",
                        f"Handler '{fn_name}' has no signer validation (Context<{ctx_type}>)",
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# Check: owner_checks
# ---------------------------------------------------------------------------

_OWNER_PATTERNS = [
    re.compile(r"#\[account\([^)]*owner\s*="),
    re.compile(r"#\[account\([^)]*has_one\s*="),
    re.compile(r"\.owner\s*=="),
    re.compile(r"require_keys_eq!\s*\([^,)]*\.owner"),
    re.compile(r"Account\s*<\s*'_\s*,"),  # typed Account<'_, T> implies owner check
    re.compile(r"\bProgram\b"),  # Program<'_, T> accounts have implicit owner check
]


def _check_owner_checks(files: list[Path]) -> list[Finding]:
    """
    Account owner must be validated. Flag Accounts struct fields that use
    AccountInfo or UncheckedAccount without an explicit owner constraint.
    """
    findings: list[Finding] = []

    # Patterns that indicate an unchecked account (no implicit owner validation)
    unchecked_re = re.compile(
        r"((?:#\[[^\]]*\]\s*)*)\s*pub\s+(\w+)\s*:\s*(AccountInfo|UncheckedAccount)\s*<",
        re.MULTILINE,
    )

    for path in files:
        src = _read_file(path)
        if not src:
            continue

        for m in unchecked_re.finditer(src):
            attrs_block = m.group(1)
            field_name = m.group(2)
            account_type = m.group(3)

            has_owner = bool(
                re.search(
                    r"#\[account\([^)]*(?:owner|has_one|constraint)[^)]*\)\]",
                    attrs_block,
                )
            )
            if not has_owner:
                line_no = src[: m.start()].count("\n") + 1
                findings.append(
                    _make_finding(
                        path,
                        line_no,
                        f"pub {field_name}: {account_type}<...>",
                        "warning",
                        f"Field '{field_name}' uses {account_type} without owner/constraint validation",
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# Check: overflow_patterns
# ---------------------------------------------------------------------------

# Arithmetic operators on identifiers without safe wrappers
# Matches patterns like: a + b, a * b, amount - fee (but not safe calls)
_ARITH_OP_RE = re.compile(
    r"\b(\w+)\s*([+\-*])\s*(\w+)\b(?!\s*\()",  # exclude function-call-like usage
)
# Safe arithmetic patterns — if these appear near the site, it's OK
_SAFE_ARITH_RE = re.compile(
    r"\b(?:checked_add|checked_sub|checked_mul|checked_div"
    r"|saturating_add|saturating_sub|saturating_mul"
    r"|wrapping_add|wrapping_sub|wrapping_mul"
    r"|u128::from|i128::from"
    r"|overflow_ops)\b"
)
# Lines to skip (imports, comments, use statements, string literals)
_SKIP_LINE_RE = re.compile(r"^\s*(?://|use |pub use |#\[|let\s+\w+\s*=\s*\")")


def _check_overflow_patterns(files: list[Path]) -> list[Finding]:
    """
    Flag unchecked arithmetic: +, -, * on identifiers that aren't wrapped in
    checked_ or saturating_ variants.
    """
    findings: list[Finding] = []

    for path in files:
        src = _read_file(path)
        if not src:
            continue

        for line_no, line in _lines_with_numbers(src):
            if _SKIP_LINE_RE.match(line):
                continue

            # Skip comment-only lines
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("*"):
                continue

            # Skip if line itself uses safe arithmetic
            if _SAFE_ARITH_RE.search(line):
                continue

            for m in _ARITH_OP_RE.finditer(line):
                lhs = m.group(1)
                op = m.group(2)
                rhs = m.group(3)

                # Skip numeric literals, loop variables, and indexing
                if lhs.isdigit() or rhs.isdigit():
                    continue
                if lhs in {"i", "j", "k", "n", "idx", "len"}:
                    continue

                # Only flag if neither side looks like a loop/string artifact
                if len(lhs) < 2 or len(rhs) < 2:
                    continue

                findings.append(
                    _make_finding(
                        path,
                        line_no,
                        line.strip()[:80],
                        "warning",
                        f"Unchecked arithmetic '{lhs} {op} {rhs}' — use checked_/saturating_ variants",
                    )
                )
                # Report max 1 finding per line to avoid noise
                break

    return findings


# ---------------------------------------------------------------------------
# Check: reentrancy_patterns
# ---------------------------------------------------------------------------

# CPI call patterns (Anchor invoke wrappers and raw cross-program invocations)
_CPI_PATTERNS = [
    re.compile(r"\binvoke\s*\("),
    re.compile(r"\binvoke_signed\s*\("),
    re.compile(r"\bCpiContext\b"),
    re.compile(r"::transfer\s*\("),
    re.compile(r"::mint_to\s*\("),
    re.compile(r"::burn\s*\("),
]
# State mutation patterns (field assignment on ctx.accounts)
_STATE_MUTATION_RE = re.compile(r"ctx\.accounts\.\w+(?:\.\w+)*\s*[+\-*]?=")


def _check_reentrancy_patterns(files: list[Path]) -> list[Finding]:
    """
    Basic reentrancy heuristic: flag functions where a CPI call appears
    *before* a state mutation (ctx.accounts.x.field = ...).

    This is a conservative check — false positives are possible.
    """
    findings: list[Finding] = []

    for path in files:
        src = _read_file(path)
        if not src:
            continue

        # Find instruction handler bodies
        for m in _HANDLER_RE.finditer(src):
            fn_name = m.group(1)
            fn_start = m.end()
            brace_depth = 0
            fn_body_start = None
            fn_body_end = None

            for i, ch in enumerate(src[fn_start:], fn_start):
                if ch == "{":
                    if fn_body_start is None:
                        fn_body_start = i
                    brace_depth += 1
                elif ch == "}":
                    brace_depth -= 1
                    if brace_depth == 0:
                        fn_body_end = i
                        break

            if fn_body_start is None or fn_body_end is None:
                continue

            fn_body = src[fn_body_start:fn_body_end]

            # Find first CPI call offset
            first_cpi_offset = None
            for cpi_re in _CPI_PATTERNS:
                cm = cpi_re.search(fn_body)
                if cm and (first_cpi_offset is None or cm.start() < first_cpi_offset):
                    first_cpi_offset = cm.start()

            if first_cpi_offset is None:
                continue  # No CPI in this handler

            # Check for state mutation *after* the CPI
            post_cpi = fn_body[first_cpi_offset:]
            mutation_match = _STATE_MUTATION_RE.search(post_cpi)

            if mutation_match:
                line_no = (
                    src[:fn_body_start].count("\n")
                    + fn_body[:first_cpi_offset].count("\n")
                    + 1
                )
                findings.append(
                    _make_finding(
                        path,
                        line_no,
                        f"fn {fn_name}(...) — CPI before state write",
                        "critical",
                        f"Potential reentrancy in '{fn_name}': CPI call precedes state mutation. "
                        "Move state updates before external calls.",
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# Check: seed_canonicalization
# ---------------------------------------------------------------------------

_CREATE_PDA_RE = re.compile(r"\bcreate_program_address\s*\(")


def _check_seed_canonicalization(files: list[Path]) -> list[Finding]:
    """
    create_program_address does not enforce canonical bump seeds.
    Flag all uses — find_program_address (which finds the canonical bump) is preferred.
    """
    findings: list[Finding] = []

    for path in files:
        src = _read_file(path)
        if not src:
            continue

        for line_no, line in _lines_with_numbers(src):
            if _CREATE_PDA_RE.search(line):
                findings.append(
                    _make_finding(
                        path,
                        line_no,
                        line.strip()[:80],
                        "warning",
                        "create_program_address used — prefer find_program_address to enforce canonical bump",
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# Check: pattern_search
# ---------------------------------------------------------------------------


def _check_pattern_search(
    files: list[Path],
    patterns: list[dict],
) -> list[Finding]:
    """
    User-defined pattern search. Each pattern dict has:
      pattern: str (regex)
      severity: "critical" | "warning" | "info"
      message: str
    """
    findings: list[Finding] = []

    compiled = []
    for p in patterns:
        raw = p.get("pattern", "")
        if not raw:
            continue
        try:
            compiled.append(
                (re.compile(raw), p.get("severity", "warning"), p.get("message", raw))
            )
        except re.error:
            pass  # Skip invalid patterns silently

    for path in files:
        src = _read_file(path)
        if not src:
            continue

        for line_no, line in _lines_with_numbers(src):
            for pat_re, severity, message in compiled:
                if pat_re.search(line):
                    findings.append(
                        _make_finding(
                            path, line_no, line.strip()[:80], severity, message
                        )
                    )
                    break  # One finding per line per file pass

    return findings


# ---------------------------------------------------------------------------
# Verdict determination
# ---------------------------------------------------------------------------


def _determine_verdict(
    all_findings: list[Finding],
    signer_failures: int,
    reentrancy_count: int,
    unchecked_fields: int,
    overflow_count: int,
    max_unchecked_fields: int,
    max_overflow_sites: int,
) -> tuple[str, str]:
    """Return (verdict, summary_string)."""
    critical = [f for f in all_findings if f["severity"] == "critical"]
    warnings = [f for f in all_findings if f["severity"] == "warning"]

    reasons_failure: list[str] = []
    reasons_warning: list[str] = []

    if signer_failures > 0:
        reasons_failure.append(f"{signer_failures} handler(s) with no signer check")
    if reentrancy_count > 0:
        reasons_failure.append(f"{reentrancy_count} reentrancy pattern(s)")
    if unchecked_fields > max_unchecked_fields:
        reasons_failure.append(
            f"{unchecked_fields} unchecked field(s) (max {max_unchecked_fields})"
        )

    if overflow_count > max_overflow_sites:
        reasons_warning.append(
            f"{overflow_count} unchecked arithmetic site(s) (threshold {max_overflow_sites})"
        )

    # Critical findings from pattern_search also cause FAILURE
    pattern_criticals = [
        f
        for f in critical
        if "Handler" not in f["message"] and "reentrancy" not in f["message"].lower()
    ]
    if pattern_criticals:
        reasons_failure.append(f"{len(pattern_criticals)} critical pattern finding(s)")

    total = len(all_findings)
    if reasons_failure:
        verdict = "FAILURE"
        summary = "; ".join(reasons_failure)
        if reasons_warning:
            summary += " | warnings: " + "; ".join(reasons_warning)
    elif reasons_warning or warnings:
        verdict = "WARNING"
        parts = reasons_warning[:]
        if not parts and warnings:
            parts.append(f"{len(warnings)} warning(s)")
        summary = "; ".join(parts)
    else:
        verdict = "HEALTHY"
        summary = f"No issues found — {total} total findings (all info)"

    if total == 0:
        summary = "No findings"

    return verdict, summary


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def run_contract(question: dict) -> dict:
    """Run static contract analysis and return a verdict envelope."""
    spec = question.get("spec") or {}

    if not spec:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "contract runner: no spec provided",
            "data": {"error": "missing_spec"},
            "details": "question['spec'] is empty. Provide path and checks.",
        }

    path_raw = spec.get("path")
    if not path_raw:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "contract runner: spec missing 'path'",
            "data": {"error": "missing_path"},
            "details": "spec must include 'path' pointing to a source file or directory.",
        }

    framework = spec.get("framework", "anchor").lower()
    source_path = Path(path_raw)

    if not source_path.exists():
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"contract runner: path not found: {source_path}",
            "data": {"error": "path_not_found", "path": str(source_path)},
            "details": f"Source path does not exist: {source_path}",
        }

    exclude_dirs = list(spec.get("exclude") or [])
    files = _collect_source_files(source_path, framework, exclude_dirs)

    if not files:
        ext = ".sol" if framework == "generic_sol" else ".rs"
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"contract runner: no {ext} files found under {source_path}",
            "data": {"error": "no_source_files", "path": str(source_path)},
            "details": (
                f"No {ext} files found. "
                f"Check that 'path' points to a directory containing {ext} sources "
                "and that exclude patterns are not too broad."
            ),
        }

    checks_spec = spec.get("checks") or []
    if not checks_spec:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "contract runner: no checks specified in spec",
            "data": {"error": "no_checks"},
            "details": "spec.checks is empty. Add at least one check type.",
        }

    max_unchecked_fields = int(spec.get("max_unchecked_fields", 0))
    max_overflow_sites = int(spec.get("max_overflow_sites", 5))

    # --- Run checks ---
    all_findings: list[Finding] = []
    checks_run: list[str] = []

    signer_findings: list[Finding] = []
    reentrancy_findings: list[Finding] = []
    invariant_findings: list[Finding] = []
    overflow_findings: list[Finding] = []

    for check in checks_spec:
        check_type = check.get("type", "")

        if check_type == "invariant_coverage":
            findings = _check_invariant_coverage(files)
            invariant_findings = findings
            all_findings.extend(findings)
            checks_run.append(check_type)

        elif check_type == "signer_checks":
            findings = _check_signer_checks(files)
            signer_findings = findings
            all_findings.extend(findings)
            checks_run.append(check_type)

        elif check_type == "owner_checks":
            findings = _check_owner_checks(files)
            all_findings.extend(findings)
            checks_run.append(check_type)

        elif check_type == "overflow_patterns":
            findings = _check_overflow_patterns(files)
            overflow_findings = findings
            all_findings.extend(findings)
            checks_run.append(check_type)

        elif check_type == "reentrancy_patterns":
            findings = _check_reentrancy_patterns(files)
            reentrancy_findings = findings
            all_findings.extend(findings)
            checks_run.append(check_type)

        elif check_type == "seed_canonicalization":
            findings = _check_seed_canonicalization(files)
            all_findings.extend(findings)
            checks_run.append(check_type)

        elif check_type == "pattern_search":
            patterns = check.get("patterns") or []
            findings = _check_pattern_search(files, patterns)
            all_findings.extend(findings)
            checks_run.append(check_type)

        else:
            # Unknown check type — record as inconclusive warning finding
            all_findings.append(
                _make_finding(
                    source_path, 0, "", "info", f"Unknown check type: '{check_type}'"
                )
            )

    # --- Aggregate counts ---
    by_severity: dict[str, int] = {"critical": 0, "warning": 0, "info": 0}
    for f in all_findings:
        sev = f["severity"]
        by_severity[sev] = by_severity.get(sev, 0) + 1

    verdict, summary = _determine_verdict(
        all_findings,
        signer_failures=len(signer_findings),
        reentrancy_count=len(reentrancy_findings),
        unchecked_fields=len(invariant_findings),
        overflow_count=len(overflow_findings),
        max_unchecked_fields=max_unchecked_fields,
        max_overflow_sites=max_overflow_sites,
    )

    # --- Build details string ---
    detail_lines = [
        "Contract static analysis results",
        f"  source path : {source_path}",
        f"  framework   : {framework}",
        f"  files scanned: {len(files)}",
        f"  checks run  : {', '.join(checks_run) or 'none'}",
        "",
        f"Findings: {len(all_findings)} total"
        f" (critical: {by_severity['critical']}"
        f", warning: {by_severity['warning']}"
        f", info: {by_severity['info']})",
        "",
    ]

    # Group findings by check type for readability
    _type_prefix = {
        "signer_checks": signer_findings,
        "reentrancy_patterns": reentrancy_findings,
        "invariant_coverage": invariant_findings,
        "overflow_patterns": overflow_findings,
    }

    for finding in all_findings[:50]:
        detail_lines.append(
            f"  [{finding['severity'].upper()}] {finding['file']}:{finding['line']} "
            f"— {finding['message']}"
        )
        if finding["snippet"]:
            detail_lines.append(f"    {finding['snippet']}")

    if len(all_findings) > 50:
        detail_lines.append(f"  … and {len(all_findings) - 50} more findings")

    return {
        "verdict": verdict,
        "summary": summary,
        "data": {
            "files_scanned": len(files),
            "total_findings": len(all_findings),
            "by_severity": by_severity,
            "checks_run": checks_run,
        },
        "details": "\n".join(detail_lines),
    }
