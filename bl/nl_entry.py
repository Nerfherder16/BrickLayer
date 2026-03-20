"""
bl/nl_entry.py — Natural language entry point for BrickLayer 2.0.

Converts a plain English description of what just changed into a targeted set of
BrickLayer research questions, ready to append to questions.md and run.

Usage:
    from bl.nl_entry import generate_from_description, quick_campaign, format_preview

    questions = generate_from_description("I just added concurrent Neo4j writes to the session store")
    print(format_preview(questions))

    # Or full pipeline — generates + appends to questions.md:
    result = quick_campaign("I just added concurrent Neo4j writes to the session store", project_dir=".")
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Intent patterns — what kind of change was made
# ---------------------------------------------------------------------------

INTENT_PATTERNS: dict[str, list[str]] = {
    "new_feature": [
        "just added",
        "just built",
        "implemented",
        "created",
        "new",
        "introduced",
        "added",
        "built",
        "wrote",
    ],
    "bug_fix": [
        "fixed",
        "patched",
        "resolved",
        "corrected",
        "repaired",
        "bugfix",
        "bug fix",
        "fix for",
        "addressed",
    ],
    "performance": [
        "optimized",
        "faster",
        "cache",
        "latency",
        "throughput",
        "speed",
        "slow",
        "bottleneck",
        "profiling",
        "memory",
        "cpu",
        "benchmark",
    ],
    "security": [
        "auth",
        "permission",
        "encrypt",
        "secret",
        "token",
        "access",
        "authentication",
        "authorization",
        "credential",
        "privilege",
        "acl",
        "jwt",
        "oauth",
        "api key",
    ],
    "data_model": [
        "schema",
        "migration",
        "database",
        "table",
        "column",
        "index",
        "model",
        "field",
        "relation",
        "foreign key",
        "constraint",
    ],
    "integration": [
        "api",
        "webhook",
        "endpoint",
        "external",
        "third-party",
        "connected",
        "integrated",
        "plugin",
        "adapter",
        "client",
        "sdk",
    ],
    "concurrency": [
        "concurrent",
        "parallel",
        "async",
        "thread",
        "lock",
        "race",
        "mutex",
        "semaphore",
        "coroutine",
        "worker",
        "queue",
        "batch",
        "simultaneous",
        "multi",
    ],
    "config": [
        "config",
        "setting",
        "environment",
        "variable",
        "flag",
        "toggle",
        "env",
        "dotenv",
        "feature flag",
        "configuration",
    ],
    "refactor": [
        "refactored",
        "refactor",
        "restructured",
        "reorganized",
        "split",
        "extracted",
        "moved",
        "renamed",
        "cleaned up",
    ],
    "deployment": [
        "deployed",
        "deploy",
        "container",
        "kubernetes",
        "k8s",
        "ci/cd",
        "pipeline",
        "release",
        "rollout",
        "helm",
        "terraform",
    ],
}

# ---------------------------------------------------------------------------
# Technology keywords → concerns to probe
# ---------------------------------------------------------------------------

TECH_KEYWORDS: dict[str, dict] = {
    "neo4j": {
        "type": "graph_db",
        "concerns": [
            "transaction isolation",
            "concurrent write",
            "query performance",
            "index",
        ],
    },
    "redis": {
        "type": "cache",
        "concerns": [
            "eviction policy",
            "ttl expiry",
            "connection pool exhaustion",
            "failover",
        ],
    },
    "postgres": {
        "type": "rdb",
        "concerns": [
            "transaction deadlock",
            "migration rollback",
            "index bloat",
            "connection limit",
        ],
    },
    "postgresql": {
        "type": "rdb",
        "concerns": [
            "transaction deadlock",
            "migration rollback",
            "index bloat",
            "connection limit",
        ],
    },
    "solana": {
        "type": "blockchain",
        "concerns": [
            "integer overflow",
            "reentrancy",
            "account validation",
            "signer check",
        ],
    },
    "fastapi": {
        "type": "api",
        "concerns": [
            "input validation",
            "auth middleware",
            "rate limiting",
            "error handling",
        ],
    },
    "docker": {
        "type": "infra",
        "concerns": [
            "resource limits",
            "network isolation",
            "volume persistence",
            "restart policy",
        ],
    },
    "ollama": {
        "type": "inference",
        "concerns": [
            "request timeout",
            "model load time",
            "throughput under load",
            "queue depth",
        ],
    },
    "websocket": {
        "type": "realtime",
        "concerns": [
            "connection limit",
            "message ordering",
            "reconnect storm",
            "memory leak",
        ],
    },
    "kafka": {
        "type": "queue",
        "concerns": [
            "consumer lag",
            "partition rebalance",
            "message ordering",
            "at-least-once delivery",
        ],
    },
    "celery": {
        "type": "task_queue",
        "concerns": [
            "worker crash recovery",
            "task retry storm",
            "result backend expiry",
            "lock contention",
        ],
    },
    "elasticsearch": {
        "type": "search",
        "concerns": [
            "mapping explosion",
            "shard allocation",
            "query timeout",
            "index refresh lag",
        ],
    },
    "s3": {
        "type": "object_store",
        "concerns": [
            "eventual consistency",
            "rate limiting",
            "cost under load",
            "multipart upload",
        ],
    },
    "jwt": {
        "type": "auth",
        "concerns": [
            "token expiry handling",
            "secret rotation",
            "algorithm confusion",
            "revocation gap",
        ],
    },
    "sqlite": {
        "type": "rdb",
        "concerns": [
            "write lock contention",
            "wal mode",
            "connection pooling",
            "data corruption",
        ],
    },
    "mongodb": {
        "type": "document_db",
        "concerns": [
            "transaction isolation",
            "index usage",
            "oplog lag",
            "write concern",
        ],
    },
    "qdrant": {
        "type": "vector_db",
        "concerns": [
            "collection consistency",
            "payload index",
            "search timeout",
            "upsert ordering",
        ],
    },
}

# ---------------------------------------------------------------------------
# Domain mapping — where each concern type belongs
# ---------------------------------------------------------------------------

_DOMAIN_MAP: dict[str, str] = {
    "new_feature": "D4",
    "bug_fix": "D4",
    "performance": "D4",
    "security": "D2",
    "data_model": "D4",
    "integration": "D4",
    "concurrency": "D4",
    "config": "D4",
    "refactor": "D4",
    "deployment": "D4",
}

_MODE_MAP: dict[str, str] = {
    "new_feature": "diagnose",
    "bug_fix": "validate",
    "performance": "diagnose",
    "security": "validate",
    "data_model": "diagnose",
    "integration": "diagnose",
    "concurrency": "diagnose",
    "config": "validate",
    "refactor": "validate",
    "deployment": "diagnose",
}

# ---------------------------------------------------------------------------
# Generic question templates — used when no technology is matched
# ---------------------------------------------------------------------------

_GENERIC_TEMPLATES: dict[str, list[str]] = {
    "new_feature": [
        "What are the failure modes of {nouns} under load? At what scale does it break?",
        "Does {nouns} handle edge cases (empty input, null, zero, max values) correctly?",
        "What happens to {nouns} when a downstream dependency is unavailable or slow?",
        "Is there a race condition or ordering assumption in {nouns} that breaks under concurrency?",
        "What is the rollback strategy if {nouns} needs to be reverted in production?",
    ],
    "bug_fix": [
        "Does the fix for {nouns} address the root cause or only the symptom? What are the regression risks?",
        "Are there other call sites or code paths that have the same bug pattern as {nouns}?",
        "What test coverage exists for {nouns}? Is the fix verifiable without a full integration run?",
        "Does the fix to {nouns} introduce any new edge cases or change observable behavior?",
    ],
    "performance": [
        "What is the actual performance baseline for {nouns} before and after the optimization?",
        "Does the optimization in {nouns} hold under realistic production load (not just benchmarks)?",
        "Does the optimization introduce any correctness tradeoffs (caching stale data, skipping validation)?",
        "What is the worst-case performance for {nouns}? What triggers it?",
    ],
    "security": [
        "Does {nouns} enforce authorization at every entry point, not just the UI?",
        "What happens if an attacker supplies malformed or boundary-exceeding input to {nouns}?",
        "Are secrets and credentials in {nouns} stored safely and never logged?",
        "What is the blast radius if {nouns} is compromised? Can it escalate to other systems?",
    ],
    "data_model": [
        "Is the migration for {nouns} reversible? What is the rollback plan?",
        "Does the schema change to {nouns} break any existing queries or application code?",
        "What happens to {nouns} data integrity under concurrent writes during the migration window?",
        "Are indexes on {nouns} appropriate for the access patterns? Can any cause lock contention?",
    ],
    "integration": [
        "What happens to {nouns} when the external service is down, slow, or rate-limiting?",
        "Does {nouns} handle authentication token expiry and refresh correctly?",
        "What is the retry and backoff strategy for {nouns}? Can it cause thundering herd?",
        "Are all inputs from the external service in {nouns} validated before use?",
    ],
    "concurrency": [
        "Is there a race condition in {nouns} when two workers execute the same path simultaneously?",
        "Does {nouns} hold locks for longer than necessary, risking deadlock or starvation?",
        "What is the behavior of {nouns} when a worker crashes mid-operation? Is state left consistent?",
        "Does {nouns} scale linearly with concurrent workers, or does contention cause degradation?",
    ],
    "config": [
        "Does {nouns} fail safely if the config value is missing, malformed, or out of range?",
        "Is the config for {nouns} validated at startup or only at first use?",
        "Can {nouns} be toggled at runtime without restart, and is there a rollback path?",
        "Are there undocumented interactions between {nouns} and other config values?",
    ],
    "refactor": [
        "Does the refactor of {nouns} preserve all observable behavior under the existing test suite?",
        "Are there edge cases in {nouns} that were handled by accident (defensive code) and may now be missing?",
        "Does the refactored {nouns} have the same or better performance characteristics?",
    ],
    "deployment": [
        "What is the failure mode for {nouns} if the deployment is partial (some instances old, some new)?",
        "Does {nouns} require downtime or can it be rolled out with zero-downtime deployment?",
        "What is the rollback procedure for {nouns} if the deployment fails mid-flight?",
        "Are there health checks for {nouns} that confirm successful deployment before traffic is shifted?",
    ],
}

# ---------------------------------------------------------------------------
# Tech-specific question templates
# ---------------------------------------------------------------------------

_TECH_TEMPLATES: dict[str, dict[str, list[str]]] = {
    "graph_db": {
        "concurrent write": [
            "Does the concurrent write to {tech} in {nouns} use explicit transaction boundaries? "
            "What is the isolation level, and can two writers produce a dirty or phantom read?",
            "Under 10+ simultaneous writers to {tech} in {nouns}, is there a deadlock or write-skew "
            "failure mode? What is the retry policy?",
        ],
        "transaction isolation": [
            "Does {nouns} rely on {tech} transaction isolation to guarantee consistency, or does it "
            "assume optimistic single-writer access? What breaks if the assumption is wrong?",
        ],
        "query performance": [
            "What index coverage exists for the {tech} queries in {nouns}? Is there a full-graph scan "
            "that could cause latency spikes at production data volume?",
        ],
        "index": [
            "Are the {tech} indexes for {nouns} correct for the query patterns? Can a missing or "
            "incorrect index cause query timeout under load?",
        ],
    },
    "cache": {
        "eviction policy": [
            "If {tech} in {nouns} evicts a key under memory pressure, what is the fallback? Can the "
            "application reconstruct the value, or does this cause a hard failure?",
        ],
        "ttl expiry": [
            "When a {tech} key in {nouns} expires mid-request, is there a race between the read "
            "and the re-population that can serve stale or empty data?",
        ],
        "connection pool exhaustion": [
            "What happens to {nouns} if {tech} connection pool is exhausted? Does the caller block, "
            "fail fast, or queue? At what concurrent request volume does this trigger?",
        ],
        "failover": [
            "Does {nouns} degrade gracefully when {tech} is unreachable? Is the fallback path tested?",
        ],
    },
    "rdb": {
        "transaction deadlock": [
            "Can the transactions in {nouns} that write to {tech} deadlock? What is the lock acquisition "
            "order, and is there a consistent ordering enforced?",
        ],
        "migration rollback": [
            "Is the {tech} migration for {nouns} fully reversible with a down migration? Has the rollback "
            "been tested against a populated database?",
        ],
        "index bloat": [
            "Do the new {tech} indexes for {nouns} have an appropriate fill factor? Can they cause "
            "write amplification at high insert rates?",
        ],
        "connection limit": [
            "Does {nouns} use a {tech} connection pool with a bounded size? What happens when the pool "
            "limit is reached under burst load?",
        ],
    },
    "blockchain": {
        "integer overflow": [
            "Are all arithmetic operations in {nouns} on {tech} checked for integer overflow? "
            "What is the worst-case value that could cause silent truncation?",
        ],
        "reentrancy": [
            "Does {nouns} on {tech} update state before or after external calls? Can a malicious "
            "program call back into {nouns} before state is committed?",
        ],
        "account validation": [
            "Does {nouns} validate all {tech} account ownership and type before use? "
            "What happens if an attacker substitutes a different account?",
        ],
        "signer check": [
            "Are all privileged instructions in {nouns} on {tech} gated by a signer check? "
            "Can an unsigned transaction invoke any privileged path?",
        ],
    },
    "api": {
        "input validation": [
            "Does every input to the {tech} endpoints in {nouns} have explicit type and range validation? "
            "What happens if an attacker sends an unexpected type or oversized payload?",
        ],
        "auth middleware": [
            "Is the auth middleware for {nouns} applied uniformly to all {tech} routes, including "
            "any newly added routes? Is there a route that bypasses it?",
        ],
        "rate limiting": [
            "Does {nouns} on {tech} have per-user or per-IP rate limits? What is the behavior "
            "under a burst of 1000 requests in 1 second?",
        ],
        "error handling": [
            "Do error responses from {nouns} on {tech} leak internal state, stack traces, or "
            "file paths? Is there a consistent error response schema?",
        ],
    },
    "infra": {
        "resource limits": [
            "Does the {tech} container for {nouns} have CPU and memory limits set? What is the "
            "OOM behavior — restart policy and data safety?",
        ],
        "network isolation": [
            "Is the {tech} container for {nouns} network-isolated to only the services that need "
            "access? Can an attacker pivot from a compromised container?",
        ],
        "volume persistence": [
            "Are the volumes for {nouns} on {tech} persisted across container restarts? "
            "What data is lost if the container is replaced?",
        ],
        "restart policy": [
            "Does the {tech} restart policy for {nouns} cause a crash loop if the process fails "
            "immediately on start? Is there a backoff?",
        ],
    },
    "inference": {
        "request timeout": [
            "What is the timeout configuration for {nouns} calling {tech}? Does a slow model "
            "response cascade into the caller and cause a timeout storm?",
        ],
        "model load time": [
            "What is the cold-start latency for {nouns} using {tech}? Can a process restart "
            "cause a request queue buildup during model load?",
        ],
        "throughput under load": [
            "What is the maximum sustained throughput for {nouns} through {tech}? At what request "
            "rate does queuing delay become observable?",
        ],
        "queue depth": [
            "Does {nouns} bound the {tech} request queue depth? What is the behavior when "
            "the queue is full — drop, block, or error?",
        ],
    },
    "realtime": {
        "connection limit": [
            "What is the per-server connection limit for {nouns} using {tech}? What happens "
            "when it is reached — silent drop or explicit error?",
        ],
        "message ordering": [
            "Does {nouns} on {tech} guarantee message ordering? Can two messages from the same "
            "client arrive out of order, and does the application handle it?",
        ],
        "reconnect storm": [
            "If the {tech} server for {nouns} restarts, do all clients reconnect simultaneously? "
            "Is there jitter in the reconnect backoff?",
        ],
        "memory leak": [
            "Are {tech} connections in {nouns} properly closed on client disconnect? "
            "Is there a resource leak when connections are abandoned (no close frame)?",
        ],
    },
    "queue": {
        "consumer lag": [
            "Under what message rate does the {tech} consumer for {nouns} accumulate lag? "
            "What is the recovery time after a consumer restart?",
        ],
        "partition rebalance": [
            "Does a {tech} partition rebalance for {nouns} cause duplicate processing or "
            "message loss during the rebalance window?",
        ],
        "message ordering": [
            "Does {nouns} depend on {tech} message ordering across partitions? "
            "Is there a sequence number or deduplication key?",
        ],
        "at-least-once delivery": [
            "Does {nouns} handle {tech} duplicate delivery idempotently? "
            "What is the state left if a message is processed twice?",
        ],
    },
    "task_queue": {
        "worker crash recovery": [
            "If a {tech} worker for {nouns} crashes mid-task, is the task requeued and retried "
            "safely, or is it silently dropped?",
        ],
        "task retry storm": [
            "Does the retry policy for {nouns} on {tech} use exponential backoff? "
            "Can a failing task cause a retry storm that saturates the queue?",
        ],
        "result backend expiry": [
            "Does {nouns} read results from {tech} within the result backend TTL? "
            "What happens when the result expires before it is read?",
        ],
        "lock contention": [
            "Are {tech} task locks in {nouns} scoped narrowly enough to avoid contention? "
            "What is the worst-case lock hold time?",
        ],
    },
    "vector_db": {
        "collection consistency": [
            "Does {nouns} ensure {tech} writes are flushed before reading them back? "
            "Can a read-after-write return stale results?",
        ],
        "payload index": [
            "Are the {tech} payload indexes for {nouns} covering the filter fields used in searches? "
            "Can a missing index cause full-collection scans?",
        ],
        "search timeout": [
            "What is the timeout for {tech} similarity searches in {nouns}? "
            "At what collection size does search latency exceed the SLA?",
        ],
        "upsert ordering": [
            "If two concurrent upserts to {tech} in {nouns} use the same ID, which wins? "
            "Is the result deterministic, or can partial state be written?",
        ],
    },
    "object_store": {
        "eventual consistency": [
            "Does {nouns} read from {tech} immediately after a write? "
            "Can eventual consistency cause {nouns} to see an old version?",
        ],
        "rate limiting": [
            "Does {nouns} handle {tech} rate limit errors (HTTP 503/429) with backoff? "
            "Can a burst cause a cascading retry loop?",
        ],
        "cost under load": [
            "What is the estimated {tech} cost for {nouns} at 10x current request volume? "
            "Is there a request pattern that causes unexpected cost amplification?",
        ],
        "multipart upload": [
            "Does {nouns} use multipart uploads for large objects to {tech}? "
            "What is the cleanup strategy for incomplete multipart uploads?",
        ],
    },
    "auth": {
        "token expiry handling": [
            "Does {nouns} handle {tech} token expiry gracefully — refreshing silently or failing "
            "fast with a clear error rather than serving a stale authenticated response?",
        ],
        "secret rotation": [
            "Can the {tech} signing secret in {nouns} be rotated without downtime? "
            "Is there a grace period for tokens signed with the old secret?",
        ],
        "algorithm confusion": [
            "Does {nouns} pin the {tech} algorithm to a specific value? "
            "Can an attacker supply a token with `alg: none` or switch to a weak algorithm?",
        ],
        "revocation gap": [
            "How long does a revoked {tech} token remain valid in {nouns}? "
            "Is there a blocklist or short-TTL design to close the revocation gap?",
        ],
    },
    "search": {
        "mapping explosion": [
            "Can {nouns} send dynamic fields to {tech} that cause mapping explosion? "
            "Is there a strict mapping with `dynamic: strict` or equivalent?",
        ],
        "shard allocation": [
            "Are {tech} shards for {nouns} sized appropriately for the expected document count? "
            "Can over-sharding cause excessive overhead?",
        ],
        "query timeout": [
            "Does {nouns} set a timeout on {tech} queries? "
            "What is the behavior when a query times out — error or partial results?",
        ],
        "index refresh lag": [
            "Does {nouns} read from {tech} immediately after indexing? "
            "Can the refresh interval cause stale search results?",
        ],
    },
    "document_db": {
        "transaction isolation": [
            "Does the transaction in {nouns} on {tech} use the correct write concern and "
            "read concern to prevent dirty reads?",
        ],
        "index usage": [
            "Are the queries in {nouns} on {tech} using indexes? "
            "Can a collection scan under production data volume cause latency spikes?",
        ],
        "oplog lag": [
            "Can replica lag in {tech} cause {nouns} to read stale data from a secondary? "
            "Is there a read preference override for consistency-critical reads?",
        ],
        "write concern": [
            "Does {nouns} use an appropriate {tech} write concern for durability? "
            "What data is lost if the primary fails before replication?",
        ],
    },
}


# ---------------------------------------------------------------------------
# Noun extraction helpers
# ---------------------------------------------------------------------------

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "is",
        "it",
        "this",
        "that",
        "was",
        "are",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "can",
        "just",
        "i",
        "my",
        "we",
        "our",
        "the",
        "so",
        "also",
        "now",
        "then",
        "into",
        "onto",
        "over",
        "under",
        "when",
        "which",
        "who",
        "where",
        "what",
        "how",
        "if",
        "as",
        "about",
        "up",
        "out",
        "off",
        "some",
        "new",
        "just",
        "added",
        "built",
        "fixed",
        "refactored",
        "use",
        "used",
        "using",
        "via",
        "get",
        "set",
        "run",
        "make",
        "put",
        "call",
        "send",
        "read",
        "write",
    }
)

# Multi-word compound nouns worth keeping whole
_COMPOUND_PATTERNS = [
    r"session store",
    r"connection pool",
    r"message queue",
    r"event loop",
    r"worker thread",
    r"background task",
    r"rate limit(?:er|ing)?",
    r"circuit breaker",
    r"retry logic",
    r"health check",
    r"dead letter",
    r"write ahead log",
    r"foreign key",
    r"primary key",
    r"api endpoint",
    r"auth(?:entication|orization)? middleware",
    r"cache layer",
    r"data model",
    r"object store",
    r"vector store",
    r"graph store",
]

_COMPOUND_RE = re.compile(
    r"\b(?:" + "|".join(_COMPOUND_PATTERNS) + r")\b",
    re.IGNORECASE,
)


def _extract_nouns(text: str) -> list[str]:
    """
    Extract meaningful nouns and compound phrases from free text.
    Returns a list of lowercase noun strings, deduplicated, most specific first.
    """
    found: list[str] = []

    # 1. Compound phrases first
    for m in _COMPOUND_RE.finditer(text.lower()):
        found.append(m.group())

    # 2. Remaining single words that are not stopwords or intent verbs
    intent_verbs = {
        v
        for values in INTENT_PATTERNS.values()
        for v in values
        if " " not in v  # single word only
    }
    tech_names = set(TECH_KEYWORDS.keys())

    words = re.findall(r"\b[a-z][a-z0-9_-]*\b", text.lower())
    for w in words:
        if (
            w not in _STOPWORDS
            and w not in intent_verbs
            and w not in tech_names
            and len(w) >= 3
        ):
            found.append(w)

    # Build a set of words already covered by a compound phrase so single-word
    # residuals like "session" or "store" don't repeat what "session store" already says.
    compound_words: set[str] = set()
    for item in found:
        if " " in item:
            for word in item.split():
                compound_words.add(word)

    # Deduplicate preserving order, prefer longer (more specific) matches.
    # Skip single words that are sub-components of an already-captured compound.
    seen: set[str] = set()
    result: list[str] = []
    for item in found:
        if item not in seen:
            if " " not in item and item in compound_words:
                continue  # already represented by a compound phrase
            seen.add(item)
            result.append(item)

    return result[:6]  # keep top 6 nouns max


def _noun_phrase(nouns: list[str]) -> str:
    """Format noun list as a readable phrase for question templates."""
    if not nouns:
        return "the changed component"
    if len(nouns) == 1:
        return nouns[0]
    if len(nouns) == 2:
        return f"{nouns[0]} and {nouns[1]}"
    return f"{nouns[0]}, {nouns[1]}, and {nouns[2]}"


# ---------------------------------------------------------------------------
# Core parsing
# ---------------------------------------------------------------------------


def parse_intent(description: str) -> dict:
    """
    Extract intent from a natural language description.

    Returns:
        {
            "intent_category": "new_feature",   # from INTENT_PATTERNS
            "technologies": ["neo4j", "redis"], # matched from TECH_KEYWORDS
            "concerns": ["concurrent write", "transaction"],  # from tech concerns
            "nouns": ["session store", "writes"],  # key nouns extracted
            "raw": description
        }

    Uses regex + word matching, no LLM.
    """
    lower = description.lower()

    # --- Intent category ---
    intent_category = "new_feature"  # default
    intent_scores: dict[str, int] = {}
    for category, patterns in INTENT_PATTERNS.items():
        score = 0
        for pattern in patterns:
            if pattern in lower:
                # Multi-word patterns score higher
                score += len(pattern.split())
        if score > 0:
            intent_scores[category] = score

    if intent_scores:
        intent_category = max(intent_scores, key=lambda k: intent_scores[k])

    # --- Technologies ---
    technologies: list[str] = []
    for tech in TECH_KEYWORDS:
        if tech in lower:
            technologies.append(tech)

    # --- Concerns from matched technologies ---
    concerns: list[str] = []
    seen_concerns: set[str] = set()
    for tech in technologies:
        for concern in TECH_KEYWORDS[tech]["concerns"]:
            if concern not in seen_concerns:
                concerns.append(concern)
                seen_concerns.add(concern)

    # --- Nouns ---
    nouns = _extract_nouns(description)

    return {
        "intent_category": intent_category,
        "technologies": technologies,
        "concerns": concerns,
        "nouns": nouns,
        "raw": description,
    }


# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------

_EST_MINUTES_PER_QUESTION = 3


def _make_id(question_text: str) -> str:
    """Generate a stable short ID from question content."""
    h = hashlib.sha256(question_text.encode()).hexdigest()
    return f"NL-{h[:6]}"


def _render_template(template: str, tech: str, tech_type: str, nouns: list[str]) -> str:
    """Substitute placeholders in a question template."""
    noun_phrase = _noun_phrase(nouns)
    return (
        template.replace("{tech}", tech)
        .replace("{nouns}", noun_phrase)
        .replace("{tech_type}", tech_type)
    )


def generate_from_description(
    description: str,
    max_questions: int = 5,
) -> list[dict]:
    """
    Convert a plain English description → BL 2.0 question list.

    Generation logic:
    1. parse_intent(description)
    2. For each (intent_category, technology, concern) combination, generate a question
    3. If no technology matched, use generic templates based on intent_category alone
    4. Deduplicate and rank by specificity (more context = higher priority)
    5. Cap at max_questions

    Returns a list of question dicts compatible with questions.md format:
        {
            "id": "NL-a3f2b1",
            "title": "...",
            "mode": "diagnose",
            "domain": "D4",
            "status": "PENDING",
            "priority": "high",
            "source": "nl_entry",
            "question": "full question text",
            "estimated_minutes": 3
        }
    """
    intent = parse_intent(description)
    category = intent["intent_category"]
    technologies = intent["technologies"]
    nouns = intent["nouns"]

    domain = _DOMAIN_MAP.get(category, "D4")
    mode = _MODE_MAP.get(category, "diagnose")

    candidates: list[dict] = []

    # --- Tech-specific questions (highest specificity) ---
    for tech in technologies:
        tech_type = TECH_KEYWORDS[tech]["type"]
        type_templates = _TECH_TEMPLATES.get(tech_type, {})
        tech_concerns = TECH_KEYWORDS[tech]["concerns"]

        for concern in tech_concerns:
            concern_templates = type_templates.get(concern, [])
            for template in concern_templates:
                question_text = _render_template(template, tech, tech_type, nouns)
                qid = _make_id(description + concern + template)
                title = f"{tech.upper()} {concern} — {_noun_phrase(nouns)}"
                # Security concerns bump to D2
                effective_domain = (
                    "D2"
                    if category == "security"
                    or "auth" in concern
                    or "permission" in concern
                    else domain
                )
                candidates.append(
                    {
                        "id": qid,
                        "title": title,
                        "mode": mode,
                        "domain": effective_domain,
                        "status": "PENDING",
                        "priority": "high",
                        "source": "nl_entry",
                        "question": question_text,
                        "estimated_minutes": _EST_MINUTES_PER_QUESTION,
                        "_specificity": 3,  # tech + concern = most specific
                    }
                )

    # --- Generic intent-category questions (fallback or supplement) ---
    generic_templates = _GENERIC_TEMPLATES.get(
        category, _GENERIC_TEMPLATES["new_feature"]
    )
    for template in generic_templates:
        question_text = _render_template(template, "", "", nouns)
        qid = _make_id(description + template)
        title = f"{category.replace('_', ' ').title()} — {_noun_phrase(nouns)}"
        candidates.append(
            {
                "id": qid,
                "title": title,
                "mode": mode,
                "domain": domain,
                "status": "PENDING",
                "priority": "medium" if technologies else "high",
                "source": "nl_entry",
                "question": question_text,
                "estimated_minutes": _EST_MINUTES_PER_QUESTION,
                "_specificity": 1 if technologies else 2,
            }
        )

    # --- Deduplicate by ID ---
    seen_ids: set[str] = set()
    deduped: list[dict] = []
    for q in candidates:
        if q["id"] not in seen_ids:
            seen_ids.add(q["id"])
            deduped.append(q)

    # --- Rank by specificity descending ---
    deduped.sort(key=lambda q: q["_specificity"], reverse=True)

    # --- Cap ---
    result = deduped[:max_questions]

    # Strip internal field
    for q in result:
        q.pop("_specificity", None)

    return result


# ---------------------------------------------------------------------------
# questions.md serialization
# ---------------------------------------------------------------------------


def _question_to_md(q: dict) -> str:
    """Render a question dict as a questions.md block."""
    lines = [
        f"## {q['id']} [PENDING] {q['title']}",
        f"**Mode**: {q['mode']}",
        f"**Domain**: {q.get('domain', 'D4')}",
        f"**Priority**: {q.get('priority', 'high')}",
        "**Source**: nl_entry",
        "**Status**: PENDING",
        f"**Hypothesis**: {q['question']}",
        "**Test**: Read the relevant code and verify the behavior described above.",
        "**Verdict threshold**:",
        "- HEALTHY: No failure mode found; behavior is correct under the described conditions",
        "- FAILURE: A concrete failure mode, race, or correctness gap is found",
        "",
    ]
    return "\n".join(lines)


def _append_to_questions_md(questions: list[dict], project_dir: str) -> Path:
    """Append a new NL wave block to questions.md. Creates the file if absent."""
    questions_path = Path(project_dir) / "questions.md"

    wave_header = (
        "\n---\n\n## Wave NL — Generated from Natural Language Description\n\n---\n\n"
    )
    blocks = "\n---\n\n".join(_question_to_md(q) for q in questions)

    if not questions_path.exists():
        content = (
            "# Research Questions\n\nStatus values: PENDING | DONE | INCONCLUSIVE\n\n"
        )
        content += wave_header + blocks
        questions_path.write_text(content, encoding="utf-8")
    else:
        existing = questions_path.read_text(encoding="utf-8")
        questions_path.write_text(existing + wave_header + blocks, encoding="utf-8")

    return questions_path


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def quick_campaign(
    description: str,
    project_dir: str = ".",
    max_questions: int = 5,
) -> dict:
    """
    Full pipeline: description → questions → appended to questions.md.

    Returns:
        {
            "questions_generated": 4,
            "estimated_minutes": 12,
            "questions": [...],
            "next_step": "Run: ..."
        }
    """
    questions = generate_from_description(description, max_questions=max_questions)
    _append_to_questions_md(questions, project_dir)

    estimated_minutes = sum(q["estimated_minutes"] for q in questions)

    next_step = (
        "Run: DISABLE_OMC=1 claude --dangerously-skip-permissions "
        "'Read program.md and questions.md. Begin the research loop from the first "
        "PENDING question. NEVER STOP.'"
    )

    return {
        "questions_generated": len(questions),
        "estimated_minutes": estimated_minutes,
        "questions": questions,
        "next_step": next_step,
    }


def format_preview(questions: list[dict]) -> str:
    """
    Human-readable preview of generated questions.

    Format:
        Generated 4 questions (~12 min):

          [high] NL-a3f2b1  diagnose/D4
          Does the concurrent Neo4j write in session store handle transaction
          isolation correctly? What happens under 10+ simultaneous writes?

          [high] NL-b7c3d2  validate/D2
          ...

        Run /masonry-run to start the campaign.
    """
    if not questions:
        return "No questions generated — try a more specific description."

    total_minutes = sum(q["estimated_minutes"] for q in questions)
    lines = [
        f"Generated {len(questions)} question{'s' if len(questions) != 1 else ''} (~{total_minutes} min):\n"
    ]

    for q in questions:
        qid = q["id"]
        priority = q.get("priority", "high")
        mode = q.get("mode", "diagnose")
        domain = q.get("domain", "D4")
        question_text = q["question"]

        # Wrap question text at ~80 chars for readability
        words = question_text.split()
        wrapped_lines: list[str] = []
        current = "  "
        for word in words:
            if len(current) + len(word) + 1 > 82 and current.strip():
                wrapped_lines.append(current.rstrip())
                current = "  " + word + " "
            else:
                current += word + " "
        if current.strip():
            wrapped_lines.append(current.rstrip())

        lines.append(f"  [{priority}] {qid}  {mode}/{domain}")
        lines.extend(wrapped_lines)
        lines.append("")

    lines.append("Run /masonry-run to start the campaign.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo_description = "I just added concurrent Neo4j writes to the session store"
    print(f"Input: {demo_description!r}\n")
    questions = generate_from_description(demo_description)
    print(format_preview(questions))
