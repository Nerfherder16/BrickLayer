# Monitor Targets — [PROJECT NAME]

Monitor mode reads this file at the start of each session.
Define what to measure, what thresholds trigger ALERT vs DEGRADED, and how to measure it.

## Format

```
## [metric-name]
Source: [endpoint / file / command that produces the measurement]
Healthy threshold: [value or condition for OK verdict]
Warning threshold: [value or condition for DEGRADED verdict]
Alert threshold: [value or condition for ALERT verdict]
Cadence: [how often to check]
```

## Targets

<!-- Add targets here -->
