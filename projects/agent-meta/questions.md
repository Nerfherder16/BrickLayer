# Agent Meta-Campaign — Question Bank

## Domain: D1 — Agent Architecture & Completeness

### Q1.1
**Question**: Does Mortar's routing table cover all Mode values that appear in template questions.md examples?
**Domain**: D1
**Mode**: diagnose
**Priority**: HIGH
**Status**: DONE
**Finding**: findings/Q1.1.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: Mortar's routing table (simulate/diagnose/fix/audit/research/benchmark/agent) may be missing modes that appear in actual campaigns, causing silent routing failures to the default quantitative-analyst.

---

### Q1.1-FU1
**Question**: Does question-designer-bl2 or question-designer have a documented list of valid Mode values, and does it match Mortar's routing table?
**Domain**: D1
**Mode**: diagnose
**Priority**: HIGH
**Status**: DONE
**Finding**: findings/Q1.1-FU1.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: question-designer-bl2 generates undocumented Mode values (code_audit, correctness, quality, subprocess) not in Mortar's routing table — it likely has no Mode enum constraint in its output spec.
**Source**: Follow-up from Q1.1

---

### Q1.1-FU3
**Question**: Do design-reviewer, evolve-optimizer, health-monitor, and cascade-analyst exist in the template agents directory? If not, Mortar would call undefined agents even with correct routing.
**Domain**: D1
**Mode**: diagnose
**Priority**: HIGH
**Status**: DONE
**Finding**: findings/Q1.1-FU3.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: The 5 BL 2.0 modes not in Mortar's routing table (Validate, Evolve, Monitor, Predict, Frontier) map to agents (design-reviewer, evolve-optimizer, health-monitor, cascade-analyst) that may not exist in the fleet.
**Source**: Follow-up from Q1.1-FU1

---

### Q1.1-FU4
**Question**: Does research-analyst.md have Frontier-mode instructions, or is it purely a Research/regulatory agent?
**Domain**: D1
**Mode**: diagnose
**Priority**: MEDIUM
**Status**: DONE
**Finding**: findings/Q1.1-FU4.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: research-analyst.md is a BL 2.0 replacement for regulatory-researcher + competitive-analyst and may not have Frontier-specific guidance (unconstrained exploration, analogical reasoning, possibility mapping).
**Source**: Follow-up from Q1.1-FU3

---

### Q1.1-FU2
**Question**: If Mortar silently misfires on code_audit questions (routing to quantitative-analyst), how many findings in existing campaign archives were produced by the wrong agent?
**Domain**: D1
**Mode**: diagnose
**Priority**: HIGH
**Status**: DONE
**Finding**: findings/Q1.1-FU2.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: Silent misrouting may have produced corrupt findings in prior campaigns that were accepted as valid without any error indication.
**Source**: Follow-up from Q1.1

---

### Q1.1-WM1 [Wave-mid]
**Question**: Does Mortar have a campaign-startup validation step to detect unrecognized Mode values before the first question runs?
**Domain**: D1
**Mode**: diagnose
**Priority**: HIGH
**Status**: DONE
**Finding**: findings/Q1.1-WM1.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: Mortar starts routing immediately on the first PENDING question. If any question has an unrecognized Mode value, the misrouting happens silently with no pre-flight warning. Mortar may lack a startup scan of all PENDING question modes.
**Source**: Wave-mid follow-up from Q1.1 cluster

---

### Q1.1-WM2 [Wave-mid]
**Question**: Does Mortar's `research` routing entry specify when to use regulatory-researcher vs competitive-analyst, or is the choice arbitrary?
**Domain**: D1
**Mode**: diagnose
**Priority**: MEDIUM
**Status**: DONE
**Finding**: findings/Q1.1-WM2.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: Mortar's routing table says "regulatory-researcher or competitive-analyst" for `research` mode without criteria for choosing — this is ambiguous routing that depends on the orchestrating agent's judgment, not a deterministic rule.
**Source**: Wave-mid follow-up from Q1.1 cluster

---

### Q1.1-WM3 [Wave-mid]
**Question**: Does question-designer-bl2's agent-mode question format (the `**Agent**:` field) match what Mortar expects to parse when Mode is `agent`?
**Domain**: D2
**Mode**: diagnose
**Priority**: HIGH
**Status**: DONE
**Finding**: findings/Q1.1-WM3.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: question-designer-bl2 uses `**Method**: {agent-name}` as the agent field (not `**Agent**:`). Mortar reads `**Agent**:` for agent-mode questions. The field name mismatch would cause Mortar to call an undefined agent or fall back silently.
**Source**: Wave-mid follow-up from Q1.1-FU1

---

### Q1.1-WM4 [Wave-mid]
**Question**: Is there a master question schema document that defines the canonical BL 2.0 question format? If not, is this the root cause of all three field-name mismatches found?
**Domain**: D1
**Mode**: diagnose
**Priority**: HIGH
**Status**: DONE
**Finding**: findings/Q1.1-WM4.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: The three field-name mismatches (**Operational Mode** vs **Mode**, CamelCase vs lowercase modes, **Method** vs **Agent**) all stem from the absence of a single authoritative question schema document — each agent defined its own format independently.
**Source**: Follow-up from Q1.1-WM3

---

### Q1.2
**Question**: Do all agents referenced in program.md have corresponding .md definition files?
**Domain**: D1
**Mode**: diagnose
**Priority**: HIGH
**Status**: DONE
**Finding**: findings/Q1.2.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: There may be phantom agents called in program.md that have no definition file, causing the loop to fall back to generic Claude behavior.

---

### Q1.3
**Question**: Does the planner agent's CAMPAIGN_PLAN.md format provide enough context for question-designer to prioritize domains correctly?
**Domain**: D1
**Mode**: diagnose
**Priority**: MEDIUM
**Status**: DONE
**Finding**: findings/Q1.3.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: The targeting brief format in planner.md may be too abstract — question-designer needs specific question templates, not just domain rankings.

---

### Q1.3-FU1 [Follow-up]
**Question**: Does QUICKSTART.md or CLAUDE.md document the correct workflow for calling planner before question-designer? If not, is planner effectively an undiscoverable optional step?
**Domain**: D1
**Mode**: diagnose
**Priority**: MEDIUM
**Status**: DONE
**Finding**: findings/Q1.3-FU1.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: The planner→question-designer interface is severed. If the documentation also doesn't mention calling planner before question-designer, the planner is effectively dead code.
**Source**: Follow-up from Q1.3

---

## Domain: D2 — Inter-Agent Interface Compatibility

### Q2.1
**Question**: Does fix-implementer's Fix Specification format match what code-reviewer expects to read?
**Domain**: D2
**Mode**: diagnose
**Priority**: HIGH
**Status**: DONE
**Finding**: findings/Q2.1.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: fix-implementer's Fix Specification (File/Line/Change/Verification) and code-reviewer's diff assessment logic may be misaligned — code-reviewer may look for fields that fix-implementer doesn't always produce.

---

### Q2.2
**Question**: Does peer-reviewer's OVERRIDE escalation actually reach Mortar's wave-start OVERRIDE check?
**Domain**: D2
**Mode**: diagnose
**Priority**: HIGH
**Status**: DONE
**Finding**: findings/Q2.2.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: peer-reviewer appends "Verdict: OVERRIDE" to the finding file. Mortar checks for this via `grep -l "Verdict.*OVERRIDE" findings/*.md`. The grep pattern may not match the exact format peer-reviewer uses.

---

### Q2.3
**Question**: Does agent-auditor's scoring methodology match the definitive rate thresholds in constants.py?
**Domain**: D2
**Mode**: simulate
**Priority**: MEDIUM
**Status**: DONE
**Finding**: findings/Q2.3.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: agent-auditor defines its own HEALTHY/WARNING/UNDERPERFORMING thresholds internally. These may differ from the MIN_DEFINITIVE_RATE constant, creating a double standard.

---

## Domain: D3 — Scoring Calibration

### Q3.1
**Question**: Does the simulate.py fleet scorer accurately identify FAILING agents, or does it score too leniently?
**Domain**: D3
**Mode**: simulate
**Priority**: HIGH
**Status**: DONE
**Finding**: findings/Q3.1.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: The scoring function starts at 100 and deducts points. An agent with no output contract (-20), no recall (-10), no recognized verdicts (-15) would score 55 = WARNING. But an agent with no output contract is effectively broken — it should score FAILING.

---

### Q3.2
**Question**: Does code-reviewer's NEEDS_REVISION vs BLOCKED distinction have clear enough criteria to be applied consistently?
**Domain**: D3
**Mode**: diagnose
**Priority**: MEDIUM
**Status**: DONE
**Finding**: findings/Q3.2.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: The boundary between NEEDS_REVISION and BLOCKED is defined by "lint errors vs lint warnings" and "verification failure" — but lint availability varies by project. An agent may always return APPROVED when no linter is available.

---

## Domain: D4 — Background Agent Scheduling

### Q4.1
**Question**: Can Mortar's 5-question forge-check and 10-question agent-auditor sentinels fire correctly if questions complete out of order?
**Domain**: D4
**Mode**: diagnose
**Priority**: MEDIUM
**Status**: DONE
**Finding**: findings/Q4.1.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: Mortar counts questions processed "this session" for sentinel triggering. If a campaign resumes mid-wave, the count resets to 0, causing both sentinels to fire immediately on resume even if they just ran.

---

### Q4.2
**Question**: Does Mortar's OVERRIDE re-queuing logic correctly identify which question to re-queue when a finding file is overridden?
**Domain**: D4
**Mode**: diagnose
**Priority**: HIGH
**Status**: DONE
**Finding**: findings/Q4.2.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: Mortar extracts the question ID from the finding filename (e.g., Q3.2.md → Q3.2). But if the finding file was renamed or the question has a non-standard ID format, the re-queuing may silently fail.

---

## Domain: D5 — Recall Integration

### Q5.1
**Question**: Are Mortar's Recall checkpoint stores consistent with how agent-auditor and planner query them?
**Domain**: D5
**Mode**: diagnose
**Priority**: MEDIUM
**Status**: DONE
**Finding**: findings/Q5.1.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: Mortar stores checkpoints with tags ["bricklayer", "agent:mortar", "type:checkpoint"]. Planner queries with tags ["agent:mortar"]. agent-auditor pulls prior audit scores with tags ["agent:agent-auditor"]. The tag namespacing may cause cross-agent queries to miss relevant stores.

---

## Domain: D6 — Tail Risks

### Q6.1
**Question**: What happens to the campaign if Mortar calls a specialist agent that produces an empty or malformed finding file?
**Domain**: D6
**Mode**: diagnose
**Priority**: HIGH
**Status**: DONE
**Finding**: findings/Q6.1.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: Mortar reads the finding to extract verdict and update questions.md. If the finding is empty or missing the expected sections, Mortar may silently mark the question DONE with no actual finding, creating a ghost entry in results.tsv.

---

### Q6.2
**Question**: Is there a maximum recursion risk if peer-reviewer issues OVERRIDE on a re-queued question, and Mortar re-queues it again?
**Domain**: D6
**Mode**: diagnose
**Priority**: MEDIUM
**Status**: DONE
**Finding**: findings/Q6.2.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: A question could loop: PENDING → specialist → OVERRIDE → RE-QUEUED → specialist → OVERRIDE → RE-QUEUED indefinitely. Neither Mortar nor peer-reviewer has a max-retry limit.

---

## Wave 2 Questions

### Q7.1
**Question**: Does hypothesis-generator's Recall query use the correct domain string for BL 2.0 campaigns?
**Domain**: D5
**Status**: DONE
**Finding**: findings/Q7.1.md
**Completed**: 2026-03-17T00:00:00Z
**Mode**: diagnose
**Priority**: HIGH
**Status**: PENDING
**Hypothesis**: hypothesis-generator queries Recall with `domain="{project}-autoresearch"` but all BL 2.0 agents (Mortar, agent-auditor, peer-reviewer) store under `domain="{project}-bricklayer"`. The domain suffix mismatch means hypothesis-generator's Recall queries return empty — no prior wave summaries, no cross-agent failure context, no benchmark baselines.
**Derived from**: Q5.1 (Recall tag namespacing), hypothesis-generator.md Recall section

---

### Q7.2
**Question**: Does agent-auditor's "Escalate to Overseer immediately" recommendation have a reachable target agent?
**Domain**: D1
**Mode**: diagnose
**Priority**: HIGH
**Status**: DONE
**Finding**: findings/Q7.2.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: agent-auditor recommends "ESCALATE_TO_OVERSEER" for UNDERPERFORMING agents. No `overseer.md` exists in the template agents directory. The escalation path terminates at a phantom agent, making all UNDERPERFORMING alerts unactionable.
**Derived from**: Q2.3 (agent-auditor scoring), Q1.2 (phantom agents)

---

### Q7.3
**Question**: What observable symptom does a user see when running a question-designer-bl2 campaign through Mortar, given the three field-name mismatches?
**Domain**: D1
**Mode**: diagnose
**Priority**: MEDIUM
**Status**: DONE
**Finding**: findings/Q7.3.md
**Completed**: 2026-03-17T00:00:00Z
**Hypothesis**: When Mortar parses a question-designer-bl2 question: (1) it reads `**Mode**:` which is absent (designer uses `**Operational Mode**:`) → defaults to quantitative-analyst, (2) even if it found "Diagnose", mode "Diagnose" ≠ "diagnose" → defaults again. Every question in a BL2.0 campaign silently routes to quantitative-analyst. The user sees no error, just subtly wrong findings.
**Derived from**: Q1.1-WM3, Q1.1-FU1, Q1.1-WM1
