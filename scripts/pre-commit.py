#!/usr/bin/env python3
"""
Pre-commit hook — implements lint-guard + commit-reviewer agents as a real script.

Lint-guard:  detects stack, runs ruff/eslint/clippy, auto-fixes, re-stages.
Commit-reviewer: pattern-based scan for secrets, silent swallows, injection risks.

Exits 0 (clean/warnings only) or 1 (BLOCK — must fix before committing).
"""

import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run(cmd: list[str], cwd: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd
    )


def get_staged_files() -> list[str]:
    result = run(["git", "diff", "--staged", "--name-only"])
    return [f.strip() for f in (result.stdout or "").splitlines() if f.strip()]


def get_staged_diff() -> str:
    return run(["git", "diff", "--staged"]).stdout or ""


def tool_available(name: str) -> bool:
    return run(["where" if sys.platform == "win32" else "which", name]).returncode == 0


# ---------------------------------------------------------------------------
# Lint Guard
# ---------------------------------------------------------------------------


def run_lint_guard(staged_files: list[str]) -> tuple[list[str], list[str]]:
    """Run linters on staged files. Auto-fix where possible. Returns (errors, fixed_files)."""
    errors: list[str] = []
    fixed: list[str] = []

    py_files = [f for f in staged_files if f.endswith(".py")]
    ts_files = [f for f in staged_files if f.endswith((".ts", ".tsx", ".js", ".jsx"))]
    rs_files = [f for f in staged_files if f.endswith(".rs")]

    # Python — ruff
    if py_files:
        if tool_available("ruff"):
            run(["ruff", "check", "--fix"] + py_files)
            run(["ruff", "format"] + py_files)
            check = run(["ruff", "check"] + py_files)
            if check.returncode != 0:
                errors.extend(
                    [
                        f"  {ln}"
                        for ln in check.stdout.strip().splitlines()
                        if ln.strip()
                    ]
                )
            else:
                fixed.extend(py_files)
                run(["git", "add"] + py_files)
        else:
            # Fallback to flake8 (check-only)
            if tool_available("flake8"):
                check = run(["flake8"] + py_files)
                if check.returncode != 0:
                    errors.extend(
                        [
                            f"  {ln}"
                            for ln in check.stdout.strip().splitlines()
                            if ln.strip()
                        ]
                    )
            else:
                print("[lint-guard] ruff/flake8 not found — skipping Python lint")

    # TypeScript/JavaScript — eslint
    if ts_files:
        eslint_cmd = ["npx", "--no-install", "eslint"]
        check_version = run(eslint_cmd + ["--version"])
        if check_version.returncode == 0:
            run(eslint_cmd + ["--fix"] + ts_files)
            check = run(eslint_cmd + ts_files)
            if check.returncode != 0:
                errors.extend(
                    [
                        f"  {ln}"
                        for ln in check.stdout.strip().splitlines()
                        if ln.strip()
                    ]
                )
            else:
                fixed.extend(ts_files)
                run(["git", "add"] + ts_files)
        else:
            print("[lint-guard] eslint not found — skipping JS/TS lint")

    # Rust — clippy (check-only, no auto-fix)
    if rs_files and tool_available("cargo"):
        # Find unique Cargo.toml roots for all staged .rs files
        cargo_roots: set[str] = set()
        for rs_file in rs_files:
            d = Path(rs_file).resolve().parent
            for _ in range(15):
                if (d / "Cargo.toml").exists():
                    cargo_roots.add(str(d))
                    break
                parent = d.parent
                if parent == d:
                    break
                d = parent
        for cargo_root in cargo_roots:
            check = run(["cargo", "clippy", "--", "-D", "warnings"], cwd=cargo_root)
            if check.returncode != 0:
                errors.extend(
                    [
                        f"  {ln}"
                        for ln in (check.stdout + check.stderr).strip().splitlines()
                        if ln.strip() and not ln.startswith("warning: unused")
                    ][:20]
                )

    return errors, fixed


# ---------------------------------------------------------------------------
# Commit Reviewer — pattern-based
# ---------------------------------------------------------------------------

# Lines matching these patterns → BLOCK (do not commit)
_BLOCK_PATTERNS: list[tuple[str, str]] = [
    (
        r'(?i)(api_key|apikey|secret_key|password|passwd|auth_token|access_token)\s*=\s*["\'][^"\']{8,}["\']',
        "Hardcoded secret/credential",
    ),
    (
        r"(?:sk-|pk_live_|ghp_|ghs_|AKIA|eyJhbGci)[a-zA-Z0-9_\-]{16,}",
        "Possible live API key value",
    ),
    (
        r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----",
        "Private key embedded in file",
    ),
    (
        r"subprocess\.[a-z_]+\([^)]*shell\s*=\s*True[^)]*\+",
        "Command injection risk (shell=True with string concat)",
    ),
    (
        r"TODO[:\s]+remove before commit",
        "Explicit TODO to remove before commit",
    ),
]

# Lines matching these → REQUEST_CHANGES (warn but don't block)
_WARN_PATTERNS: list[tuple[str, str]] = [
    (r"except\s*:\s*$", "Bare except — swallows all exceptions"),
    (r"except\s*:\s*pass", "Silent bare except"),
    (
        r"except\s+Exception\s*(?:as\s+\w+)?\s*:\s*(?:pass\s*)?$",
        "Silent Exception swallow",
    ),
    (r"def \w+\s*\([^)]*=\s*\[\]", "Mutable default argument (list)"),
    (r"def \w+\s*\([^)]*=\s*\{\}", "Mutable default argument (dict)"),
    (r"\beval\s*\(", "eval() usage — potential code injection"),
    (r"\bpickle\.loads\s*\(", "pickle.loads() on potentially untrusted data"),
]

# Lines matching these → advisory note only
_NOTE_PATTERNS: list[tuple[str, str]] = [
    (r"\bprint\s*\((?!.*#\s*noqa)", "Debug print (remove if not intentional)"),
    (r"#\s*TODO(?!.*#\s*noqa)", "TODO comment added"),
    (r"#\s*type:\s*ignore", "type: ignore added"),
    (r"@ts-ignore", "@ts-ignore added"),
]


def run_commit_reviewer(diff: str) -> tuple[list[str], list[str], list[str]]:
    """Scan staged diff. Returns (blocks, warnings, notes)."""
    blocks: list[str] = []
    warns: list[str] = []
    notes: list[str] = []

    current_file = ""
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
            continue
        if not line.startswith("+") or line.startswith("+++"):
            continue
        code = line[1:]  # strip leading +

        # Lines with # noqa or # noqa: secrets skip all pattern checks
        if re.search(r"#\s*noqa", code):
            continue

        for pattern, desc in _BLOCK_PATTERNS:
            if re.search(pattern, code):
                blocks.append(f"  [{current_file}] {desc}")
                blocks.append(f"    > {code.strip()[:120]}")

        for pattern, desc in _WARN_PATTERNS:
            if re.search(pattern, code):
                warns.append(f"  [{current_file}] {desc}")
                warns.append(f"    > {code.strip()[:120]}")

        for pattern, desc in _NOTE_PATTERNS:
            if re.search(pattern, code):
                notes.append(f"  [{current_file}] {desc}: {code.strip()[:80]}")

    return blocks, warns, notes


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    staged = get_staged_files()
    if not staged:
        sys.exit(0)

    # Filter to code files only
    code_exts = {".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go", ".java", ".cs"}
    code_files = [f for f in staged if Path(f).suffix in code_exts]

    print(f"\n[pre-commit] {len(staged)} staged file(s) ({len(code_files)} code)")

    # --- Lint Guard ---
    lint_errors, lint_fixed = [], []
    if code_files:
        lint_errors, lint_fixed = run_lint_guard(code_files)

    if lint_fixed:
        print(f"[lint-guard]  auto-fixed: {', '.join(lint_fixed)}")

    # --- Commit Reviewer ---
    diff = get_staged_diff()
    blocks, warns, notes = run_commit_reviewer(diff)

    # --- Report ---
    if blocks:
        print("\n[commit-reviewer] BLOCK — must fix before committing:")
        for line in blocks:
            print(line)

    if warns:
        print("\n[commit-reviewer] WARNINGS — review before committing:")
        for line in warns:
            print(line)

    if lint_errors:
        print("\n[lint-guard] Lint errors remaining:")
        for line in lint_errors[:30]:
            print(line)
        if len(lint_errors) > 30:
            print(f"  ... and {len(lint_errors) - 30} more")

    if notes:
        print("\n[commit-reviewer] Notes (advisory):")
        for line in notes[:10]:
            print(f"  {line}")

    has_hard_errors = bool(blocks or lint_errors)

    if has_hard_errors:
        print("\n[pre-commit] BLOCKED — fix the issues above, re-stage, and retry.\n")
        sys.exit(1)
    elif warns:
        print("\n[pre-commit] APPROVED with warnings.\n")
    else:
        print("[pre-commit] CLEAN\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
