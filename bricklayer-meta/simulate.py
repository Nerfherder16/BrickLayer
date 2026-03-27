"""
simulate.py — BrickLayer campaign quality simulation.

Models a research campaign as an information-density function across waves.
The agent modifies SCENARIO PARAMETERS, reruns, reads output, and records
whether the campaign configuration produces reliable signal or noise.

Primary metric: campaign_yield = unique_actionable_findings / total_questions_run

A finding is "actionable" iff:
  (1) the question was well-formed (not malformed by the hypothesis generator),
  (2) the question explored novel failure space (not a restatement of prior waves),
  (3) the agent produced a trustworthy verdict (not drifted or hallucinated).

All three conditions must hold. Missing any one produces noise: an INCONCLUSIVE,
a redundant finding, or a confident-but-wrong HEALTHY verdict.

Usage:
    python simulate.py > run.log 2>&1
    grep "^verdict:" run.log
    grep "^primary_metric:" run.log

Output format (grep-friendly, one metric per line):
    primary_metric:       <float>   # campaign_yield
    secondary_metric:     <float>   # synthesis_coherence
    fix_regression_rate:  <float>
    wave_novelty_floor:   <float>
    total_questions:      <int>
    total_actionable:     <int>
    verdict:              <HEALTHY|WARNING|FAILURE>
    failure_reason:       <str or NONE>
"""

import io
import random
import sys

from constants import (
    BASE_GENERALIST_ACCURACY,
    BASE_SPECIALIST_ACCURACY,
    CAMPAIGN_YIELD_FAILURE,
    CAMPAIGN_YIELD_WARNING,
    FIX_REGRESSION_FAILURE,
    PEER_REVIEW_CORRECTION_RATE,
    SYNTHESIS_COHERENCE_FAILURE,
    WAVE_NOVELTY_FLOOR_FAILURE,
    WAVE_SATURATION_RATE,
)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# =============================================================================
# SCENARIO PARAMETERS — The agent modifies this section.
# Each run tests one hypothesis about campaign quality under a given config.
# Change one or more parameters, run, observe the verdict.
# =============================================================================

SCENARIO_NAME = "Recalibrated baseline — changes 1-3 applied (Q6.1/Q6.7)"

# --- Campaign structure ---
WAVE_COUNT = 4
# Number of research waves before the synthesizer terminates the campaign.
# More waves increase total coverage but accelerate saturation and hypothesis drift.

QUESTIONS_PER_WAVE = 7
# Questions per wave: 5 from qwen2.5:7b hypothesis generator + ~2 added by human.
# Matches observed BrickLayer default (generator produces 5 except wave >= 8 → 4).
# Higher values → faster saturation, more redundancy, higher INCONCLUSIVE rate.

SIMULATION_SEED = 42
# RNG seed for reproducibility across runs. Change to test distribution variance.

# --- Agent fleet quality ---
AGENT_SPECIALIZATION_RATIO = 0.65
# Fraction of questions that have a matching specialist agent.
# 0.0 = all questions fall back to the generalist (fix-agent, probe-runner).
# 1.0 = every question has a purpose-built agent.
# Recall campaign average over 36 waves: ~65% had a specialist, ~35% fell back.
# Forge fills gaps over time — this parameter represents the fleet state at run start.

# --- Domain parameters ---
DOMAIN_NOVELTY = 0.35
# How far outside the agent fleet's training the questions push (0.0–1.0).
# 0.0 = well-covered ground (SQL injection, N+1 queries, known FastAPI patterns).
# 1.0 = frontier territory (emergent multi-service failure modes, new architecture).
# High novelty → higher confident-but-wrong verdict rate ("hallucination cliff").

# --- Hypothesis generator (qwen2.5:7b) ---
HYPOTHESIS_TEMPERATURE = 0.30
# LLM temperature for next-wave question generation. Matches actual bl/hypothesis.py.
# 0.0–0.50: well-formed questions, moderate novelty.
# 0.50–0.80: more creative questions, increasing malformed/duplicate rate.
# 0.80–1.00: high novelty, high malformed rate, circular reasoning risk.

# --- Quality assurance ---
PEER_REVIEW_RATE = 1.00
# Fraction of questions that receive a peer-review pass.
# 1.0 matches actual code: peer-reviewer is spawned after every question.
# In practice, async spawn means some reviews lag — set to 0.85 to model that.

# --- Recalibrations from Q6.1 / Q6.7 (applied as overrides in simulate.py) ---
# Change 1: PEER_REVIEW_CORRECTION_RATE recalibrated 0.55 → 0.40 (Q6.1)
RECALIBRATED_PEER_REVIEW_CORRECTION_RATE = 0.40

# Change 3: BASE_GENERALIST_ACCURACY recalibrated 0.625 → 0.50 (Q6.7)
RECALIBRATED_BASE_GENERALIST_ACCURACY = 0.50
# (Change 2 — novelty discount formula — is applied directly in _peer_correction())

# --- Fix loop (opt-in: --fix-loop flag in actual BrickLayer) ---
FIX_LOOP_ENABLED = False
# Whether the fix loop is active. When True: FAILURE verdicts trigger a blocking
# repair agent (max 2 attempts, 600s timeout each). Repairs carry regression risk.

FIX_LOOP_REGRESSION_PROBABILITY = 0.08
# Per-fix-attempt probability of the repair introducing a regression elsewhere.
# 8% is the estimated rate from Recall fix-loop data (2 regressions / ~25 fixes).
# Regressions flip a prior HEALTHY question → FAILURE silently (no re-run check).

# =============================================================================
# SIMULATION ENGINE — Do not modify below this line.
# =============================================================================


def _agent_accuracy() -> float:
    """Weighted verdict accuracy from agent fleet composition.

    Uses RECALIBRATED_BASE_GENERALIST_ACCURACY (0.50) instead of the constant
    BASE_GENERALIST_ACCURACY (0.625) per Q6.7 recalibration (Change 3).
    """
    return (
        AGENT_SPECIALIZATION_RATIO * BASE_SPECIALIST_ACCURACY
        + (1.0 - AGENT_SPECIALIZATION_RATIO) * RECALIBRATED_BASE_GENERALIST_ACCURACY
    )


def _novelty_penalty() -> float:
    """Accuracy multiplier applied by domain novelty.

    At high novelty, agents operate outside their training distribution and
    produce confident-but-wrong verdicts. The relationship is nonlinear:
    modest novelty (< 0.3) has minimal effect; above 0.6 the penalty steepens.
    """
    if DOMAIN_NOVELTY <= 0.30:
        return 1.0 - DOMAIN_NOVELTY * 0.10  # shallow: -3% at 0.3
    elif DOMAIN_NOVELTY <= 0.60:
        return 0.97 - (DOMAIN_NOVELTY - 0.30) * 0.35  # medium: -0.97 to -0.865
    else:
        return 0.865 - (DOMAIN_NOVELTY - 0.60) * 0.55  # steep: falls to 0.645 at 1.0


def _question_validity() -> float:
    """Fraction of hypothesis-generated questions that are well-formed and runnable.

    At temperature <= 0.50 (BrickLayer default of 0.30), the qwen2.5:7b model
    reliably produces valid question blocks. Above 0.50, malformed structure,
    duplicate IDs, and circular hypothesis-test pairs increase.
    """
    if HYPOTHESIS_TEMPERATURE <= 0.50:
        return 1.0
    return max(0.50, 1.0 - (HYPOTHESIS_TEMPERATURE - 0.50) * 0.50)


def _wave_uniqueness(wave: int) -> float:
    """Fraction of wave's questions that probe unexplored failure space.

    Decays each wave as coverage saturates. The rate accelerates when more
    questions are run per wave (more ground covered per iteration).
    Floor of 0.10: there is always some residual novelty even in late waves
    (emergent failure modes, environment drift, new dependencies).
    """
    saturation = WAVE_SATURATION_RATE * (QUESTIONS_PER_WAVE / 7.0)
    return max(0.10, 1.0 - (wave - 1) * saturation)


def _peer_correction(drift_rate: float) -> float:
    """Yield improvement from peer-reviewer catching drifted verdicts.

    Not all drifted verdicts are correctable. Critically: the peer-reviewer
    operates in the same domain as the primary agent. At high novelty, it faces
    the same training-distribution blindspot — it confirms wrong verdicts rather
    than overriding them. This novelty discount captures that effect.

    At DOMAIN_NOVELTY=0.0:  full correction rate applies
    At DOMAIN_NOVELTY=0.90: correction rate discounted to ~19% of nominal

    Recalibrations applied (Q6.1/Q6.7):
      Change 1: RECALIBRATED_PEER_REVIEW_CORRECTION_RATE = 0.40 (was 0.55)
      Change 2: novelty_discount = max(0.05, 1.0 - DOMAIN_NOVELTY * 0.90) (was max(0.20, 1-DN*0.60))
    """
    novelty_discount = max(0.05, 1.0 - DOMAIN_NOVELTY * 0.90)
    return (
        PEER_REVIEW_RATE
        * drift_rate
        * RECALIBRATED_PEER_REVIEW_CORRECTION_RATE
        * novelty_discount
    )


def run_simulation() -> tuple[list[dict], dict]:
    """Run the campaign quality simulation wave by wave.

    Returns:
        records: per-wave diagnostic data
        totals: aggregate counts for evaluate()
    """
    rng = random.Random(SIMULATION_SEED)

    base_accuracy = _agent_accuracy()
    novelty_mult = _novelty_penalty()
    q_validity = _question_validity()

    # Net accuracy after novelty penalty
    accuracy = base_accuracy * novelty_mult
    # Drift: fraction of verdicts that are wrong (before peer correction)
    drift_rate = 1.0 - accuracy
    # Effective accuracy after peer review correction
    effective_accuracy = accuracy + _peer_correction(drift_rate)
    effective_accuracy = min(effective_accuracy, 0.98)  # cap: peer review isn't perfect

    records = []
    total_questions = 0
    total_actionable = 0
    fix_attempts = 0
    fix_regressions = 0

    for wave in range(1, WAVE_COUNT + 1):
        uniqueness = _wave_uniqueness(wave)

        wave_questions = 0
        wave_actionable = 0
        wave_malformed = 0

        for _ in range(QUESTIONS_PER_WAVE):
            total_questions += 1
            wave_questions += 1

            # Gate 1: Is this question well-formed?
            if rng.random() > q_validity:
                wave_malformed += 1
                # Malformed → INCONCLUSIVE. Counts as a question run, adds no signal.
                continue

            # Gate 2: Is this question novel (unexplored territory)?
            is_novel = rng.random() < uniqueness

            # Gate 3: Does the agent produce a trustworthy verdict?
            is_accurate = rng.random() < effective_accuracy

            # A finding is actionable only if both gates pass.
            if is_novel and is_accurate:
                wave_actionable += 1
                total_actionable += 1

        # Fix loop: fires on questions that found real failures.
        # Model: some fraction of actionable findings are FAILUREs that trigger
        # a fix attempt. Regressions reduce total_actionable (a prior HEALTHY
        # question silently flips back to FAILURE with no re-run).
        if FIX_LOOP_ENABLED and wave_actionable > 0:
            # Estimate FAILURE-type findings as ~30% of actionable (empirical Recall rate)
            estimated_failures = max(1, int(wave_actionable * 0.30))
            for _ in range(estimated_failures):
                for attempt in range(2):  # max 2 attempts per fix
                    fix_attempts += 1
                    if rng.random() < FIX_LOOP_REGRESSION_PROBABILITY:
                        # Regression: a previously-HEALTHY finding is now wrong
                        fix_regressions += 1
                        total_actionable = max(0, total_actionable - 1)
                    else:
                        break  # fix succeeded, no regression

        wave_yield = wave_actionable / wave_questions if wave_questions > 0 else 0.0

        records.append(
            {
                "wave": wave,
                "questions": wave_questions,
                "actionable": wave_actionable,
                "malformed": wave_malformed,
                "wave_yield": round(wave_yield, 3),
                "uniqueness": round(uniqueness, 3),
                "effective_accuracy": round(effective_accuracy, 3),
            }
        )

    fix_regression_rate = fix_regressions / fix_attempts if fix_attempts > 0 else 0.0

    totals = {
        "total_questions": total_questions,
        "total_actionable": total_actionable,
        "fix_regression_rate": round(fix_regression_rate, 3),
    }
    return records, totals


def _synthesis_coherence(records: list[dict]) -> float:
    """Model synthesis coherence across waves.

    Coherence measures how much of the final synthesis is novel content vs.
    rephrasing of prior waves. It decays as wave_yield drops and redundancy
    pressure increases. A coherence below SYNTHESIS_COHERENCE_FAILURE means
    the synthesizer's STOP/PIVOT/CONTINUE recommendation is based on
    saturated signal — it may recommend STOP prematurely.

    Model: coherence_wave_N = wave_yield_N * max(0.30, 1.0 - (N-1) * 0.12)
    The 0.12 per-wave redundancy pressure is calibrated to produce ~50% coherence
    at wave 4 under nominal yield — consistent with synthesis notes.
    """
    if not records:
        return 0.0
    total = sum(
        r["wave_yield"] * max(0.30, 1.0 - (r["wave"] - 1) * 0.12) for r in records
    )
    return round(total / len(records), 3)


def evaluate(records: list[dict], totals: dict) -> dict:
    total_questions = totals["total_questions"]
    total_actionable = totals["total_actionable"]
    fix_regression_rate = totals["fix_regression_rate"]

    campaign_yield = total_actionable / total_questions if total_questions > 0 else 0.0
    synthesis_coherence = _synthesis_coherence(records)
    wave_yields = [r["wave_yield"] for r in records]
    wave_novelty_floor = min(wave_yields) if wave_yields else 0.0

    verdict = "HEALTHY"
    reasons = []

    # Primary gate: campaign yield
    if campaign_yield < CAMPAIGN_YIELD_FAILURE:
        reasons.append(
            f"Campaign yield {campaign_yield:.3f} < {CAMPAIGN_YIELD_FAILURE} failure threshold"
        )
        verdict = "FAILURE"
    elif campaign_yield < CAMPAIGN_YIELD_WARNING:
        reasons.append(
            f"Campaign yield {campaign_yield:.3f} < {CAMPAIGN_YIELD_WARNING} warning threshold"
        )
        verdict = "WARNING"

    # Secondary gate: synthesis coherence
    if synthesis_coherence < SYNTHESIS_COHERENCE_FAILURE:
        reasons.append(
            f"Synthesis coherence {synthesis_coherence:.3f} < {SYNTHESIS_COHERENCE_FAILURE}"
            f" — synthesizer is rephrasing, not advancing"
        )
        if verdict == "HEALTHY":
            verdict = "WARNING"

    # Secondary gate: wave novelty floor
    if wave_novelty_floor < WAVE_NOVELTY_FLOOR_FAILURE:
        reasons.append(
            f"Wave novelty floor {wave_novelty_floor:.3f} < {WAVE_NOVELTY_FLOOR_FAILURE}"
            f" — at least one wave fully saturated"
        )
        if verdict == "HEALTHY":
            verdict = "WARNING"

    # Secondary gate: fix loop regressions (only meaningful when fix loop active)
    if FIX_LOOP_ENABLED and fix_regression_rate > FIX_REGRESSION_FAILURE:
        reasons.append(
            f"Fix regression rate {fix_regression_rate:.3f} > {FIX_REGRESSION_FAILURE}"
            f" — fix loop is net-negative"
        )
        if verdict == "HEALTHY":
            verdict = "WARNING"

    return {
        "primary_metric": round(campaign_yield, 3),
        "synthesis_coherence": round(synthesis_coherence, 3),
        "fix_regression_rate": round(fix_regression_rate, 3),
        "wave_novelty_floor": round(wave_novelty_floor, 3),
        "total_questions": total_questions,
        "total_actionable": total_actionable,
        "verdict": verdict,
        "failure_reason": "; ".join(reasons) if reasons else "NONE",
    }


if __name__ == "__main__":
    print(f"Simulation -- {SCENARIO_NAME}")
    print(
        f"Parameters: {WAVE_COUNT} waves x {QUESTIONS_PER_WAVE} q/wave"
        f" = {WAVE_COUNT * QUESTIONS_PER_WAVE} total questions"
    )
    print(f"  Agent specialization:  {AGENT_SPECIALIZATION_RATIO:.0%}")
    print(f"  Domain novelty:        {DOMAIN_NOVELTY:.0%}")
    print(f"  Hypothesis temp:       {HYPOTHESIS_TEMPERATURE}")
    print(f"  Peer review rate:      {PEER_REVIEW_RATE:.0%}")
    print(f"  Fix loop:              {'enabled' if FIX_LOOP_ENABLED else 'disabled'}")
    print("---")

    records, totals = run_simulation()
    results = evaluate(records, totals)

    for key, val in results.items():
        print(f"{key}: {val}")

    print("---")
    print("Wave-by-wave breakdown:")
    for r in records:
        bar_len = int(r["wave_yield"] * 20)
        bar = "#" * bar_len + "." * (20 - bar_len)
        malformed_note = f", {r['malformed']} malformed" if r["malformed"] else ""
        print(
            f"  Wave {r['wave']}: yield={r['wave_yield']:.3f} [{bar}]"
            f"  ({r['actionable']}/{r['questions']} actionable"
            f"{malformed_note}"
            f", uniqueness={r['uniqueness']:.2f}"
            f", accuracy={r['effective_accuracy']:.2f})"
        )
