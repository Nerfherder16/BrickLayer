# BrickLayer Training Branch — Implementation Plan

_Source: MASTER_HANDOFF.md + bridge files in docs/_
_Last updated: 2026-03-25_

---

## Scope

Work executable **in this repo on Windows**. Linux-only steps (B1–B3, B7–B11) and the System-Recall
repo change (A4) are documented as out-of-scope below and tracked separately.

---

## Task List

### A1 — Simplify Mortar Dispatch
**Status:** `[ ] PENDING`
**File:** `template/.claude/agents/mortar.md`

Remove the conversational routing table and dev task routing table. Replace both with a
deterministic 5-condition binary:

```
1. Has **Mode**: field in question payload?          → Trowel
2. Is /masonry-run or /masonry-status command?       → Trowel
3. Is campaign state file present in project dir?    → Trowel
4. Does request touch questions.md or findings/?     → Trowel
5. Everything else                                   → Rough-in
```

Output contract: `{ target: "trowel" | "rough-in", reason: string }`

**Keep untouched:** ACTION REQUIRED handling, Trowel handoff format, Recall orientation.

---

### A2 — Create Rough-in Agent
**Status:** `[ ] PENDING`
**File:** `template/.claude/agents/rough-in.md` _(new)_
**Registry:** `masonry/agent_registry.yml` _(add entry)_

Dev workflow orchestrator. Mirrors Trowel's structure for dev tasks:
- Receives dev task from Mortar
- Reads `.autopilot/spec.md` if exists; otherwise delegates to spec-writer
- Decomposes spec into ordered task list
- Dispatches developer + test-writer (parallel where safe)
- Gates on code-reviewer approval before marking complete
- Max 3 retry cycles on failure, then escalates to user
- On success: delegates to git-nerd, reports done

Required behaviours from Trowel to mirror:
- Typed payload contracts (from `masonry/src/schemas/payloads.py`)
- State written to `masonry-state.json` with `rough_in_status` key
- Resumable on context compaction
- Confidence signaling on every agent output: high/medium/low/uncertain
- Failure mode tagging before Recall write: syntax | logic | tool_failure | timeout

Registry entry:
```yaml
name: rough-in
model: sonnet
tier: trusted
modes: [build, fix, plan, verify]
capabilities: [dev-orchestration, task-decomposition, agent-dispatch]
```

---

### A3 — Intra-Campaign Recall Feedback Loop
**Status:** `[ ] PENDING`
**Files:** `bl/recall_bridge.py`, `template/.claude/agents/trowel.md`

**Part 1 — recall_bridge.py additions:**

1. Add `_write_recall_degraded(degraded: bool)` helper — writes `recall_degraded` flag to
   `masonry-state.json` (path from `MASONRY_STATE` env var, default `.mas/masonry-state.json`).
   Uses stdlib only (no httpx). Never blocks on state write.

2. Add `get_campaign_context(project_name, current_qid, limit=5)` — queries Recall at
   `/memory/search` with tags `[f"project:{project_name}"]`, domain `autoresearch`,
   `min_importance: 0.3`, limit 5. Returns `[]` silently on any failure. Calls
   `_write_recall_degraded(True)` on exception, `_write_recall_degraded(False)` on success.

3. Add `_write_recall_degraded(True)` call to every existing `except Exception: return`
   block in the file. Add `_write_recall_degraded(False)` at the top of each successful
   function return.

**Part 2 — trowel.md injection point:**

In the question dispatch section, before each question is dispatched to a specialist:
```
1. Call get_campaign_context(project_name, current_qid, limit=5)
2. If results: summarize verdicts/patterns and inject into QuestionPayload.context
   as "Prior campaign findings: ..."
3. If empty: proceed without prior context (Wave 1 normal)
4. Never wait more than 3s (already enforced by RECALL_TIMEOUT)
```

Note: `bl/campaign_context.py` already handles *local* finding context (reads findings/ dir).
This is *remote* Recall context — cross-campaign, cross-project patterns. Different purpose.

---

### B4 — Install Bridge Files
**Status:** `[ ] PENDING`
**Source:** `docs/` (already present in this repo)
**Destinations:**
- `docs/training_schema.py` → `bl/training_schema.py`
- `docs/training_export.py` → `bl/training_export.py`
- `docs/masonry-training-export.js` → `masonry/src/hooks/masonry-training-export.js`

Verify after copy:
```bash
python -c "from bl.training_schema import verdict_to_binary_pass; print('schema ok')"
python -c "from bl.training_export import BLTrainingExporter; print('exporter ok')"
node --check masonry/src/hooks/masonry-training-export.js
```

Note: `training_export.py` imports from `training_schema` using a bare import
(`from training_schema import ...`). When invoked as a module from `bl/`, the import
must resolve correctly — verify this works or add a relative import fix.

---

### B5 — Patch score_all_agents.py
**Status:** `[ ] PENDING`
**File:** `masonry/scripts/score_all_agents.py`

Add after line 453 (final print in `_main()`, before `if __name__ == "__main__"`):

```python
    # Auto-export to training store after scoring
    import os as _os
    _training_db = _os.environ.get("BRICKLAYER_TRAINING_DB")
    if _training_db:
        from bl.training_export import BLTrainingExporter
        BLTrainingExporter(bl_root=str(args.base_dir), db_path=_training_db).export_all()
```

The `BL_ROOT` equivalent here is `args.base_dir` (verified from line 438 of score_all_agents.py).

---

### B6 — Register Stop Hook in settings.json
**Status:** `[ ] PENDING`
**File:** `C:/Users/trg16/.claude/settings.json`

In the `Stop` hooks array, add after `masonry-score-trigger.js` entry (currently last in Stop block):

```json
{
  "type": "command",
  "command": "node C:/Users/trg16/Dev/Bricklayer2.0/masonry/src/hooks/masonry-training-export.js",
  "timeout": 65,
  "async": true
}
```

`async: true` and 65s timeout — export is non-blocking and should complete in <60s.
The hook silently exits if `BRICKLAYER_TRAINING_DB` env var is not set.

---

## Out of Scope (Linux LXC / Other Repos)

These items require the Proxmox LXC machine with RTX 3060 or the System-Recall repo.

| Item | Location | Notes |
|------|----------|-------|
| B1 — Environment checks | Linux LXC | `python3 --version`, `nvidia-smi`, `ollama list`, disk space |
| B2 — Python venv + pytest | Linux LXC | `~/bricklayer`, needs `42 passed` |
| B3 — Configure .env files | Linux LXC | `BRICKLAYER_TRAINING_DB`, `AGENT_MODEL` etc. |
| B7 — Smoke tests | Linux LXC | agent, critic, export smoke tests |
| B8 — Dry run | Linux LXC | `bricklayer run-round --no-train` |
| B9 — Training deps | Linux LXC | torch CUDA, unsloth |
| B10 — Full training round | Linux LXC | 3–5 hours on RTX 3060 |
| B11 — Load adapter into Ollama | Linux LXC | merge, Modelfile, `ollama create` |
| A4 — Importance-weighted retrieval | System-Recall repo | Score fusion in POST `/memory/search` handler |

---

## Execution Order

```
1. B4 — Install bridge files (enables imports needed by B5)
2. A1 — Simplify Mortar
3. A2 — Create Rough-in + registry entry
4. A3 — recall_bridge.py additions + trowel.md update
5. B5 — Patch score_all_agents.py
6. B6 — Register Stop hook in settings.json
```

B4 goes first because B5 imports from `bl.training_export`.

---

## Verification Checklist

- [ ] A1: `template/.claude/agents/mortar.md` contains only 5-condition binary, no routing tables
- [ ] A2: `template/.claude/agents/rough-in.md` exists; entry in `masonry/agent_registry.yml`
- [ ] A3: `bl/recall_bridge.py` has `get_campaign_context()` and `_write_recall_degraded()`; `trowel.md` has context injection step
- [ ] B4: All 3 bridge files in place; imports print ok; `node --check` passes
- [ ] B5: `score_all_agents.py` patch present; no import errors on `--dry-run`
- [ ] B6: `masonry-training-export.js` in Stop hook array in settings.json

---

## Progress Log

| Date | Task | Status | Notes |
|------|------|--------|-------|
| 2026-03-25 | Plan created | ✓ | Initial plan from MASTER_HANDOFF.md |
