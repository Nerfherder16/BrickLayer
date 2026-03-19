---
name: tools-manifest
description: Canonical catalog of all MCP tools available to BrickLayer agents. Reference when writing new agents or checking tool coverage.
type: reference
---

# BrickLayer Tools Manifest

This file is the authoritative reference for tools available to all campaign agents.
When writing a new agent, declare the tools it uses in frontmatter: `tools: [recall, filesystem]`
forge-check validates this manifest exists and has at least 5 tool entries.

---

## recall
Memory system at `100.70.195.84:8200`. Cross-session fact storage and retrieval.
- `recall_search(query, domain, limit)` — semantic similarity search across stored memories
- `recall_store(content, domain, tags, importance)` — persist a fact for future sessions
- `recall_timeline(domain, limit)` — chronological retrieval of memories in a domain
- `recall_get(id)` — fetch full content of a specific memory by ID

## simulate
Python subprocess for quantitative boundary testing.
- `python simulate.py` — run current scenario parameters, returns verdict JSON
- Edit SCENARIO PARAMETERS section only; never touch `constants.py`
- Use `baseline.py` for snapshot anchoring

## filesystem
Standard Claude Code file tools. Always available to all agents.
- `Read`, `Write`, `Edit` — file I/O with line-level precision
- `Glob` — file pattern search (e.g. `findings/*.md`)
- `Grep` — content search with regex
- `Bash` — shell commands: git, python, curl, jq

## github
GitHub MCP server for repository operations.
- `mcp__github__create_pull_request` — open PR from current branch with title + body
- `mcp__github__create_issue` — file a bug or finding as a GitHub issue
- `mcp__github__push_files` — push file changes to a remote branch
- `mcp__github__get_pull_request` — read an existing PR's details
- `mcp__github__list_commits` — list recent commits on a branch

## masonry
Masonry MCP server (`masonry-mcp.js`). Campaign state queries and operations.
- `masonry_status` — current campaign state and wave progress
- `masonry_findings` — recent findings with verdicts, summaries
- `masonry_questions` — question bank query (filter by status/domain)
- `masonry_weights` — priority weight report from `.bl-weights.json`
- `masonry_fleet` — agent registry with performance scores from `agent_db.json`
- `masonry_git_hypothesis` — generate research questions from recent git diffs
- `masonry_nl_generate` — convert NL description to BL research questions
- `masonry_run_question` — run a single question by ID, return verdict envelope
- `masonry_recall` — proxy to Recall API for campaign-scoped memory
- `masonry_run_simulation` — run a simulation with custom params, return structured results
- `masonry_sweep` — parameter sweep across multiple values

### masonry_run_simulation
Run a single simulation for a project. Returns verdict, records, failure_reason.
- project_path (required): absolute path to project dir containing simulate.py
- Optional: months, initial_units, monthly_growth_rate, churn_rate, price_per_unit, ops_cost_base

Example:
```
masonry_run_simulation(project_path="/path/to/project", churn_rate=0.08)
→ {"verdict": "WARNING", "records": [...], "failure_reason": null}
```

### masonry_sweep
Sweep a parameter across multiple values. Returns list of {param_value, scenario, verdict, final_primary, records}.
- project_path (required): absolute path to project dir
- param_name (required): parameter to sweep e.g. "churn_rate"
- values (required): array of values e.g. [0.02, 0.05, 0.08, 0.12]
- scenarios (optional): array of scenario labels
- base_params (optional): {param: value} object applied as baseline

Example:
```
masonry_sweep(project_path="/path/to/project", param_name="churn_rate", values=[0.02,0.05,0.10])
→ {"results": [{param_value: 0.02, verdict: "HEALTHY", ...}, ...], "count": 3}
```

## exa
Exa MCP for web research and external documentation retrieval.
- `mcp__exa__web_search_exa` — semantic web search with natural language queries
- `mcp__exa__get_code_context_exa` — fetch code examples for a specific library or API
- `mcp__exa__crawling_exa` — fetch full page content from a URL

## context7
Library documentation retrieval via context7 MCP.
- `mcp__context7__resolve-library-id` — find the context7 ID for a package name
- `mcp__context7__query-docs` — fetch current API docs for a resolved library ID

---

## agent-fleet-management
Agent self-improvement tools. These are not MCP tools — they are agent files invoked by
mortar at specific trigger points during the campaign loop.

- `agent-auditor` — Scores agent fleet performance using findings and results.tsv. Writes AUDIT_REPORT.md.
  Trigger: every 10 questions (background) + wave end (foreground). Inputs: agents_dir, findings_dir, results_tsv.
  Output: `.claude/agents/AUDIT_REPORT.md` with fleet scorecard and underperformer analysis.

- `overseer` — Fleet manager. Reads agent_db.json + AUDIT_REPORT.md, rewrites underperforming agent .md files,
  creates new agents from FORGE_NEEDED.md. Trigger: when agent-auditor reports FLEET_UNDERPERFORMING.
  Inputs: agent_db_json, agents_dir, findings_dir, project_brief. Output: OVERSEER_REPORT.md, edited agent files.

- `skill-forge` — Distills campaign findings into reusable skills at ~/.claude/skills/. Writes skill_registry.json.
  Trigger: wave end (after synthesis). Inputs: synthesis_md, findings_dir, project_root, skill_registry_json,
  skills_dir (~/.claude/skills/), project_name. Output: new SKILL.md files + SKILL_FORGE_LOG.md.

- `forge-check` — Scans agent fleet for capability gaps. Writes FORGE_NEEDED.md if gaps found.
  Trigger: every 5 questions (background) + wave end. Inputs: agents_dir, findings_dir, questions_md.
  Output: `.claude/agents/FORGE_NEEDED.md` (consumed by overseer).

- `agent_db.json` — Per-agent performance database at project root. Written by mortar after every finding.
  Schema: `{ "agent_name": { runs, verdicts: {}, score, last_run, created, repair_count, last_repair, run_history: [] } }`.
  Python API: `from bl.agent_db import record_run, get_score, get_trend, get_underperformers`.

---

## Declaring Tool Usage in Agent Frontmatter

Add a `tools:` array to your agent's YAML frontmatter to declare which tool categories it uses:

```yaml
---
name: my-agent
description: Does X
model: sonnet
tools: [recall, filesystem, masonry]
---
```

This declaration is informational — it helps forge-check audit tool coverage and helps
overseer understand each agent's capabilities without reading the full instruction file.
