# Monitor Mode — Program

**Purpose**: Continuous lightweight health checking. Tracks known metrics against
defined thresholds. Alerts when a threshold is crossed. Does NOT find new failures
(that's Diagnose) — it watches things we already know to watch.

**Input**: `monitor-targets.md` — list of metrics, thresholds, and alert conditions
**Verdict vocabulary**: OK | DEGRADED_TRENDING | DEGRADED | ALERT | UNKNOWN
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
- `OK` — metric within expected range and trend is stable or improving
- `DEGRADED_TRENDING` — metric has NOT yet crossed the WARNING threshold, but has moved
  monotonically toward it in ≥3 consecutive runs AND is projected to cross it within 5 more runs
  at the current rate. Log the projected crossing run count. Handoff trigger: → Predict mode.
- `DEGRADED` — metric has crossed the WARNING threshold; note delta from baseline
- `ALERT` — metric has crossed the FAILURE threshold; immediate attention required
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

### Trend projection (for DEGRADED_TRENDING)

When ≥3 consecutive runs show monotonic movement toward a threshold:
1. Compute per-run delta: `(current - prior) / prior`
2. If delta trend is consistent (all same sign), project: `runs_to_cross = (threshold - current) / avg_delta`
3. If `runs_to_cross ≤ 5`: verdict = `DEGRADED_TRENDING`
4. Log format: `DEGRADED_TRENDING: {metric} at {value}, projected to cross {threshold} in {n} runs`

### Session end

Produce `monitor-summary.md`:
- Timestamp of this run
- All metrics measured: OK / DEGRADED_TRENDING / DEGRADED / ALERT / UNKNOWN counts
- Any ALERTs with full context
- Any DEGRADED_TRENDING items with projected crossing run count
- Trend: delta from last run for each metric
