import sys
import math

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

N = 22_000
K = 10
N_CLUSTERS = 100
CLUSTER_SIZE = N // N_CLUSTERS  # 220
INTRA_P = 0.80

rng = np.random.default_rng(42)
cluster_id = np.repeat(np.arange(N_CLUSTERS), CLUSTER_SIZE)

# --- Analytical: uniform retrieval ---
p_pair_uniform = K * (K - 1) / (N * (N - 1))


def sessions_for_degree(target_deg):
    val = 1 - target_deg / (N - 1)
    if val <= 0:
        return float("inf")
    return -math.log(val) / p_pair_uniform


print("Analytical (uniform retrieval):")
for d in [1, 3, 5, 10]:
    print(f"  avg_degree={d}: {sessions_for_degree(d):.0f} sessions")
print(f"  Giant component (avg_degree>1): {sessions_for_degree(1):.0f} sessions")
print()


# --- Simulation: clustered retrieval ---
def one_session_retrievals():
    focal = int(rng.integers(N_CLUSTERS))
    k_intra = round(K * INTRA_P)
    k_cross = K - k_intra
    intra_start = focal * CLUSTER_SIZE
    intra_ids = rng.choice(
        np.arange(intra_start, intra_start + CLUSTER_SIZE), size=k_intra, replace=False
    )
    others = np.concatenate(
        [np.arange(intra_start), np.arange(intra_start + CLUSTER_SIZE, N)]
    )
    cross_ids = rng.choice(others, size=k_cross, replace=False)
    return np.concatenate([intra_ids, cross_ids])


n_samples = 2000
# Sample pairs: half intra, half inter
sampled_pairs = []
pair_labels = []  # 'intra' or 'inter'
for _ in range(n_samples // 2):
    c = int(rng.integers(N_CLUSTERS))
    start = c * CLUSTER_SIZE
    i, j = rng.choice(np.arange(start, start + CLUSTER_SIZE), size=2, replace=False)
    sampled_pairs.append((int(i), int(j)))
    pair_labels.append("intra")
for _ in range(n_samples // 2):
    c1, c2 = rng.choice(N_CLUSTERS, size=2, replace=False)
    i = int(rng.integers(c1 * CLUSTER_SIZE, (c1 + 1) * CLUSTER_SIZE))
    j = int(rng.integers(c2 * CLUSTER_SIZE, (c2 + 1) * CLUSTER_SIZE))
    sampled_pairs.append((i, j))
    pair_labels.append("inter")

pair_co_counts = np.zeros(n_samples, dtype=np.int32)
checkpoints = [50, 100, 250, 500, 1000, 2000, 5000, 10000]
cp_idx = 0
results = {}

print("Clustered retrieval simulation (INTRA_P=0.80, K=10, N=22000, 100 clusters):")
print(
    f"{'Sessions':>10} | {'AvgDeg':>8} | {'IntraDeg':>9} | {'InterDeg':>9} | {'SNR':>7} | {'Baseline':>8} | {'Lift':>6}"
)
print("-" * 75)

baseline_snr = (CLUSTER_SIZE - 1) / (N - 1)

for s in range(1, max(checkpoints) + 1):
    retrieved = one_session_retrievals()
    retrieved_set = set(int(x) for x in retrieved)
    for pidx, (i, j) in enumerate(sampled_pairs):
        if i in retrieved_set and j in retrieved_set:
            pair_co_counts[pidx] += 1

    if cp_idx < len(checkpoints) and s == checkpoints[cp_idx]:
        intra_ep = float(np.sum(pair_co_counts[: n_samples // 2] > 0)) / (
            n_samples // 2
        )
        inter_ep = float(np.sum(pair_co_counts[n_samples // 2 :] > 0)) / (
            n_samples // 2
        )
        intra_deg = intra_ep * (CLUSTER_SIZE - 1)
        inter_deg = inter_ep * (N - CLUSTER_SIZE)
        total_deg = intra_deg + inter_deg
        snr = intra_deg / total_deg if total_deg > 0 else 0
        lift = snr / baseline_snr if baseline_snr > 0 else 0
        results[s] = dict(
            total_deg=total_deg,
            intra_deg=intra_deg,
            inter_deg=inter_deg,
            snr=snr,
            lift=lift,
        )
        print(
            f"{s:>10} | {total_deg:>8.3f} | {intra_deg:>9.3f} | {inter_deg:>9.3f} | {snr:>7.4f} | {baseline_snr:>8.4f} | {lift:>6.1f}x"
        )
        cp_idx += 1

print()
print(f"Baseline SNR (random): {baseline_snr:.4f} ({baseline_snr * 100:.1f}%)")
print()

# Cold-start threshold: avg_degree >= 1 AND SNR > 2x baseline
print("Cold-start analysis:")
for S, r in results.items():
    if r["total_deg"] >= 1.0 and r["snr"] > 2 * baseline_snr:
        print(f"  First viable spreading activation: S={S} sessions")
        print(
            f"    avg_degree={r['total_deg']:.2f}, SNR={r['snr']:.4f}, lift={r['lift']:.1f}x baseline"
        )
        break
else:
    print("  No threshold crossed in simulation range")

# Extrapolate to 22K corpus build sessions
print()
print("22K corpus build estimate:")
print(f"  If avg 5 memories stored per session: {N // 5} sessions to fill corpus")
print("  If avg 10 queries per session: retrieval sessions drive density faster")

# For real Recall: each session has multiple queries (many UserPromptSubmits)
# Estimate 3-5 UserPromptSubmits per session = 3-5 retrieval events = 3-5 sets of K co-retrievals
queries_per_session = 4
effective_sessions_per_calendar_session = queries_per_session
print(
    f"  With {queries_per_session} queries/calendar-session: effective density sessions = actual_sessions x {queries_per_session}"
)

# Find closest result to N//5 effective sessions
target_eff = N // 5  # 4400
closest = min(results.keys(), key=lambda x: abs(x - target_eff))
r = results[closest]
print(f"  At S={closest} (proxy for {target_eff} effective sessions):")
print(f"    avg_degree={r['total_deg']:.2f}, SNR={r['snr']:.4f}, lift={r['lift']:.1f}x")
