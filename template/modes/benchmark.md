# Benchmark Mode — Program

**Purpose**: Establish measurable baselines. Pure measurement — no verdicts on quality,
no failure hunting. Answer: where are we RIGHT NOW? This is the "before" state
that all other modes compare against.

**Verdict vocabulary**: CALIBRATED | UNCALIBRATED | NOT_MEASURABLE
**Output**: `benchmarks.json` — structured baseline data for all measured metrics

---

## Loop Instructions

### Per-question

Questions are measurement requests, not hypotheses:
- "What is the current p95 API latency?"
- "What is the current test coverage percentage?"
- "How many active memories are in the corpus?"
- "What is the current error rate on endpoint X?"

Evidence gathering: measure the actual system directly
- HTTP requests to live endpoints for performance metrics
- Code analysis tools for coverage
- Database queries for data volume metrics
- Log analysis for error rates

Verdict assignment:
- `CALIBRATED` — metric was measured successfully; value recorded
- `UNCALIBRATED` — metric measurement failed or produced unreliable data; note why
- `NOT_MEASURABLE` — metric cannot be measured with available tooling; note what's needed

**No HEALTHY/FAILURE verdicts** — Benchmark mode does not judge. It only records.
Judgment about whether a baseline is good or bad happens in Diagnose or Audit.

### Output format per measurement

```json
{
  "metric": "p95_api_latency_ms",
  "value": 1247,
  "unit": "ms",
  "measured_at": "2026-03-16T04:00:00Z",
  "method": "10 requests to /memory/store, p95 of response times",
  "conditions": "system under normal load, 20K memories in corpus"
}
```

All measurements append to `benchmarks.json`.

### Wave structure

- Questions are the metrics list, not hypothesis-driven
- No saturation stop — measure everything on the list
- Stop condition: all metrics in the measurement plan have been attempted

### Session end

Produce `benchmark-report.md`:
- Table of all metrics: name, value, unit, measured_at, method
- Note any UNCALIBRATED or NOT_MEASURABLE items
- This report is the reference baseline for all future Evolve and Monitor sessions
