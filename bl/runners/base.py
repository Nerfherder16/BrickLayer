"""
bl/runners/base.py — Runner Protocol and registry.

Any callable that accepts a question dict and returns a verdict envelope
qualifies as a Runner. Register external runners with `register()`.

Verdict envelope shape (all runners must return this):
    {
        "verdict":  "FAILURE" | "WARNING" | "HEALTHY" | "INCONCLUSIVE",
        "summary":  str,          # one-line evidence
        "data":     dict,         # raw structured data
        "details":  str,          # full evidence text
        # optional:
        "failure_type":  str,     # set by campaign after classify_failure_type()
        "confidence":    str,     # "high" | "medium" | "low" | "uncertain"
    }
"""

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class RunnerInfo:
    """Metadata about a registered runner."""

    mode: str
    description: str  # one-line description
    target_types: list[str] = field(
        default_factory=list
    )  # e.g. ["api", "service", "url"]
    syntax_summary: str = ""  # key question fields this runner reads
    example_question: str = ""  # minimal example question block


@runtime_checkable
class Runner(Protocol):
    """Protocol that every BrickLayer runner must satisfy."""

    def __call__(self, question: dict[str, Any]) -> dict[str, Any]:
        """
        Run the question and return a verdict envelope.

        Args:
            question: Parsed question dict from questions.md (id, title, mode,
                      hypothesis, test, verdict_threshold, target, status).

        Returns:
            Verdict envelope dict with at minimum:
                verdict, summary, data, details.
        """
        ...


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, Runner] = {}
_INFO: dict[str, RunnerInfo] = {}


def register(mode: str, runner: Runner, info: RunnerInfo | None = None) -> None:
    """Register a runner for the given mode string.

    Args:
        mode:   The mode string as it appears in questions.md (e.g. "http", "browser").
        runner: Any callable satisfying the Runner protocol.
        info:   Optional RunnerInfo metadata for this runner.

    Raises:
        TypeError: If runner does not satisfy the Runner protocol.
    """
    if not isinstance(runner, Runner):
        raise TypeError(
            f"Runner for mode '{mode}' does not satisfy the Runner protocol. "
            "It must be callable with signature (question: dict) -> dict."
        )
    _REGISTRY[mode] = runner
    if info is not None:
        _INFO[mode] = info


def get(mode: str) -> Runner | None:
    """Return the registered runner for mode, or None if not found."""
    return _REGISTRY.get(mode)


def registered_modes() -> list[str]:
    """Return sorted list of all registered mode strings."""
    return sorted(_REGISTRY.keys())


def describe(mode: str) -> RunnerInfo | None:
    """Return RunnerInfo for mode, or None if not registered or no info provided."""
    return _INFO.get(mode)


def list_runners() -> list[RunnerInfo]:
    """Return RunnerInfo for all registered runners that have metadata, sorted by mode."""
    return sorted(_INFO.values(), key=lambda r: r.mode)


def runner_menu() -> str:
    """Return a human-readable menu of all runners with descriptions — used by goal/question agents."""
    lines = []
    for info in list_runners():
        lines.append(f"- `{info.mode}`: {info.description}")
        if info.syntax_summary:
            lines.append(f"  Syntax: {info.syntax_summary}")
    if not lines:
        return "No runner metadata available."
    return "\n".join(lines)
