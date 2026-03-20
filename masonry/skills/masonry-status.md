---
name: masonry-status
description: Show current Masonry project health — questions, verdicts, agent scores, wave
---

## masonry-status — Campaign Health Report

Read the following files from the current working directory and produce a clear health
summary. All reads are best-effort — skip gracefully if a file doesn't exist.

### Files to Read

1. **`questions.md`** — Count lines containing PENDING, DONE, and any terminal status
   (BLOCKED, INCONCLUSIVE, HEAL_EXHAUSTED, etc.)
2. **`results.tsv`** — Read last 5 rows (most recent verdicts). Columns: timestamp, qid, verdict, agent, score
3. **`agent_db.json`** — If present, identify top 3 and bottom 3 agents by score
4. **`masonry-state.json`** — Current loop state (mode, wave, q_current, q_total, verdicts, active_agent)
5. **`findings/synthesis.md`** — If present, extract the Recommendation and Confidence lines

### Output Format

Print a formatted health summary like this:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  MASONRY  ·  {project}  ·  Wave {N}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Questions
  PENDING:    {N}
  DONE:       {N}
  Terminal:   {N}  (BLOCKED, HEAL_EXHAUSTED, etc.)
  Total:      {N}

Recent Verdicts (last 5)
  {qid}  {verdict}  {agent}  score:{score}
  ...

Verdict Totals
  HEALTHY:     {N}
  WARNING:     {N}
  FAILURE:     {N}
  (other verdicts if present)

Agent Performance  (from agent_db.json)
  Top:    {agent} ({score}), {agent} ({score}), {agent} ({score})
  Bottom: {agent} ({score}), {agent} ({score}), {agent} ({score})

Synthesis  (from findings/synthesis.md)
  Recommendation: {CONTINUE|STOP|PIVOT}
  Confidence:     {value}

Loop State
  Mode:         {mode}
  Active agent: {agent}
  Last verdict: {verdict}  ({qid})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Actionable Signals

After printing the table, add 1-3 bullet points based on what you see:

- If PENDING = 0: "Question bank exhausted — run hypothesis-generator to add Wave N+1 questions"
- If FAILURE rate > 40%: "High failure rate — consider PIVOT or running the synthesizer"
- If active_agent matches a bottom-3 agent: "Active agent has low score — consider manual review"
- If Synthesis says STOP: "Synthesizer recommends stopping — review findings/synthesis.md"
- If no masonry-state.json: "No active campaign — run /masonry-run to start one"
