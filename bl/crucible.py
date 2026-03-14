"""
bl/crucible.py — Agent benchmarking and promotion/retirement system (C-15).

Scores agent output quality against rubrics derived from each agent's .md spec.
Tracks scores in SQLite (crucible_scores table in history.db per project).
Promotes reliable agents; flags/retires underperformers.

Usage:
    from bl.crucible import run_all_benchmarks, get_all_statuses, print_report
    scores = run_all_benchmarks(project_dir)
    statuses = get_all_statuses(project_dir)
    print_report(scores, statuses)
"""

import json
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

PROMOTE_THRESHOLD = 0.80
FLAG_THRESHOLD = 0.50
RETIRE_THRESHOLD = 0.40
MIN_RUNS_FOR_STATUS = 3

_KNOWN_AGENTS = [
    "hypothesis-generator",
    "question-designer",
    "synthesizer",
    "quantitative-analyst",
]

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class AgentScore:
    agent: str
    score: float
    checks: dict = field(default_factory=dict)
    details: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class AgentStatus:
    agent: str
    status: str  # active | promoted | flagged | retired
    avg_score: float
    run_count: int
    last_score: float


# ---------------------------------------------------------------------------
# SQLite
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS crucible_scores (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    agent   TEXT NOT NULL,
    score   REAL NOT NULL,
    checks  TEXT NOT NULL,
    details TEXT,
    ts      TEXT NOT NULL
);
"""


def _get_db(project_dir: Path) -> sqlite3.Connection:
    """Open history.db and ensure crucible_scores table exists."""
    db_path = project_dir / "history.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


def record_score(project_dir: Path, score: AgentScore) -> None:
    """Write a benchmark result to the ledger."""
    with _get_db(project_dir) as conn:
        conn.execute(
            "INSERT INTO crucible_scores (agent, score, checks, details, ts) VALUES (?, ?, ?, ?, ?)",
            (
                score.agent,
                score.score,
                json.dumps(score.checks),
                score.details[:1000],
                score.timestamp,
            ),
        )
        conn.commit()


def get_agent_status(project_dir: Path, agent: str) -> AgentStatus:
    """Compute current status for an agent based on historical scores (last 10)."""
    with _get_db(project_dir) as conn:
        rows = conn.execute(
            "SELECT score FROM crucible_scores WHERE agent = ? ORDER BY id DESC LIMIT 10",
            (agent,),
        ).fetchall()

    run_count = len(rows)
    if run_count == 0:
        return AgentStatus(
            agent=agent, status="active", avg_score=0.0, run_count=0, last_score=0.0
        )

    scores = [r["score"] for r in rows]
    avg = sum(scores) / len(scores)
    last = scores[0]

    if run_count >= MIN_RUNS_FOR_STATUS:
        if avg >= PROMOTE_THRESHOLD:
            status = "promoted"
        elif avg < RETIRE_THRESHOLD:
            status = "retired"
        elif avg < FLAG_THRESHOLD:
            status = "flagged"
        else:
            status = "active"
    else:
        status = "active"

    return AgentStatus(
        agent=agent, status=status, avg_score=avg, run_count=run_count, last_score=last
    )


# ---------------------------------------------------------------------------
# Rubrics
# ---------------------------------------------------------------------------


def _weighted(checks: dict[str, tuple[float, float]]) -> tuple[float, dict[str, float]]:
    """Compute weighted score. checks = {name: (pass_value, weight)}."""
    total_weight = sum(w for _, w in checks.values())
    score = sum(v * w for v, w in checks.values()) / max(total_weight, 1.0)
    return score, {name: v for name, (v, _) in checks.items()}


def _score_hypothesis_generator(project_dir: Path) -> AgentScore:
    """Score hypothesis-generator by checking Wave 2+ questions in questions.md."""
    qpath = project_dir / "questions.md"
    if not qpath.exists():
        return AgentScore("hypothesis-generator", 0.0, {}, "questions.md not found")

    text = qpath.read_text(encoding="utf-8", errors="replace")

    # Find Wave 2+ sections
    wave_match = re.search(r"## Wave [2-9]\d*", text)
    if not wave_match:
        return AgentScore(
            "hypothesis-generator", 0.0, {}, "No Wave 2+ sections found in questions.md"
        )

    wave2_text = text[wave_match.start() :]

    # Split on question headers ## Q<n>.<m> where n >= 2
    blocks = re.split(r"(?=^## Q[2-9]\d*\.\d+)", wave2_text, flags=re.MULTILINE)
    blocks = [b.strip() for b in blocks if re.match(r"## Q[2-9]\d*\.\d+", b.strip())]

    if not blocks:
        return AgentScore(
            "hypothesis-generator", 0.0, {}, "No Wave 2+ question blocks found"
        )

    def check_block(b: str) -> dict[str, float]:
        return {
            "has_status": 1.0 if re.search(r"PENDING|DONE|Status", b) else 0.0,
            "has_derived_from": 1.0 if "Derived from" in b else 0.0,
            "has_test": 1.0 if re.search(r"Test:|pytest|Simulation path", b) else 0.0,
            "has_verdict_threshold": 1.0
            if ("FAILURE:" in b and "HEALTHY:" in b)
            else 0.0,
            "has_hypothesis": 1.0 if "Hypothesis:" in b else 0.0,
        }

    weights = {
        "has_status": 0.10,
        "has_derived_from": 0.35,
        "has_test": 0.20,
        "has_verdict_threshold": 0.25,
        "has_hypothesis": 0.10,
    }

    all_results: dict[str, list[float]] = {k: [] for k in weights}
    for block in blocks:
        result = check_block(block)
        for k, v in result.items():
            all_results[k].append(v)

    # Average pass rate per check
    pass_rates = {k: sum(vs) / len(vs) for k, vs in all_results.items()}
    score = sum(pass_rates[k] * weights[k] for k in weights)

    details = (
        f"Scored {len(blocks)} Wave 2+ questions. Per-check pass rates: "
        + ", ".join(f"{k}={v:.2f}" for k, v in pass_rates.items())
    )
    return AgentScore("hypothesis-generator", round(score, 4), pass_rates, details)


def _score_question_designer(project_dir: Path) -> AgentScore:
    """Score question-designer by checking Wave 1 / initial questions in questions.md."""
    qpath = project_dir / "questions.md"
    if not qpath.exists():
        return AgentScore("question-designer", 0.0, {}, "questions.md not found")

    text = qpath.read_text(encoding="utf-8", errors="replace")

    # Take only Wave 1 content (before any Wave 2 section)
    wave2_match = re.search(r"^## Wave [2-9]", text, re.MULTILINE)
    wave1_text = text[: wave2_match.start()] if wave2_match else text

    # Split on question headers
    blocks = re.split(r"(?=^## Q\d+\.\d+)", wave1_text, flags=re.MULTILINE)
    blocks = [b.strip() for b in blocks if re.match(r"## Q\d+\.\d+", b.strip())]

    if len(blocks) < 5:
        return AgentScore(
            "question-designer",
            0.0,
            {},
            f"Only {len(blocks)} Wave 1 questions found (need >= 5)",
        )

    # domains_covered: count unique D1–D6 domain codes across all text
    domain_hits = set()
    domain_keywords = {
        "D1": ["D1", "performance", "load", "latency"],
        "D2": ["D2", "legal", "compliance", "regulatory"],
        "D3": ["D3", "market", "competitive", "analogue"],
        "D4": ["D4", "correctness", "accuracy", "quality"],
        "D5": ["D5", "benchmark", "ablation", "model"],
        "D6": ["D6", "security", "auth", "vulnerability"],
    }
    for code, keywords in domain_keywords.items():
        for kw in keywords:
            if kw in wave1_text:
                domain_hits.add(code)
                break
    domains_score = len(domain_hits) / 6.0

    # Per-question checks
    has_thresholds = sum(
        1 for b in blocks if "FAILURE:" in b and "HEALTHY:" in b
    ) / len(blocks)
    has_status = sum(1 for b in blocks if re.search(r"PENDING|DONE", b)) / len(blocks)
    has_hypothesis = sum(1 for b in blocks if "Hypothesis:" in b) / len(blocks)

    weights = {
        "domains_covered": 0.35,
        "has_thresholds": 0.30,
        "has_status": 0.15,
        "has_hypothesis": 0.20,
    }
    pass_rates = {
        "domains_covered": domains_score,
        "has_thresholds": has_thresholds,
        "has_status": has_status,
        "has_hypothesis": has_hypothesis,
    }
    score = sum(pass_rates[k] * weights[k] for k in weights)

    details = (
        f"Scored {len(blocks)} Wave 1 questions. Domains found: {sorted(domain_hits)}. "
        + ", ".join(f"{k}={v:.2f}" for k, v in pass_rates.items())
    )
    return AgentScore("question-designer", round(score, 4), pass_rates, details)


def _score_synthesizer(project_dir: Path) -> AgentScore:
    """Score synthesizer by checking findings/synthesis.md structure."""
    spath = project_dir / "findings" / "synthesis.md"
    if not spath.exists():
        return AgentScore("synthesizer", 0.0, {}, "findings/synthesis.md not found")

    text = spath.read_text(encoding="utf-8", errors="replace")

    checks_raw = {
        "has_critical_path": (1.0 if "Critical Path" in text else 0.0, 0.25),
        "has_finding_refs": (1.0 if re.search(r"Q\d+\.\d+", text) else 0.0, 0.30),
        "has_residual_risk": (
            1.0 if re.search(r"[Rr]esidual [Rr]isk|residual", text) else 0.0,
            0.20,
        ),
        "has_tiered_roadmap": (
            1.0 if re.search(r"Phase [23]|Before", text) else 0.0,
            0.15,
        ),
        "has_mitigation": (1.0 if "mitigat" in text.lower() else 0.0, 0.10),
    }

    score, pass_rates = _weighted(checks_raw)
    details = "synthesis.md checks: " + ", ".join(
        f"{k}={v:.0f}" for k, v in pass_rates.items()
    )
    return AgentScore("synthesizer", round(score, 4), pass_rates, details)


def _score_quantitative_analyst(project_dir: Path) -> AgentScore:
    """Score quantitative-analyst by checking performance/D1/D5 finding files."""
    findings_dir = project_dir / "findings"
    if not findings_dir.exists():
        return AgentScore(
            "quantitative-analyst", 0.0, {}, "findings/ directory not found"
        )

    perf_files = []
    for fpath in sorted(findings_dir.glob("Q*.md")):
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if re.search(r"\b(performance|D1|D5|PERFORMANCE)\b", content):
            perf_files.append(content)

    if not perf_files:
        return AgentScore(
            "quantitative-analyst", 0.0, {}, "No performance/D1/D5 findings found"
        )

    weights = {
        "has_metric": 0.30,
        "has_verdict_justification": 0.30,
        "has_boundary_value": 0.25,
        "has_recommendation": 0.15,
    }

    per_check: dict[str, list[float]] = {k: [] for k in weights}
    for content in perf_files:
        per_check["has_metric"].append(
            1.0 if re.search(r"\d+\s*(ms|%|req/s|rps|s\b|MB|KB|GB)", content) else 0.0
        )
        per_check["has_verdict_justification"].append(
            1.0 if re.search(r"[Vv]erdict\s*:", content) else 0.0
        )
        per_check["has_boundary_value"].append(
            1.0 if re.search(r"threshold|boundary|>\s*\d|<\s*\d", content) else 0.0
        )
        per_check["has_recommendation"].append(
            1.0
            if re.search(r"recommend|mitigat|action", content, re.IGNORECASE)
            else 0.0
        )

    pass_rates = {k: sum(vs) / len(vs) for k, vs in per_check.items()}
    score = sum(pass_rates[k] * weights[k] for k in weights)

    details = f"Scored {len(perf_files)} performance findings. " + ", ".join(
        f"{k}={v:.2f}" for k, v in pass_rates.items()
    )
    return AgentScore("quantitative-analyst", round(score, 4), pass_rates, details)


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------

_SCORERS = {
    "hypothesis-generator": _score_hypothesis_generator,
    "question-designer": _score_question_designer,
    "synthesizer": _score_synthesizer,
    "quantitative-analyst": _score_quantitative_analyst,
}


def run_all_benchmarks(project_dir: Path) -> list[AgentScore]:
    """Run all rubrics against project_dir. Record each score. Return list of AgentScore."""
    scores = []
    for agent, scorer in _SCORERS.items():
        try:
            score = scorer(project_dir)
        except Exception as e:
            score = AgentScore(agent, 0.0, {}, f"Scorer raised: {e}")
        record_score(project_dir, score)
        scores.append(score)
    return scores


def get_all_statuses(project_dir: Path) -> list[AgentStatus]:
    """Return current AgentStatus for all known agents."""
    return [get_agent_status(project_dir, agent) for agent in _KNOWN_AGENTS]


def print_report(scores: list[AgentScore], statuses: list[AgentStatus]) -> None:
    """Print a formatted benchmark report to stdout."""
    status_by_agent = {s.agent: s for s in statuses}
    score_by_agent = {s.agent: s for s in scores}

    header = "CRUCIBLE REPORT"
    print(f"\n┌{'─' * 55}┐")
    print(f"│ {header:<53} │")
    print(f"├{'─' * 20}┬{'─' * 7}┬{'─' * 8}┬{'─' * 15}┤")
    print(f"│ {'Agent':<18} │ {'Score':^5} │ {'Runs':^6} │ {'Status':<13} │")
    print(f"├{'─' * 20}┼{'─' * 7}┼{'─' * 8}┼{'─' * 15}┤")

    for agent in _KNOWN_AGENTS:
        sc = score_by_agent.get(agent)
        st = status_by_agent.get(agent)
        score_str = f"{sc.score:.2f}" if sc else "—"
        runs_str = str(st.run_count) if st else "0"
        if st:
            status_label = st.status.upper()
            if st.run_count == 0:
                status_label = "ACTIVE (new)"
        else:
            status_label = "ACTIVE (new)"
        short_name = agent[:18]
        print(
            f"│ {short_name:<18} │ {score_str:^5} │ {runs_str:^6} │ {status_label:<13} │"
        )

    print(f"└{'─' * 20}┴{'─' * 7}┴{'─' * 8}┴{'─' * 15}┘")

    # Detail section for flagged/retired
    flagged = [s for s in statuses if s.status in ("flagged", "retired")]
    if flagged:
        print("\n--- Attention Required ---")
        for st in flagged:
            sc = score_by_agent.get(st.agent)
            print(f"\n[{st.status.upper()}] {st.agent}")
            print(
                f"  avg_score={st.avg_score:.3f}  runs={st.run_count}  last={st.last_score:.3f}"
            )
            if sc and sc.details:
                print(f"  details: {sc.details}")

    print()
