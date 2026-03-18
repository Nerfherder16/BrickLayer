---
name: masonry-pipeline
description: Chain agents/skills in a DAG with data passing. Run pipelines defined in .pipeline/*.yml. "pipeline run X", "chain these steps", "run research then build".
---

## masonry-pipeline — DAG Pipeline Execution

Chain agents and skills in a directed acyclic graph where each step's output becomes the next step's input.

### Pipeline Definition

Create `.pipeline/{name}.yml` in the project root:

```yaml
name: research-and-build
description: Research a topic, synthesize findings, then build the implementation

steps:
  - id: research
    agent: research-analyst
    input:
      topic: "{{pipeline.input.topic}}"
    output_key: research_findings

  - id: synthesize
    agent: synthesizer-bl2
    depends_on: [research]
    input:
      findings: "{{steps.research.output}}"
    output_key: synthesis

  - id: plan
    skill: plan
    depends_on: [synthesize]
    input:
      goal: "{{steps.synthesize.output}}"

  - id: build
    skill: build
    depends_on: [plan]
```

### Variable Syntax

- `{{pipeline.input.KEY}}` — initial inputs passed at invocation
- `{{steps.ID.output}}` — output captured from a completed step

Substitution happens at step invocation time, just before spawning the agent/skill.

### Step Fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | ✅ | Unique step identifier |
| `agent` OR `skill` | ✅ | What to run — agent name or skill name |
| `depends_on` | ❌ | List of step IDs that must complete first |
| `input` | ❌ | Key-value map of inputs (supports variable syntax) |
| `output_key` | ❌ | Name to store this step's output under (defaults to step id) |

### Execution Model

**1. Parse and validate** the pipeline YAML. Check all `depends_on` references exist.

**2. Topological sort** steps by `depends_on` to determine execution order. Steps with no dependencies form the first batch.

**3. For each batch of steps with all dependencies resolved**, spawn agents/skills in parallel (single message, multiple Agent calls).

**4. Capture output** from each step — the last markdown block in the agent's response, or any line prefixed with `OUTPUT:`. Store in `.pipeline/{name}-state.json` under `outputs.{step_id}`.

**5. Substitute variables** for the next batch using captured outputs.

**6. On completion**, print a summary:
```
Pipeline: research-and-build
  ✓ research     → 847 chars captured
  ✓ synthesize   → 312 chars captured
  ✓ plan         → spec.md written
  ✓ build        → 7 tasks complete
```

### State File

`.pipeline/{name}-state.json`:
```json
{
  "pipeline": "research-and-build",
  "status": "RUNNING|COMPLETE|FAILED",
  "steps": {
    "research": { "status": "DONE", "output": "..." },
    "synthesize": { "status": "PENDING", "output": null }
  },
  "started_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

### Sub-commands

```
/pipeline run {name}           — run a pipeline by name (looks in .pipeline/{name}.yml)
/pipeline run {path/to/file}   — run a specific YAML file
/pipeline status {name}        — show step statuses from state file
/pipeline list                 — list all .pipeline/*.yml files
```

### Error Handling

- If a step fails, mark it FAILED in the state file and stop the pipeline (don't run dependent steps)
- Report which step failed and what the error was
- The pipeline can be resumed from the failed step by running `/pipeline run {name}` again — completed steps are skipped

### Rules

- **Never skip dependency order** — always wait for `depends_on` steps before spawning dependents
- **Parallel where possible** — steps with no shared dependencies in the same batch run simultaneously
- **Preserve outputs** — write state file after each step; don't rely on memory
- **Pipelines are composable** — a pipeline step can invoke another skill (including `/pipeline`) for nested workflows
