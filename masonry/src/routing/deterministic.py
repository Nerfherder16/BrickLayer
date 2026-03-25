"""Layer 1 — Deterministic routing.

Handles 60%+ of routing decisions with zero LLM calls using:
1. Slash command pattern matching
2. Autopilot state file inspection
3. Campaign state file inspection
4. UI compose/review state inspection
5. Question **Mode**: field extraction

Returns RoutingDecision with confidence=1.0 on any match, or None to fall through.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from masonry.src.schemas.payloads import AgentRegistryEntry, RoutingDecision
from masonry.src.schemas.registry_loader import get_agents_for_mode

# ── Slash command table ────────────────────────────────────────────────────

_SLASH_COMMANDS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"/plan\b"), "spec-writer"),
    (re.compile(r"/build\b"), "build-workflow"),
    (re.compile(r"/fix\b"), "fix-workflow"),
    (re.compile(r"/verify\b"), "verify-workflow"),
    (re.compile(r"/bl-run\b"), "campaign-conductor"),
    (re.compile(r"/masonry-run\b"), "campaign-conductor"),
]

# ── Agent keyword patterns (deterministic, zero LLM calls) ────────────────

_GIT_PATTERN = re.compile(
    r"\b(git\s+\w+|commit|push|pull\s+request|open\s+a\s+pr|create\s+a?\s*pr|"
    r"branch\s+off|merge\s+branch|rebase|git\s+stash|"
    r"stage\s+(files?|changes?)|unstage|amend\s+commit|cherry.pick)\b",
    re.IGNORECASE,
)

_UI_PATTERN = re.compile(
    r"\b(figma|tailwind|css|component|dashboard|dark\s+mode|design\s+system|"
    r"ui\s+review|ui\s+fix|ui\s+init|ui\s+compose|frontend|design\s+brief|"
    r"tokens\.json|glassmorphi|bento\s+grid)\b",
    re.IGNORECASE,
)

_KAREN_PATTERN = re.compile(
    r"\b(changelog|roadmap|folder\s+audit|organize\s+(the\s+)?(docs|folder|project)|"
    r"docs\s+organization|readme|project\s+structure|tidy\s+up)\b",
    re.IGNORECASE,
)

_DIAGNOSE_PATTERN = re.compile(
    r"\b(root\s+cause|why\s+is\s+(\w+\s+)?(broken|failing|not\s+working)|"
    r"why\s+(isn.t|isn.t|doesn.t|won.t)\s+\w+\s+work|"
    r"how\s+do\s+I\s+fix\s+(this|the)\s+(bug|error|issue|problem)|"
    r"diagnose|trace\s+(the\s+)?error|something\s+is\s+broken|debug\s+this|"
    r"what\s+is\s+broken|what's\s+broken|it.s\s+broken)\b",
    re.IGNORECASE,
)

_SECURITY_PATTERN = re.compile(
    r"\b(security\s+(audit|review)|owasp|vulnerability|xss|sql\s+injection|"
    r"csrf|injection\s+attack|penetration\s+test|pentest|hardening)\b",
    re.IGNORECASE,
)

_KILN_PATTERN = re.compile(
    r"\b(kiln|bricklayerhub|electron\s+app)\b",
    re.IGNORECASE,
)

_SOLANA_PATTERN = re.compile(
    r"\b(solana|anchor\s+program|spl\s+token|token.?2022|defi|adbp|"
    r"on.?chain|blockchain|wallet\s+integration)\b",
    re.IGNORECASE,
)

_REFACTOR_PATTERN = re.compile(
    r"\b(refactor|clean\s+up\s+(the\s+)?code|restructure|rename\s+(the\s+)?\w+|"
    r"extract\s+(a\s+)?(function|class|module)|code\s+smell)\b",
    re.IGNORECASE,
)

_ARCHITECT_PATTERN = re.compile(
    r"\b(system\s+design|architecture\s+(decision|review)|tech\s+stack|"
    r"scalab(le|ility)|trade.?off|design\s+pattern|microservice|monolith|"
    r"architect\s+a|how\s+should\s+I\s+design|design\s+a)\b",
    re.IGNORECASE,
)

_CAMPAIGN_PATTERN = re.compile(
    r"\b(start\s+(a\s+)?campaign|resume\s+(the\s+)?campaign|question\s+bank|"
    r"research\s+loop|wave\s+\d|bl.run|masonry.run)\b",
    re.IGNORECASE,
)

_RESEARCH_PATTERN = re.compile(
    r"\b(stress.test\s+(the\s+)?assumption|validate\s+assumption|"
    r"research\s+question|hypothesis\s+test|research\s+this)\b",
    re.IGNORECASE,
)

_COMPETITIVE_PATTERN = re.compile(
    r"\b(competitor|competitive\s+landscape|analogous\s+system|"
    r"how\s+have\s+others\s+solved|market\s+dynamic|benchmark\s+against)\b",
    re.IGNORECASE,
)

_REGULATORY_PATTERN = re.compile(
    r"\b(legal\s+(question|risk|review)|compliance\s+(question|requirement)|"
    r"regulation|licensing|gdpr|hipaa|tax\s+implication|regulatory)\b",
    re.IGNORECASE,
)

_QUANTITATIVE_PATTERN = re.compile(
    r"\b(parameter\s+sweep|failure\s+boundary|stress\s+test\s+(the\s+)?number|"
    r"run\s+(the\s+)?simulation|simulate\s+this|sweep\s+parameters)\b",
    re.IGNORECASE,
)

_BENCHMARK_PATTERN = re.compile(
    r"\b(benchmark|measure\s+(latency|throughput|performance)|"
    r"performance\s+test|latency\s+measurement|throughput\s+test)\b",
    re.IGNORECASE,
)

_BUG_CATCHER_PATTERN = re.compile(
    r"\b(hook\s+(error|failing|broken)|script\s+health|hook\s+syntax|"
    r"audit\s+(the\s+)?hooks|hook\s+not\s+firing)\b",
    re.IGNORECASE,
)

_FIX_IMPLEMENTER_PATTERN = re.compile(
    r"\b(DIAGNOSIS_COMPLETE|implement\s+the\s+fix|apply\s+the\s+fix|"
    r"fix\s+is\s+known|root\s+cause\s+is\s+known)\b",
    re.IGNORECASE,
)

_CODE_REVIEWER_PATTERN = re.compile(
    r"\b(review\s+(the|this|my)\s+code|code\s+review|review\s+the\s+diff|"
    r"review\s+this\s+PR|pre.commit\s+review)\b",
    re.IGNORECASE,
)

_CASCADE_PATTERN = re.compile(
    r"\b(what\s+breaks\s+next|failure\s+cascade|downstream\s+(impact|consequence)|"
    r"propagation\s+risk|what\s+else\s+(breaks|fails))\b",
    re.IGNORECASE,
)

_EVOLVE_PATTERN = re.compile(
    r"\b(highest.ROI\s+change|make\s+it\s+(faster|better)|next\s+level|"
    r"optimize\s+(the\s+)?system|what.s\s+the\s+next\s+improvement)\b",
    re.IGNORECASE,
)

_HEALTH_PATTERN = re.compile(
    r"\b(health\s+check|system\s+health|check\s+uptime|live\s+targets|"
    r"service\s+status|is\s+.+\s+up)\b",
    re.IGNORECASE,
)

_COMPLIANCE_AUDITOR_PATTERN = re.compile(
    r"\b(owasp\s+audit|wcag|audit\s+against|compliance\s+(audit|check)|"
    r"accessibility\s+audit)\b",
    re.IGNORECASE,
)

_AGENT_AUDITOR_PATTERN = re.compile(
    r"\b(audit\s+the\s+fleet|agent\s+scores|underperform(ing)?\s+agent|"
    r"fleet\s+audit|agent\s+performance)\b",
    re.IGNORECASE,
)

_SKILL_FORGE_PATTERN = re.compile(
    r"\b(distill\s+(into|to)\s+skills?|skill\s+registry|reusable\s+skill|"
    r"encode\s+(as\s+)?(a\s+)?skill)\b",
    re.IGNORECASE,
)

_PROMPT_ENGINEER_PATTERN = re.compile(
    r"\b(sharpen\s+this\s+prompt|rewrite\s+this\s+prompt|prompt\s+(isn.t|not)\s+working|"
    r"improve\s+this\s+prompt|prompt\s+engineering)\b",
    re.IGNORECASE,
)

_DEVOPS_PATTERN = re.compile(
    r"\b(CI/?CD|github\s+actions|pipeline\s+(config|setup)|kubernetes|"
    r"infrastructure\s+(as\s+code|config)|helm\s+chart|terraform)\b",
    re.IGNORECASE,
)

_SPREADSHEET_PATTERN = re.compile(
    r"\b(excel|spreadsheet|workbook|formula\s+(error|repair)|"
    r"\.xlsx|pivot\s+table)\b",
    re.IGNORECASE,
)

_SELF_HOST_PATTERN = re.compile(
    r"\b(self.host|deploy\s+(to\s+)?(casaos|vps|streamy)|"
    r"publish\s+(to\s+)?subdomain|nginx\s+config|casaos\s+deploy)\b",
    re.IGNORECASE,
)

_HYPOTHESIS_PATTERN = re.compile(
    r"\b(generate\s+(new|more)\s+questions|question\s+bank\s+exhausted|"
    r"new\s+wave\s+questions|hypothesis\s+generator)\b",
    re.IGNORECASE,
)

_SYNTHESIZER_PATTERN = re.compile(
    r"\b(synthesize\s+findings|write\s+(the\s+)?synthesis|end.of.session\s+report|"
    r"synthesis\.md)\b",
    re.IGNORECASE,
)

_FRONTIER_PATTERN = re.compile(
    r"\b(blue.sky|possibility\s+space|what\s+could\s+this\s+become|"
    r"ceiling\s+estimation|explore\s+what\s+.+\s+could\s+be)\b",
    re.IGNORECASE,
)

_EVAL_PATTERN = re.compile(
    r"\b(run\s+eval\b|improve.agent|eval\s+score|optimize\s+\w+\s+agent|"
    r"eval_agent\.py|baseline\s+eval|improve\s+agent\s+prompt)\b",
    re.IGNORECASE,
)

_MODE_GUIDANCE_PATTERN = re.compile(
    r"\b(what\s+mode|which\s+mode|what\s+bricklayer\s+mode|"
    r"what\s+stage\s+is|what\s+phase)\b",
    re.IGNORECASE,
)

_DEVELOPER_PATTERN = re.compile(
    r"\b(scaffold\s+(a\s+)?(new\s+)?(feature|component|service|module)|"
    r"add\s+(a\s+)?(new\s+)?(api\s+)?(endpoint|route|field|column|table|migration)|"
    r"implement\s+(a\s+)?(new\s+)?(function|method|feature|class|handler)|"
    r"I\s+need\s+(a\s+)?(new\s+)?(api|endpoint|route|table|field)|"
    r"build\s+(a\s+)?(new\s+)?(feature|service|module|integration))\b",
    re.IGNORECASE,
)

_TEST_WRITER_PATTERN = re.compile(
    r"\b(write\s+(unit\s+)?tests?\s+for|add\s+tests?\s+(for|to|covering)|"
    r"test\s+coverage\s+for|create\s+(unit|integration)\s+tests?|"
    r"spec\s+out\s+tests?|generate\s+tests?\s+for)\b",
    re.IGNORECASE,
)

_EXPLAIN_PATTERN = re.compile(
    r"\b(explain\s+(this|the|what|how)|what\s+does\s+\w+\s+do|"
    r"help\s+me\s+understand\s+(this|the|how)|"
    r"walk\s+me\s+through|how\s+does\s+\w+\s+work|"
    r"explain\s+(to\s+me\s+)?how)\b",
    re.IGNORECASE,
)

# ── Mode field regex ───────────────────────────────────────────────────────

_MODE_FIELD_RE = re.compile(r"\*\*(?:Operational\s+)?Mode\*\*:\s*(\w+)", re.IGNORECASE)


def _read_file(path: Path) -> str | None:
    """Read a text file, returning None on any error."""
    try:
        return path.read_text(encoding="utf-8").strip()
    except (OSError, FileNotFoundError, PermissionError):
        return None


def _read_json(path: Path) -> dict | None:
    """Read a JSON file, returning None on any error."""
    try:
        raw = path.read_text(encoding="utf-8")
        return json.loads(raw)
    except (OSError, FileNotFoundError, ValueError):
        return None


def _decision(target_agent: str, reason: str) -> RoutingDecision:
    return RoutingDecision(
        target_agent=target_agent,
        layer="deterministic",
        confidence=1.0,
        reason=reason[:100],
    )


def _route_from_registry_keywords(
    request_text: str,
    registry: list[AgentRegistryEntry],
) -> RoutingDecision | None:
    """Check registry entries' routing_keywords before hardcoded patterns.

    Each entry's routing_keywords are OR-joined into a single word-boundary
    regex. First match wins. Returns None if no registry entry matches.
    """
    for entry in registry:
        if not entry.routing_keywords:
            continue
        escaped = [re.escape(kw) for kw in entry.routing_keywords]
        pattern = re.compile(r"\b(" + "|".join(escaped) + r")\b", re.IGNORECASE)
        if pattern.search(request_text):
            return _decision(entry.name, f"Registry keyword matched for {entry.name}")
    return None


def route_deterministic(
    request_text: str,
    project_dir: Path,
    registry: list[AgentRegistryEntry],
) -> RoutingDecision | None:
    """Try to route deterministically. Returns None if no rule matches."""

    # 1. Slash commands
    for pattern, target in _SLASH_COMMANDS:
        if pattern.search(request_text):
            return _decision(target, f"Slash command matched: {pattern.pattern}")

    # 1b. Registry-driven keyword routing (frontmatter routing_keywords take precedence)
    registry_match = _route_from_registry_keywords(request_text, registry)
    if registry_match:
        return registry_match

    # 1c. Hardcoded fallback patterns (for agents without routing_keywords in frontmatter)
    if _GIT_PATTERN.search(request_text):
        return _decision("git-nerd", "Git operation keyword matched")
    if _SOLANA_PATTERN.search(request_text):
        return _decision("solana-specialist", "Solana/blockchain keyword matched")
    if _KILN_PATTERN.search(request_text):
        return _decision("kiln-engineer", "Kiln/Electron keyword matched")
    if _SECURITY_PATTERN.search(request_text):
        return _decision("security", "Security audit keyword matched")
    if _UI_PATTERN.search(request_text):
        return _decision("uiux-master", "UI/design keyword matched")
    if _KAREN_PATTERN.search(request_text):
        return _decision("karen", "Docs/changelog/organization keyword matched")
    if _DIAGNOSE_PATTERN.search(request_text):
        return _decision("diagnose-analyst", "Diagnosis keyword matched")
    if _REFACTOR_PATTERN.search(request_text):
        return _decision("refactorer", "Refactor keyword matched")
    if _ARCHITECT_PATTERN.search(request_text):
        return _decision("architect", "Architecture keyword matched")
    if _CAMPAIGN_PATTERN.search(request_text):
        return _decision("trowel", "Campaign keyword matched")
    if _RESEARCH_PATTERN.search(request_text):
        return _decision("research-analyst", "Research/hypothesis keyword matched")
    if _COMPETITIVE_PATTERN.search(request_text):
        return _decision("competitive-analyst", "Competitive/market keyword matched")
    if _REGULATORY_PATTERN.search(request_text):
        return _decision("regulatory-researcher", "Legal/regulatory keyword matched")
    if _QUANTITATIVE_PATTERN.search(request_text):
        return _decision("quantitative-analyst", "Simulation/parameter keyword matched")
    if _BENCHMARK_PATTERN.search(request_text):
        return _decision("benchmark-engineer", "Benchmark/perf keyword matched")
    if _BUG_CATCHER_PATTERN.search(request_text):
        return _decision("bug-catcher", "Hook/script health keyword matched")
    if _FIX_IMPLEMENTER_PATTERN.search(request_text):
        return _decision("fix-implementer", "Fix implementation keyword matched")
    if _CODE_REVIEWER_PATTERN.search(request_text):
        return _decision("code-reviewer", "Code review keyword matched")
    if _CASCADE_PATTERN.search(request_text):
        return _decision("cascade-analyst", "Failure cascade keyword matched")
    if _EVOLVE_PATTERN.search(request_text):
        return _decision("evolve-optimizer", "Optimization keyword matched")
    if _HEALTH_PATTERN.search(request_text):
        return _decision("health-monitor", "Health check keyword matched")
    if _COMPLIANCE_AUDITOR_PATTERN.search(request_text):
        return _decision("compliance-auditor", "Compliance audit keyword matched")
    if _AGENT_AUDITOR_PATTERN.search(request_text):
        return _decision("agent-auditor", "Fleet audit keyword matched")
    if _SKILL_FORGE_PATTERN.search(request_text):
        return _decision("skill-forge", "Skill distillation keyword matched")
    if _PROMPT_ENGINEER_PATTERN.search(request_text):
        return _decision("prompt-engineer", "Prompt engineering keyword matched")
    if _DEVOPS_PATTERN.search(request_text):
        return _decision("devops", "DevOps/CI/CD keyword matched")
    if _SPREADSHEET_PATTERN.search(request_text):
        return _decision("spreadsheet-wizard", "Excel/spreadsheet keyword matched")
    if _SELF_HOST_PATTERN.search(request_text):
        return _decision("self-host", "Self-host/deploy keyword matched")
    if _HYPOTHESIS_PATTERN.search(request_text):
        return _decision("hypothesis-generator", "Hypothesis generation keyword matched")
    if _SYNTHESIZER_PATTERN.search(request_text):
        return _decision("synthesizer-bl2", "Synthesis keyword matched")
    if _FRONTIER_PATTERN.search(request_text):
        return _decision("frontier-analyst", "Blue-sky/frontier keyword matched")
    if _EVAL_PATTERN.search(request_text):
        return _decision("evolve-optimizer", "Eval/improve-agent keyword matched")
    if _MODE_GUIDANCE_PATTERN.search(request_text):
        return _decision("mortar", "Mode guidance keyword matched")
    if _DEVELOPER_PATTERN.search(request_text):
        return _decision("developer", "Feature/endpoint/scaffold keyword matched")
    if _TEST_WRITER_PATTERN.search(request_text):
        return _decision("test-writer", "Test writing keyword matched")
    if _EXPLAIN_PATTERN.search(request_text):
        return _decision("general-purpose", "Explain/understand keyword matched")

    # 2. Autopilot state
    autopilot_mode = _read_file(project_dir / ".autopilot" / "mode")
    if autopilot_mode:
        if autopilot_mode == "build":
            return _decision("build-workflow", "Autopilot mode=build")
        if autopilot_mode == "fix":
            return _decision("fix-workflow", "Autopilot mode=fix")
        if autopilot_mode == "verify":
            return _decision("verify-workflow", "Autopilot mode=verify")

    # 3. Campaign state
    campaign_data = _read_json(project_dir / "masonry-state.json")
    if campaign_data:
        if campaign_data.get("mode") == "campaign" and campaign_data.get("active_agent"):
            active = campaign_data["active_agent"]
            return _decision(active, f"Campaign active_agent={active}")

    # 4. UI state
    ui_mode = _read_file(project_dir / ".ui" / "mode")
    if ui_mode:
        if ui_mode == "compose":
            return _decision("ui-compose-workflow", "UI mode=compose")
        if ui_mode == "review":
            return _decision("ui-review-workflow", "UI mode=review")

    # 5. Question **Mode**: field
    m = _MODE_FIELD_RE.search(request_text)
    if m:
        mode_value = m.group(1).strip().lower()
        agents = get_agents_for_mode(registry, mode_value)
        if agents:
            return _decision(agents[0].name, f"Mode field: {mode_value}")

    return None
