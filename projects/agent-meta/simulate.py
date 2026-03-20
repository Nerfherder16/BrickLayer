"""
Agent Meta-Campaign — Simulation
Scores the BrickLayer 2.0 agent fleet against quality criteria.
The SCENARIO PARAMETERS section is the only part agents should modify.
"""

import os
import re
import glob
from pathlib import Path

# ============================================================
# CONSTANTS (never edit)
# ============================================================
from constants import (
    MIN_DESCRIPTION_LENGTH,
    REQUIRED_SECTIONS,
    REQUIRED_AGENTS,
    VALID_VERDICTS,
)

# ============================================================
# SCENARIO PARAMETERS — agents edit only this section
# ============================================================

# Path to the agents directory being audited
AGENTS_DIR = "../../template/.claude/agents"

# Agent subset to focus on (empty list = all agents)
FOCUS_AGENTS = []

# Whether to check cross-agent interface compatibility
CHECK_INTERFACES = True

# Whether to check for phantom agents (called but no .md file)
CHECK_PHANTOMS = True

# program.md path (for phantom agent detection)
PROGRAM_MD = "../../template/program.md"

# ============================================================
# SIMULATION ENGINE (never edit below this line)
# ============================================================


def load_agents(agents_dir: str) -> dict:
    """Load all agent .md files and parse frontmatter + sections."""
    agents = {}
    pattern = os.path.join(agents_dir, "*.md")
    for path in glob.glob(pattern):
        name = Path(path).stem
        if name in ("AUDIT_REPORT", "FORGE_NEEDED"):
            continue
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse frontmatter (handles block scalars like "description: >\n  text")
        frontmatter = {}
        fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if fm_match:
            fm_text = fm_match.group(1)
            current_key = None
            current_block = []
            in_block = False

            for line in fm_text.splitlines():
                if (
                    ":" in line
                    and not line.startswith(" ")
                    and not line.startswith("\t")
                ):
                    # Save previous block if any
                    if current_key and in_block:
                        frontmatter[current_key] = " ".join(current_block).strip()
                    k, v = line.split(":", 1)
                    current_key = k.strip()
                    v = v.strip()
                    if v in (">", "|", ">-", "|-"):
                        in_block = True
                        current_block = []
                    else:
                        in_block = False
                        frontmatter[current_key] = v
                elif in_block and (line.startswith("  ") or line.startswith("\t")):
                    current_block.append(line.strip())

            # Save last block
            if current_key and in_block and current_block:
                frontmatter[current_key] = " ".join(current_block).strip()

        agents[name] = {
            "path": path,
            "content": content,
            "frontmatter": frontmatter,
            "description": frontmatter.get("description", ""),
            "sections": re.findall(r"^#{1,3} .+", content, re.MULTILINE),
        }
    return agents


def score_agent(name: str, agent: dict) -> dict:
    """Score a single agent on all quality dimensions."""
    issues = []
    score = 100  # Start at 100, deduct for issues

    content = agent["content"]
    description = agent["description"]

    # 1. Description quality
    if len(description) < MIN_DESCRIPTION_LENGTH:
        issues.append(
            f"Description too short ({len(description)} chars, min {MIN_DESCRIPTION_LENGTH})"
        )
        score -= 15

    # 2. Required sections — check presence AND that section has substantive content
    # (hollow section bypass: "## Output contract" header with empty body scored as present)
    content_lines = content.splitlines()
    for required in REQUIRED_SECTIONS:
        req_lower = required.lower()
        # Find the first section heading that starts with the required prefix
        section_idx = None
        for i, line in enumerate(content_lines):
            if re.match(r"^#{1,3} ", line) and line.lower().lstrip(
                "#"
            ).strip().startswith(req_lower.lstrip("#").strip()):
                section_idx = i
                break

        if section_idx is None:
            issues.append(f"Missing required section: {required}")
            score -= 10
        else:
            # Check that the section has substantive content (> 10 non-whitespace chars
            # before the next section heading)
            section_body = []
            for line in content_lines[section_idx + 1 :]:
                if re.match(r"^#{1,3} ", line):
                    break
                section_body.append(line)
            body_text = " ".join(section_body).strip()
            if len(body_text) < 10:
                issues.append(
                    f"Section '{required}' exists but has hollow content (< 10 chars)"
                )
                score -= 20  # Harsher penalty than missing — intentional bypass

    # 3. Output contract
    if "output contract" not in content.lower():
        issues.append("No output contract defined")
        score -= 20

    # 4. Recall section
    if "recall_store" not in content and "recall_search" not in content:
        issues.append("No recall_store or recall_search calls")
        score -= 10

    # 5. Verdict taxonomy
    verdicts_in_agent = re.findall(r"\b(" + "|".join(VALID_VERDICTS) + r")\b", content)
    if not verdicts_in_agent:
        issues.append("No recognized BL 2.0 verdicts found in agent definition")
        score -= 15

    # 6. Tag format
    if 'tags=["bricklayer"' not in content and "tags:" not in content:
        issues.append("Recall tags don't follow bricklayer tagging convention")
        score -= 5

    return {
        "name": name,
        "score": max(0, score),
        "issues": issues,
        "verdict": "HEALTHY"
        if score >= 80
        else "WARNING"
        if score >= 60
        else "FAILING",
        "description_length": len(description),
        "verdict_count": len(set(verdicts_in_agent)),
    }


def check_phantom_agents(agents: dict, program_md_path: str) -> list:
    """Find agents called in program.md that have no .md definition."""
    if not os.path.exists(program_md_path):
        return []

    with open(program_md_path, "r", encoding="utf-8") as f:
        program = f.read()

    # Find agent names referenced in program.md
    referenced = set(re.findall(r"\.claude/agents/([\w-]+)\.md", program))
    referenced |= set(re.findall(r'agent[_-]name["\s]*[:=]["\s]*([\w-]+)', program))

    # Exclude known generated output files that are not agents
    NOT_AGENTS = {"AUDIT_REPORT", "FORGE_NEEDED", "CAMPAIGN_PLAN", "GITHUB_HANDOFF"}
    phantoms = [
        name for name in referenced if name not in agents and name not in NOT_AGENTS
    ]
    return phantoms


def check_required_fleet(agents: dict) -> list:
    """Check that all required agents exist."""
    missing = [name for name in REQUIRED_AGENTS if name not in agents]
    return missing


def run_simulation():
    """Main simulation — scores the agent fleet."""
    print(f"Loading agents from: {AGENTS_DIR}")
    agents = load_agents(AGENTS_DIR)

    focus = FOCUS_AGENTS if FOCUS_AGENTS else list(agents.keys())
    results = []

    for name in focus:
        if name not in agents:
            print(f"WARNING: Focus agent '{name}' not found in {AGENTS_DIR}")
            continue
        result = score_agent(name, agents[name])
        results.append(result)

    # Fleet-level checks
    phantom_agents = check_phantom_agents(agents, PROGRAM_MD) if CHECK_PHANTOMS else []
    missing_required = check_required_fleet(agents)

    # Aggregate scoring
    if not results:
        print("No agents to score.")
        return

    avg_score = sum(r["score"] for r in results) / len(results)
    failing = [r for r in results if r["verdict"] == "FAILING"]
    warning = [r for r in results if r["verdict"] == "WARNING"]
    healthy = [r for r in results if r["verdict"] == "HEALTHY"]

    # Verdict
    if phantom_agents or missing_required or failing:
        verdict = "CRITICAL"
    elif warning:
        verdict = "WARNING"
    else:
        verdict = "HEALTHY"

    print(f"\n{'=' * 60}")
    print(f"FLEET VERDICT: {verdict}")
    print(f"Agents scored: {len(results)}")
    print(
        f"Healthy: {len(healthy)} | Warning: {len(warning)} | Failing: {len(failing)}"
    )
    print(f"Average score: {avg_score:.1f}/100")

    if phantom_agents:
        print(f"\nPHANTOM AGENTS (called but no .md): {phantom_agents}")

    if missing_required:
        print(f"\nMISSING REQUIRED AGENTS: {missing_required}")

    print(f"\n{'=' * 60}")
    for r in sorted(results, key=lambda x: x["score"]):
        status = (
            "[FAIL]"
            if r["verdict"] == "FAILING"
            else "[WARN]"
            if r["verdict"] == "WARNING"
            else "[ OK ]"
        )
        print(f"{status} {r['name']:30s} {r['score']:3d}/100  ({r['verdict']})")
        for issue in r["issues"]:
            print(f"   -> {issue}")

    return {
        "verdict": verdict,
        "avg_score": avg_score,
        "fleet_size": len(results),
        "failing": [r["name"] for r in failing],
        "phantom_agents": phantom_agents,
        "missing_required": missing_required,
    }


if __name__ == "__main__":
    run_simulation()
