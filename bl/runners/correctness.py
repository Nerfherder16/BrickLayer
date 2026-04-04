"""
bl/runners/correctness.py — pytest subprocess runner.

Extracts pytest paths from the question's Test field, runs the suite,
and returns a verdict envelope.
"""

import re
import subprocess

from bl.config import cfg


def run_correctness(question: dict) -> dict:
    """Run pytest for correctness questions. Parse output for verdict."""
    test_spec = question.get("test", "")

    pytest_matches = re.findall(r"pytest\s+([^\s`]+(?:\s+[^\s`]+)*\.py[^\s`]*)", test_spec)

    if not pytest_matches:
        path_matches = re.findall(r"(?:C:/Users/trg16/Dev/Recall|/home/\w+/Dev/Recall)/[^\s`\n]+", test_spec)
        if path_matches:
            paths = " ".join(path_matches)
            pytest_cmd = f"pytest {paths} -v --tb=short -q"
        else:
            return {
                "verdict": "INCONCLUSIVE",
                "summary": "Could not extract pytest path from question Test field",
                "data": {},
                "details": f"Test field: {test_spec}",
            }
    else:
        paths = pytest_matches[0]
        k_match = re.search(r'-k\s+"([^"]+)"', test_spec)
        k_filter = f' -k "{k_match.group(1)}"' if k_match else ""
        pytest_cmd = f"pytest {paths} -v --tb=short -q{k_filter}"

    cmd = f"python -m {pytest_cmd}"

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(cfg.recall_src),
        )
        combined = result.stdout + ("\n" + result.stderr if result.stderr else "")

        passed = int(m.group(1)) if (m := re.search(r"(\d+) passed", combined)) else 0
        failed = int(m.group(1)) if (m := re.search(r"(\d+) failed", combined)) else 0
        errors = int(m.group(1)) if (m := re.search(r"(\d+) error", combined)) else 0

        no_tests = (
            "no tests ran" in combined.lower()
            or "collected 0 items" in combined
            or ("ERROR" in combined and "not found" in combined.lower())
        )

        if no_tests and passed == 0 and failed == 0:
            alt_paths = _find_test_paths(question)
            if alt_paths and alt_paths != paths:
                retry = subprocess.run(
                    f"python -m pytest {alt_paths} -v --tb=short -q",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    cwd=str(cfg.recall_src),
                )
                retry_out = retry.stdout + retry.stderr
                passed = (
                    int(m.group(1))
                    if (m := re.search(r"(\d+) passed", retry_out))
                    else 0
                )
                failed = (
                    int(m.group(1))
                    if (m := re.search(r"(\d+) failed", retry_out))
                    else 0
                )
                combined = f"[RETRY with {alt_paths}]\n" + retry_out
                no_tests = passed == 0 and failed == 0

        if no_tests:
            verdict, summary = (
                "INCONCLUSIVE",
                "No tests found for paths in question. Check test paths.",
            )
        elif failed > 0 or errors > 0:
            verdict, summary = (
                "FAILURE",
                f"{passed} passed, {failed} failed, {errors} errors",
            )
        else:
            verdict, summary = "HEALTHY", f"{passed} passed, {failed} failed"

        return {
            "verdict": verdict,
            "summary": summary,
            "data": {
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "returncode": result.returncode,
            },
            "details": combined[:4000],
        }

    except subprocess.TimeoutExpired:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "pytest timed out after 300s",
            "data": {},
            "details": "Subprocess timeout",
        }
    except Exception as exc:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"pytest subprocess error: {exc}",
            "data": {},
            "details": str(exc),
        }


def _find_test_paths(question: dict) -> str | None:
    """Try to find test file paths by scanning known Recall test directories."""
    test_dirs = [
        cfg.recall_src / "tests" / "integration",
        cfg.recall_src / "tests" / "core",
        cfg.recall_src / "tests" / "ml",
    ]
    filenames = re.findall(r"test_\w+\.py", question.get("test", ""))
    found = []
    for fname in filenames:
        for d in test_dirs:
            candidate = d / fname
            if candidate.exists():
                found.append(str(candidate))
    return " ".join(found) if found else None
