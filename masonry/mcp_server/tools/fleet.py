"""masonry/mcp_server/tools/fleet.py — Fleet, recall, optimization, and drift tool implementations."""

from __future__ import annotations

import json
import os
from pathlib import Path

from masonry.mcp_server.js_engine import _REPO_ROOT


def _tool_masonry_fleet(args: dict) -> dict:
    """List fleet agents and their scores from registry.json / agent_db.json."""
    project_dir = args.get("project_dir", os.getcwd())
    limit = int(args.get("limit", 30))

    registry_file = Path(project_dir) / "registry.json"
    agent_db_file = Path(project_dir) / "agent_db.json"

    agents = []

    if registry_file.exists():
        try:
            registry = json.loads(registry_file.read_text())
            agents = (
                registry.get("agents", registry)
                if isinstance(registry, dict)
                else registry
            )
        except Exception:
            pass

    scores: dict = {}
    if agent_db_file.exists():
        try:
            db = json.loads(agent_db_file.read_text())
            for name, data in db.items():
                scores[name] = data.get("score", data.get("avg_score", 0))
        except Exception:
            pass

    for a in agents:
        name = a.get("name", "")
        if name in scores:
            a["score"] = scores[name]

    agents_sorted = sorted(agents, key=lambda a: a.get("score", 0), reverse=True)[:limit]

    return {
        "agents": agents_sorted,
        "count": len(agents_sorted),
        "has_scores": bool(scores),
    }


def _tool_masonry_recall_search(args: dict) -> dict:
    """Search Recall for memories relevant to a query."""
    query = args.get("query", "")
    limit = int(args.get("limit", 10))
    domain = args.get("domain")

    if not query:
        return {"error": "query is required"}

    from bl.recall_bridge import search_prior_findings  # noqa: PLC0415

    try:
        results = search_prior_findings(query, domain=domain, limit=limit)
        return {
            "results": results,
            "count": len(results) if isinstance(results, list) else 0,
        }
    except Exception as e:
        return {"error": str(e)}


def _tool_masonry_optimization_status(args: dict) -> dict:
    """Return optimization scores for all agents that have been through the improve loop."""
    optimized_dir = Path(
        args.get("optimized_dir", str(_REPO_ROOT / "masonry" / "optimized_prompts"))
    )

    if not optimized_dir.exists():
        return {"agents": [], "count": 0}

    agents = []
    for json_file in optimized_dir.glob("*.json"):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            agents.append({"agent": json_file.stem, "score": data.get("score", 0.0)})
        except Exception:
            pass

    return {"agents": agents, "count": len(agents)}


MIN_VERDICTS_FOR_AUTO_OPTIMIZE = 10


def _tool_masonry_drift_check(args: dict) -> dict:
    """Run drift detection for all registry agents that have verdict history."""
    import platform
    import subprocess

    agent_db_path = Path(args.get("agent_db_path", str(_REPO_ROOT / "agent_db.json")))
    registry_path = Path(args.get("registry_path", str(_REPO_ROOT / "masonry" / "agent_registry.yml")))
    auto_trigger: bool = args.get("auto_trigger", False)
    trigger_level: str = args.get("trigger_level", "critical")

    try:
        from masonry.src.schemas.registry_loader import load_registry  # noqa: PLC0415
        from masonry.src.drift_detector import run_drift_check  # noqa: PLC0415

        registry = load_registry(registry_path)
        reports = run_drift_check(agent_db_path, registry)

        triggered: list[str] = []
        trigger_errors: list[str] = []

        if auto_trigger:
            levels_to_trigger = {"critical"} if trigger_level == "critical" else {"critical", "warning"}
            agent_db: dict = {}
            if agent_db_path.exists():
                try:
                    agent_db = json.loads(agent_db_path.read_text(encoding="utf-8"))
                except Exception:
                    agent_db = {}
            for report in reports:
                if report.alert_level not in levels_to_trigger:
                    continue
                verdict_count = len(agent_db.get(report.agent_name, {}).get("verdicts", []))
                if verdict_count < MIN_VERDICTS_FOR_AUTO_OPTIMIZE:
                    continue
                try:
                    python = "python" if platform.system() == "Windows" else "python3"
                    proc = subprocess.Popen(
                        [python, "masonry/scripts/improve_agent.py", report.agent_name],
                        cwd=str(_REPO_ROOT),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    triggered.append(f"{report.agent_name} (pid={proc.pid})")
                except Exception as exc:
                    trigger_errors.append(f"{report.agent_name}: {exc}")

        result = {
            "reports": [r.model_dump() for r in reports],
            "count": len(reports),
            "summary": {
                "critical": sum(1 for r in reports if r.alert_level == "critical"),
                "warning": sum(1 for r in reports if r.alert_level == "warning"),
                "ok": sum(1 for r in reports if r.alert_level == "ok"),
            },
        }
        if auto_trigger:
            result["triggered"] = triggered
            if trigger_errors:
                result["trigger_errors"] = trigger_errors
        return result

    except ImportError:
        return {"error": "drift_detector module not available", "reports": []}
    except Exception as exc:
        return {"error": str(exc), "reports": []}
