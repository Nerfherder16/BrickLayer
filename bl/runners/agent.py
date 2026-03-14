"""
bl/runners/agent.py — Specialist agent runner and Scout.

Invokes Claude CLI agents non-interactively and parses their JSON output
contract into a BrickLayer verdict envelope.
"""

import json
import os
import re
import shutil
import subprocess

from bl.config import cfg


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _strip_frontmatter(text: str) -> str:
    """Strip YAML frontmatter (--- ... ---) from a markdown file."""
    if not text.startswith("---"):
        return text
    try:
        end = text.index("---", 3)
        return text[end + 3 :].strip()
    except ValueError:
        return text


def _verdict_from_agent_output(agent_name: str, output: dict) -> str:
    """Map agent JSON output contract to a BrickLayer verdict."""
    if not output:
        return "INCONCLUSIVE"

    if agent_name == "security-hardener":
        if output.get("risks_fixed", 0) > 0 or output.get("changes_committed", 0) > 0:
            return "HEALTHY"
        if output.get("risks_reported", 0) > 0:
            return "WARNING"

    elif agent_name == "test-writer":
        before = output.get("coverage_before", 0.0)
        after = output.get("coverage_after", 0.0)
        written = output.get("tests_written", 0)
        if written > 0 and after > before:
            return "HEALTHY"
        if written > 0:
            return "WARNING"

    elif agent_name == "type-strictener":
        before = output.get("errors_before", 0)
        after = output.get("errors_after", 0)
        committed = output.get("changes_committed", 0)
        if committed > 0 and after < before:
            return "HEALTHY"
        if committed > 0:
            return "WARNING"
        if output.get("mitigation_required") is False:
            return "HEALTHY"
        if output.get("architectural_debt") and not committed:
            return "WARNING"

    elif agent_name == "perf-optimizer":
        pct = output.get("improvement_pct", 0.0)
        committed = output.get("changes_committed", 0)
        if committed > 0 and pct >= 20:
            return "HEALTHY"
        if committed > 0 and pct >= 5:
            return "WARNING"

    else:
        if output.get("changes_committed", 0) > 0:
            return "HEALTHY"

    self_verdict = output.get("verdict", "").upper()
    if self_verdict in ("HEALTHY", "WARNING", "FAILURE", "INCONCLUSIVE"):
        return self_verdict

    return "INCONCLUSIVE"


def _parse_text_output(agent_name: str, text: str) -> dict:
    """
    Fallback parser when the agent produces plain text instead of a JSON block.
    Extracts key metrics using regex patterns matched to each agent type.
    """
    out: dict = {}

    commit_matches = re.findall(
        r"commit[ted]*\s+[`']?([0-9a-f]{7,})[`']?", text, re.IGNORECASE
    )
    if commit_matches:
        out["changes_committed"] = len(commit_matches)

    if agent_name == "security-hardener":
        for pattern in [
            r"(\d+)\s+risks?\s+fixed",
            r"(\d+)\s+\w[\w\s]+\s+fixed",
        ]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m and not out.get("risks_fixed"):
                out["risks_fixed"] = int(m.group(1))
        m = re.search(r"(\d+)\s+risks?\s+(?:found|identified)", text, re.IGNORECASE)
        if m:
            out["risks_found"] = int(m.group(1))
        m = re.search(
            r"(\d+)\s+(?:new\s+)?(?:security\s+)?tests?\s+written", text, re.IGNORECASE
        )
        if m:
            out["tests_written"] = int(m.group(1))
        m = re.search(r"(\d+)\s+risks?\s+reported", text, re.IGNORECASE)
        if m:
            out["risks_reported"] = int(m.group(1))

    elif agent_name == "test-writer":
        m = re.search(r"(\d+)\s+tests?\s+written", text, re.IGNORECASE)
        if m:
            out["tests_written"] = int(m.group(1))
        m = re.search(
            r"coverage[:\s]+(\d+(?:\.\d+)?)%\s*[→\-]+\s*(\d+(?:\.\d+)?)%", text
        )
        if m:
            out["coverage_before"] = float(m.group(1)) / 100
            out["coverage_after"] = float(m.group(2)) / 100

    elif agent_name == "type-strictener":
        m = re.search(r"(\d+)\s+errors?\s+[→\-]+\s*(\d+)", text)
        if m:
            out["errors_before"] = int(m.group(1))
            out["errors_after"] = int(m.group(2))

    elif agent_name == "perf-optimizer":
        m = re.search(r"p99[:\s]+(\d+(?:\.\d+)?)ms\s*[→\-]+\s*(\d+(?:\.\d+)?)ms", text)
        if m:
            out["p99_before"] = float(m.group(1))
            out["p99_after"] = float(m.group(2))
            if out["p99_before"] > 0:
                out["improvement_pct"] = round(
                    (out["p99_before"] - out["p99_after"]) / out["p99_before"] * 100, 1
                )

    return out


def _summary_from_agent_output(agent_name: str, output: dict) -> str:
    """Build a concise summary from agent output contract."""
    if not output:
        return f"{agent_name}: no structured output produced"

    if agent_name == "security-hardener":
        return (
            f"risks_found={output.get('risks_found', '?')} "
            f"fixed={output.get('risks_fixed', '?')} "
            f"committed={output.get('changes_committed', '?')} "
            f"tests_written={output.get('tests_written', '?')}"
        )
    if agent_name == "test-writer":
        before = output.get("coverage_before", 0.0)
        after = output.get("coverage_after", 0.0)
        return (
            f"coverage {before * 100:.0f}% → {after * 100:.0f}% "
            f"({output.get('tests_written', '?')} tests written)"
        )
    if agent_name == "type-strictener":
        return (
            f"mypy errors {output.get('errors_before', '?')} → "
            f"{output.get('errors_after', '?')} "
            f"({output.get('changes_committed', '?')} changes committed)"
        )
    if agent_name == "perf-optimizer":
        return (
            f"p99 {output.get('p99_before', '?')}ms → {output.get('p99_after', '?')}ms "
            f"({output.get('improvement_pct', 0.0):.1f}% improvement)"
        )
    return f"{agent_name}: {json.dumps(output)[:200]}"


# ---------------------------------------------------------------------------
# Agent runner
# ---------------------------------------------------------------------------


def run_agent(question: dict) -> dict:
    """
    Invoke a specialist agent against a BrickLayer finding via Claude CLI.

    The agent's system prompt is read from agents/{agent_name}.md.
    The finding context is injected from findings/{finding_id}.md.
    The agent runs non-interactively via `claude -p` and its JSON output
    contract is parsed from the response to produce the verdict envelope.
    """
    agent_name = question.get("agent_name", "").strip()
    finding_id = question.get("finding", "").strip()
    source_file = question.get("source", "").strip()

    if not agent_name:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "No agent specified — add **Agent**: <name> to question",
            "data": {},
            "details": f"Available: {[f.stem for f in cfg.agents_dir.glob('*.md') if f.stem != 'SCHEMA']}",
        }

    agent_path = cfg.agents_dir / f"{agent_name}.md"
    if not agent_path.exists():
        available = [f.stem for f in cfg.agents_dir.glob("*.md") if f.stem != "SCHEMA"]
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"Agent file not found: {agent_name}.md",
            "data": {"available_agents": available},
            "details": f"Expected at: {agent_path}",
        }

    agent_prompt = _strip_frontmatter(agent_path.read_text(encoding="utf-8"))

    # C-27: inject project doctrine if present
    doctrine_prefix = ""
    doctrine_path = cfg.project_root / "doctrine.md"
    if doctrine_path.exists():
        doctrine_content = doctrine_path.read_text(encoding="utf-8")
        doctrine_prefix = (
            f"## Campaign Doctrine\n\n"
            f"{doctrine_content}\n\n"
            f"---\n\n"
            f"## Agent Instructions\n\n"
        )

    finding_context = "(no finding specified)"
    if finding_id:
        finding_path = cfg.findings_dir / f"{finding_id}.md"
        if finding_path.exists():
            finding_context = finding_path.read_text(encoding="utf-8")
        else:
            finding_context = (
                f"(Finding {finding_id} not found — run that question first)"
            )

    source_line = (
        f"\n**Source file**: `{cfg.recall_src / source_file}`" if source_file else ""
    )

    # C-29: inject REMEDIATION GUARD when the question involves a corrective action
    _REMEDIATION_KEYWORDS = (
        "amnesty",
        "reconcile",
        "backfill",
        "rehabilitate",
        "repair",
        "boost",
    )
    _question_text = (
        question.get("hypothesis", "") + " " + question.get("test", "")
    ).lower()
    remediation_guard = ""
    if question.get("mode") == "agent" and any(
        kw in _question_text for kw in _REMEDIATION_KEYWORDS
    ):
        remediation_guard = """
---
## REMEDIATION GUARD (C-29)

Before executing ANY corrective action (calling amnesty, reconcile, backfill, rehabilitate,
or any endpoint that modifies data), you MUST first:

1. Measure the current metric (e.g. GET /admin/health/memory-quality → mean_quality)
2. Calculate whether the proposed action can move that metric past the HEALTHY threshold
   - If action floor < threshold: the action CANNOT move the mean past threshold — document
     this as "structural fix required" and DO NOT apply the patch
3. Only proceed if projected_outcome >= threshold

If the action is infeasible, record: "remediation_infeasible: projected_delta={delta}, threshold={threshold}"
This prevents applying ineffective patches that create false confidence.
"""

    full_prompt = f"""{doctrine_prefix}{agent_prompt}

---

## Your Assignment

**Project root**: `{cfg.recall_src}`{source_line}
**Test directory**: `{cfg.recall_src / "tests"}`

**Finding to address**:

{finding_context}{remediation_guard}

Begin your agent loop now. Output your JSON result contract in a ```json ... ``` block when complete."""

    claude_bin = shutil.which("claude") or "claude"
    child_env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    try:
        proc = subprocess.run(
            [
                claude_bin,
                "-p",
                "-",
                "--output-format",
                "json",
                "--allowedTools",
                "Read,Write,Edit,Bash,Glob,Grep",
            ],
            input=full_prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=600,
            cwd=str(cfg.recall_src),
            env=child_env,
        )
        raw = proc.stdout

        agent_text = raw
        try:
            wrapper = json.loads(raw)
            if isinstance(wrapper, dict):
                agent_text = wrapper.get("result", raw)
        except json.JSONDecodeError:
            pass

        agent_output: dict = {}
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", agent_text, re.DOTALL)
        if json_match:
            try:
                agent_output = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        if not agent_output and agent_text:
            agent_output = _parse_text_output(agent_name, agent_text)

        verdict = _verdict_from_agent_output(agent_name, agent_output)
        summary = _summary_from_agent_output(agent_name, agent_output)

        return {
            "verdict": verdict,
            "summary": summary,
            "data": agent_output,
            "details": agent_text[:4000],
        }

    except subprocess.TimeoutExpired:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"{agent_name} timed out after 600s",
            "data": {},
            "details": "Agent loop exceeded time limit — check for infinite loops or missing iteration bounds",
        }
    except FileNotFoundError:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "claude CLI not found — ensure Claude Code is installed and on PATH",
            "data": {},
            "details": "Install: https://claude.ai/download",
        }


# ---------------------------------------------------------------------------
# Scout runner
# ---------------------------------------------------------------------------


def run_scout_for_project() -> None:
    """Invoke the Scout agent to regenerate questions.md."""
    scout_path = cfg.agents_dir / "scout.md"
    if not scout_path.exists():
        print(json.dumps({"error": "scout.md not found in agents/"}))
        return

    body = _strip_frontmatter(scout_path.read_text(encoding="utf-8"))

    project_cfg: dict = {}
    cfg_path = cfg.project_root / "project.json"
    if cfg_path.exists():
        project_cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    docs_dir = cfg.project_root / "docs"
    docs_content = ""
    if docs_dir.exists():
        for doc in sorted(docs_dir.iterdir()):
            if doc.is_file():
                try:
                    docs_content += f"\n\n### {doc.name}\n{doc.read_text(encoding='utf-8', errors='ignore')[:3000]}"
                except Exception as exc:  # noqa: BLE001
                    import sys

                    print(f"[scout] skipping {doc.name}: {exc}", file=sys.stderr)

    prompt = f"""{body}

---

## Your Assignment

**Project**: {project_cfg.get("display_name", "Unknown")}
**Target git**: {cfg.recall_src}
**Stack**: {", ".join(project_cfg.get("stack", [])) or "unknown"}
**Live service**: {project_cfg.get("target_live_url", "none")}
**Docs folder**: {docs_dir}
{f"**Supporting docs content**:{docs_content}" if docs_content else "**Docs folder**: empty — scan the codebase only"}

Scan the target codebase now and output the complete questions.md content."""

    claude_bin = shutil.which("claude") or "claude"
    child_env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    print("Running Scout — scanning codebase to generate questions...", flush=True)
    try:
        proc = subprocess.run(
            [claude_bin, "-p", "-", "--dangerously-skip-permissions"],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=child_env,
            timeout=300,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(json.dumps({"error": str(e)}))
        return

    output = proc.stdout.strip()
    idx = output.find("# BrickLayer Campaign Questions")
    if idx == -1:
        print(json.dumps({"error": "Scout output not recognized", "raw": output[:500]}))
        return

    questions_md = output[idx:]
    cfg.questions_md.write_text(questions_md, encoding="utf-8")
    count = questions_md.count("## Q")
    print(
        json.dumps(
            {"status": "ok", "questions_written": count, "path": str(cfg.questions_md)}
        )
    )
