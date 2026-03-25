# Finding: M-mid.2 — predict_subjectivity_rate added to monitor-targets.md

**Question**: Add Predict mode subjectivity metric to `monitor-targets.md`: `predict_subjectivity_rate` with WARNING threshold ≥0.30 and FAILURE ≥0.60. Measurement: Predict findings with SUBJECTIVE qualifier / total Predict outputs per wave.
**Agent**: quantitative-analyst
**Verdict**: CALIBRATED
**Severity**: Medium
**Mode**: monitor
**Target**: `bricklayer-v2/monitor-targets.md`

## Summary

`predict_subjectivity_rate` added to `monitor-targets.md` alongside `fix_preflight_rejection_rate` (M-mid.1). Thresholds set at WARNING ≥0.30 and FAILURE ≥0.60 as specified. Baseline not yet established — no Predict mode waves have run. The metric definition includes both explicit `SUBJECTIVE` verdict qualifiers and hedge-phrase detection in evidence sections.

## Evidence

### Entry in monitor-targets.md

```
| predict_subjectivity_rate | ≥0.30 | ≥0.60 | Count Predict findings where agent marks
  verdict reasoning as SUBJECTIVE ÷ total Predict outputs per wave | Q2.4 |
```

### Threshold rationale

| Threshold | Value | Rationale |
|-----------|-------|-----------|
| WARNING | ≥0.30 | More than 3 in 10 Predict outputs being unquantified suggests the Predict mode program is not enforcing probability calibration |
| FAILURE | ≥0.60 | More than 6 in 10 being SUBJECTIVE means Predict mode is failing its core purpose; switch unquantifiable questions to Diagnose mode instead |

The ≥0.30 threshold is deliberately loose — some fraction of Predict outputs being inherently uncertain is expected. The goal is to catch systematic drift toward unquantified language, not penalise individual uncertain outputs.

### Subjectivity detection criteria

Defined in `monitor-targets.md` as either:
1. Agent explicitly tags verdict reasoning as "SUBJECTIVE" in the finding
2. Evidence section uses hedge phrases without quantification: "seems likely", "probably", "might", "could be", "appears to"

This is a heuristic — edge cases (e.g., "probably PROBABLE with P≈0.65" is quantified despite using "probably") require human review. The metric is intended to surface systemic drift, not catch every instance.

### Relationship to Q2.4 finding

Q2.4 (WARNING) found that Predict mode inherently requires probability calibration infrastructure (historical base rates, calibration datasets) that BrickLayer 2.0 does not yet provide. The monitor metric converts this structural warning into a per-wave measurement that can detect when subjectivity is becoming a systematic problem rather than an occasional limitation.

## Verdict Threshold

CALIBRATED: metric defined, thresholds established, measurement method documented. Baseline will be populated after first Predict mode wave. No action required until WARNING threshold is crossed.

## Open Follow-up Questions

If `predict_subjectivity_rate` crosses WARNING (≥0.30) in a future wave, the appropriate response is: (1) add a calibration protocol to `modes/predict.md` requiring agents to cite base rate evidence, or (2) gate Predict questions behind a pre-flight check verifying that base rate data exists for the predicted domain.
