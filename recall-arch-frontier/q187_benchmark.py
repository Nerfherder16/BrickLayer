"""Q187: Cross-Cluster CO_RETRIEVED Edge Formation and Lifecycle"""

# Parameters from project
N = 22423
K = 200
k_retrieval = 5
gamma = 0.95
delta = 0.05
bootstrap_weight = 0.1

cluster_size = N // K  # ~112 per cluster

print("=== Q187: Cross-Cluster CO_RETRIEVED Edge Formation ===")
print(f"N={N}, K={K}, cluster_size~={cluster_size}")
print(f"k_retrieval={k_retrieval} per session")
print()

# Intra-cluster pairs
intra_pairs_per_cluster = cluster_size * (cluster_size - 1) // 2
total_intra_pairs = K * intra_pairs_per_cluster
print(f"Intra-cluster pairs per cluster: {intra_pairs_per_cluster:,}")
print(f"Total intra-cluster pairs (bootstrap edges): {total_intra_pairs:,}")
print()

# Cross-cluster edge formation probability
p_all_same_cluster = K * (cluster_size / N) ** k_retrieval
p_at_least_one_cross = 1 - p_all_same_cluster
print(f"P(all k retrievals from same cluster): {p_all_same_cluster:.6f}")
print(f"P(at least one cross-cluster pair in session): {p_at_least_one_cross:.6f}")
print()

# Expected cross-cluster pairs per session
total_pairs_per_session = k_retrieval * (k_retrieval - 1) // 2
p_intra_pair = (cluster_size - 1) / (N - 1)
e_intra_pairs = total_pairs_per_session * p_intra_pair
e_cross_pairs = total_pairs_per_session - e_intra_pairs

print(f"Total pairs per session (k=5): {total_pairs_per_session}")
print(f"P(same cluster for any pair): {p_intra_pair:.4f} (= 1/K = {1 / K:.4f})")
print(f"E[intra-cluster pairs per session]: {e_intra_pairs:.4f}")
print(f"E[cross-cluster pairs per session]: {e_cross_pairs:.4f}")
print()

# Cross vs intra totals
total_cross_pairs = (N * (N - 1) // 2) - total_intra_pairs
print(f"Total cross-cluster pairs: {total_cross_pairs:,}")
print(f"Total intra-cluster pairs: {total_intra_pairs:,}")
print(f"Ratio cross:intra pairs = {total_cross_pairs / total_intra_pairs:.1f}:1")
print()

e_sessions_to_first_credit = total_cross_pairs / e_cross_pairs
print(
    f"E[sessions to first credit on specific cross pair]: {e_sessions_to_first_credit:.0f}"
)
print()

# Steady-state weight comparison
sessions_per_week = 7
cross_k_per_week = (e_cross_pairs / total_cross_pairs) * sessions_per_week
intra_k_per_week = (e_intra_pairs / total_intra_pairs) * sessions_per_week

print("=== Steady-State Weight Comparison ===")
print(f"E[cross-cluster retrievals per pair per week]: {cross_k_per_week:.2e}")
print(f"E[intra-cluster retrievals per pair per week]: {intra_k_per_week:.2e}")
w_ss_cross = 20 * delta * cross_k_per_week
w_ss_intra = 20 * delta * intra_k_per_week
print(f"Cross-cluster w_ss (organic uniform): {w_ss_cross:.6f}")
print(f"Intra-cluster w_ss (organic uniform only): {w_ss_intra:.6f}")
print(f"Bootstrap contribution to intra weight: {bootstrap_weight}")
print()

# Time to exceed noise floor
noise_floor = 0.005  # 1/K=200
print("=== Time to Noise Floor ===")
print("Cross-cluster edges start at w=0 (no bootstrap)")
sessions_to_nf = noise_floor / delta
print(f"Sessions to noise floor if credited every session: {sessions_to_nf:.0f}")
print(
    f"  At 7/week: {sessions_to_nf / 7:.1f} weeks = {sessions_to_nf / 7 / 52:.1f} years"
)
print()
print(
    f"Intra-cluster edges start at w={bootstrap_weight} ({bootstrap_weight / noise_floor:.1f}x noise floor at creation)"
)
print()

# Organic cross-cluster edge weight after 1000 sessions
avg_credits_in_1000 = 1000 * (e_cross_pairs / total_cross_pairs)
avg_weight_1000 = delta * avg_credits_in_1000
print("=== Organic Cross-Cluster Edge Weight After 1000 Sessions ===")
print(f"Expected credits on specific pair: {avg_credits_in_1000:.6f}")
print(f"Expected weight (no decay): {avg_weight_1000:.2e}")
print(f"Noise floor: {noise_floor:.4f}")
print(f"Ratio weight/noise_floor: {avg_weight_1000 / noise_floor:.2e}")
print()
print(
    "VERDICT: Organically-formed cross-cluster edges NEVER approach noise floor under uniform retrieval."
)
print()

# Topic-concentrated sessions
print("=== Topic-Concentrated Sessions (Tim retrieves 3 clusters per session) ===")
# If Tim fetches k=5 across 3 clusters (2+2+1 split), cross pairs = 2*2 + 2*1 + 2*1 = 8
# Simpler: k=5 from 2 clusters means 3+2 split -> cross pairs = 3*2 = 6
cross_concentrated_1 = 3 * 2  # 3+2 split across 2 clusters
print(f"2-cluster session (3+2 split): {cross_concentrated_1} cross pairs per session")
w_after_100_sessions_2c = cross_concentrated_1 * delta * 100
print(f"  Weight after 100 sessions (no decay): {w_after_100_sessions_2c:.3f}")

# Decay equilibrium: w_ss = delta * cross_pairs_per_session / (1-gamma) = delta * 6 / 0.05 = 6.0
# (per session, not per week -- assuming daily sessions)
w_ss_concentrated = delta * cross_concentrated_1 / (1 - gamma)
print(f"  Steady-state (daily sessions): {w_ss_concentrated:.1f}")
print(f"  Ratio to intra-cluster w_ss=1.0: {w_ss_concentrated:.1f}x")
print()

# Bootstrap asymmetry: how long before a cross-cluster edge matches bootstrap intra weight?
sessions_to_match_bootstrap = bootstrap_weight / (cross_concentrated_1 * delta)
print(
    f"Sessions to match bootstrap weight (concentrated): {sessions_to_match_bootstrap:.0f}"
)
print()

# Decay schedule for cross-cluster (if they form)
print("=== Decay Schedule for Cross-Cluster Edges (if formed at w=0.5) ===")
w0_cross = 0.5  # formed by 10 concentrated sessions
print(f"Starting weight: {w0_cross}")
for week in [1, 5, 10, 20, 35, 58, 70, 90]:
    w = w0_cross * (gamma**week)
    above_nf = "above noise floor" if w > noise_floor else "BELOW noise floor"
    print(f"  Week {week:3d}: w={w:.5f}  ({above_nf})")

print()
print("=== Summary: Does Cross-Cluster Decay Need Separate Policy? ===")
print(
    "Uniform retrieval: cross-cluster edges NEVER form (expected weight after 1000 sessions << noise floor)"
)
print(
    "Concentrated retrieval (same-topic sessions): cross-cluster edges CAN form at same rate as intra"
)
print(
    "Once formed, cross-cluster edges follow IDENTICAL decay schedule (same gamma=0.95)"
)
print("Same noise floor (0.005) applies: no separate decay policy needed")
print(
    "The Q183 noise-floor threshold (0.005) correctly gates out decayed cross-cluster edges"
)
print()
print(
    "KEY FINDING: Cross-cluster edges are retrieval-pattern-dependent, not architecture-dependent."
)
print("They form when Tim's sessions span topic clusters (cross-domain queries).")
print(
    "They are governed by the same dynamics as intra-cluster edges -- no special treatment needed."
)
