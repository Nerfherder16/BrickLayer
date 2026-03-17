# Audit Checklist — BrickLayer 2.0 Engine

Audit mode reads this file to determine compliance checks.
Define the standard being audited against and the specific checks.

## Standard

BrickLayer 2.0 spec as defined in `bricklayer-v2/project-brief.md` and
`bricklayer-v2/modes/`. Verifies the engine implementation matches its spec.

## Checks

| ID | Check | Pass Condition | Fail Condition | Auto-checkable? |
|----|-------|---------------|----------------|-----------------|
| A1 | `_PARKED_STATUSES` completeness | Contains all 10 required terminal verdicts from constants.py REQUIRED_PARKED | Any required verdict absent | Yes (grep + set comparison) |
| A2 | `_NON_FAILURE_VERDICTS` completeness | All 18 verdicts present in `findings.py` frozenset | Any verdict missing | Yes (grep) |
| A3 | Heal loop termination guarantee | `healloop.py` has bounded `for` loop with explicit `break` paths, no `while True` | Unbounded loop without guaranteed exit | Yes (grep) |
| A4 | Recall bridge graceful-fail | Every httpx call wrapped in try/except | Any bare httpx call without exception handling | Yes (grep) |
| A5 | Session context append-only | `session-context.md` opened with `"a"` mode only | Opened with `"w"` anywhere in `campaign.py` | Yes (grep) |
| A6 | `operational_mode` defaults to `"diagnose"` | `questions.py` sets default `"diagnose"` when field absent | No default or wrong default | Yes (grep) |
| A7 | Heal loop agent existence check | `healloop.py` calls `_agent_exists()` before spawning each agent | Agent spawned without prior existence check | Yes (grep) |
| A8 | `mode_context` injection order | In `campaign.py`, `mode_context` set on question dict before `run_question()` call | Injected after run_question, or not at all | Yes (line order check) |
| A9 | `session_ctx_block` prompt order | In `runners/agent.py`: mode_ctx_block then session_ctx_block then doctrine_prefix | Out of order | Yes (line order check) |
| A10 | Heal intermediate finding IDs | Synthetic IDs follow `{qid}_heal{n}_{type}` pattern with no collision risk | ID pattern could collide with real question IDs | Yes (grep pattern) |
| A11 | Heal intermediates recorded in results.tsv | Both `_heal{n}_diag` and `_heal{n}_fix` verdicts written via update_results_tsv | Intermediate findings not recorded | Yes (grep) |
| A12 | BL 1.x backwards compatibility | BRICKLAYER_FIX_LOOP and BRICKLAYER_HEAL_LOOP are independent env vars | One overrides or disables the other | Yes (grep) |

## Verdict thresholds

- COMPLIANT: 0 fails
- PARTIAL: 1-3 fails, none are structural
- NON_COMPLIANT: Any structural violation (A3, A4, A5 are structural) OR 4+ total fails
