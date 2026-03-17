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
    # BL 2.0 operational agents
    "diagnose-analyst",
    "fix-implementer",
    "compliance-auditor",
    "design-reviewer",
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

    # F11.1: detect wave number from question IDs (supports BL 2.0 IDs like D7.1, F8.1)
    # BL 1.x: Q2.1 → wave 2; BL 2.0: D7.1 → wave 7 (digit after letter prefix)
    wave_nums = [int(m) for m in re.findall(r"^## \w+(\d+)\.\d+", text, re.MULTILINE)]
    max_wave = max(wave_nums) if wave_nums else 0
    if max_wave < 2:
        return AgentScore(
            "hypothesis-generator",
            0.0,
            {},
            "No Wave 2+ questions found in questions.md",
        )

    # F11.1: split on any letter-prefixed question header for wave 2+ (BL 1.x and BL 2.0)
    blocks = re.split(r"(?=^## \w+[2-9]\d*\.\d+)", text, flags=re.MULTILINE)
    blocks = [b.strip() for b in blocks if re.match(r"## \w+[2-9]\d*\.\d+", b.strip())]

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

    # F11.1: find Wave 1 content by splitting on first Wave 2+ question ID
    # BL 1.x: Q1.x are wave 1, Q2.x+ are wave 2+
    # BL 2.0: D1.x/A1.x etc. are wave 1, D2.x+ are wave 2+
    wave2_match = re.search(r"^## \w+[2-9]\d*\.\d+", text, re.MULTILINE)
    wave1_text = text[: wave2_match.start()] if wave2_match else text

    # F11.1: split on any letter-prefixed question header (BL 1.x and BL 2.0)
    blocks = re.split(r"(?=^## \w+\d+\.\d+)", wave1_text, flags=re.MULTILINE)
    blocks = [b.strip() for b in blocks if re.match(r"## \w+\d+\.\d+", b.strip())]

    if len(blocks) < 5:
        return AgentScore(
            "question-designer",
            0.0,
            {},
            f"Only {len(blocks)} Wave 1 questions found (need >= 5)",
        )

    # domains_covered: find unique operational mode prefixes from wave1 block headers
    unique_prefixes = set(re.findall(r"^## ([A-Z])\d+\.\d+", wave1_text, re.MULTILINE))
    domains_score = min(1.0, len(unique_prefixes) / 5.0)  # 5 BL 2.0 prefixes: D/F/A/V/M

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
        f"Scored {len(blocks)} Wave 1 questions. Prefixes found: {sorted(unique_prefixes)}. "
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
        "has_finding_refs": (1.0 if re.search(r"\b[A-Z]\d+\.\d+", text) else 0.0, 0.30),
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
    for fpath in sorted(
        f for f in findings_dir.glob("*.md") if f.name != "synthesis.md"
    ):
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
# BL 2.0 operational agent scorers (F17.1)
# All follow the _score_synthesizer static-file pattern.
# ---------------------------------------------------------------------------


def _score_diagnose_analyst(project_dir: Path) -> AgentScore:
    """Score diagnose-analyst: DIAGNOSIS_COMPLETE rate + fix-spec completeness."""
    findings_dir = project_dir / "findings"
    results_tsv = project_dir / "results.tsv"
    if not findings_dir.exists():
        return AgentScore("diagnose-analyst", 0.0, {}, "findings/ not found")

    # DIAGNOSIS_COMPLETE rate from results.tsv
    # V18.1: scope to BL 2.0 D-prefix rows only (new format: col[0]="N/A", col[1] starts with "D")
    def _is_bl2_diag_row(ln: str) -> bool:
        parts = ln.split("\t")
        if len(parts) >= 3 and parts[0] == "N/A":
            return parts[1].startswith("D") and bool(
                re.search(
                    r"^(DIAGNOSIS_COMPLETE|HEALTHY|FAILURE|INCONCLUSIVE)$", parts[2]
                )
            )
        return False

    dc_rate = 0.0
    if results_tsv.exists():
        lines = results_tsv.read_text(encoding="utf-8", errors="replace").splitlines()
        diag_rows = [
            ln
            for ln in lines
            if _is_bl2_diag_row(ln)
            and ("\tDIAGNOSIS_COMPLETE\t" in ln or "\tHEALTHY\t" in ln)
        ]
        all_diag = [ln for ln in lines if _is_bl2_diag_row(ln)]
        dc_rate = len(diag_rows) / len(all_diag) if all_diag else 0.0

    # Fix-spec completeness: findings containing all 4 required fields
    spec_fields = [
        "Target file",
        "Target location",
        "Concrete edit",
        "Verification command",
    ]
    spec_scores = []
    for fpath in sorted(
        f for f in findings_dir.glob("*.md") if f.name != "synthesis.md"
    ):
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        # V18.2: exact verdict line match — excludes FIXED findings that embed "Fix Specification"
        if "**Verdict**: DIAGNOSIS_COMPLETE" not in content:
            continue
        hit = sum(1 for field in spec_fields if field in content) / len(spec_fields)
        spec_scores.append(hit)
    spec_completeness = sum(spec_scores) / len(spec_scores) if spec_scores else 0.0

    checks_raw = {
        "dc_rate": (dc_rate, 0.60),
        "fix_spec_completeness": (spec_completeness, 0.40),
    }
    score, pass_rates = _weighted(checks_raw)
    details = f"DIAGNOSIS_COMPLETE rate={dc_rate:.2f}, fix_spec_completeness={spec_completeness:.2f}"
    return AgentScore("diagnose-analyst", round(score, 4), pass_rates, details)


def _score_fix_implementer(project_dir: Path) -> AgentScore:
    """Score fix-implementer: FIXED rate + verification section presence in FIXED findings."""
    findings_dir = project_dir / "findings"
    results_tsv = project_dir / "results.tsv"
    if not findings_dir.exists():
        return AgentScore("fix-implementer", 0.0, {}, "findings/ not found")

    # A20.2: scope fix_rows to F-prefix questions — excludes D-prefix self-fix edge cases (e.g. D-mid.4)
    def _is_fix_row(ln: str) -> bool:
        parts = ln.split("\t")
        # New format: N/A | qid | verdict | ...
        if len(parts) >= 3 and parts[0] == "N/A":
            return parts[1].startswith("F") and bool(
                re.search(r"^(FIXED|FIX_FAILED)$", parts[2])
            )
        # Old format (BL 1.x): qid | verdict | ... — preserve existing behavior
        return bool(re.search(r"\t(FIXED|FIX_FAILED)\t", ln))

    fixed_rate = 0.0
    fix_failed_rate = 0.0
    if results_tsv.exists():
        lines = results_tsv.read_text(encoding="utf-8", errors="replace").splitlines()
        fix_rows = [ln for ln in lines if _is_fix_row(ln)]
        if fix_rows:
            fixed_rate = sum(1 for ln in fix_rows if "\tFIXED\t" in ln) / len(fix_rows)
            fix_failed_rate = 1.0 - fixed_rate

    # Verification section presence in FIXED findings
    verify_scores = []
    for fpath in sorted(
        f for f in findings_dir.glob("*.md") if f.name != "synthesis.md"
    ):
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if "**Verdict**: FIXED" not in content and "\nVerdict: FIXED" not in content:
            continue
        has_verify = bool(re.search(r"## (Verification|Fix Applied|Evidence)", content))
        verify_scores.append(1.0 if has_verify else 0.0)
    verify_rate = sum(verify_scores) / len(verify_scores) if verify_scores else 0.0

    # Penalise high FIX_FAILED rate
    reliability = max(0.0, 1.0 - fix_failed_rate * 2)

    checks_raw = {
        "fixed_rate": (fixed_rate, 0.45),
        "verify_section_rate": (verify_rate, 0.35),
        "reliability": (reliability, 0.20),
    }
    score, pass_rates = _weighted(checks_raw)
    details = f"fixed_rate={fixed_rate:.2f}, verify_section={verify_rate:.2f}, reliability={reliability:.2f}"
    return AgentScore("fix-implementer", round(score, 4), pass_rates, details)


def _score_compliance_auditor(project_dir: Path) -> AgentScore:
    """Score compliance-auditor: definitive verdict rate + fix-spec in NON_COMPLIANT findings."""
    findings_dir = project_dir / "findings"
    results_tsv = project_dir / "results.tsv"
    if not findings_dir.exists():
        return AgentScore("compliance-auditor", 0.0, {}, "findings/ not found")

    definitive_rate = 0.0
    if results_tsv.exists():
        lines = results_tsv.read_text(encoding="utf-8", errors="replace").splitlines()
        audit_rows = [
            ln
            for ln in lines
            if re.search(r"\t(COMPLIANT|NON_COMPLIANT|PARTIAL|INCONCLUSIVE)\t", ln)
        ]
        if audit_rows:
            definitive = sum(
                1
                for ln in audit_rows
                if re.search(r"\t(COMPLIANT|NON_COMPLIANT|PARTIAL)\t", ln)
            )
            definitive_rate = definitive / len(audit_rows)

    # NON_COMPLIANT findings that include a Fix Specification section
    fix_spec_scores = []
    for fpath in sorted(
        f for f in findings_dir.glob("*.md") if f.name != "synthesis.md"
    ):
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if "NON_COMPLIANT" not in content:
            continue
        has_spec = "Fix Specification" in content or "Concrete edit" in content
        fix_spec_scores.append(1.0 if has_spec else 0.0)
    fix_spec_rate = (
        sum(fix_spec_scores) / len(fix_spec_scores) if fix_spec_scores else 0.0
    )

    checks_raw = {
        "definitive_verdict_rate": (definitive_rate, 0.60),
        "non_compliant_has_fix_spec": (fix_spec_rate, 0.40),
    }
    score, pass_rates = _weighted(checks_raw)
    details = (
        f"definitive_rate={definitive_rate:.2f}, fix_spec_rate={fix_spec_rate:.2f}"
    )
    return AgentScore("compliance-auditor", round(score, 4), pass_rates, details)


def _score_design_reviewer(project_dir: Path) -> AgentScore:
    """Score design-reviewer: COMPLIANT rate + line-number reference presence in findings."""
    findings_dir = project_dir / "findings"
    results_tsv = project_dir / "results.tsv"
    if not findings_dir.exists():
        return AgentScore("design-reviewer", 0.0, {}, "findings/ not found")

    compliant_rate = 0.0
    if results_tsv.exists():
        lines = results_tsv.read_text(encoding="utf-8", errors="replace").splitlines()
        review_rows = [
            ln
            for ln in lines
            if re.search(r"\t(COMPLIANT|NON_COMPLIANT|PARTIAL)\t", ln)
        ]
        if review_rows:
            compliant_rate = sum(
                1 for ln in review_rows if "\tCOMPLIANT\t" in ln
            ) / len(review_rows)

    # Line-number references in validate/design findings (indicates concrete code tracing)
    lineno_scores = []
    for fpath in sorted(
        f for f in findings_dir.glob("*.md") if f.name != "synthesis.md"
    ):
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if not re.search(r"\b(COMPLIANT|NON_COMPLIANT|VALIDATE|VALIDATE)\b", content):
            continue
        has_lineno = bool(
            re.search(r"line[s]?\s+\d+|:\d+[-–]\d+|lines?\s+\d+[-–]\d+", content)
        )
        lineno_scores.append(1.0 if has_lineno else 0.0)
    lineno_rate = sum(lineno_scores) / len(lineno_scores) if lineno_scores else 0.0

    checks_raw = {
        "compliant_rate": (compliant_rate, 0.55),
        "lineno_reference_rate": (lineno_rate, 0.45),
    }
    score, pass_rates = _weighted(checks_raw)
    details = (
        f"compliant_rate={compliant_rate:.2f}, lineno_reference_rate={lineno_rate:.2f}"
    )
    return AgentScore("design-reviewer", round(score, 4), pass_rates, details)


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------

_SCORERS = {
    "hypothesis-generator": _score_hypothesis_generator,
    "question-designer": _score_question_designer,
    "synthesizer": _score_synthesizer,
    "quantitative-analyst": _score_quantitative_analyst,
    # BL 2.0 operational agents (F17.1)
    "diagnose-analyst": _score_diagnose_analyst,
    "fix-implementer": _score_fix_implementer,
    "compliance-auditor": _score_compliance_auditor,
    "design-reviewer": _score_design_reviewer,
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
