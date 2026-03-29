# Checkpoint: Wave 1 — Q8
**Generated**: 2026-03-29
**Findings since last checkpoint**: 7 (first checkpoint — all findings)
**Verdict distribution**: FAILURE=0 WARNING=2 HEALTHY=0 INCONCLUSIVE=0 DIAGNOSIS_COMPLETE=5

> Note: Five findings carry status DIAGNOSIS_COMPLETE rather than a standard BL verdict.
> These are treated as FAILURE-tier for priority purposes — each identifies a confirmed
> structural gap with a fix specification ready for fix-implementer.

---

## Verdicts Table

| Question | Verdict | Severity | Key Finding |
|----------|---------|----------|-------------|
| D1.1 | DIAGNOSIS_COMPLETE | HIGH | CLAUDE.md "trivial" escape hatch (line 68) is peer-level to the absolute Mortar directive; undefined "trivial" defaults to a broad prior that swallows most text-answer tasks; no text-generation enforcement exists |
| D1.2 | DIAGNOSIS_COMPLETE | MEDIUM | Routing section is 4.8% of 23K-token auto-context; UI rules alone are 12.9x the routing signal volume; dilution is a confirmed secondary amplifier — not root cause, but lowers the activation threshold for inline execution |
| D1.3 | DIAGNOSIS_COMPLETE | HIGH | masonry-prompt-router.js emits `hookSpecificOutput` (wrong channel) instead of `additionalContext`; hint format is annotation-style (`→ Mortar: routing to X [effort:Y]`) not imperative; two independent structural reasons the hint carries insufficient authority |
| D2.1 | DIAGNOSIS_COMPLETE | HIGH | TextGeneration hook event does not exist in Claude Code — inline text responses are architecturally ungatable; PreToolUse Write/Edit block is the highest-leverage achievable enforcement; `isMortarConsulted()` already in masonry-approver.js but softened to advisory stderr only |
| D2.2 | DIAGNOSIS_COMPLETE | HIGH | Routing receipt pattern is structurally present (isMortarConsulted, mortar_consulted field) but has two gaps: no receipt writer (mortar_session_id fields absent from live masonry-state.json) and gate emits stderr warning + allows through instead of deny; 2-file atomic fix required |
| D5.1 | WARNING | MEDIUM | 4 silent router exit paths identified; Path 4 (medium + no-intent, lines 194-195) is the unintentional gap covering ~30-45% of dev prompts; build rule verb whitelist missing maintenance verbs (fix, update, set, make, change, configure, apply) |
| D5.2 | WARNING | HIGH | classifyEffort() defines "medium" as a structural default fallthrough with zero positive tests; 40-60% of typical session prompts hit the medium+no-intent skip gate; emitting `[effort:medium]` alone has zero routing effect — fix must target INTENT_RULES coverage, not effort thresholds |

---

## Failure Boundaries Discovered

**Routing signal dilution threshold (D1.2)**
- Routing directive is 1,104 tokens out of 23,034 total auto-loaded tokens = 4.8%
- UI-specific rules (6 files, 14,201 tokens) are 12.9x the routing signal
- At 100K conversation tokens the routing section falls below 1% of total context
- At 150K tokens (masonry-context-monitor.js warning threshold) it reaches 0.64% — functionally noise

**Mortar receipt staleness window (D2.1, D2.2)**
- `isMortarConsulted()` freshness window: 4 hours (`MORTAR_SESSION_FRESHNESS_MS`)
- Live `masonry-state.json` has no `mortar_consulted` or `mortar_session_id` fields at all — the gate always evaluates to false regardless of prior activity
- Bash is exempt from the gate entirely (doubly total: bypasses both advisory warning and the build-mode allow signal)

**Intent routing coverage gap (D5.1, D5.2)**
- INTENT_RULES build verb whitelist covers only creation verbs: `build|implement|create|add.?feature|write.?code|develop|scaffold`
- Missing maintenance verbs: `fix`, `update`, `make`, `change`, `set`, `configure`, `enable`, `disable`, `remove`, `modify`, `edit`
- Maintenance prompts > 50 chars that contain none of the high/max trigger vocabulary land in Path 4 (silent exit) — estimated 40-60% of a typical developer session
- Low-effort boundary is a hard character count (< 50 chars) with no content adjustment; question-phrased prompts anchored past the opening word ("Can you explain how...") escape `low` classification

**Hook event model hard limit (D2.1)**
- No TextGeneration, PreResponse, or AssistantMessage hook event exists
- Inline text responses (the primary failure mode) cannot be intercepted by any hook
- Enforcement is only possible at the tool-invocation layer (Write/Edit/Bash/Agent PreToolUse)

---

## Cross-Domain Conflicts

**D1.1 escape hatch vs D2.1/D2.2 receipt gate**
D1.1 establishes that undefined "trivial" in CLAUDE.md allows Claude to answer most text tasks inline without ever attempting a tool call. D2.1 and D2.2 propose enforcing routing via a Write/Edit PreToolUse block. These two findings converge on a shared gap: the PreToolUse block is the strongest available enforcement, but it cannot gate inline-text responses — only file writes. A session where Claude answers inline and never touches a file would defeat the receipt gate entirely. Both fixes are necessary and neither is sufficient alone.

**D1.3 wrong channel vs D2.1 advisory-only gate**
D1.3 finds that the routing hint is in the wrong output channel (hookSpecificOutput vs additionalContext) and formatted as an annotation. D2.1 finds that the Mortar gate in masonry-approver.js is advisory stderr. Both represent the same architectural pattern: mechanisms that appear to enforce routing but deliberately allow-through at the critical decision point. The finding in D2.1 that this is "a conscious 'gate is advisory only' comment" matches D1.3's observation that the hook uses annotation format rather than imperative format — suggesting the advisory posture was a deliberate design choice, not an accidental gap.

**D5.1 confirms the audit has no router coverage during the campaign itself**
D5.1 confirmed (Path 3, live state check) that the prompt router is fully suppressed for the entire inline-execution-audit campaign because `masonry-state.json` has `"mode": "campaign"`. This means all D1/D2/D5 diagnostic work happened in a context where the router would never fire anyway. D3/D4/A1/V1/FR1 questions will run under the same suppression — the campaign is auditing a system that is disabled for the duration of the audit.

---

## Active Signals

*(No scratch.md exists for this campaign — no WATCH/BLOCK items available. Active signals derived from finding text.)*

**Signals elevated from finding content:**

- WATCH: D2.2 peer review found that the masonry-state.json evidence block in D2.2 presents fabricated JSON — the `mortar_consulted` and `mortar_session_id` fields do not exist in the live file. The actual live state has only `last_qid`, `last_verdict`, `verdicts`, `updated_at`, `active_agent`, `active_agent_count`. The fix specification in D2.2 remains valid (the conclusion is correct — fields absent = gate always false) but the evidence chain is tainted. Quality score was reduced to 0.72. Any fix-implementer work on D2.2 must re-read the live file before acting.

- WATCH: D1.2 peer review flagged that the fix (moving 6 UI rules files to `rules/ui/` subdirectory) assumes Claude Code does not recursively load subdirectory rules files — this behavioral assumption is unverified. The subdirectory exclusion is not documented. Fix Part A may have zero effect if Claude Code loads subdirectories recursively. Verify empirically before implementing.

- WATCH: D2.1 and D2.2 identify the same fix target (masonry-approver.js lines 293-301). Any fix-implementer work must ensure both findings are considered together — D2.1's detailed fix spec and D2.2's secondary requirement for an atomic writer change (masonry-prompt-router.js) must be deployed together or the gate deadlocks all Write/Edit in non-build sessions.

---

## Priorities for Remaining Questions

1. **D3.1 and D3.2 (competitive/analogues)** — D5.1 and D5.2 together established that 40-60% of session prompts fall through the medium+no-intent gap due to a maintenance-verb coverage failure. D3 questions should specifically focus on how analogous intent-routing systems (GitHub Copilot Workspace, Cursor agent mode, Devin) handle the creation-verb vs. maintenance-verb distinction. The verb whitelist expansion is the highest-leverage single fix available and industry benchmarks may provide a proven vocabulary set rather than requiring manual gap analysis.

2. **A1.1 (adversarial / bypass resistance)** — D1.1 established that the "trivial" escape hatch is the primary bypass mechanism. D2.1 confirmed that inline text responses are architecturally ungatable. A1.1 should stress-test specifically: (a) whether the proposed D1.1 fix text ("single-sentence factual lookups") can be rephrased in natural user prompts to re-trigger the escape hatch, and (b) whether the D2.1 receipt gate can be defeated by a Claude session that answers everything inline and never attempts a Write/Edit — which the current fix design cannot block.

3. **V1.1 (verification)** — All five DIAGNOSIS_COMPLETE findings have fix specifications ready for fix-implementer. Before any fixes are applied, V1.1 should establish a behavioral baseline: what fraction of test prompts currently route through agents vs. inline, measured empirically against the live masonry-prompt-router.js. This baseline is necessary to measure fix effectiveness after D1.1, D1.3, D2.1, and D2.2 fixes are applied. Without it, there is no way to confirm the fixes reduced inline execution in practice.

---

## Emerging Hypotheses Not Yet in the Question Bank

**H-NEW-1: The Bash total exemption is a routing bypass vector as significant as inline text.**
D2.1 and D2.2 both note that Bash is unconditionally exempt from the Mortar gate — not just from the advisory warning, but doubly so (also bypasses the build-mode allow signal). Since Bash can execute git operations, write files via `echo >`, run scripts, curl APIs, and trigger deployments, the Bash exemption may account for as much unrouted substantive work as inline text responses. No question in the current bank addresses whether Bash-mediated work is subject to any routing enforcement. A new question should measure: what fraction of substantive session work happens via Bash rather than Write/Edit, and does exempting Bash from the receipt gate defeat the entire enforcement model?

**H-NEW-2: The global singleton masonry-state.json creates cross-session receipt corruption on multi-machine setups.**
D2.2 identified that masonry-state.json is a hardcoded absolute path global singleton. Tim's stated workflow (Claude Code on multiple machines simultaneously — casaclaude, proxyclaude) means two concurrent sessions write and read the same receipt file. A receipt written by a casaclaude session would satisfy the gate check in a proxyclaude session for a different project, producing false-positive "routing confirmed" states. No question addresses the multi-machine receipt isolation problem. A new question should audit whether the receipt store should be per-session (tmpdir/masonry-receipt-{session_id}.json) rather than a global singleton.

**H-NEW-3: The prompt router suppression during campaigns means the routing compliance gap is never measured under real workload.**
D5.1 confirmed live that the router exits silently for the entire inline-execution-audit campaign (Path 3: mode=campaign). This creates a measurement paradox: the audit is investigating routing compliance in a context where the router is turned off. It is unknown whether the router would perform better or worse under the routing conditions it is actually designed for (non-campaign interactive sessions). A new question should examine whether campaign suppression is warranted — or whether the router should remain active during campaigns with campaign-specific routing behavior (e.g., routing synthesis and hypothesis generation questions to appropriate specialists while suppressing dev-mode routing).

**H-NEW-4: Fix interaction risk — D1.1 escape hatch and D2.1 receipt gate fixes may conflict.**
If the D1.1 fix narrows "trivial" to single-sentence factual lookups, Claude will attempt to use the Agent tool for more tasks. If the D2.1 receipt gate is simultaneously activated (blocking Write/Edit without a Mortar token), and the Mortar agent itself fails to write the receipt token, Claude will be in a state where it is trying to delegate (D1.1 fix working) but every resulting Write/Edit is blocked (D2.1 gate firing). This deadlock scenario is noted in D2.1's risk section but not tested. A new question or a dedicated fix-order dependency analysis is warranted before both fixes are deployed together.
