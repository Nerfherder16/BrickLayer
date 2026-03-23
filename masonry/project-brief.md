# Project Brief — Masonry Self-Research Campaign

**Authority tier: Tier 1 — Ground Truth. Human eyes only. Do not modify during campaigns.**

---

## What Masonry Is

Masonry is a Claude Code orchestration platform built on BrickLayer 2.0. It is the bridge layer in the three-tier model:

```
Claude Code  (user-facing AI)
     ↕
  Masonry    (bridge: MCP server, hooks, routing engine, DSPy optimization, agent registry)
     ↕
BrickLayer   (research loop, campaigns, simulations, agent fleet, findings)
```

Masonry is not a subprocess of Claude Code — it is a parallel layer that carries messages between Claude Code and the BrickLayer research machinery. It is implemented as:

- A Node.js MCP server (`mcp_server/`) exposing tools like `masonry_route`, `masonry_onboard`, `masonry_optimize_agent`, `masonry_drift_check`
- A set of Claude Code hook scripts (`src/hooks/`) that intercept session events (SessionStart, PreToolUse, PostToolUse, Stop)
- A Python routing engine (`src/routing/`) implementing four routing layers in priority order
- A DSPy optimization pipeline (`src/dspy_pipeline/`) for improving agent prompts via MIPROv2
- A declarative agent registry (`agent_registry.yml`) listing all known agents with their modes, capabilities, and tier status

---

## Research Domains for This Campaign

This campaign investigates two distinct domains in Masonry's own implementation.

### Domain A — Routing Quality

The four-layer router is Masonry's central dispatch mechanism. It claims to handle 60%+ of routing deterministically with zero LLM calls. We want to know:

- Does the deterministic layer actually cover the claimed 60%+ of real requests?
- What is the misrouting rate for each layer transition?
- When does semantic routing (Layer 2) fire vs. fall through to LLM (Layer 3)?
- Is the cosine similarity threshold of 0.70 well-calibrated, or does it cause premature fallthrough or premature matches?
- Does the LLM router (Layer 3, claude-haiku-4-5) produce consistent routing decisions for the same input?
- What classes of requests reliably reach Layer 4 (fallback), and is that correct behavior or a gap?
- Does the registry population (number and quality of agent descriptions) materially affect routing accuracy?
- Are there request types that deterministic routing mishandles — e.g., slash commands with trailing text, Mode fields in unusual positions?

Key code locations:
- `src/routing/router.py` — orchestrating pipeline
- `src/routing/deterministic.py` — Layer 1 (slash commands, state files, Mode field)
- `src/routing/semantic.py` — Layer 2 (Ollama embeddings, threshold 0.70, model qwen3-embedding:0.6b)
- `src/routing/llm_router.py` — Layer 3 (claude-haiku-4-5, 8-second timeout)

### Domain B — Hook Interaction Safety

Masonry runs up to 14+ hooks across multiple Claude Code lifecycle events. Some are synchronous (blocking), some are async (fire-and-forget). We want to know:

- Do the three PostToolUse hooks (masonry-observe, masonry-guard, masonry-agent-onboard) ever race or conflict?
- Can masonry-approver (PreToolUse) and masonry-guard (PostToolUse) produce contradictory outcomes on the same tool call?
- Do the two Stop hooks (masonry-stop-guard, masonry-build-guard) ever both fire and conflict?
- What happens when a hook's timeout fires before completion — is state left dirty?
- Are there ordering dependencies between hooks that are not enforced by the current hooks.json configuration?
- Does the async flag on PostToolUse hooks mean they can outlive the tool call and write to state that a subsequent synchronous hook has already read?
- Is there a scenario where masonry-observe writes a finding to Recall while masonry-guard has simultaneously flagged the same tool call as an error?
- What is the failure mode when Ollama (192.168.50.62:11434) is unreachable during semantic routing?

Key code locations:
- `src/hooks/masonry-approver.js` — PreToolUse, blocks/approves Write/Edit/Bash
- `src/hooks/masonry-guard.js` — PostToolUse async, 3-strike error pattern detection
- `src/hooks/masonry-observe.js` — PostToolUse async, finding detection and Recall storage
- `src/hooks/masonry-agent-onboard.js` — PostToolUse async, new agent auto-registration
- `src/hooks/masonry-stop-guard.js` — Stop, blocks if uncommitted git changes
- `src/hooks/masonry-build-guard.js` — Stop, blocks if .autopilot/ has pending tasks
- `hooks.json` — hook configuration (active hooks in this project)

---

## Key Invariants

1. **No source modifications during campaign.** Agents may read `src/`, `hooks/`, `agent_registry.yml` freely but must never write to them. All output goes to `findings/`.
2. **findings/ is write-only for agents.** Each finding is one markdown file per question.
3. **This project-brief.md is the authority.** If a finding contradicts this brief, note the contradiction in the finding and do not update this file.
4. **The campaign uses research/analysis modes only.** There is no `simulate.py` or `constants.py` for this project — questions are answered by reading code, running static analysis, and constructing argument-based findings.
5. **Ollama availability is not guaranteed.** The semantic layer depends on `http://192.168.50.62:11434`. Any finding that requires testing the semantic layer must document whether Ollama was available at time of research and mark the finding INCONCLUSIVE if it was not.

---

## Known Uncertainties (Investigate These)

| Uncertainty | Location | Why It Matters |
|-------------|----------|----------------|
| Semantic threshold 0.70 calibration | `semantic.py:_DEFAULT_THRESHOLD` | Too high = premature fallthrough. Too low = false positives routing to wrong agent. |
| Ollama model `qwen3-embedding:0.6b` — is it registered? | `semantic.py:_DEFAULT_MODEL` | If model is not pulled on the Ollama host, all semantic calls fail silently. |
| LLM router 8-second timeout | `llm_router.py:_LLM_TIMEOUT` | Claude haiku may exceed 8s under load, always falling through to Layer 4. |
| Async hook ordering in PostToolUse | `hooks.json` | Three async PostToolUse hooks with no guaranteed execution order. |
| `hooks.json` at project root vs. `src/hooks/` | Multiple locations | The project-level `hooks.json` only activates 4 hooks (masonry-register, masonry-observe, masonry-guard, masonry-agent-onboard, masonry-stop). The full fleet (14+ hooks) lives in the global `~/.claude/settings.json`. |
| `_load_registry` path resolution | `router.py:_load_registry` | Tries `{project_dir}/masonry/agent_registry.yml` first, then relative CWD fallback. If CWD is not the repo root, routing silently uses an empty registry. |
| `extra="forbid"` on `RoutingDecision` | `payloads.py` | LLM router may produce JSON with extra keys that cause a Pydantic validation failure, silently returning None and falling through to fallback. |

---

## Source Authority Hierarchy

| Tier | Files | Who Edits |
|------|-------|-----------|
| 1 | `project-brief.md`, `docs/` | Human only |
| 2 | All `src/` code, `hooks.json`, `agent_registry.yml` | Human only (read-only for agents) |
| 3 | `findings/`, `questions.md` | Agent output |

---

## Past Misunderstandings to Avoid

- **Masonry is not a subprocess.** It runs alongside Claude Code, not under it. Treat the MCP server and hooks as peer processes.
- **The hooks in `hooks.json` at the masonry project root are the project-scoped hooks.** The full fleet described in CLAUDE.md (14+ hooks) is configured in the user's global `~/.claude/settings.json`, not here.
- **`src/hooks/` and `hooks/` (top-level) are different directories.** The top-level `hooks/` contains only `bricklayer-retro.js` and a local `hooks.json`. All active hook scripts live in `src/hooks/`.
- **The routing engine is pure Python** — it does not call back into Claude Code. It runs as a standalone callable from the MCP server.
