# Wave 6 Synthesis — Masonry Self-Research

**Wave**: 6
**Questions**: F6.1, F6.2, D6.1, D6.2, R6.1, V6.1
**All questions**: DONE
**Date**: 2026-03-21

---

## Verdicts Summary

| ID | Question (short) | Verdict | Severity |
|---|---|---|---|
| F6.1 | `_load_registry` path diagnostic logging | FIX_APPLIED | Low |
| F6.2 | `optimize_all()` DiagnoseAgentSig mismatch | FIX_APPLIED | Medium |
| D6.1 | `upsert_registry_entry()` non-atomic write | FAILURE | Medium |
| D6.2 | `masonry_optimize_agent` MCP tool missing | FAILURE | High |
| R6.1 | `runBackground()` path-with-spaces on Windows | FAILURE | Low |
| V6.1 | `_tool_masonry_route` error fallback schema | FAILURE | Medium |

---

## Pattern Analysis

### Two fixes applied, four new failures found

Wave 6 continued the trajectory of Wave 5: each wave of fixes surfaces new structural issues. The two fixes (F6.1, F6.2) addressed pre-identified problems — the registry silence bug from D1.3 and the DSPy signature mismatch from R5.2. The four failures (D6.1, D6.2, R6.1, V6.1) are new discoveries.

### The "implemented vs. documented" gap (D6.2, V6.1)

Both D6.2 and V6.1 expose the same category of bug: code that doesn't match its own documentation or schema contract.

- **D6.2** (High): `masonry_optimize_agent` is described as a first-class MCP tool in `project-brief.md`, `ARCHITECTURE.md`, and CLAUDE.md. It does not exist in `server.py`. The Kiln OPTIMIZE button is completely non-functional.
- **V6.1** (Medium): The `_tool_masonry_route` error fallback returns `{"layer": 4, ...}` (integer) when the schema requires `Literal["deterministic", "semantic", "llm", "fallback"]` (string). `reason` is missing (required field). The success and error paths return structurally different dicts.

The pattern: features were documented/planned before implementation, and the gap was never closed. D6.2 is a missing implementation; V6.1 is an implementation that diverged from its own schema.

### Ongoing atomic write vulnerability (D6.1)

D6.1 is the same TOCTOU pattern as the Wave 5 strikes (F5.1) and the agents.json race (F5.3), applied to `agent_registry.yml` via `onboard_agent.py:upsert_registry_entry()`. The blast radius is larger: a mid-write kill truncates all 46 registered agents from the router's view, silently causing all requests to fall through to Layer 4. The fix is the same as F5.1/F5.3: write to `.tmp.{pid}`, then `Path.replace()`.

### Windows-only silent formatter failure (R6.1)

R6.1 is a low-severity but confirmed platform-specific bug: all three background formatters (ruff, prettier, eslint) break on Windows paths containing spaces because `shell: true` joins args without quoting. Failures are doubly silent (stdio: ignore + proc.unref). The synchronous lint check on line 182 correctly quotes paths — the inconsistency is in the background-only calls.

---

## Open Items by Priority

### P1 — Blocking Phase 16 DSPy Training and Kiln OPTIMIZE

| Item | Finding | Status |
|---|---|---|
| Implement `masonry_optimize_agent` MCP tool | D6.2 | UNFIXED |

### P2 — Data Loss Risk

| Item | Finding | Status |
|---|---|---|
| Atomic write for `upsert_registry_entry()` in `onboard_agent.py` | D6.1 | UNFIXED |
| Fix `_tool_masonry_route` error fallback schema (`layer: "fallback"`, add `reason`) | V6.1 | UNFIXED |

### P3 — Developer Experience

| Item | Finding | Status |
|---|---|---|
| Quote paths in `runBackground()` or replace `shell: true` with cmd.exe wrapper | R6.1 | UNFIXED |

---

## Cumulative Campaign State (Waves 1–6)

### Confirmed system-wide patterns

1. **Non-atomic write races** — three instances found (masonry-guard strikes, masonry-subagent-tracker agents.json, onboard_agent.py registry). Two fixed (F5.1, F5.3). One unfixed (D6.1).
2. **Documentation/implementation gaps** — two instances: `masonry_optimize_agent` never implemented (D6.2), `_tool_masonry_route` error shape diverges from schema (V6.1).
3. **Windows platform isolation** — R6.1 (shell:true path quoting) joins F4.2 (cmd.exe wrapper for .cmd files) as confirmed Windows-only bugs.
4. **Silent failure amplification** — `stdio: "ignore"` + `proc.unref()` (R6.1), `yaml.YAMLError → return []` (D6.1), `ConfigDict(extra="forbid")` silent `ValidationError` on wrong layer type (V6.1) — failures do not surface.

### Routing pipeline health

- Layer 1 (Deterministic): HEALTHY (V1.1 ✓, V1.2 ✓)
- Layer 2 (Semantic): WARNING — 0.70 threshold potentially too low (R2.1); cosine similarity can misroute (R3.1)
- Layer 3 (LLM): HEALTHY post-F5.2 (route_llm() validates before constructing RoutingDecision)
- Layer 4 (Fallback): WARNING — indistinguishable from infrastructure failure (R1.6 open); error fallback schema broken (V6.1 UNFIXED)
- Registry: WARNING — non-atomic write (D6.1 UNFIXED) + path resolution silent failure (fixed by F6.1)

### DSPy pipeline health

- `build_dataset()`: HEALTHY — ResearchAgentSig fields correctly populated
- `optimize_all()`: HEALTHY post-F6.2 — DiagnoseAgentSig mismatch removed
- MCP trigger (`masonry_optimize_agent`): BLOCKED — tool not implemented (D6.2)
- Drift detection: not yet investigated

---

## Wave 7 Focus Areas

Highest-value research directions given Wave 6 findings:

1. **F7.x — Fix `_tool_masonry_route` error fallback** (V6.1) — small, precise fix; unblocks schema compliance
2. **F7.x — Fix `upsert_registry_entry()` atomic write** (D6.1) — same pattern as F5.1/F5.3
3. **D7.x — Investigate `masonry_optimize_agent` implementation feasibility** — D6.2 gave the fix spec; validate imports and DSPy dependency availability
4. **R7.x — Validate `_tool_masonry_route` on successful routing paths** — V6.1 found error path issues; does the success path also have edge cases?
5. **D7.x — Investigate drift detector: does it detect agent prompt drift after F6.2 optimizer change?**
