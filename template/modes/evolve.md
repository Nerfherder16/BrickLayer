# Evolve Mode — Program

**Purpose**: Improve a healthy, working system. Not fixing bugs (Diagnose/Fix) —
making good things better. Targets: performance, architecture, developer experience,
code quality, test coverage, scalability. Requires a Benchmark baseline to measure
against.

**Prerequisite**: A `benchmarks.json` from a prior Benchmark session
**Verdict vocabulary**: HEALTHY | IMPROVEMENT | REGRESSION | WARNING
**Output**: Findings with specific improvement proposals and delta measurements

---

## Loop Instructions

### Per-question

Questions target improvement opportunities:
- "Can the p95 latency of endpoint X be reduced by >20% without changing behavior?"
- "Is there a simpler implementation of module Y with equivalent test coverage?"
- "Does increasing connection pool size improve throughput under load?"
- "Can the scoring algorithm be made more cache-friendly?"

Evidence gathering:
- Read the current implementation
- Propose the improvement
- Run before/after measurement (reference `benchmarks.json` as baseline)
- Check that improvement doesn't regress any existing metrics

Verdict assignment:
- `IMPROVEMENT` — the change produces measurable improvement without regression
  Include: delta metric, before/after values, confidence
- `HEALTHY` — the area is already well-optimized; no meaningful improvement found
- `WARNING` — the area needs attention but the improvement path isn't clear
- `REGRESSION` — an attempted optimization regressed a different metric; revert

### Wave structure

- Hypothesis generator asks: "Given the benchmark baseline, where is the largest gap between current performance and theoretical optimum?"
- Questions are ordered by expected impact × ease
- Stop condition: all high-impact improvement opportunities explored
  OR benchmark delta < 5% across all remaining candidates (diminishing returns)

### Delta measurement format

Every `IMPROVEMENT` finding must include:
```
## Delta
- Metric: p95_latency_ms
- Baseline: 1,247ms (from benchmarks.json 2026-03-16)
- After: 892ms
- Improvement: -28.5%
- Regression check: throughput unchanged (452 req/s vs 451 req/s baseline)
```

### Session end

Update `benchmarks.json` with new measurements for any changed metrics.
Produce `evolve-report.md`:
- All IMPROVEMENT findings with delta measurements
- Total improvement across all metrics vs. baseline
- Recommended next Evolve targets (remaining high-impact opportunities)
