"""
bl/runners/simulate.py — Simulation parameter-sweep runner.

Executes BrickLayer simulate.py scripts with parameter sweeps to find failure
boundaries. Two modes:

  Sweep mode  — stress a single parameter across a range to find where the
                verdict flips HEALTHY → FAILURE / WARNING.

  Single-run  — run the script once (optionally with param overrides) and
                return the verdict envelope as-is.

Handles questions with mode: simulate

Test field syntax:
    script: simulate.py              — path relative to project root (default: simulate.py)
    stress_param: churn_rate         — parameter variable name to sweep
    stress_range: [0.05, 0.50]       — [min, max] for the sweep
    stress_steps: 10                 — number of steps across the range (default: 8)
    baseline_check: true             — run baseline first to verify HEALTHY (default: true)
    timeout: 30                      — per-run timeout in seconds (default: 30)

Single-run (no stress_param):
    script: simulate.py
    params:
      churn_rate: 0.15
      months: 24
"""

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from bl.config import cfg

# ---------------------------------------------------------------------------
# Spec parser
# ---------------------------------------------------------------------------

_CODE_FENCE = "```"


def _parse_simulate_spec(test_field: str) -> dict:
    """Parse the Test field into a simulation execution spec.

    Returns a dict with keys:
        script, stress_param, stress_range, stress_steps,
        baseline_check, timeout, params
    """
    spec: dict = {
        "script": "simulate.py",
        "stress_param": None,
        "stress_range": None,
        "stress_steps": 8,
        "baseline_check": True,
        "timeout": 30,
        "params": {},
    }

    in_params_block = False

    for raw_line in test_field.splitlines():
        stripped = raw_line.strip()

        # Strip markdown code fences
        if stripped.startswith(_CODE_FENCE):
            continue

        if not stripped:
            in_params_block = False
            continue

        low = stripped.lower()

        if low.startswith("script:"):
            spec["script"] = stripped.split(":", 1)[1].strip()
            in_params_block = False
            continue

        if low.startswith("stress_param:"):
            spec["stress_param"] = stripped.split(":", 1)[1].strip()
            in_params_block = False
            continue

        if low.startswith("stress_range:"):
            raw_range = stripped.split(":", 1)[1].strip()
            # Accept "[0.05, 0.50]" or "0.05, 0.50"
            numbers = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", raw_range)
            if len(numbers) >= 2:
                try:
                    spec["stress_range"] = [float(numbers[0]), float(numbers[1])]
                except ValueError:
                    pass
            in_params_block = False
            continue

        if low.startswith("stress_steps:"):
            try:
                spec["stress_steps"] = max(2, int(stripped.split(":", 1)[1].strip()))
            except ValueError:
                pass
            in_params_block = False
            continue

        if low.startswith("baseline_check:"):
            val = stripped.split(":", 1)[1].strip().lower()
            spec["baseline_check"] = val not in ("false", "0", "no")
            in_params_block = False
            continue

        if low.startswith("timeout:"):
            try:
                spec["timeout"] = int(stripped.split(":", 1)[1].strip())
            except ValueError:
                pass
            in_params_block = False
            continue

        # params: block — key: value pairs, indented or not
        if low.startswith("params:"):
            in_params_block = True
            # Inline value on the same line (rare but handle it)
            remainder = stripped.split(":", 1)[1].strip()
            if remainder:
                # "{key}: {value}" on one line after "params:"
                kv_match = re.match(r"(\w+)\s*:\s*(.+)", remainder)
                if kv_match:
                    spec["params"][kv_match.group(1)] = _coerce_value(
                        kv_match.group(2).strip()
                    )
            continue

        if in_params_block:
            # Indented key: value pair
            kv_match = re.match(r"(\w+)\s*:\s*(.+)", stripped)
            if kv_match:
                spec["params"][kv_match.group(1)] = _coerce_value(
                    kv_match.group(2).strip()
                )
            continue

    return spec


def _coerce_value(raw: str):
    """Try to coerce a string value to int, float, bool, or keep as string."""
    low = raw.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


# ---------------------------------------------------------------------------
# Simulation executor
# ---------------------------------------------------------------------------


def _patch_script_source(source: str, param_overrides: dict) -> str:
    """Patch SCENARIO PARAMETER assignments at the top of a simulate.py script.

    For each param in param_overrides, find the first line of the form:
        {param_name} = {old_value}
    and replace it with:
        {param_name} = {new_value}

    Uses regex so it handles spaces, comments on the same line, etc.
    Falls back to appending an override block if the param line isn't found.
    """
    lines = source.splitlines(keepends=True)
    patched_params = set()

    for i, line in enumerate(lines):
        for param, value in param_overrides.items():
            if param in patched_params:
                continue
            # Match: optional whitespace, param_name, whitespace, =, anything
            pattern = re.compile(
                r"^(\s*" + re.escape(param) + r"\s*=\s*)(.+?)(\s*(?:#.*)?)$"
            )
            m = pattern.match(line.rstrip("\n\r"))
            if m:
                # Preserve trailing comment if present
                trailing = m.group(3) if m.group(3).strip().startswith("#") else ""
                new_line = f"{m.group(1)}{_format_value(value)}{trailing}\n"
                lines[i] = new_line
                patched_params.add(param)
                break

    # Any params not found in the source: append as overrides before the end
    missing = set(param_overrides.keys()) - patched_params
    if missing:
        lines.append("\n# -- simulate runner overrides --\n")
        for param in sorted(missing):
            lines.append(f"{param} = {_format_value(param_overrides[param])}\n")

    return "".join(lines)


def _format_value(value) -> str:
    """Format a Python value for source injection."""
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, str):
        # Simple string — use repr to handle quoting
        return repr(value)
    return str(value)


def _run_simulation(script_path: str, param_overrides: dict, timeout: int) -> dict:
    """Run a simulate.py script (with optional param overrides) and return verdict envelope.

    Strategy:
    1. Read the script source.
    2. Patch SCENARIO PARAMETER lines via regex.
    3. Write to a temp file.
    4. Run with sys.executable.
    5. Parse JSON from stdout.
    """
    script_p = Path(cfg.project_root) / script_path

    if not script_p.exists():
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"Script not found: {script_path}",
            "data": {
                "script": script_path,
                "project_root": str(cfg.project_root),
                "error": "file_not_found",
            },
            "details": (
                f"Simulation script '{script_path}' not found under project root "
                f"'{cfg.project_root}'. Check the 'script:' directive."
            ),
        }

    try:
        source = script_p.read_text(encoding="utf-8")
    except OSError as exc:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"Cannot read script: {exc}",
            "data": {"script": script_path, "error": str(exc)},
            "details": f"Failed to read '{script_path}': {exc}",
        }

    if param_overrides:
        try:
            source = _patch_script_source(source, param_overrides)
        except Exception as exc:
            return {
                "verdict": "INCONCLUSIVE",
                "summary": f"Failed to patch script params: {exc}",
                "data": {
                    "script": script_path,
                    "param_overrides": param_overrides,
                    "error": str(exc),
                },
                "details": f"Error patching parameters into '{script_path}': {exc}",
            }

    tmp_path = None
    try:
        # Write patched source to a temp file in the project root so relative
        # imports and file paths inside simulate.py continue to work.
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            dir=str(cfg.project_root),
            delete=False,
            encoding="utf-8",
        ) as tmp:
            tmp.write(source)
            tmp_path = tmp.name

        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cfg.project_root),
        )

        stdout = result.stdout or ""
        stderr = result.stderr or ""
        returncode = result.returncode

    except subprocess.TimeoutExpired:
        return {
            "verdict": "FAILURE",
            "summary": f"Simulation timed out after {timeout}s",
            "data": {
                "script": script_path,
                "param_overrides": param_overrides,
                "timeout": timeout,
                "failure_type": "timeout",
            },
            "details": (
                f"Script: {script_path}\n"
                f"Params: {param_overrides}\n"
                f"Timeout: {timeout}s exceeded"
            ),
        }
    except Exception as exc:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"Failed to run simulation: {exc}",
            "data": {
                "script": script_path,
                "param_overrides": param_overrides,
                "error": str(exc),
            },
            "details": f"Unexpected error running '{script_path}': {exc}",
        }
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    # Parse JSON verdict envelope from stdout
    stdout_stripped = stdout.strip()

    # Find the last JSON object in stdout (simulate.py may print debug lines first)
    json_candidate = None
    for line in reversed(stdout_stripped.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            json_candidate = line
            break

    if json_candidate is None:
        # Try the whole stdout as one blob
        if stdout_stripped.startswith("{"):
            json_candidate = stdout_stripped

    if json_candidate:
        try:
            parsed = json.loads(json_candidate)
            if "verdict" in parsed:
                parsed.setdefault("summary", f"{script_path}: {parsed['verdict']}")
                parsed.setdefault("data", {})
                parsed["data"]["script"] = script_path
                if param_overrides:
                    parsed["data"]["param_overrides"] = param_overrides
                return parsed
        except json.JSONDecodeError:
            pass

    # Script exited non-zero with no parseable JSON
    if returncode != 0:
        return {
            "verdict": "FAILURE",
            "summary": f"Script exited {returncode} with no JSON verdict",
            "data": {
                "script": script_path,
                "returncode": returncode,
                "stdout_preview": stdout[:300],
                "stderr_preview": stderr[:200],
                "param_overrides": param_overrides,
            },
            "details": (
                f"Script: {script_path}\n"
                f"Exit: {returncode}\n"
                f"Stdout:\n{stdout[:500]}\n"
                f"Stderr:\n{stderr[:300]}"
            ),
        }

    return {
        "verdict": "INCONCLUSIVE",
        "summary": f"Script produced no JSON verdict (exit {returncode})",
        "data": {
            "script": script_path,
            "returncode": returncode,
            "stdout_preview": stdout[:300],
            "stderr_preview": stderr[:200],
            "param_overrides": param_overrides,
        },
        "details": (
            f"Script: {script_path}\n"
            f"Exit: {returncode}\n"
            "Expected stdout to contain a JSON object with a 'verdict' key.\n"
            f"Stdout:\n{stdout[:500]}\n"
            f"Stderr:\n{stderr[:300]}"
        ),
    }


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def run_simulate(question: dict) -> dict:
    """Execute simulation script from Test field and return verdict envelope.

    Dispatches to single-run or sweep mode based on whether stress_param is set.
    """
    test_field = question.get("test", "") or question.get("Test", "")
    spec = _parse_simulate_spec(test_field)

    script = spec["script"]
    stress_param = spec["stress_param"]
    stress_range = spec["stress_range"]
    stress_steps = spec["stress_steps"]
    baseline_check = spec["baseline_check"]
    timeout = spec["timeout"]
    params = spec["params"]

    # ── Single-run mode ──────────────────────────────────────────────────────
    if not stress_param:
        result = _run_simulation(script, params, timeout)
        result.setdefault("data", {})
        result["data"]["mode"] = "single_run"
        result["data"]["script"] = script
        return result

    # ── Sweep mode ───────────────────────────────────────────────────────────
    if stress_range is None or len(stress_range) < 2:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"stress_param '{stress_param}' set but stress_range is missing or invalid",
            "data": {"script": script, "stress_param": stress_param, "spec": spec},
            "details": (
                f"When stress_param is specified, stress_range must be provided as "
                f"'[min, max]'. Got: {stress_range}"
            ),
        }

    range_min, range_max = stress_range[0], stress_range[1]

    # Step 0: baseline check
    baseline_verdict = None
    if baseline_check:
        baseline_result = _run_simulation(script, {}, timeout)
        baseline_verdict = baseline_result.get("verdict", "INCONCLUSIVE")
        if baseline_verdict != "HEALTHY":
            return {
                "verdict": "WARNING",
                "summary": (
                    f"{script} baseline is already {baseline_verdict} "
                    f"before sweeping {stress_param}"
                ),
                "data": {
                    "script": script,
                    "stress_param": stress_param,
                    "stress_range": [range_min, range_max],
                    "baseline_verdict": baseline_verdict,
                    "baseline_summary": baseline_result.get("summary", ""),
                    "mode": "sweep",
                },
                "details": (
                    f"Baseline run returned {baseline_verdict} before any stress was "
                    f"applied. Fix the baseline before sweeping.\n\n"
                    f"Baseline summary: {baseline_result.get('summary', '')}\n"
                    f"Baseline details:\n{baseline_result.get('details', '')}"
                ),
            }

    # Step 1: generate sweep values
    if stress_steps <= 1:
        sweep_values = [range_min]
    else:
        step_size = (range_max - range_min) / (stress_steps - 1)
        sweep_values = [
            round(range_min + i * step_size, 10) for i in range(stress_steps)
        ]

    # Step 2: run sweep
    sweep_results = []
    failure_threshold = None
    warning_threshold = None

    for value in sweep_values:
        overrides = {stress_param: value}
        run_result = _run_simulation(script, overrides, timeout)
        verdict = run_result.get("verdict", "INCONCLUSIVE")
        sweep_results.append({"value": value, "verdict": verdict})

        # Track first warning (if no failure found yet)
        if (
            verdict == "WARNING"
            and warning_threshold is None
            and failure_threshold is None
        ):
            warning_threshold = value

        # Track first failure
        if verdict not in ("HEALTHY",) and verdict != "WARNING":
            # FAILURE, INCONCLUSIVE, or anything unexpected → treat as failure boundary
            if failure_threshold is None:
                failure_threshold = value
            break  # Stop at the first failure — we've found the boundary

    # Step 3: classify overall verdict
    steps_tested = len(sweep_results)

    if failure_threshold is not None:
        # Determine baseline value for safety margin calculation
        # Use the current (unpatched) param value if we can read it from the script
        baseline_value = _read_baseline_param(script, stress_param)
        safety_margin = None
        if baseline_value is not None:
            safety_margin = round(failure_threshold - baseline_value, 10)

        if baseline_value is not None:
            summary = (
                f"{stress_param} breaks at {_fmt(failure_threshold)} "
                f"(baseline {_fmt(baseline_value)}, margin: {_fmt(safety_margin)})"
            )
        else:
            summary = (
                f"{stress_param} breaks at {_fmt(failure_threshold)} "
                f"(step {steps_tested}/{stress_steps} across "
                f"[{_fmt(range_min)}, {_fmt(range_max)}])"
            )

        overall_verdict = "FAILURE"

    elif warning_threshold is not None:
        # All failures were WARNING level — no outright FAILURE
        summary = (
            f"{stress_param}: WARNING threshold at {_fmt(warning_threshold)}, "
            f"no FAILURE found across [{_fmt(range_min)}, {_fmt(range_max)}]"
        )
        overall_verdict = "WARNING"
        failure_threshold = None
        baseline_value = _read_baseline_param(script, stress_param)
        safety_margin = None

    else:
        # All steps HEALTHY — system is robust
        summary = (
            f"{stress_param}: no failure found across "
            f"[{_fmt(range_min)}, {_fmt(range_max)}] — system is robust"
        )
        overall_verdict = "HEALTHY"
        failure_threshold = None
        baseline_value = _read_baseline_param(script, stress_param)
        safety_margin = None

    return {
        "verdict": overall_verdict,
        "summary": summary,
        "data": {
            "script": script,
            "stress_param": stress_param,
            "stress_range": [range_min, range_max],
            "steps_tested": steps_tested,
            "baseline_verdict": baseline_verdict,
            "failure_threshold": failure_threshold,
            "safety_margin": safety_margin if failure_threshold is not None else None,
            "sweep_results": sweep_results,
            "mode": "sweep",
        },
        "details": _format_sweep_details(
            script,
            stress_param,
            range_min,
            range_max,
            sweep_results,
            baseline_verdict,
            failure_threshold,
        ),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_baseline_param(script_path: str, param_name: str):
    """Try to read the current value of a parameter from the script source.

    Returns the value as a float/int/str, or None if not found.
    """
    script_p = Path(cfg.project_root) / script_path
    try:
        source = script_p.read_text(encoding="utf-8")
    except OSError:
        return None

    pattern = re.compile(
        r"^\s*" + re.escape(param_name) + r"\s*=\s*([^\n#]+)",
        re.MULTILINE,
    )
    m = pattern.search(source)
    if not m:
        return None

    raw = m.group(1).strip()
    # Use ast.literal_eval for safety
    try:
        return ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return None


def _fmt(value) -> str:
    """Format a numeric value compactly (strip trailing zeros for floats)."""
    if value is None:
        return "None"
    if isinstance(value, float):
        # Format with up to 6 significant digits, strip trailing zeros
        formatted = f"{value:.6g}"
        return formatted
    return str(value)


def _format_sweep_details(
    script: str,
    stress_param: str,
    range_min: float,
    range_max: float,
    sweep_results: list,
    baseline_verdict,
    failure_threshold,
) -> str:
    """Build a human-readable details string for a sweep run."""
    lines = [
        f"Script: {script}",
        f"Sweep: {stress_param} across [{_fmt(range_min)}, {_fmt(range_max)}]",
        f"Steps tested: {len(sweep_results)}",
        f"Baseline: {baseline_verdict}",
        "",
        "Sweep results:",
    ]
    for entry in sweep_results:
        marker = " <-- FAILS HERE" if entry["value"] == failure_threshold else ""
        lines.append(
            f"  {stress_param}={_fmt(entry['value'])}: {entry['verdict']}{marker}"
        )

    if failure_threshold is None:
        lines.append("\nNo failure found across the full range.")
    else:
        lines.append(f"\nFailure boundary: {stress_param} = {_fmt(failure_threshold)}")

    return "\n".join(lines)
