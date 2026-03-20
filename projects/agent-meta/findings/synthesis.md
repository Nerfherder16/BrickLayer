# Synthesis: BrickLayer 2.0 Agent Fleet — Best Way Forward

**Campaign**: agent-meta | **Questions answered**: 28 | **Completed**: 2026-03-17

---

## Executive Summary

BrickLayer 2.0's agent fleet has a complete inter-agent interface breakdown at its most critical junction: **question-designer-bl2 produces questions that Mortar cannot route**. Every BL 2.0 campaign using question-designer-bl2 silently misroutes 100% of questions to quantitative-analyst. This is a system-level failure, not a configuration issue — it requires a deliberate fix before any BL 2.0 campaign can be trusted.

Beyond the routing failure, the fleet contains a genuine infinite-loop risk (OVERRIDE re-queuing without retry limits), a broken fleet-health scoring system (agent-auditor's verdict whitelist excludes 14 valid verdicts), and a memory isolation failure (hypothesis-generator uses the wrong Recall domain). These are high-severity structural gaps, not tuning issues.

The fleet also has two agents that are effectively dead: **planner** (output unconsumed, not documented) and **overseer** (wired to a phantom interface, never invoked by Mortar).

---

## Critical Path (must resolve before any BL 2.0 campaign is trusted)

### 1. Fix the question-designer-bl2 → Mortar interface contract
**Resolves**: Q1.1, Q1.1-FU1, Q1.1-WM3, Q1.1-WM4, Q7.3
**Effort**: Medium (modify either question-designer-bl2 or mortar.md)

Two options:
- **Option A** (preferred): Update question-designer-bl2.md to use `**Mode**:` (lowercase, no "Operational") and lowercase mode values matching Mortar's routing table. Update `**Method**:` → `**Agent**:`.
- **Option B**: Update mortar.md to recognize `**Operational Mode**:` and CamelCase mode values.

Also create a master question schema document that both agents reference. This prevents the root cause (Q1.1-WM4) from recurring.

### 2. Add OVERRIDE retry limit and handled-marker
**Resolves**: Q2.2, Q6.2, Q4.2
**Effort**: Low (mortar.md + peer-reviewer.md text changes)

The NEVER STOP instruction combined with no retry limit is the only identified scenario that produces a true infinite loop. Fix:
- Add `**Override count**:` field to question blocks, increment on re-queue
- Add `MAX_OVERRIDES = 3` to constants.py
- After re-queuing, append `<!-- OVERRIDE-HANDLED: {date} -->` to finding file to prevent double re-queue
- At `override_count >= MAX_OVERRIDES`: mark PENDING_HUMAN, output escalation message

### 3. Fix agent-auditor's definitive verdict whitelist
**Resolves**: Q2.3
**Effort**: Low (agent-auditor.md one-line formula change)

Change from whitelist to exclusion model:
```
non_definitive = ["INCONCLUSIVE", "RE_QUEUED"]
definitive_rate = (total - non_definitive_count) / total
```
Prevents code-reviewer, peer-reviewer, forge-check from always scoring UNDERPERFORMING.

### 4. Fix hypothesis-generator's Recall domain
**Resolves**: Q7.1
**Effort**: Trivial (6 string replacements in hypothesis-generator.md)

Replace `{project}-autoresearch` with `{project}-bricklayer` in all 6 Recall calls. Also fix synthesizer.md (same bug — uses `-autoresearch` domain).

---

## Phase 2 Gate Requirements (fix before running production campaigns)

### 5. Create frontier-analyst.md
**Resolves**: Q1.1-FU3, Q1.1-FU4

research-analyst is epistemologically incompatible with Frontier questions (falsification vs exploration). A dedicated frontier-analyst.md is needed with:
- Exploration epistemology (not falsification)
- Output: possibility map with feasibility estimates
- Verdicts: FRONTIER_VIABLE / FRONTIER_BLOCKED / FRONTIER_PARTIAL
- Add `frontier → frontier-analyst` to Mortar's routing table

### 6. Add the 9 missing BL 2.0 routing entries to Mortar
**Resolves**: Q1.1, Q1.1-FU1

Mortar's routing table covers 7 modes but BL 2.0 defines 9 modes. Add:
- `validate` → design-reviewer
- `evolve` → evolve-optimizer
- `monitor` → health-monitor
- `predict` → cascade-analyst
- `frontier` → frontier-analyst (from #5)

### 7. Add finding validation step to Mortar
**Resolves**: Q6.1

After specialist returns, before marking DONE:
1. Verify finding file exists and is non-empty
2. Verify `**Verdict**:` field is present
3. Verify verdict is in VALID_VERDICTS
4. On failure: write INCONCLUSIVE stub finding with note

### 8. Fix sentinel timer to use global count instead of session count
**Resolves**: Q4.1

Replace session counter with: `global_count = len(results.tsv rows)`. Fire at multiples of 5/10 of global count, not session count. Always trigger both sentinels before calling synthesizer at campaign close.

### 9. Wire Overseer into the loop
**Resolves**: Q7.2

- Add overseer invocation to Mortar's sentinel logic: on FLEET_UNDERPERFORMING verdict from agent-auditor, invoke overseer
- Update agent-auditor to write `agent_db.json` format that overseer can consume (or update overseer.md to accept AUDIT_REPORT.md)
- Add overseer to REQUIRED_AGENTS in constants.py

### 10. Fix simulate.py hollow section bypass
**Resolves**: Q3.1

Check section content, not just section presence: if `## Output contract` header exists but the content below it is < 10 chars, apply the same -20 deduction as if the section were absent.

---

## Phase 3 Gate Requirements (BL 2.0 self-improvement loop)

### 11. Document planner in QUICKSTART.md and CLAUDE.md
**Resolves**: Q1.3, Q1.3-FU1

Add planner to both documents as "Step 5a" before question-designer. Mark optional but recommended. Planner's landmine detection (query Recall for prior campaign failures) prevents re-investigating settled questions across campaigns.

### 12. Implement planner → question-designer-bl2 interface
**Resolves**: Q1.3

Update question-designer-bl2.md to:
1. Check if CAMPAIGN_PLAN.md exists; if so, read it before generating questions
2. Map D-domain priorities from planner to BL 2.0 mode allocations

Update planner.md to output a BL 2.0 mode allocation table in addition to the D-domain risk ranking.

### 13. Create master question schema document
**Resolves**: Q1.1-WM4 (root cause of all field-name mismatches)

Document canonical question format as a standalone `docs/question-schema.md`. Reference from question-designer.md, question-designer-bl2.md, mortar.md. Include: field names, valid mode values, valid verdict values.

---

## Ongoing Monitoring

| Risk | Severity | Status | Owner |
|------|----------|--------|-------|
| Planner produces BL 1.x domain model for BL 2.0 campaigns | Medium | Unresolved until #12 | Planner update |
| research routing ambiguous (regulatory vs competitive) | Low | Recoverable from agent descriptions | Monitor |
| Fix spec field name mismatch (Q2.1) | Low | Semantically mappable | Monitor |
| code-reviewer reads original finding, not _fix.md | Medium | Latent until first FIXED question | Fix with code-reviewer.md update |
| OVERRIDE checked every 10q, not every question | Low | Acceptable timing gap | Monitor |
| project name substitution in Recall domain not enforced | Low | Documentation gap | Monitor |

---

## Residual Risk Inventory (after all recommended mitigations)

| Risk | Severity | Likelihood | Trigger | Residual owner |
|------|----------|------------|---------|----------------|
| LLM non-determinism producing inconsistent specialist findings | Medium | Low | Any question run twice | Peer-reviewer (mitigates, doesn't eliminate) |
| Regression detection in code-reviewer relies on LLM static reading | Low | Medium | Any fix-implementer run | Add test runner to code-reviewer protocol |
| Recall domain name inconsistency if project renamed | Low | Low | Any project rename | Add RECALL_DOMAIN constant to constants.py |
| agent-meta project has no .claude/agents/ directory | Low | Active | Any new agent-meta session | Copy agents dir (Q1.2 mitigation) |

---

## Campaign Verdict by Domain

| Domain | Questions | Verdict distribution | Systemic finding |
|--------|-----------|---------------------|-----------------|
| D1 — Architecture | 15 | 14 WARNING, 1 HEALTHY | Interface contract failures throughout |
| D2 — Interface Compat | 3 | 3 WARNING | Fix spec mismatch + OVERRIDE loop + definitive whitelist |
| D3 — Scoring | 2 | 2 WARNING | Hollow section bypass; revision criteria soft |
| D4 — Scheduling | 2 | 2 WARNING | Session counter reset; ID extraction bugs |
| D5 — Recall | 1 | 1 HEALTHY | Tag namespacing works; minor domain naming gap |
| D6 — Tail Risks | 2 | 2 WARNING | Ghost DONE entries; infinite OVERRIDE loop |

**Fleet verdict**: CRITICAL — the BL 2.0 routing interface is broken. No production campaign should use question-designer-bl2 + Mortar until fix #1 is applied.

---

## Minimum Viable Fix Set (ship condition)

To make BL 2.0 functional for a first real campaign, implement only items 1–4:

1. Fix question-designer-bl2 → Mortar interface (routing works)
2. Add OVERRIDE retry limit (no infinite loops)
3. Fix agent-auditor verdict whitelist (accurate fleet health)
4. Fix hypothesis-generator Recall domain (inter-campaign memory works)

Items 5–13 improve reliability and capability but are not blocking for a first campaign.
