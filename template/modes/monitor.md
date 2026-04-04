# Monitor Mode — Program

**Purpose**: Continuous lightweight health checking. Tracks known metrics against
defined thresholds. Alerts when a threshold is crossed. Does NOT find new failures
(that's Diagnose) — it watches things we already know to watch.

**Input**: `monitor-targets.md` — list of metrics, thresholds, and alert conditions
**Verdict vocabulary**: OK | ALERT | DEGRADED | UNKNOWN
**Cadence**: Runs on a schedule (cron or manual trigger); not campaign-based

---

## Loop Instructions

### Pre-flight

1. Read `monitor-targets.md` — the list of what to watch
2. Read `benchmarks.json` — the baseline values for each target
3. Each run is a single-pass check, not a multi-wave campaign

### Per-target measurement

For each item in `monitor-targets.md`:
1. Measure the current value (HTTP, database query, file analysis, etc.)
2. Compare against the defined threshold
3. Compare against the `benchmarks.json` baseline (delta from baseline)

Verdict assignment:
- `OK` — metric within expected range
- `DEGRADED` — metric crossed WARNING threshold; note delta from baseline
- `ALERT` — metric crossed FAILURE threshold; immediate attention required
- `UNKNOWN` — measurement failed; cannot determine current state

### Alert format

Any `ALERT` verdict generates an immediate output:
```
🚨 ALERT: {metric_name}
Current: {value}
Threshold: {failure_threshold}
Baseline: {benchmark_value} ({delta:+.1f}%)
Finding reference: {original_finding_id if applicable}
```

### Output

Monitor does NOT write to `findings/` for OK verdicts — it would flood the findings directory.

Write to `monitor-log.tsv`:
```
timestamp    metric              value    verdict    delta_from_baseline
```

Write to `findings/` ONLY for `ALERT` verdicts — these become new Diagnose seeds.

### `monitor-targets.md` format

```markdown
## Monitor Targets

| Metric | Threshold WARNING | Threshold FAILURE | Measurement Method | Finding Ref |
|--------|------------------|-------------------|--------------------|-------------|
| floor_clamped_count | >800 | >1000 | SELECT COUNT FROM qdrant WHERE importance <= 0.05 | Q29.6 |
| p95_api_latency_ms | >500 | >2000 | 10 requests to /memory/store | Q13.3 |
| retrieval_coverage_pct | <20% | <10% | /admin/stats retrieval_rate field | Q13.1 |
```

### Relationship to Diagnose

- Monitor watches metrics identified by prior Diagnose sessions
- When Monitor fires an ALERT, the alert finding seeds a new Diagnose question
- Monitor is Diagnose's early-warning system
- Monitor never replaces Diagnose — it can't find NEW unknown failures

### Session end

Produce `monitor-summary.md`:
- Timestamp of this run
- All metrics measured: OK / DEGRADED / ALERT counts
- Any ALERTs with full context
- Trend: delta from last run for each metric
