# Playbook: Weekly Team Update

## Trigger

- **Schedule:** Every Friday at 17:00 (cron: `0 17 * * 5`)
- **Agent:** `synthesizer-bl2`
- **Conductor ID:** `team-update`

## Purpose

Produce a human-readable weekly status report summarising agent performance, key findings,
build health, and priorities for the coming week. Saves to `.charlie/reports/`.

## Inputs

1. **Agent scores** — `masonry/agent_db.json` (performance history per agent)
2. **New findings** — all `*.md` files in `findings/` modified since last Monday
3. **Git log** — `git log --oneline --since="last monday"` for build activity
4. **Test results** — latest pytest exit code and summary (if `tests/` directory exists)

## Expected Output

File: `.charlie/reports/team-update-YYYY-MM-DD.md`

```markdown
# Weekly Team Update — YYYY-MM-DD

## Top 3 Findings This Week

1. **[Finding title]** — `findings/finding-id.md`
   Summary: one sentence description of the finding and its verdict.

2. **[Finding title]** — `findings/finding-id.md`
   Summary: ...

3. **[Finding title]** — `findings/finding-id.md`
   Summary: ...

_N total findings this week._

---

## Agent Performance Rankings

### Top 3 Agents

| Rank | Agent | Score | Findings |
|------|-------|-------|----------|
| 1 | agent-name | 0.91 | 12 |
| 2 | agent-name | 0.87 | 9 |
| 3 | agent-name | 0.84 | 7 |

### Bottom 3 Agents (need attention)

| Rank | Agent | Score | Issue |
|------|-------|-------|-------|
| N | agent-name | 0.41 | Low verdict accuracy |
| N-1 | agent-name | 0.45 | High skip rate |
| N-2 | agent-name | 0.52 | Stale (no runs this week) |

---

## Build Health

- **Tests:** N passing / N failing (exit code: 0)
- **Coverage:** N% (threshold: N%)
- **Commits this week:** N
- **Open issues:** N (from git log FIX/TODO mentions)

---

## Next Week Priorities

1. [Priority derived from lowest-scoring agents or open findings]
2. [Priority derived from failing tests or coverage gaps]
3. [Priority derived from unanswered questions in questions.md]
```

## Ranking Criteria

- **Top agents:** sorted by `avg_verdict_accuracy` descending (from `agent_db.json`)
- **Bottom agents:** sorted by `avg_verdict_accuracy` ascending, only include agents active
  in the last 30 days (exclude retired agents)
- If `agent_db.json` is missing, omit the rankings section and log a notice

## Priority Generation Rules

Priorities are inferred from data, not invented:

1. Any agent with score < 0.5 → "Investigate and retrain `{agent-name}` (score: N)"
2. Any failing tests → "Fix N failing tests in `{test_file}`"
3. PENDING questions in `questions.md` → "Run N pending questions (wave X)"
4. No findings this week → "Restart campaign — no findings recorded"

## Write Procedure

1. Ensure `.charlie/reports/` directory exists (create if missing)
2. Compute output filename: `.charlie/reports/team-update-YYYY-MM-DD.md`
3. Write the full report to that file
4. Log: `Team update written to .charlie/reports/team-update-YYYY-MM-DD.md`
5. Do NOT commit this file — it is a local report only

## Safety Rules

1. Never include raw API keys, tokens, or credentials in the report
2. Agent scores must be read from `agent_db.json` — never fabricated
3. Finding summaries must come from the finding files — never summarised from memory
4. If fewer than 3 findings exist, report only what is available (do not pad)
