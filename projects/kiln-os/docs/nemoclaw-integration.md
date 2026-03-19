# NemoClaw Integration Notes

Last updated: 2026-03-19
Status: PLANNING — no access yet, design based on GTC 2026 announcements

---

## What NemoClaw Is

NemoClaw is NVIDIA's enterprise agentic AI runtime stack, announced at GTC 2026. It consists of:

- **OpenShell** — per-agent YAML sandbox profiles (filesystem + network surface definition)
- **nvidia-nat** — A2A (Agent-to-Agent) protocol dispatch layer
- **Privacy Router** — policy-enforced local-vs-cloud inference routing
- **NIM** — NVIDIA Inference Microservices (swappable model containers)
- **NeMo Framework** — fine-tuning pipeline for domain model training
- **Triton Inference Server** — backing inference runtime for NIM
- **Parakeet** — NVIDIA speech recognition model (ASR)
- **ACE** — Avatar Cloud Engine (voice + embodied agent runtime)

The integration thesis: BL2.0 agents are exactly the agentic workloads NemoClaw was designed to orchestrate. The two stacks are complementary, not competitive.

---

## OpenShell Profile Mapping

Each BL2.0 agent type gets an OpenShell profile. Profiles are YAML files that define the sandbox boundary for that agent class.

### Profile Table

| Agent Type | Filesystem Access | Network Access | Profile Name |
|------------|-------------------|----------------|--------------|
| `quantitative-analyst` | `{project}/simulate.py` (read+write scenario params only), `{project}/results.tsv` (write), `{project}/findings/` (write) | None (pure compute) | `bl-quantitative` |
| `regulatory-researcher` | `{project}/findings/` (write), `{project}/docs/` (read) | Web search API only (no direct internet) | `bl-regulatory` |
| `competitive-analyst` | `{project}/findings/` (write), `{project}/docs/` (read) | Web search API only | `bl-competitive` |
| `benchmark-engineer` | `{project}/` (read), `{project}/results.tsv` (write) | Target service endpoint only (allowlist) | `bl-benchmark` |
| `hypothesis-generator` | `{project}/questions.md` (write), `{project}/findings/` (read) | None | `bl-hypothesis` |
| `synthesizer` | `{project}/findings/` (read), `{project}/findings/synthesis.md` (write) | None | `bl-synthesizer` |
| `masonry-build` | `{project}/src/` (read+write), `{project}/tests/` (read+write) | npm registry, pip index | `masonry-worker` |
| `kiln-monitor` | `{project}/*.json` (read), `.autopilot/` (read) | None | `kiln-readonly` |
| `codevv-session` | `{project}/` (read+write), shared workspace | Recall API (:8200), LiveKit | `codevv-session` |

### Profile YAML Template

```yaml
# bl-quantitative.yaml
name: bl-quantitative
version: "1.0"
description: "BrickLayer 2.0 quantitative analyst — simulation only"

filesystem:
  allow:
    - path: "${PROJECT_DIR}/simulate.py"
      mode: read-write
      constraint: "scenario_parameters_section_only"  # custom constraint
    - path: "${PROJECT_DIR}/constants.py"
      mode: read-only
    - path: "${PROJECT_DIR}/results.tsv"
      mode: append-only
    - path: "${PROJECT_DIR}/findings/"
      mode: write
    - path: "${TEMP_DIR}"
      mode: read-write
  deny:
    - path: "~/.ssh/"
    - path: "~/.claude/"
    - path: "/etc/"
    - path: "${PROJECT_DIR}/docs/"  # docs are Tier 1, read-only for humans

network:
  allow: []  # pure compute, no external calls
  deny: ["*"]

env:
  inherit: ["PROJECT_DIR", "QUESTION_ID"]
  block: ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "HOME"]

resources:
  max_tokens_per_run: 50000
  timeout_seconds: 300
```

### The `constraint: scenario_parameters_section_only` Enforcement

This is the key constraint for quantitative-analyst. The agent can write to `simulate.py` but only within the `# SCENARIO PARAMETERS` block. OpenShell would need to enforce this at the diff level — or we enforce it in `bl/campaign.py` by validating the diff before committing.

If OpenShell doesn't support section-level constraints natively: validate in `bl/campaign.py`:
```python
def validate_simulate_diff(diff: str) -> bool:
    """Reject any diff that touches lines outside SCENARIO PARAMETERS block."""
    ...
```

---

## nvidia-nat: Replacing subprocess.Popen

### Current Implementation (to be replaced)

```python
# bl/campaign.py — current approach (subprocess)
import subprocess

def launch_agent(agent_type: str, question_id: str, project_dir: str) -> int:
    prompt = build_agent_prompt(agent_type, question_id, project_dir)
    result = subprocess.run(
        ["claude", "--dangerously-skip-permissions", prompt],
        env={**os.environ, "DISABLE_OMC": "1"},
        cwd=project_dir,
    )
    return result.returncode
```

Problems: requires DISABLE_OMC=1, no agent registry, no parallel isolation, no telemetry.

### Target Implementation (nvidia-nat A2A)

```python
# bl/campaign.py — nvidia-nat A2A approach
import httpx

NAT_ENDPOINT = "http://localhost:8350"  # mcp_gateway.py → nvidia-nat

async def dispatch_agent(agent_type: str, question_id: str, project_dir: str) -> str:
    """Dispatch agent via nvidia-nat A2A. Returns task_id."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NAT_ENDPOINT}/a2a/dispatch",
            json={
                "agent": agent_type,           # matches registered agent name
                "profile": f"bl-{agent_type}", # OpenShell profile
                "input": {
                    "question_id": question_id,
                    "project_dir": project_dir,
                },
                "callback": f"{NAT_ENDPOINT}/a2a/callback/{question_id}",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()["task_id"]

async def await_agent(task_id: str, timeout: int = 300) -> dict:
    """Poll for agent completion."""
    async with httpx.AsyncClient() as client:
        deadline = time.time() + timeout
        while time.time() < deadline:
            r = await client.get(f"{NAT_ENDPOINT}/a2a/status/{task_id}")
            status = r.json()
            if status["state"] in ("COMPLETE", "FAILED"):
                return status
            await asyncio.sleep(5)
    raise TimeoutError(f"Agent {task_id} did not complete in {timeout}s")
```

### Agent Manifests (nvidia-nat registration)

Each agent type must be registered with nvidia-nat:

```yaml
# agents/bl-quantitative.manifest.yaml
name: bl-quantitative
display_name: "BL2.0 Quantitative Analyst"
profile: bl-quantitative
runtime: claude-code
entrypoint:
  type: prompt
  template: "bl/prompts/quantitative-analyst.md"
model_preferences:
  primary: "kiln-research-v1"   # fine-tuned (Phase 6)
  fallback: "qwen3:14b"         # Ollama local
  cloud_fallback: "claude-sonnet-4-6"  # if local unavailable
telemetry:
  otel_endpoint: "http://localhost:4317"
  service_name: "bl2-quantitative-analyst"
```

---

## mcp_gateway.py Design

Port 8350. This is the unified MCP tool surface — the Kiln OS system call interface.

### Purpose

Every BL2.0 agent that needs external tool access (web search, Recall, simulation runner) goes through mcp_gateway.py instead of calling tools directly. This gives:
- Centralized audit log (every tool call logged)
- Rate limiting per agent profile
- Privacy Router enforcement before cloud calls
- Single registration point for nvidia-nat

### API Shape

```
POST /mcp/tool/call
  body: { agent_id, profile, tool_name, tool_args }
  → validates profile permissions
  → routes through Privacy Router if needed
  → calls actual MCP tool
  → logs to audit trail
  → returns tool result

GET /mcp/tool/list
  → returns available tools for the calling agent's profile

GET /health
  → health check for all downstream services (Recall, Ollama, nvidia-nat)

GET /metrics
  → Prometheus metrics (token usage, tool call counts, error rates)
```

### Privacy Router Integration

```python
# mcp_gateway.py — routing decision
async def route_inference_call(agent_id: str, prompt: str, policy: PrivacyPolicy) -> str:
    tags = await classify_prompt_tags(prompt)  # extract sensitivity tags

    for rule in policy.rules:
        if rule.matches(tags):
            if rule.action == "local-only":
                return await ollama_call(prompt, model=policy.local_model)
            elif rule.action == "cloud-allowed":
                return await claude_api_call(prompt)

    # default: local
    return await ollama_call(prompt, model=policy.local_model)
```

---

## Telemetry: agent_db.py → OpenTelemetry

Current: agent_db.json is a flat JSON file with per-agent scores. No structured telemetry.

Target: agent_db.py wraps agent_db.json writes and emits OpenTelemetry spans:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

tracer = trace.get_tracer("bl2-agent-db")

def record_agent_run(agent_type: str, question_id: str, result: AgentResult):
    with tracer.start_as_current_span("agent_run") as span:
        span.set_attribute("agent.type", agent_type)
        span.set_attribute("agent.question_id", question_id)
        span.set_attribute("agent.verdict", result.verdict)
        span.set_attribute("agent.tokens_in", result.tokens_in)
        span.set_attribute("agent.tokens_out", result.tokens_out)
        span.set_attribute("agent.score", result.score)
        # write to agent_db.json as before
        _write_to_json(agent_type, question_id, result)
```

Telemetry backend: **Langfuse** (self-hosted on CasaOS) or **Phoenix** (Arize). Both support OTEL ingestion and are free self-hosted. Langfuse has better LLM-specific features (prompt versioning, session tracing). Phoenix has better Phoenix for tracing agent chains.

---

## Privacy Router Policy File Template

```yaml
# recall-privacy-policy.yml
# Human-controlled. No silent cloud egress.
version: "1.0"
default_action: local-only

local_model: "qwen3:14b"          # Ollama on 192.168.50.62
cloud_model: "claude-sonnet-4-6"  # Anthropic API (opt-in only)

rules:
  # Medical or family data: always local
  - match:
      tags: ["medical", "health", "family", "personal"]
    action: local-only
    reason: "Personal/family data never leaves homelab"

  # BL2.0 ADBP research: local only (sensitive business model data)
  - match:
      project: ["adbp", "kiln-os"]
    action: local-only
    reason: "Business model research is confidential"

  # INCONCLUSIVE findings: allow cloud for higher-quality second opinion
  - match:
      verdict: ["INCONCLUSIVE"]
      tags: ["!medical", "!family"]  # negation: not medical, not family
    action: cloud-allowed
    reason: "Second-opinion inference on ambiguous findings"

  # Code analysis: cloud allowed (no PII)
  - match:
      tags: ["code", "typescript", "python", "react"]
    action: cloud-allowed
    reason: "Code analysis is not sensitive"

audit:
  enabled: true
  log_path: "/var/log/kiln-os/privacy-router.log"
  include_routing_decision: true
  include_matched_rule: true
  # do NOT log prompt content — log decision only
```

---

## NIM Integration Points

Once NIM microservices are available:

1. **Registration in nvidia-nat:** NIM endpoint appears as a named model backend
2. **Model selection in BL2.0:** `questions.md` gets a `model` field per question
3. **Routing:** mcp_gateway.py → nvidia-nat → NIM endpoint (or Ollama fallback)
4. **Version pinning:** `kiln-research-v1` is a pinned NIM version — campaigns can specify which version they use for reproducibility

NIM container format means the fine-tuned checkpoint from Phase 6 is deployable with `docker run` — no custom serving infrastructure. The RTX 3090 on the Ollama VM is the target hardware.

---

## Access Path

Current status: NemoClaw/OpenShell/nvidia-nat was announced at GTC 2026. No public release date confirmed. Steps to get early access:

1. Apply to NVIDIA Developer Program (existing account needed)
2. Request early access to NemoClaw via the enterprise AI developer portal
3. Engage with NVIDIA DEx (Developer Experience) team — Tim's homelab AI stack is a strong pilot candidate
4. Alternatively: monitor for open-source components (nvidia-nat A2A spec may be open; OpenShell YAML schema may be published independently)

In the interim: Phase 1 can be partially prototyped by writing OpenShell-compatible YAML profiles even before the enforcement runtime is available. The profiles document the intended security model.
