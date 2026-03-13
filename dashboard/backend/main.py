import os
import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Autosearch Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3100", "http://127.0.0.1:3100"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_project_path(project: str | None = None) -> Path:
    path_str = project or os.environ.get(
        "AUTOSEARCH_PROJECT", "C:/Users/trg16/Dev/autosearch/adbp"
    )
    resolved = Path(path_str).resolve()
    base = Path(
        os.getenv("AUTOSEARCH_BASE", str(Path(__file__).parent.parent.parent))
    ).resolve()
    if not resolved.is_relative_to(base):
        raise HTTPException(status_code=400, detail="Invalid project path")
    return resolved


def parse_questions(project_path: Path) -> list[dict]:
    """Parse questions.md — supports both block format (## Q1.1 [CAT] Title) and
    legacy table format (| ID | Status | Question |)."""
    qfile = project_path / "questions.md"
    if not qfile.exists():
        return []

    content = qfile.read_text(encoding="utf-8")
    lines = content.splitlines()

    # Detect format: block format uses "## Q{N}.{M}" headers
    is_block_format = any(re.match(r"^##\s+Q\d+\.\d+", line) for line in lines)

    questions = []

    if is_block_format:
        # Block format: ## Q1.1 [CATEGORY] Title followed by **Status**: field
        current_q = None
        for line in lines:
            header_match = re.match(r"^##\s+(Q\d+\.\d+\w*)\s+\[([^\]]+)\]\s+(.*)", line)
            if header_match:
                current_q = {
                    "id": header_match.group(1),
                    "title": header_match.group(3).strip(),
                    "status": "PENDING",
                    "domain": f"D{header_match.group(1).split('.')[0][1:]}",
                    "hypothesis": None,
                    "mode": None,
                }
                questions.append(current_q)
                continue

            if current_q is not None:
                status_match = re.match(r"^\*\*Status\*\*:\s*(\w+)", line)
                if status_match:
                    val = status_match.group(1).upper()
                    if val in ("PENDING", "DONE", "INCONCLUSIVE", "IN_PROGRESS"):
                        current_q["status"] = val
                    continue

                mode_match = re.match(r"^\*\*Mode\*\*:\s*(\S+)", line)
                if mode_match:
                    current_q["mode"] = mode_match.group(1).strip()
                    continue

                hyp_match = re.match(r"^\*\*Hypothesis\*\*:\s*(.*)", line)
                if hyp_match:
                    current_q["hypothesis"] = hyp_match.group(1).strip()
                    continue
    else:
        # Legacy table format: | ID | Status | Question |
        current_domain = None
        for line in lines:
            domain_match = re.match(r"^##\s+Domain\s+(\d+)\s*[—-]\s*(.+)", line)
            if domain_match:
                current_domain = f"D{domain_match.group(1)}"
                continue

            row_match = re.match(
                r"^\|\s*([^\|]+?)\s*\|\s*([^\|]+?)\s*\|\s*(.+?)\s*\|$", line
            )
            if row_match:
                q_id = row_match.group(1).strip()
                status = row_match.group(2).strip().upper()
                title = row_match.group(3).strip()

                if q_id.upper() in ("ID", "---", "") or status in ("STATUS", "---", ""):
                    continue
                if re.match(r"^[-\s]+$", q_id):
                    continue

                if status in ("PENDING", "DONE", "INCONCLUSIVE", "IN_PROGRESS"):
                    questions.append(
                        {
                            "id": q_id,
                            "title": title,
                            "status": status,
                            "domain": current_domain or "D?",
                            "hypothesis": None,
                        }
                    )

    return questions


def parse_results(project_path: Path) -> list[dict]:
    """Parse results.tsv."""
    rfile = project_path / "results.tsv"
    if not rfile.exists():
        return []

    rows = []
    lines = rfile.read_text(encoding="utf-8").splitlines()
    if not lines:
        return []

    headers = [h.strip() for h in lines[0].split("\t")]
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split("\t")]
        row = dict(zip(headers, parts))
        rows.append(row)
    return rows


_findings_cache: dict = {}
_FINDINGS_CACHE_TTL = 5.0  # seconds


def parse_findings_index(project_path: Path) -> list[dict]:
    """List findings/ directory and parse metadata from each .md file.

    Results are cached for _FINDINGS_CACHE_TTL seconds to avoid re-reading
    all .md files on every dashboard refresh (Q6.3).
    """
    import time

    cache_key = str(project_path)
    cached = _findings_cache.get(cache_key)
    if cached and time.monotonic() - cached["ts"] < _FINDINGS_CACHE_TTL:
        return cached["data"]

    findings_dir = project_path / "findings"
    if not findings_dir.exists():
        return []

    findings = []
    for f in sorted(
        findings_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True
    ):
        content = f.read_text(encoding="utf-8")
        # Title: first # line
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else f.stem

        # Verdict: **Verdict**: WARNING / HEALTHY / FAILURE / INCONCLUSIVE
        verdict_match = re.search(r"\*\*Verdict\*\*:\s*(\w+)", content)
        verdict = verdict_match.group(1).upper() if verdict_match else "UNKNOWN"

        # Severity: **Severity**: ...
        sev_match = re.search(r"\*\*Severity\*\*:\s*([^\n]+)", content)
        severity = sev_match.group(1).strip() if sev_match else ""

        has_correction = "## Human Correction" in content

        findings.append(
            {
                "id": f.stem,
                "title": title,
                "verdict": verdict,
                "severity": severity,
                "has_correction": has_correction,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            }
        )

    _findings_cache[cache_key] = {"data": findings, "ts": time.monotonic()}
    return findings


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class AddQuestion(BaseModel):
    question: str
    domain: str
    hypothesis: str = ""
    priority: str = "end"  # "next" | "end"


class AddCorrection(BaseModel):
    correction: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/api/status")
def get_status(project: str | None = Query(None)):
    project_path = get_project_path(project)
    questions = parse_questions(project_path)
    results = parse_results(project_path)

    verdict_counts = {"FAILURE": 0, "WARNING": 0, "HEALTHY": 0, "INCONCLUSIVE": 0}
    for row in results:
        v = row.get("verdict", "").upper()
        if v in verdict_counts:
            verdict_counts[v] += 1

    q_counts = {"PENDING": 0, "DONE": 0, "INCONCLUSIVE": 0, "IN_PROGRESS": 0}
    for q in questions:
        s = q["status"]
        if s in q_counts:
            q_counts[s] += 1

    rfile = project_path / "results.tsv"
    last_modified = None
    if rfile.exists():
        last_modified = datetime.fromtimestamp(rfile.stat().st_mtime).isoformat()

    return {
        "project": project_path.name,
        "project_path": str(project_path),
        "questions": q_counts,
        "verdicts": verdict_counts,
        "last_modified": last_modified,
    }


@app.get("/api/questions")
def get_questions(project: str | None = Query(None)):
    project_path = get_project_path(project)
    return parse_questions(project_path)


@app.post("/api/questions")
def add_question(body: AddQuestion, project: str | None = Query(None)):
    project_path = get_project_path(project)
    qfile = project_path / "questions.md"
    if not qfile.exists():
        raise HTTPException(status_code=404, detail="questions.md not found")

    title = body.question.strip()
    hypothesis = body.hypothesis.strip() if body.hypothesis else title

    # Find next question ID within domain — use max to avoid collision after deletions
    questions = parse_questions(project_path)
    domain_num = body.domain.replace("D", "")
    domain_ids = [q["id"] for q in questions if q["domain"] == body.domain]
    existing_nums = []
    for qid in domain_ids:
        m = re.match(r"Q?\d+\.(\d+)", qid)
        if m:
            existing_nums.append(int(m.group(1)))
    next_num = (max(existing_nums) + 1) if existing_nums else 1
    new_id = f"Q{domain_num}.{next_num}x"  # 'x' suffix marks manually added

    new_block = (
        f"\n## {new_id} [CUSTOM] {title}\n"
        f"**Mode**: custom\n"
        f"**Target**: TBD\n"
        f"**Hypothesis**: {hypothesis}\n"
        f"**Status**: PENDING\n"
    )

    content = qfile.read_text(encoding="utf-8")

    if body.priority == "next":
        # Insert before the first PENDING block header
        lines = content.splitlines()
        insert_at = None
        for i, line in enumerate(lines):
            if re.match(r"^##\s+Q\d+\.\d+", line):
                # Check if this block's status is PENDING (default if no Status field)
                block_status = "PENDING"
                for j in range(i + 1, min(i + 10, len(lines))):
                    sm = re.match(r"^\*\*Status\*\*:\s*(\w+)", lines[j])
                    if sm:
                        block_status = sm.group(1).upper()
                        break
                    if re.match(r"^##", lines[j]):
                        break
                if block_status == "PENDING":
                    insert_at = i
                    break
        if insert_at is not None:
            lines.insert(insert_at, new_block.rstrip())
            content = "\n".join(lines) + "\n"
        else:
            content = content.rstrip() + new_block
    else:
        content = content.rstrip() + new_block

    qfile.write_text(content, encoding="utf-8")
    return {"ok": True, "id": new_id}


@app.get("/api/findings")
def get_findings(project: str | None = Query(None)):
    project_path = get_project_path(project)
    return parse_findings_index(project_path)


@app.get("/api/findings/{finding_id}")
def get_finding(finding_id: str, project: str | None = Query(None)):
    project_path = get_project_path(project)
    fpath = (project_path / "findings" / f"{finding_id}.md").resolve()
    findings_dir = (project_path / "findings").resolve()
    if not fpath.is_relative_to(findings_dir):
        raise HTTPException(status_code=400, detail="Invalid finding ID")
    if not fpath.exists():
        raise HTTPException(status_code=404, detail="Finding not found")
    return {"id": finding_id, "content": fpath.read_text(encoding="utf-8")}


@app.post("/api/findings/{finding_id}/correct")
def correct_finding(
    finding_id: str, body: AddCorrection, project: str | None = Query(None)
):
    project_path = get_project_path(project)
    fpath = (project_path / "findings" / f"{finding_id}.md").resolve()
    findings_dir = (project_path / "findings").resolve()
    if not fpath.is_relative_to(findings_dir):
        raise HTTPException(status_code=400, detail="Invalid finding ID")
    if not fpath.exists():
        raise HTTPException(status_code=404, detail="Finding not found")

    correction_block = f"""

## Human Correction
**Flagged by**: human
**Correction**: {body.correction.strip()}
**This overrides the finding above. Agents must treat this section as Tier 1 authority.**
"""
    with fpath.open("a", encoding="utf-8") as f:
        f.write(correction_block)

    # Invalidate findings cache so next GET /api/findings reflects the correction
    _findings_cache.pop(str(project_path), None)

    return {"ok": True}


@app.get("/api/results")
def get_results(project: str | None = Query(None)):
    project_path = get_project_path(project)
    return parse_results(project_path)


@app.get("/api/projects")
def get_projects():
    base = Path(os.getenv("AUTOSEARCH_BASE", str(Path(__file__).parent.parent.parent)))
    projects = []
    if base.exists():
        for d in sorted(base.iterdir()):
            if d.is_dir() and (d / "questions.md").exists():
                projects.append({"name": d.name, "path": str(d)})
    return projects


# Mount static frontend (after API routes)
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
