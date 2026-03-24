# Monitor Targets — BrickLayer 2.0

Metrics tracked by Monitor mode. Each entry represents a signal identified by prior
Diagnose/Research sessions that is worth watching continuously.

See `modes/monitor.md` for the monitor loop protocol, verdict vocabulary, and output format.

---

## Monitor Targets

| Metric | Threshold WARNING | Threshold FAILURE | Measurement Method | Finding Ref |
|--------|------------------|-------------------|--------------------|-------------|
| fix_preflight_rejection_rate | ≥0.20 | ≥0.40 | Count Fix findings with verdict=FIX_FAILED at pre-flight gate ÷ total Fix questions run per wave | Q2.2 |
| predict_subjectivity_rate | ≥0.30 | ≥0.60 | Count Predict findings where agent marks verdict reasoning as SUBJECTIVE ÷ total Predict outputs per wave | Q2.4 |

---

## Metric Definitions

### `fix_preflight_rejection_rate`

**What it measures**: Fraction of Fix mode questions that fail the pre-flight checklist (source finding lacks a complete fix specification, target file path is missing, or the diagnosed root cause is insufficiently specified).

**Why we watch it**: Q2.2 (WARNING) found that the Fix mode pre-flight checklist was too permissive — underspecified DIAGNOSIS_COMPLETE findings can cause Fix agents to scope-creep or produce incomplete fixes. A high rejection rate indicates Fix questions are being created before their upstream Diagnose findings are mature enough.

**Measurement method**:
1. After each wave that included Fix questions, count findings in `findings/fix/` with `Verdict: FIX_FAILED` where the failure reason includes "pre-flight" or "insufficient specification"
2. Divide by total Fix questions run in that wave
3. Compare against thresholds

**Thresholds**:
- `WARNING` (≥0.20): More than 1 in 5 Fix questions failing pre-flight — Diagnose quality may be degrading
- `FAILURE` (≥0.40): More than 2 in 5 Fix questions failing — campaign is generating premature Fix questions; review Diagnose → Fix transition criteria

---

### `predict_subjectivity_rate`

**What it measures**: Fraction of Predict mode outputs where the agent uses hedge language or marks its verdict reasoning as SUBJECTIVE rather than assigning a concrete tier (IMMINENT/PROBABLE/POSSIBLE/UNLIKELY) with a calibrated probability estimate.

**Why we watch it**: Q2.4 (WARNING) found that Predict mode verdict assignment was inherently subjective without a probability calibration protocol. Unchecked subjectivity degrades campaign signal quality — a finding that says "probably PROBABLE" is less actionable than one that says "PROBABLE (0.72 based on base rate × acceleration factor)".

**Measurement method**:
1. After each wave that included Predict questions, count findings in `findings/predict/` where:
   - The verdict is accompanied by "SUBJECTIVE" qualifier, OR
   - The evidence section uses hedge phrases without quantification ("seems likely", "probably", "might", "could be")
2. Divide by total Predict outputs in that wave
3. Compare against thresholds

**Thresholds**:
- `WARNING` (≥0.30): More than 3 in 10 Predict outputs are unquantified — Predict mode may need calibration protocol enforcement
- `FAILURE` (≥0.60): More than 6 in 10 Predict outputs are SUBJECTIVE — Predict mode is not producing actionable verdicts; consider switching to Diagnose for these questions

---

## Baseline Values

*To be filled in after first Monitor run.*

| Metric | Baseline Value | Baseline Run Date | Notes |
|--------|---------------|------------------|-------|
| fix_preflight_rejection_rate | — | — | No Fix mode runs yet at time of writing |
| predict_subjectivity_rate | — | — | No Predict mode runs yet at time of writing |
