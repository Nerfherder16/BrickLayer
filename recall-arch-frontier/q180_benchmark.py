"""Q180: SimHash Calibration — Theoretical Calibration Curves via Hyperplane Projection

No live Qdrant required. Uses analytical SimHash probability model:
  P(bit_agree | cosine) = 1 - arccos(cosine) / pi
  P(Hamming <= k | cosine, n_bits=64) = Binomial CDF
"""

import math
from scipy.stats import binom

N_BITS = 64
N_MEMORIES = 22_423

# Assume 1-3% near-duplicate rate (from Q152/Q160)
dup_rate_low = 0.01
dup_rate_high = 0.03
n_dup_low = int(N_MEMORIES * dup_rate_low)
n_dup_high = int(N_MEMORIES * dup_rate_high)

print("=== Q180: SimHash Calibration — Theoretical Model ===")
print(f"n_bits={N_BITS}, N_memories={N_MEMORIES:,}")
print(
    f"Near-duplicate rate: {dup_rate_low:.0%}-{dup_rate_high:.0%} -> "
    f"{n_dup_low}-{n_dup_high} near-dup memories"
)
print()


def expected_hamming(cosine_sim: float, n_bits: int = 64) -> float:
    """Expected Hamming distance given cosine similarity."""
    p_disagree = math.acos(cosine_sim) / math.pi
    return n_bits * p_disagree


def p_hamming_leq(cosine_sim: float, threshold: int, n_bits: int = 64) -> float:
    """P(Hamming distance <= threshold | cosine similarity) using Binomial CDF."""
    p_disagree = math.acos(cosine_sim) / math.pi
    return binom.cdf(threshold, n_bits, p_disagree)


# Representative cosine similarities for different pair types
cosine_cases = {
    "identical (copy)": 1.000,
    "near-duplicate (wording variant)": 0.980,
    "high-similarity (same topic)": 0.950,
    "related (same domain)": 0.900,
    "moderate (different aspects)": 0.850,
    "low (different topics)": 0.750,
    "unrelated": 0.600,
}

thresholds = [4, 6, 8, 10, 12]

print("--- Expected Hamming Distance by Cosine Similarity ---")
for label, cos in cosine_cases.items():
    if cos >= 1.0:
        e_h = 0.0
    else:
        e_h = expected_hamming(cos)
    print(f"  cos={cos:.3f} ({label}): E[Hamming] = {e_h:.1f} bits")
print()

print("--- P(Hamming <= threshold) = Detection Rate ---")
header = f"{'Cosine':>6}  {'Label':<35}"
for t in thresholds:
    header += f"  H<={t:2d}"
print(header)
print("-" * len(header))

for label, cos in cosine_cases.items():
    row = f"{cos:>6.3f}  {label:<35}"
    for t in thresholds:
        if cos >= 1.0:
            p = 1.0
        else:
            p = p_hamming_leq(cos, t)
        row += f"  {p:.3f}"
    print(row)
print()

# ============================================================
# FALSE POSITIVE / FALSE NEGATIVE ANALYSIS
# ============================================================
# Assume:
#   "True near-duplicate" = cosine >= 0.95 (should be caught)
#   "True distinct" = cosine <= 0.85 (should NOT be caught)
#   "Near-duplicate" pair has cosine drawn from N(0.975, 0.015) — wording variants
#   "Distinct" pair has cosine drawn from N(0.80, 0.05) — same rough topic, different content

print("--- False Positive / False Negative at Decision Thresholds ---")
print("  Model: near-dup pairs ~ cosine=0.975, distinct pairs ~ cosine=0.80")
print()

# Use representative single cosine values for each class
cos_neardupe = 0.975  # typical near-duplicate
cos_distinct = 0.80  # typical distinct pair

print(
    f"  Near-duplicate pairs (cos={cos_neardupe}):  E[Hamming]={expected_hamming(cos_neardupe):.1f}"
)
print(
    f"  Distinct pairs (cos={cos_distinct}):         E[Hamming]={expected_hamming(cos_distinct):.1f}"
)
print()

print(
    f"  {'Threshold':>9}  {'Hit Rate (TP rate)':>18}  {'FP Rate':>8}  {'Miss Rate (FN)':>14}  {'Verdict'}"
)
print("  " + "-" * 75)

for t in thresholds:
    tp_rate = p_hamming_leq(cos_neardupe, t)  # P(catch true near-dup)
    fp_rate = p_hamming_leq(cos_distinct, t)  # P(false alarm on distinct pair)
    fn_rate = 1.0 - tp_rate  # P(miss a true near-dup)

    # Score: minimize FP while catching most near-dups
    # Tim's error case: FP hurts (distinct memories collapsed) more than FN (dup stored)
    if fp_rate < 0.01 and tp_rate > 0.70:
        verdict = "OPTIMAL"
    elif fp_rate < 0.05 and tp_rate > 0.85:
        verdict = "good"
    elif fp_rate > 0.10:
        verdict = "too aggressive"
    else:
        verdict = "ok"

    print(
        f"  H <= {t:2d}:      {tp_rate:>8.1%} TP rate    {fp_rate:>7.1%} FP    "
        f"{fn_rate:>7.1%} FN    [{verdict}]"
    )

print()

# ============================================================
# CORPUS-LEVEL PROJECTION
# ============================================================
print("--- Corpus-Level Projection (N=22,423 memories) ---")
# Total pairs = N*(N-1)/2
total_pairs = N_MEMORIES * (N_MEMORIES - 1) // 2
print(f"  Total possible pairs: {total_pairs:,}")

for dup_rate in [dup_rate_low, dup_rate_high]:
    n_dup_pairs = int(
        total_pairs * dup_rate * 0.001
    )  # ~0.01% of pairs are near-dups (not 1% of memories)
    # Note: 1% of memories being near-dups means ~N * 0.01 / 2 duplicate pairs
    n_dup_pairs = int(N_MEMORIES * dup_rate / 2)
    n_distinct = total_pairs - n_dup_pairs
    print(
        f"\n  Near-duplicate rate={dup_rate:.0%}: ~{n_dup_pairs:,} dup pairs, {n_distinct:,} distinct pairs"
    )
    print(
        f"  {'Threshold':>9}  {'True Positives':>14}  {'False Positives':>15}  {'Missed Dups':>11}"
    )
    for t in thresholds:
        tp_rate = p_hamming_leq(cos_neardupe, t)
        fp_rate = p_hamming_leq(cos_distinct, t)
        tp_count = int(n_dup_pairs * tp_rate)
        fp_count = int(n_distinct * fp_rate)
        fn_count = n_dup_pairs - tp_count
        print(
            f"  H <= {t:2d}:      {tp_count:>7,} caught    {fp_count:>10,} false alarms  {fn_count:>6,} missed"
        )

print()

# ============================================================
# RECOMMENDATION
# ============================================================
print("=== RECOMMENDATION ===")
print()
print("Optimal threshold: H <= 6 (Hamming distance <= 6/64 bits)")
print()
print("Rationale:")
print(
    f"  - cos=0.975 (near-dup): E[H]={expected_hamming(0.975):.1f}, P(catch)={p_hamming_leq(0.975, 6):.1%}"
)
print(
    f"  - cos=0.80  (distinct): E[H]={expected_hamming(0.80):.1f}, P(false alarm)={p_hamming_leq(0.80, 6):.2%}"
)
print()
print("Tim's error case: FALSE POSITIVES (merging distinct memories) are worse than")
print("FALSE NEGATIVES (storing a near-duplicate). H<=6 minimizes FP while catching")
print("the clearest near-duplicates (wording variants, copy-paste edits).")
print()
print("Current default (H<=8) analysis:")
print(f"  - cos=0.975 (near-dup): P(catch)={p_hamming_leq(0.975, 8):.1%}")
print(f"  - cos=0.80  (distinct): P(false alarm)={p_hamming_leq(0.80, 8):.2%}")
print()
print(
    "H<=8 is defensible but H<=6 is better for Tim's corpus (diverse developer memories)."
)
print("Recommendation: change default from H<=8 to H<=6.")
