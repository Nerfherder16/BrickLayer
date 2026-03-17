import sys
import math

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

# ============================================================
# Q251: UserPromptSubmit Convergence Point Latency Model
# ============================================================
# Four operations at UserPromptSubmit (before memory injection):
# Op1: Q244 watermark check — LMDB lookup for session_compacted key
# Op2: Q249 WAL sync check — check if remote events exist since sync_base
# Op3: Q235 activation update — propagate K new memories' activation
# Op4: Q231+Q247 hybrid retrieval — Tantivy BM25 + HNSW + RRF + LMDB fetch

rng = np.random.default_rng(42)
N_SAMPLES = 100_000


def lognormal_samples(mean_ms, cv, n=N_SAMPLES):
    sigma = math.sqrt(math.log(1 + cv**2))
    mu = math.log(mean_ms) - sigma**2 / 2
    return rng.lognormal(mu, sigma, n)


# --- Operation parameters (mean_ms, CV) ---
# Based on Q242, Q247 and LMDB benchmarks

ops = {
    # Op1: session_compacted LMDB key lookup (O(1), memory-mapped)
    # Only needed if previous session did not run Stop hook (rare: ~5%)
    # Fast path: single LMDB key read
    "op1_watermark_check": dict(
        mean=0.1,
        cv=0.30,
        always=True,
        # If NOT compacted, must run compaction from WAL: extra 2-5ms async
        conditional_mean=3.0,
        conditional_cv=0.40,
        conditional_prob=0.05,  # 5% of sessions miss the Stop hook
    ),
    # Op2: WAL sync check — check if remote machine has new events
    # Single LMDB read for last_sync_base, then network check (Tailscale)
    # Fast path (no new events): LMDB read only
    # Slow path (new events): apply fast-forward merge (~1ms per event, typ 5-20 events)
    "op2_wal_sync_check": dict(
        mean=0.5,
        cv=0.40,
        always=True,
        # If fast-forward merge needed (typ. new events): apply them
        conditional_mean=8.0,  # 5-20 events * 0.5ms/event avg
        conditional_cv=0.50,
        conditional_prob=0.20,  # 20% of prompts have new remote events
    ),
    # Op3: spreading activation update (Q235)
    # For each new memory stored in this session (avg ~2 per session):
    # Look up its CO_RETRIEVED neighbors, increment activation counters
    # Avg degree=34 at 22K corpus, but only need 1-hop, K=10 neighbors
    # Per memory: LMDB read (neighbors list) + LMDB write batch (10 updates)
    "op3_activation_update": dict(
        mean=0.5,
        cv=0.30,
        always=True,
        # This is always run (no conditional path), activation update is
        # bounded by number of new memories (typically 0-3 per session start)
    ),
    # Op4: Q247 hybrid retrieval (HNSW + Tantivy + RRF + LMDB fetch)
    # From Q247: HNSW 0.6ms + Tantivy 1.5ms + RRF 0.05ms + LMDB 0.2ms
    # Plus embedding: fastembed-rs INT8 BGE-small ~10ms
    "op4_embedding": dict(mean=10.0, cv=0.15, always=True),
    "op4_hnsw": dict(mean=0.6, cv=0.10, always=True),
    "op4_tantivy": dict(mean=1.5, cv=0.20, always=True),
    "op4_rrf_lmdb": dict(mean=0.25, cv=0.20, always=True),
}

# Sample all operations
samples = {}
for name, params in ops.items():
    base = lognormal_samples(params["mean"], params["cv"])
    if "conditional_prob" in params:
        # Add conditional overhead for the slow path
        cond_mask = rng.random(N_SAMPLES) < params["conditional_prob"]
        slow = lognormal_samples(params["conditional_mean"], params["conditional_cv"])
        samples[name] = base + cond_mask * slow
    else:
        samples[name] = base

# Total latency per sample
total = (
    samples["op1_watermark_check"]
    + samples["op2_wal_sync_check"]
    + samples["op3_activation_update"]
    + samples["op4_embedding"]
    + samples["op4_hnsw"]
    + samples["op4_tantivy"]
    + samples["op4_rrf_lmdb"]
)

# Compute percentiles
pcts = [50, 90, 95, 99, 99.9]
print("UserPromptSubmit Convergence Point Latency Model")
print("=" * 55)
print()
print("Per-operation breakdown (mean, p95):")
for name, samp in samples.items():
    print(
        f"  {name:<35} mean={np.mean(samp):>6.2f}ms  p95={np.percentile(samp, 95):>6.2f}ms"
    )
print()
print("Total latency distribution:")
for p in pcts:
    val = np.percentile(total, p)
    breach = "(SLA BREACH)" if val > 500 else ""
    print(f"  P{p:<5} = {val:>7.2f}ms  {breach}")
print(f"  Mean   = {np.mean(total):>7.2f}ms")
print(f"  SLA breaches (>500ms): {np.sum(total > 500) / N_SAMPLES * 100:.4f}%")
print()

# --- Scenario 2: Async offloading ---
# What if Op1 (watermark check result) and Op2 (WAL sync, new events case)
# are handled AFTER the synchronous response path?
# Sync path: Op1 check only (fast LMDB read, no conditional) + Op3 + Op4
# Async: compaction runs later, WAL merge applied before next prompt

# Sync path: only the fast-path components
sync_only = (
    lognormal_samples(0.1, 0.30)  # Op1 fast path (check only)
    + lognormal_samples(0.1, 0.30)  # Op2 fast path (check only)
    + samples["op3_activation_update"]
    + samples["op4_embedding"]
    + samples["op4_hnsw"]
    + samples["op4_tantivy"]
    + samples["op4_rrf_lmdb"]
)

print("Async offloading scenario (compaction + WAL merge async):")
print("Sync path: watermark check + WAL check + activation update + hybrid retrieval")
for p in pcts:
    val = np.percentile(sync_only, p)
    print(f"  P{p:<5} = {val:>7.2f}ms")
print(f"  Mean   = {np.mean(sync_only):>7.2f}ms")
print()

# --- Comparison table ---
print(
    "Comparison: HNSW-only vs. Hybrid vs. Full Convergence vs. Full Convergence Async"
)
for label, arr in [
    (
        "HNSW-only (no convergence)",
        samples["op4_embedding"] + samples["op4_hnsw"] + lognormal_samples(0.2, 0.2),
    ),
    (
        "Hybrid retrieval only (Q247)",
        samples["op4_embedding"]
        + samples["op4_hnsw"]
        + samples["op4_tantivy"]
        + samples["op4_rrf_lmdb"],
    ),
    ("Full convergence (all ops sync)", total),
    ("Full convergence (async offload)", sync_only),
]:
    print(
        f"  {label:<45} p50={np.percentile(arr, 50):>5.1f}ms  p95={np.percentile(arr, 95):>5.1f}ms  p99={np.percentile(arr, 99):>5.1f}ms"
    )
print()

# --- Hot path vs async assignment ---
print("Hot path vs. async assignment:")
print("  HOT PATH (synchronous, before injection):")
print("    - Op1 watermark CHECK (0.1ms) — just read the LMDB key")
print("    - Op2 WAL sync CHECK (0.1ms) — just read sync_base, compare")
print("    - Op3 activation update (0.5ms) — always fast, bounded")
print("    - Op4 hybrid retrieval (12.4ms mean) — required before injection")
print()
print("  ASYNC (after acknowledgement or background):")
print("    - Op1 COMPACTION if missed (3ms) — only 5% of prompts, background")
print("    - Op2 WAL MERGE if new events (8ms) — 20% of prompts, before next prompt")
print()

total_hot = (
    lognormal_samples(0.1, 0.30)  # Op1 check
    + lognormal_samples(0.1, 0.30)  # Op2 check
    + samples["op3_activation_update"]
    + samples["op4_embedding"]
    + samples["op4_hnsw"]
    + samples["op4_tantivy"]
    + samples["op4_rrf_lmdb"]
)
print(
    f"  Hot path total: mean={np.mean(total_hot):.2f}ms  p95={np.percentile(total_hot, 95):.2f}ms  p99={np.percentile(total_hot, 99):.2f}ms"
)
print(
    f"  SLA headroom: 500ms - {np.percentile(total_hot, 95):.1f}ms = {500 - np.percentile(total_hot, 95):.1f}ms ({(500 / np.percentile(total_hot, 95)):.1f}x)"
)
