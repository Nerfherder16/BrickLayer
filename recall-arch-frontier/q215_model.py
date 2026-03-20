"""
Q215 Model: Memory Poisoning via Agent Hallucination
Models SourceTrust scoring gap and conditions where false memories dominate retrieval.
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# =============================================
# Recall 2.0 Scoring Model (inferred from Q200)
# score = cosine * (w_trust * source_trust + w_coret * co_retrieved + w_recency * recency)
# =============================================

W_TRUST = 0.40
W_CORET = 0.35
W_RECENCY = 0.25

# SourceTrust values (from Q195/Q200 design)
ST_USER_VERIFIED = 0.9  # User explicitly confirmed
ST_SESSION_SUMMARY = 0.7  # Session summary hook (observed_edit / summarizer)
ST_AGENT_GENERATED = 0.4  # Agent-written during task (PostToolUse observe)
ST_EXTERNAL_INGEST = 0.5  # External document ingested


def retrieval_score(cosine, source_trust, co_retrieved=0.0, recency=1.0):
    """Compute retrieval score given components."""
    trust_component = W_TRUST * source_trust
    coret_component = W_CORET * co_retrieved
    recency_component = W_RECENCY * recency
    return cosine * (trust_component + coret_component + recency_component)


# =============================================
# Part 1: Break-even cosine for false memory to dominate
# =============================================
print("=" * 65)
print("PART 1: Break-even Cosine Similarity for False Memory Dominance")
print("=" * 65)
print()
print("False memory (SourceTrust=0.4) vs True memory (SourceTrust=0.9)")
print("No CO_RETRIEVED boost for either. Both fresh (recency=1.0).")
print()
print("Break-even: cos_false * score_factor_false = cos_true * score_factor_true")
print()

true_factor = W_TRUST * ST_USER_VERIFIED + W_CORET * 0 + W_RECENCY * 1.0
false_factor = W_TRUST * ST_AGENT_GENERATED + W_CORET * 0 + W_RECENCY * 1.0

print(
    f"True memory score factor:  {true_factor:.3f}  ({W_TRUST}*{ST_USER_VERIFIED} + {W_RECENCY}*1.0)"
)
print(
    f"False memory score factor: {false_factor:.3f}  ({W_TRUST}*{ST_AGENT_GENERATED} + {W_RECENCY}*1.0)"
)
print(f"Ratio (true/false):        {true_factor / false_factor:.3f}")
print()

# For each true_cosine, find min false_cosine needed to dominate
print(f"{'cos_true':>10} {'score_true':>12} {'cos_false needed':>17} {'Feasible?':>10}")
print("-" * 55)
for cos_true in [0.95, 0.85, 0.75, 0.65, 0.55, 0.45, 0.35, 0.25]:
    score_true = retrieval_score(cos_true, ST_USER_VERIFIED)
    cos_false_needed = score_true / false_factor
    feasible = "YES" if cos_false_needed <= 1.0 else "NO (impossible)"
    print(
        f"{cos_true:>10.2f} {score_true:>12.4f} {cos_false_needed:>17.4f} {feasible:>10}"
    )

print()
print(
    f"FALSE MEMORY DOMINATES ONLY WHEN cos_true < {true_factor / false_factor * 1.0:.2f}..."
)
critical = false_factor / true_factor
print(
    f"  i.e., cos_true < {critical:.3f} (true memory is NOT highly relevant to query)"
)
print("  Practical interpretation: false memory wins only on off-topic queries")
print("  or when no competing true memory exists about the topic.")

# =============================================
# Part 2: CO_RETRIEVED as poisoning defense
# =============================================
print()
print("=" * 65)
print("PART 2: CO_RETRIEVED Boost as Passive Poisoning Defense")
print("=" * 65)
print()
print("Established true memory (SourceTrust=0.9, CO_RETRIEVED=0.3)")
print("vs fresh false memory (SourceTrust=0.4, CO_RETRIEVED=0.0)")
print()

CO_RET_ESTABLISHED = 0.3  # memory with behavioral history

# True established memory vs fresh false memory
for cos_true in [0.85, 0.75, 0.65, 0.55]:
    score_true = retrieval_score(
        cos_true, ST_USER_VERIFIED, co_retrieved=CO_RET_ESTABLISHED
    )
    # Required cos_false to beat this score
    cos_false_needed = score_true / false_factor
    feasible = "YES" if cos_false_needed <= 1.0 else "NO"
    print(
        f"  cos_true={cos_true}, CO_RET=0.3: score={score_true:.4f}, needs cos_false={cos_false_needed:.4f} [{feasible}]"
    )

print()
print("WITH CO_RETRIEVED boost: false memory requires much higher cosine to compete.")
print(
    "Behavioral scoring is a PASSIVE poisoning defense -- harder to fake than SourceTrust."
)

# =============================================
# Part 3: Attack vectors
# =============================================
print()
print("=" * 65)
print("PART 3: Attack Scenarios")
print("=" * 65)

scenarios = [
    {
        "name": "Cold Start Attack (no competing true memory)",
        "cos_false": 0.85,
        "cos_true": 0.0,  # no true memory exists
        "st_false": ST_AGENT_GENERATED,
        "st_true": None,
        "cr_false": 0.0,
        "cr_true": 0.0,
    },
    {
        "name": "High-Similarity Attack (false memory crafted to match queries)",
        "cos_false": 0.92,
        "cos_true": 0.75,
        "st_false": ST_AGENT_GENERATED,
        "st_true": ST_USER_VERIFIED,
        "cr_false": 0.0,
        "cr_true": 0.0,
    },
    {
        "name": "Established Memory Defense (true memory has CO_RETRIEVED=0.3)",
        "cos_false": 0.92,
        "cos_true": 0.75,
        "st_false": ST_AGENT_GENERATED,
        "st_true": ST_USER_VERIFIED,
        "cr_false": 0.0,
        "cr_true": 0.3,
    },
    {
        "name": "Stale True Memory (recency=0.5, false is fresh)",
        "cos_false": 0.80,
        "cos_true": 0.80,
        "st_false": ST_AGENT_GENERATED,
        "st_true": ST_USER_VERIFIED,
        "cr_false": 0.0,
        "cr_true": 0.0,
        "recency_false": 1.0,
        "recency_true": 0.5,
    },
]

for s in scenarios:
    recency_false = s.get("recency_false", 1.0)
    recency_true = s.get("recency_true", 1.0)
    score_false = retrieval_score(
        s["cos_false"], s["st_false"], s["cr_false"], recency_false
    )
    if s["st_true"] is None:
        score_true = 0.0
        winner = "FALSE MEMORY WINS (no true memory)"
    else:
        score_true = retrieval_score(
            s["cos_true"], s["st_true"], s["cr_true"], recency_true
        )
        if score_false > score_true:
            winner = "FALSE MEMORY WINS"
        else:
            margin = (score_true - score_false) / score_true * 100
            winner = f"True memory wins ({margin:.0f}% margin)"
    print(f"\n  Scenario: {s['name']}")
    print(
        f"    False score: {score_false:.4f} (cos={s['cos_false']}, ST={s['st_false']}, CR={s['cr_false']:.1f})"
    )
    if s["st_true"]:
        print(
            f"    True score:  {score_true:.4f} (cos={s['cos_true']}, ST={s['st_true']}, CR={s['cr_true']:.1f}, rec={recency_true})"
        )
    print(f"    Result: {winner}")

# =============================================
# Part 4: Contradiction Detection Design
# =============================================
print()
print("=" * 65)
print("PART 4: Write-Time Contradiction Detection Mechanism")
print("=" * 65)
print()
print("Insight: Two memories about the SAME topic but with DIFFERENT claims")
print("  are detectable as: high cosine similarity (same topic/keywords)")
print("                   + high SimHash distance (different content/claims)")
print()
print("  Deduplication (SimHash Q171): catches SAME claim (SimHash distance <= 6)")
print(
    "  Contradiction detection:      catches OPPOSITE claim (high cosine, high SimHash)"
)
print()
print("Detection algorithm (write-time):")
print("  1. Compute embedding for new memory (41ms, standard write path)")
print(
    "  2. HNSW search for existing memories with cosine > CONTRADICTION_COSINE_THRESHOLD"
)
print("  3. For each found memory with SourceTrust > TRUSTED_SOURCE_THRESHOLD:")
print("     a. Compute SimHash distance (already available at write time)")
print("     b. If SimHash distance > NEAR_DUPLICATE_THRESHOLD (6):")
print("        => Same topic, different claim = CONTRADICTION DETECTED")
print("     c. If SimHash distance <= NEAR_DUPLICATE_THRESHOLD:")
print("        => Near-duplicate, handled by existing dedup")
print("  4. On contradiction: QUARANTINE the write (do not store)")
print("     Add to contradiction_queue for user review")
print()

CONTRADICTION_COSINE_THRESHOLD = 0.82
TRUSTED_SOURCE_THRESHOLD = 0.65
NEAR_DUPLICATE_THRESHOLD = 6

print("  Recommended thresholds:")
print(
    f"    CONTRADICTION_COSINE_THRESHOLD  = {CONTRADICTION_COSINE_THRESHOLD} (same-topic boundary)"
)
print(
    f"    TRUSTED_SOURCE_THRESHOLD        = {TRUSTED_SOURCE_THRESHOLD} (triggers check)"
)
print(
    f"    NEAR_DUPLICATE_SIMHASH_DISTANCE = {NEAR_DUPLICATE_THRESHOLD} (above = contradiction)"
)
print()
print("  Cost analysis:")
print("  HNSW search at contradiction check: 0.215ms (Q205, standard retrieval)")
print("  SimHash computation: <0.1ms per existing memory (Q171)")
print("  Total overhead per write: +0.3-0.5ms (well within 186ms write budget)")
print(
    "  False positive rate: low -- requires both high cosine AND high SimHash distance"
)

# =============================================
# Part 5: Recommended SourceTrust floor
# =============================================
print()
print("=" * 65)
print("PART 5: SourceTrust Floor Analysis for Agent Writes")
print("=" * 65)
print()
print("Current: AgentGenerated SourceTrust = 0.40")
print()

# At what ST_AGENT does the false memory NEVER dominate a cosine-equivalent true memory?
# Condition: cos * ST_agent * W_TRUST + recency * W_RECENCY < cos * ST_user * W_TRUST + recency * W_RECENCY
# Simplifying: ST_agent < ST_user (trivially always true if ST_agent < ST_user)
# But the real question is the crossover:
# cos_false * (W_TRUST * st_a + W_RECENCY) < cos_true * (W_TRUST * 0.9 + W_RECENCY)
# At cos_false = cos_true (equal cosine): st_a + W_RECENCY/W_TRUST < 0.9 + W_RECENCY/W_TRUST
# -> st_a < 0.9 always (any st_a < 0.9 ensures true memory wins at equal cosine)
# At cos_false > cos_true: depends on magnitude

for st_agent in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]:
    false_f = W_TRUST * st_agent + W_RECENCY * 1.0
    # Critical cos_true below which false wins (cos_false=1.0)
    crit_cos_true = false_f / true_factor
    print(
        f"  ST_agent={st_agent}: critical cos_true = {crit_cos_true:.3f} "
        f"(false memory can win only if cos_true < {crit_cos_true:.2f})"
    )

print()
print(
    f"At ST_agent=0.40 (current): false memory wins only when cos_true < {(W_TRUST * 0.4 + W_RECENCY) / true_factor:.3f}"
)
print(
    f"At ST_agent=0.20 (stricter): false memory wins only when cos_true < {(W_TRUST * 0.2 + W_RECENCY) / true_factor:.3f}"
)
print()
print("Recommendation: ST_agent=0.40 is adequate WITH contradiction detection.")
print("Contradiction detection is more valuable than lowering SourceTrust floor:")
print("  Lower ST just reduces retrieval rank of poisoned memories")
print("  Contradiction detection PREVENTS poisoning of cold-start topics")
print("  (no competing true memory = SourceTrust irrelevant)")
