---
name: dark-fleet-analysis
description: Analyze an agent registry to identify dark fleet agents (registered but unreachable via routing) and quantify the coverage gap
---

# /dark-fleet-analysis — Dark Fleet Coverage Analysis

Analyzes an agent registry against the routing configuration to identify agents that exist but are never automatically routed to. Distilled from D4.2 (86% dark fleet) in the inline-execution-audit campaign.

## Steps

### 1. Locate the agent registry

Find `masonry/agent_registry.yml` (or equivalent):
- Parse all agent entries: name, tier, modes, capabilities, routing_keywords (if present)
- Count total registered agents
- Identify agents with `tier: "stub"` or empty capabilities

Find all `.md` files in agent directories:
- `~/.claude/agents/*.md`
- `.claude/agents/*.md` (project-local)
- Count resolvable agents (file exists + non-empty)

### 2. Build the reachability map

Identify ALL routing dispatch paths:
- Mortar routing table (in CLAUDE.md or mortar.md): work type → agent name
- INTENT_RULES routing targets (in prompt router): route field → agent names
- Explicit slash commands that name specific agents

For each registered agent, check:
- Is the agent named in ANY routing dispatch path? → **AUTO-ROUTABLE**
- Is the agent only invocable by explicit name reference? → **DARK FLEET**
- Does the agent have `routing_keywords` populated? → **SEMANTICALLY REACHABLE** (via semantic layer)
- Is the agent a stub with no real content? → **PLACEHOLDER**

### 3. Compute fleet statistics

```
Total registered agents: N
  Auto-routable (Mortar/INTENT_RULES named):  N (X%)
  Dark fleet (no automatic routing path):     N (X%)
    - Has routing_keywords (semantically reachable): N
    - No routing_keywords (fully dark):              N
    - Placeholder stubs:                             N
  Missing .md files (broken references):       N
```

### 4. Identify high-value dark agents

Among the dark fleet, classify by potential impact:
- **High value**: agents covering work types that commonly occur (python-specialist, typescript-specialist, database-specialist, devops, docker-specialist)
- **Medium value**: domain-specific agents used occasionally (solana-specialist, rust-specialist, fastapi-specialist)
- **Low value**: narrow specialists unlikely to be needed often (spreadsheet-wizard, blender, kiln-engineer)
- **Stub**: empty or placeholder agents with no real instructions

For high and medium value dark agents, check if their work type has ANY routing coverage (via Mortar or INTENT_RULES). If not — these are routing gaps where prompts for this work type default to inline execution.

### 5. Check routing_keywords population

For agents in the registry, check the `routing_keywords` field:
- If present and non-empty: agent is reachable via semantic routing (Ollama cosine similarity)
- If absent or empty: agent is fully dark (not even in the semantic layer)

Report the population rate: X% of agents have routing_keywords.

### 6. Report and recommend

```
DARK FLEET ANALYSIS — [project]

Fleet size: N agents total
  Auto-routable: N (X%) — reachable via Mortar dispatch or INTENT_RULES
  Dark fleet:    N (X%) — no automatic routing path
    Semantically reachable (has routing_keywords): N
    Fully dark (no routing_keywords):              N
    Placeholder stubs:                             N

routing_keywords population rate: X%

High-value dark agents (work types without coverage):
  - [agent]: covers [work type] — [N prompts/session estimated]
  - ...

Recommended activation sequence (staged to avoid routing noise):
  Stage 1 (highest impact): [agents] — populate routing_keywords + add to Mortar dispatch
  Stage 2 (medium impact): [agents] — routing_keywords only (semantic layer)
  Stage 3 (low/stub): [agents] — evaluate or retire

Estimated impact: routing N% of currently-inline prompts to specialists after Stage 1
```

### 7. Suggest routing_keywords extraction

For top dark-fleet agents, suggest routing_keywords from their .md content:
- Read the agent's frontmatter `description` field
- Read any "When to invoke" or "Trigger" section
- Extract 5-10 keyword phrases that would uniquely identify prompts for this agent
- Flag cases where auto-extraction would be ambiguous (agent covers too broad a domain)

## Notes

- Never modify agent files — read-only analysis
- Activating dark fleet agents without quality-gating their routing_keywords can flood Mortar's semantic layer with false matches — staging is important
- Stub agents (empty or placeholder content) should be evaluated for retirement before activation
- The "routing_keywords field exists but is unpopulated for 80+ agents" pattern means the infrastructure for semantic routing is built but not fed
