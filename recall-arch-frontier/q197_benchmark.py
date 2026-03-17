"""Q197: Write-Path Latency Floor on N100 CPU

Component-by-component theoretical minimum for Recall 2.0 write path:
SHA-256, SimHash, fastembed-rs embedding, CRDT merge, Hopfield update, LMDB write.
"""

print("=== Q197: Write-Path Latency Floor on N100 CPU ===")
print()

# ============================================================
# HARDWARE PARAMETERS: Intel N100 (Alder Lake-N, 4-core)
# ============================================================
# N100 specs:
#   - 4 cores, no HyperThreading, base 0.8GHz, burst 3.4GHz
#   - L1 cache: 192KB (48KB/core), L2: 2MB total, L3: 6MB
#   - LPDDR5 4800 memory bandwidth: ~38.4 GB/s theoretical
#   - AVX2 supported (256-bit SIMD)
#   - No GPU, no NPU equivalent
#   - TDP: 6W passive cooling
cpu_freq_ghz = 3.4  # burst single-core frequency (GHz)
cpu_freq = cpu_freq_ghz * 1e9
avx2_fp32_ops_per_cycle = 8  # 256-bit / 32-bit = 8 FP32 per SIMD lane
l3_cache_mb = 6
memory_bw_gbs = 38.4

print(
    f"N100: {cpu_freq_ghz}GHz burst, AVX2 ({avx2_fp32_ops_per_cycle} FP32/cycle), "
    f"L3={l3_cache_mb}MB, BW={memory_bw_gbs}GB/s"
)
print()

# ============================================================
# COMPONENT 1: SHA-256 hash check
# ============================================================
# SHA-256 throughput on modern x86 with SHA-NI extensions
# N100 has SHA-NI (Intel SHA extensions): ~4 cycles per byte
# Average memory text = 500 bytes
text_bytes = 500
sha_ni_cycles_per_byte = 4  # SHA-NI instruction throughput
sha_cycles = text_bytes * sha_ni_cycles_per_byte
sha_ns = (sha_cycles / cpu_freq) * 1e9

print("--- Component 1: SHA-256 hash check ---")
print(f"  Input: {text_bytes}B text")
print(f"  SHA-NI: {sha_ni_cycles_per_byte} cycles/byte -> {sha_cycles:,} cycles")
print(f"  Latency: {sha_ns:.3f} ms")
print()

# ============================================================
# COMPONENT 2: SimHash band lookup
# ============================================================
# SimHash: 64 random projections of 1024-dim vector
# Each projection: 1024 FP32 dot products + sign extraction
# With AVX2: 1024/8 = 128 SIMD operations per projection
# 64 projections = 64 * 128 = 8192 SIMD ops
# LMDB lookup for hash band: ~0.05ms (in-memory mmap)
D = 1024
simhash_bits = 64
avx2_ops_per_proj = D / avx2_fp32_ops_per_cycle  # SIMD operations
simhash_total_ops = simhash_bits * avx2_ops_per_proj
# Assume 2 cycles per SIMD op (load + FMA)
simhash_cycles = simhash_total_ops * 2
simhash_compute_ns = (simhash_cycles / cpu_freq) * 1e9
simhash_lmdb_ms = 0.05  # LMDB band table lookup (in-memory)
simhash_total_ms = simhash_compute_ns / 1e6 + simhash_lmdb_ms

print("--- Component 2: SimHash band lookup ---")
print(f"  {simhash_bits} projections x {D}-dim: {simhash_total_ops:.0f} SIMD ops")
print(f"  Compute: {simhash_compute_ns:.3f} ms")
print(f"  LMDB band lookup: {simhash_lmdb_ms:.2f} ms")
print(f"  Total SimHash: {simhash_total_ms:.3f} ms")
print()

# ============================================================
# COMPONENT 3: fastembed-rs ONNX embedding inference
# ============================================================
# BGE-small-en-v1.5: 33M parameters, D=384 output
# N100 with ONNX Runtime CPU execution provider:
# - Model loads once (cached in RAM after first call)
# - Inference: matrix multiplications via MKL/OpenBLAS
# - Key layer: transformer with 12 layers, hidden_dim=384, seq_len~256 tokens
#
# Benchmark data from fastembed-rs README and community reports:
# - BGE-small on M1 Pro: ~25ms/text
# - BGE-small on N100 (equivalent ~0.3x M1 performance): ~80ms/text
# - With ONNX quantized (int8): ~40ms/text on N100
#
# The N100 has AVX2 but single-channel LPDDR5 — memory bandwidth constrained
# ONNX int8 quantized model reduces memory bandwidth pressure

fastembed_full_ms = 80  # FP32 BGE-small on N100 (estimated)
fastembed_int8_ms = 40  # INT8 quantized BGE-small on N100 (estimated)

# FLOP calculation for BGE-small:
# 12 transformer layers, hidden=384, seq_len=256
# Per layer: 4 * seq_len * hidden^2 (attention + FFN, simplified)
# Total: 12 * 4 * 256 * 384^2 = ~2.3 GFLOPS
# N100 AVX2 FP32 peak: 4 cores * 3.4GHz * 8 FP32/cycle * 2 (FMA) = 218 GFLOPS peak
# Realistic efficiency: ~10% (memory bandwidth bound) = 21.8 GFLOPS effective
# Expected latency: 2.3 GFLOPS / 21.8 GFLOPS = 0.105s = 105ms
# With caching effects: ~80ms practical

flops_per_inference = 12 * 4 * 256 * (384**2)  # simplified
n100_peak_gflops = 4 * cpu_freq_ghz * avx2_fp32_ops_per_cycle * 2  # 4 cores, FMA
n100_effective_gflops = n100_peak_gflops * 0.10  # 10% efficiency (memory bound)
flop_estimate_ms = (flops_per_inference / (n100_effective_gflops * 1e9)) * 1e3

print("--- Component 3: fastembed-rs ONNX Embedding Inference ---")
print("  BGE-small-en-v1.5: 33M params, D=384, seq_len=256")
print(f"  Estimated FLOPs: {flops_per_inference / 1e9:.2f} GFLOPS")
print(
    f"  N100 peak: {n100_peak_gflops:.0f} GFLOPS, effective (~10%): {n100_effective_gflops:.1f} GFLOPS"
)
print(f"  FLOP-derived estimate: {flop_estimate_ms:.0f} ms")
print(f"  Practical estimate (FP32): ~{fastembed_full_ms} ms")
print(f"  Practical estimate (INT8 quantized): ~{fastembed_int8_ms} ms")
print()

# ============================================================
# COMPONENT 4: CRDT merge (deduplication check + merge op)
# ============================================================
# CRDT merge for memory content: compare SHA-256 hash + SimHash similarity
# If duplicate detected: update metadata fields (importance max, tags union)
# CRDT merge operation: pure in-memory computation
# Input: existing memory record (~500B) + new memory record (~500B)
# Ops: hash compare (O(1)), importance max (O(1)), tags union (O(n_tags))
# n_tags ~= 5 average

n_tags = 5
# Hash compare: 2 SHA-256 comparisons = 64 byte comparisons
crdt_hash_ns = 64 * 4 / cpu_freq * 1e9  # 4 cycles per byte compare
# Tags union: build new set = O(n_tags) hash set operations
crdt_tags_ns = n_tags * 2 * 10 / cpu_freq * 1e9  # ~10 cycles per tag op
crdt_total_ms = (crdt_hash_ns + crdt_tags_ns) / 1e6

print("--- Component 4: CRDT Merge ---")
print(f"  Hash compare: {crdt_hash_ns:.3f} ns")
print(f"  Tags union ({n_tags} tags): {crdt_tags_ns:.3f} ns")
print(f"  Total CRDT merge: {crdt_total_ms:.4f} ms (negligible)")
print()

# ============================================================
# COMPONENT 5: Hopfield weight update (CO_RETRIEVED increment)
# ============================================================
# Recall 2.0 Hopfield: co_retrieval event -> flush every 15min
# The write path enqueues an event to mpsc channel (non-blocking)
# Actual LMDB write happens in background worker
# Hot-path cost: mpsc send = lock-free queue push (~50ns)

hopfield_hot_ns = 50  # mpsc send (lock-free, single atomic CAS)
hopfield_hot_ms = hopfield_hot_ns / 1e6

# Background worker per-edge update (not on hot path):
# LMDB write transaction for each edge: ~0.1ms per edge
# At K=200 co-retrieved per session: ~20 edges per session
# Total background: 20 * 0.1ms = 2ms (deferred, not blocking)
hopfield_background_ms = 20 * 0.1

print("--- Component 5: Hopfield CO_RETRIEVED Update ---")
print(
    f"  Hot-path (mpsc channel push): {hopfield_hot_ns} ns ({hopfield_hot_ms:.4f} ms)"
)
print(
    f"  Background worker (deferred): ~{hopfield_background_ms:.1f} ms (not on critical path)"
)
print()

# ============================================================
# COMPONENT 6: LMDB persistence write
# ============================================================
# LMDB write transaction:
# - Memory record (m:{uuid}): 500B
# - Embedding vector (v:{uuid}): 1024 * 4 = 4096B (fp32)
# - Total write: ~4600B
# LMDB write throughput: ~200K small writes/sec = ~5us per write
# But LMDB MDB_NOSYNC disabled: fsync required for durability
# N100 NVMe SSD: ~50us fsync latency (typical NVMe for small writes)
# LMDB with MDB_NOSYNC=false: fsync adds ~50us per commit

lmdb_write_bytes = 500 + D * 4  # memory record + fp32 embedding
lmdb_write_ns = 5_000  # 5us for LMDB write operation
lmdb_fsync_ns = 50_000  # 50us for NVMe fsync (durable commit)
lmdb_total_ms = (lmdb_write_ns + lmdb_fsync_ns) / 1e6

# SQLite WAL write (metadata): ~0.5ms per row (WAL + fsync)
sqlite_write_ms = 0.5

print("--- Component 6: LMDB + SQLite Persistence ---")
print(f"  LMDB write ({lmdb_write_bytes}B): {lmdb_write_ns / 1000:.0f} us")
print(f"  LMDB fsync (NVMe): {lmdb_fsync_ns / 1000:.0f} us")
print(f"  Total LMDB: {lmdb_total_ms:.2f} ms")
print(f"  SQLite WAL write (metadata): {sqlite_write_ms:.1f} ms")
print()

# ============================================================
# COMPONENT 7: HNSW index update (instant-distance insert)
# ============================================================
# HNSW insert: find insertion layer + connect neighbors
# Complexity: O(ef_construction * M * D) operations for ANN graph update
# ef_construction=200, M=16, D=384
ef_construction = 200
M_hnsw = 16
hnsw_ops_per_insert = ef_construction * M_hnsw * D  # approximate
hnsw_ops_avx2 = hnsw_ops_per_insert / avx2_fp32_ops_per_cycle
hnsw_cycles = hnsw_ops_avx2 * 2  # 2 cycles per SIMD op
hnsw_compute_ms = (hnsw_cycles / cpu_freq) * 1e3
# HNSW insert must acquire write lock (RwLock): brief contention
hnsw_lock_ms = 0.1  # RwLock write acquisition (uncontended)
# HNSW checkpoint to LMDB every 100 inserts: 100 inserts / 100 = 1 LMDB write
hnsw_checkpoint_ms = 0.055 / 100  # amortized cost

print("--- Component 7: HNSW Index Update ---")
print(f"  ef_construction={ef_construction}, M={M_hnsw}, D={D}")
print(f"  Approximate ops: {hnsw_ops_per_insert:,} (SIMD: {hnsw_ops_avx2:,.0f})")
print(f"  Compute: {hnsw_compute_ms:.2f} ms")
print(f"  RwLock write: {hnsw_lock_ms:.1f} ms")
print(f"  Checkpoint (amortized): {hnsw_checkpoint_ms:.4f} ms")
hnsw_total_ms = hnsw_compute_ms + hnsw_lock_ms + hnsw_checkpoint_ms
print(f"  Total HNSW insert: {hnsw_total_ms:.2f} ms")
print()

# ============================================================
# TOTAL WRITE-PATH LATENCY
# ============================================================
components = [
    ("SHA-256 hash check", sha_ns / 1e6),
    ("SimHash compute + band lookup", simhash_total_ms),
    ("fastembed-rs (FP32)", fastembed_full_ms),
    ("CRDT merge", crdt_total_ms),
    ("Hopfield mpsc send", hopfield_hot_ms),
    ("LMDB write (memory + vector)", lmdb_total_ms),
    ("SQLite WAL write", sqlite_write_ms),
    ("HNSW insert", hnsw_total_ms),
]

components_int8 = [
    ("SHA-256 hash check", sha_ns / 1e6),
    ("SimHash compute + band lookup", simhash_total_ms),
    ("fastembed-rs (INT8 quantized)", fastembed_int8_ms),
    ("CRDT merge", crdt_total_ms),
    ("Hopfield mpsc send", hopfield_hot_ms),
    ("LMDB write (memory + vector, D=384)", lmdb_total_ms * 0.4),  # fp16 smaller
    ("SQLite WAL write", sqlite_write_ms),
    ("HNSW insert", hnsw_total_ms),
]

total_fp32 = sum(ms for _, ms in components)
total_int8 = sum(ms for _, ms in components_int8)

print("=== WRITE-PATH LATENCY SUMMARY ===")
print()
print(f"{'Component':<40}  {'ms':>8}")
print("-" * 52)
for name, ms in components:
    pct = ms / total_fp32 * 100
    print(f"{name:<40}  {ms:>7.2f}  ({pct:.0f}%)")
print("-" * 52)
print(f"{'TOTAL (FP32)':<40}  {total_fp32:>7.2f}")
print()
print(f"{'Component':<40}  {'ms':>8}")
print("-" * 52)
for name, ms in components_int8:
    pct = ms / total_int8 * 100
    print(f"{name:<40}  {ms:>7.2f}  ({pct:.0f}%)")
print("-" * 52)
print(f"{'TOTAL (INT8 quantized)':<40}  {total_int8:>7.2f}")
print()

budget_ms = 186  # from write-path.md
print(f"Write path budget (from write-path.md): {budget_ms} ms")
print(
    f"FP32 total: {total_fp32:.1f} ms ({total_fp32 / budget_ms * 100:.0f}% of budget)"
)
print(
    f"INT8 total: {total_int8:.1f} ms ({total_int8 / budget_ms * 100:.0f}% of budget)"
)
print()

# Check against Ollama comparison
ollama_embedding_ms = 150  # Ollama over network baseline
print(f"Ollama network embedding: ~{ollama_embedding_ms} ms")
print(f"fastembed-rs INT8 speedup: {ollama_embedding_ms / fastembed_int8_ms:.1f}x")
print(f"fastembed-rs FP32 speedup: {ollama_embedding_ms / fastembed_full_ms:.1f}x")
print()
print("=== KEY FINDINGS ===")
print(
    f"1. Embedding dominates: fastembed FP32={fastembed_full_ms}ms = {fastembed_full_ms / total_fp32 * 100:.0f}% of total"
)
print(
    f"2. INT8 quantization reduces total from {total_fp32:.0f}ms to {total_int8:.0f}ms ({(total_fp32 - total_int8) / total_fp32 * 100:.0f}% reduction)"
)
print(
    f"3. Both are within {budget_ms}ms budget: FP32 {'PASS' if total_fp32 < budget_ms else 'FAIL'}, INT8 {'PASS' if total_int8 < budget_ms else 'FAIL'}"
)
print(
    f"4. HNSW insert ({hnsw_total_ms:.1f}ms) and SQLite WAL ({sqlite_write_ms}ms) are secondary bottlenecks"
)
print("5. SHA-256, CRDT, SimHash, Hopfield mpsc are negligible (<1ms combined)")
