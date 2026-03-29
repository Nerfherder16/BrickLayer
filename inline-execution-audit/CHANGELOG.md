# Changelog -- inline-execution-audit

All notable campaign findings and fixes documented here.
Maintained by BrickLayer synthesizer at each wave end.

---

## [Unreleased]

---

## [Wave 1] -- 2026-03-29

Wave 1: 14 questions answered. Root cause chain fully mapped from CLAUDE.md escape hatch through enforcement absence. 5 DIAGNOSIS_COMPLETE, 1 CONFIRMED, 4 WARNING, 3 FAILURE, 1 FRONTIER_PARTIAL.

### Found (open)

- `D1.1` [DIAGNOSIS_COMPLETE] -- CLAUDE.md line 68 "trivial" escape hatch overrides absolute Mortar directive via specificity-beats-general; no operational definition of "trivial"
- `D1.2` [DIAGNOSIS_COMPLETE] -- Routing signal is 4.8% of 23K-token auto-context; UI rules 12.9x routing volume; context dilution confirmed as secondary amplifier
- `D1.3` [DIAGNOSIS_COMPLETE] -- Prompt router uses hookSpecificOutput (wrong channel) + annotation format; hint may not enter Claude's context
- `D2.1` [DIAGNOSIS_COMPLETE] -- isMortarConsulted() exists in masonry-approver.js but advisory-only (stderr warning + allow-through); TextGeneration hook absent
- `D2.2` [DIAGNOSIS_COMPLETE] -- Routing receipt pattern structurally present but no receipt writer (mortar_session_id absent from live state) + gate softened
- `A1.1` [CONFIRMED] -- 0 of 23 active hooks enforce delegation; 7 hard-blocking hooks but none check routing compliance; enforcement infrastructure complete, safety pin still in
- `D5.1` [WARNING] -- 4 silent exit paths; Path 4 (medium+no-intent) is unintentional gap covering ~30-45% of dev prompts; build rule missing maintenance verbs
- `D5.2` [WARNING] -- classifyEffort() defines "medium" as fallthrough default (zero regex); 40-60% of session prompts hit medium+no-intent gate
- `D3.1` [FAILURE] -- 1/10 Mortar work types (Spec+build) has zero INTENT_RULES coverage; 6/10 degraded; 70% routing surface dark or collision-prone
- `D3.2` [FAILURE] -- Router stateless per-prompt; zero history access; multi-turn workflows collapse to inline by Turn 2; campaign mode causes total blackout
- `D4.1` [WARNING] -- 0/20 Mortar agents missing .md files (HEALTHY); WARNING on structural grounds: router has zero file-existence validation
- `D4.2` [FAILURE] -- 114 registered agents vs 16 auto-routable (14%); 98 agents (86%) dark fleet; routing_keywords unpopulated for 80+
- `V1.1` [WARNING] -- Enforcement feasible but 5 prerequisites required; 100% false-positive immediately without receipt writer; deploy behind env flag
- `FR1.1` [FRONTIER_PARTIAL] -- Full forced-delegation BLOCKED (no PreTextGeneration hook); Write/Edit enforcement VIABLE (~80 lines code); 3 fundamental gaps, 6 incidental

### Healthy

- D4.1 confirmed all 20 Mortar routing table agents have resolvable .md files (bl-audit D2.6 stale)
- FR1.1 confirmed minimum viable enforcement architecture is buildable within current hook capabilities
