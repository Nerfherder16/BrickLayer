---
name: forge
description: >-
  This skill should be used when the user asks to "create a new agent",
  "forge an agent", "add an agent", "build a new specialist", or invokes
  "/forge". Guides the creation, testing, and onboarding of a new BrickLayer
  agent through a 5-phase workflow.
version: 1.0.0
---

# /forge — Agent Creation Workflow

Create, test, and onboard a new BrickLayer agent in 5 phases.

## Phase 1 — Interview

Gather requirements from the user. Ask these questions (use AskUserQuestion tool):

1. **Agent name** — lowercase, hyphenated (e.g., `cost-optimizer`)
2. **One-line description** — what does it do? (must be >= 20 chars for semantic routing)
3. **Modes** — which operational modes? Options: `research`, `diagnose`, `validate`, `build`, `optimize`, `monitor`
4. **Capabilities** — 3-5 specific things it can do (used for routing corpus)
5. **Model tier** — `opus` (deep analysis), `sonnet` (standard work), `haiku` (quick lookups)
6. **Example prompts** — 3-5 prompts that should route to this agent

## Phase 2 — Draft

Generate the agent `.md` file with this structure:

```markdown
---
name: {agent-name}
description: >-
  {description from Phase 1}
model: {model}
tier: draft
modes: [{modes}]
capabilities:
  - {capability 1}
  - {capability 2}
  - {capability 3}
input_schema: QuestionPayload
output_schema: FindingPayload
routing_keywords:
  - {keyword derived from description}
tools:
  - Read
  - Glob
  - Grep
  - {additional tools based on capabilities}
---

{Agent instructions body - structured with:}
# {Agent Name}

## Role
{What the agent does and when to activate it}

## Process
{Step-by-step flowchart of how the agent operates}

## Output Contract
{What the agent must return — verdict, evidence, confidence format}

## Self-Review Checklist
- [ ] Evidence cited with specific data points
- [ ] Verdict matches the evidence
- [ ] Confidence calibrated (not always 0.8)
- [ ] No assumptions stated as facts
```

### Validation

Run frontmatter validation before saving:

```python
from masonry.scripts.validate_frontmatter import validate_frontmatter

warnings = validate_frontmatter(frontmatter_dict)
if warnings:
    # Show warnings to user, ask if they want to fix
```

Required checks:
- `name` is non-empty
- `description` >= 20 chars
- `model` is opus/sonnet/haiku
- `tier` is production/candidate/draft
- `modes` is a list
- `capabilities` is a list

## Phase 3 — Test Routing

Test whether the example prompts from Phase 1 would route correctly:

```
Use the masonry_route MCP tool for each example prompt.
Report which ones route to the new agent and which don't.
```

Calculate accuracy: `correct_routes / total_prompts`

If accuracy < 60%, suggest description improvements:
- Add more specific routing_keywords
- Make description more distinctive
- Add capability terms that match the example prompts

## Phase 4 — Onboard

1. Save the `.md` file to `.claude/agents/{agent-name}.md`
2. The `masonry-agent-onboard.js` hook fires automatically on Write
3. This runs `onboard_agent.py` which:
   - Extracts frontmatter metadata
   - Upserts into `masonry/agent_registry.yml`
   - Generates a DSPy signature stub

Verify onboarding:
```bash
grep '{agent-name}' masonry/agent_registry.yml
```

## Phase 5 — Optimize (Optional)

If the user wants to tune routing accuracy:

```bash
python masonry/scripts/optimize_routing.py {agent-name} --live
```

This generates 20 test queries, routes them through Ollama semantic matching,
and scores accuracy. If below 80%, it suggests description improvements.

## Completion Checklist

Before marking forge complete, verify:
- [ ] `.claude/agents/{name}.md` exists with valid YAML frontmatter
- [ ] Agent appears in `masonry/agent_registry.yml`
- [ ] At least 1 example prompt routes correctly via `masonry_route`
- [ ] Frontmatter validation passes with 0 warnings

## Example

```
User: /forge
Assistant: Let's create a new agent. What should it be called?
User: cost-optimizer
Assistant: What does it do? (one-line description)
User: Analyzes cloud infrastructure costs and identifies savings opportunities
Assistant: [continues through phases...]
```
