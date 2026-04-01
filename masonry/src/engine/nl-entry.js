'use strict';
// engine/nl-entry.js — Natural language entry point for BrickLayer 2.0.
//
// Port of bl/nl_entry.py to Node.js.
// Converts a plain English description into targeted BrickLayer research questions.

const crypto = require('crypto');

// ---------------------------------------------------------------------------
// Intent patterns — what kind of change was made
// ---------------------------------------------------------------------------

const INTENT_PATTERNS = {
  new_feature: [
    'just added', 'just built', 'implemented', 'created', 'new',
    'introduced', 'added', 'built', 'wrote',
  ],
  bug_fix: [
    'fixed', 'patched', 'resolved', 'corrected', 'repaired',
    'bugfix', 'bug fix', 'fix for', 'addressed',
  ],
  performance: [
    'optimized', 'faster', 'cache', 'latency', 'throughput',
    'speed', 'slow', 'bottleneck', 'profiling', 'memory', 'cpu', 'benchmark',
  ],
  security: [
    'auth', 'permission', 'encrypt', 'secret', 'token', 'access',
    'authentication', 'authorization', 'credential', 'privilege', 'acl', 'jwt', 'oauth', 'api key',
  ],
  data_model: [
    'schema', 'migration', 'database', 'table', 'column', 'index',
    'model', 'field', 'relation', 'foreign key', 'constraint',
  ],
  integration: [
    'api', 'webhook', 'endpoint', 'external', 'third-party',
    'connected', 'integrated', 'plugin', 'adapter', 'client', 'sdk',
  ],
  concurrency: [
    'concurrent', 'parallel', 'async', 'thread', 'lock', 'race',
    'mutex', 'semaphore', 'coroutine', 'worker', 'queue', 'batch', 'simultaneous', 'multi',
  ],
  config: [
    'config', 'setting', 'environment', 'variable', 'flag', 'toggle',
    'env', 'dotenv', 'feature flag', 'configuration',
  ],
  refactor: [
    'refactored', 'refactor', 'restructured', 'reorganized', 'split',
    'extracted', 'moved', 'renamed', 'cleaned up',
  ],
  deployment: [
    'deployed', 'deploy', 'container', 'kubernetes', 'k8s', 'ci/cd',
    'pipeline', 'release', 'rollout', 'helm', 'terraform',
  ],
};

// ---------------------------------------------------------------------------
// Technology keywords → concerns to probe
// ---------------------------------------------------------------------------

const TECH_KEYWORDS = {
  neo4j: {
    type: 'graph_db',
    concerns: ['transaction isolation', 'concurrent write', 'query performance', 'index'],
  },
  redis: {
    type: 'cache',
    concerns: ['eviction policy', 'ttl expiry', 'connection pool exhaustion', 'failover'],
  },
  postgres: {
    type: 'rdb',
    concerns: ['transaction deadlock', 'migration rollback', 'index bloat', 'connection limit'],
  },
  postgresql: {
    type: 'rdb',
    concerns: ['transaction deadlock', 'migration rollback', 'index bloat', 'connection limit'],
  },
  solana: {
    type: 'blockchain',
    concerns: ['integer overflow', 'reentrancy', 'account validation', 'signer check'],
  },
  fastapi: {
    type: 'api',
    concerns: ['input validation', 'auth middleware', 'rate limiting', 'error handling'],
  },
  docker: {
    type: 'infra',
    concerns: ['resource limits', 'network isolation', 'volume persistence', 'restart policy'],
  },
  ollama: {
    type: 'inference',
    concerns: ['request timeout', 'model load time', 'throughput under load', 'queue depth'],
  },
  websocket: {
    type: 'realtime',
    concerns: ['connection limit', 'message ordering', 'reconnect storm', 'memory leak'],
  },
  kafka: {
    type: 'queue',
    concerns: ['consumer lag', 'partition rebalance', 'message ordering', 'at-least-once delivery'],
  },
  celery: {
    type: 'task_queue',
    concerns: ['worker crash recovery', 'task retry storm', 'result backend expiry', 'lock contention'],
  },
  elasticsearch: {
    type: 'search',
    concerns: ['mapping explosion', 'shard allocation', 'query timeout', 'index refresh lag'],
  },
  s3: {
    type: 'object_store',
    concerns: ['eventual consistency', 'rate limiting', 'cost under load', 'multipart upload'],
  },
  jwt: {
    type: 'auth',
    concerns: ['token expiry handling', 'secret rotation', 'algorithm confusion', 'revocation gap'],
  },
  sqlite: {
    type: 'rdb',
    concerns: ['write lock contention', 'wal mode', 'connection pooling', 'data corruption'],
  },
  mongodb: {
    type: 'document_db',
    concerns: ['transaction isolation', 'index usage', 'oplog lag', 'write concern'],
  },
  qdrant: {
    type: 'vector_db',
    concerns: ['collection consistency', 'payload index', 'search timeout', 'upsert ordering'],
  },
};

// ---------------------------------------------------------------------------
// Domain / mode mapping
// ---------------------------------------------------------------------------

const _DOMAIN_MAP = {
  new_feature: 'D4', bug_fix: 'D4', performance: 'D4', security: 'D2',
  data_model: 'D4', integration: 'D4', concurrency: 'D4', config: 'D4',
  refactor: 'D4', deployment: 'D4',
};

const _MODE_MAP = {
  new_feature: 'diagnose', bug_fix: 'validate', performance: 'diagnose',
  security: 'validate', data_model: 'diagnose', integration: 'diagnose',
  concurrency: 'diagnose', config: 'validate', refactor: 'validate',
  deployment: 'diagnose',
};

// ---------------------------------------------------------------------------
// Generic question templates
// ---------------------------------------------------------------------------

const _GENERIC_TEMPLATES = {
  new_feature: [
    'What are the failure modes of {nouns} under load? At what scale does it break?',
    'Does {nouns} handle edge cases (empty input, null, zero, max values) correctly?',
    'What happens to {nouns} when a downstream dependency is unavailable or slow?',
    'Is there a race condition or ordering assumption in {nouns} that breaks under concurrency?',
    'What is the rollback strategy if {nouns} needs to be reverted in production?',
  ],
  bug_fix: [
    'Does the fix for {nouns} address the root cause or only the symptom? What are the regression risks?',
    'Are there other call sites or code paths that have the same bug pattern as {nouns}?',
    'What test coverage exists for {nouns}? Is the fix verifiable without a full integration run?',
    'Does the fix to {nouns} introduce any new edge cases or change observable behavior?',
  ],
  performance: [
    'What is the actual performance baseline for {nouns} before and after the optimization?',
    'Does the optimization in {nouns} hold under realistic production load (not just benchmarks)?',
    'Does the optimization introduce any correctness tradeoffs (caching stale data, skipping validation)?',
    'What is the worst-case performance for {nouns}? What triggers it?',
  ],
  security: [
    'Does {nouns} enforce authorization at every entry point, not just the UI?',
    'What happens if an attacker supplies malformed or boundary-exceeding input to {nouns}?',
    'Are secrets and credentials in {nouns} stored safely and never logged?',
    'What is the blast radius if {nouns} is compromised? Can it escalate to other systems?',
  ],
  data_model: [
    'Is the migration for {nouns} reversible? What is the rollback plan?',
    'Does the schema change to {nouns} break any existing queries or application code?',
    'What happens to {nouns} data integrity under concurrent writes during the migration window?',
    'Are indexes on {nouns} appropriate for the access patterns? Can any cause lock contention?',
  ],
  integration: [
    'What happens to {nouns} when the external service is down, slow, or rate-limiting?',
    'Does {nouns} handle authentication token expiry and refresh correctly?',
    'What is the retry and backoff strategy for {nouns}? Can it cause thundering herd?',
    'Are all inputs from the external service in {nouns} validated before use?',
  ],
  concurrency: [
    'Is there a race condition in {nouns} when two workers execute the same path simultaneously?',
    'Does {nouns} hold locks for longer than necessary, risking deadlock or starvation?',
    'What is the behavior of {nouns} when a worker crashes mid-operation? Is state left consistent?',
    'Does {nouns} scale linearly with concurrent workers, or does contention cause degradation?',
  ],
  config: [
    'Does {nouns} fail safely if the config value is missing, malformed, or out of range?',
    'Is the config for {nouns} validated at startup or only at first use?',
    'Can {nouns} be toggled at runtime without restart, and is there a rollback path?',
    'Are there undocumented interactions between {nouns} and other config values?',
  ],
  refactor: [
    'Does the refactor of {nouns} preserve all observable behavior under the existing test suite?',
    'Are there edge cases in {nouns} that were handled by accident (defensive code) and may now be missing?',
    'Does the refactored {nouns} have the same or better performance characteristics?',
  ],
  deployment: [
    'What is the failure mode for {nouns} if the deployment is partial (some instances old, some new)?',
    'Does {nouns} require downtime or can it be rolled out with zero-downtime deployment?',
    'What is the rollback procedure for {nouns} if the deployment fails mid-flight?',
    'Are there health checks for {nouns} that confirm successful deployment before traffic is shifted?',
  ],
};

// ---------------------------------------------------------------------------
// Tech-specific question templates
// ---------------------------------------------------------------------------

const _TECH_TEMPLATES = {
  graph_db: {
    'concurrent write': [
      'Does the concurrent write to {tech} in {nouns} use explicit transaction boundaries? '
      + 'What is the isolation level, and can two writers produce a dirty or phantom read?',
      'Under 10+ simultaneous writers to {tech} in {nouns}, is there a deadlock or write-skew '
      + 'failure mode? What is the retry policy?',
    ],
    'transaction isolation': [
      'Does {nouns} rely on {tech} transaction isolation to guarantee consistency, or does it '
      + 'assume optimistic single-writer access? What breaks if the assumption is wrong?',
    ],
    'query performance': [
      'What index coverage exists for the {tech} queries in {nouns}? Is there a full-graph scan '
      + 'that could cause latency spikes at production data volume?',
    ],
    index: [
      'Are the {tech} indexes for {nouns} correct for the query patterns? Can a missing or '
      + 'incorrect index cause query timeout under load?',
    ],
  },
  cache: {
    'eviction policy': [
      'If {tech} in {nouns} evicts a key under memory pressure, what is the fallback? Can the '
      + 'application reconstruct the value, or does this cause a hard failure?',
    ],
    'ttl expiry': [
      'When a {tech} key in {nouns} expires mid-request, is there a race between the read '
      + 'and the re-population that can serve stale or empty data?',
    ],
    'connection pool exhaustion': [
      'What happens to {nouns} if {tech} connection pool is exhausted? Does the caller block, '
      + 'fail fast, or queue? At what concurrent request volume does this trigger?',
    ],
    failover: [
      'Does {nouns} degrade gracefully when {tech} is unreachable? Is the fallback path tested?',
    ],
  },
  rdb: {
    'transaction deadlock': [
      'Can the transactions in {nouns} that write to {tech} deadlock? What is the lock acquisition '
      + 'order, and is there a consistent ordering enforced?',
    ],
    'migration rollback': [
      'Is the {tech} migration for {nouns} fully reversible with a down migration? Has the rollback '
      + 'been tested against a populated database?',
    ],
    'index bloat': [
      'Do the new {tech} indexes for {nouns} have an appropriate fill factor? Can they cause '
      + 'write amplification at high insert rates?',
    ],
    'connection limit': [
      'Does {nouns} use a {tech} connection pool with a bounded size? What happens when the pool '
      + 'limit is reached under burst load?',
    ],
  },
  blockchain: {
    'integer overflow': [
      'Are all arithmetic operations in {nouns} on {tech} checked for integer overflow? '
      + 'What is the worst-case value that could cause silent truncation?',
    ],
    reentrancy: [
      'Does {nouns} on {tech} update state before or after external calls? Can a malicious '
      + 'program call back into {nouns} before state is committed?',
    ],
    'account validation': [
      'Does {nouns} validate all {tech} account ownership and type before use? '
      + 'What happens if an attacker substitutes a different account?',
    ],
    'signer check': [
      'Are all privileged instructions in {nouns} on {tech} gated by a signer check? '
      + 'Can an unsigned transaction invoke any privileged path?',
    ],
  },
  api: {
    'input validation': [
      'Does every input to the {tech} endpoints in {nouns} have explicit type and range validation? '
      + 'What happens if an attacker sends an unexpected type or oversized payload?',
    ],
    'auth middleware': [
      'Is the auth middleware for {nouns} applied uniformly to all {tech} routes, including '
      + 'any newly added routes? Is there a route that bypasses it?',
    ],
    'rate limiting': [
      'Does {nouns} on {tech} have per-user or per-IP rate limits? What is the behavior '
      + 'under a burst of 1000 requests in 1 second?',
    ],
    'error handling': [
      'Do error responses from {nouns} on {tech} leak internal state, stack traces, or '
      + 'file paths? Is there a consistent error response schema?',
    ],
  },
  infra: {
    'resource limits': [
      'Does the {tech} container for {nouns} have CPU and memory limits set? What is the '
      + 'OOM behavior — restart policy and data safety?',
    ],
    'network isolation': [
      'Is the {tech} container for {nouns} network-isolated to only the services that need '
      + 'access? Can an attacker pivot from a compromised container?',
    ],
    'volume persistence': [
      'Are the volumes for {nouns} on {tech} persisted across container restarts? '
      + 'What data is lost if the container is replaced?',
    ],
    'restart policy': [
      'Does the {tech} restart policy for {nouns} cause a crash loop if the process fails '
      + 'immediately on start? Is there a backoff?',
    ],
  },
  inference: {
    'request timeout': [
      'What is the timeout configuration for {nouns} calling {tech}? Does a slow model '
      + 'response cascade into the caller and cause a timeout storm?',
    ],
    'model load time': [
      'What is the cold-start latency for {nouns} using {tech}? Can a process restart '
      + 'cause a request queue buildup during model load?',
    ],
    'throughput under load': [
      'What is the maximum sustained throughput for {nouns} through {tech}? At what request '
      + 'rate does queuing delay become observable?',
    ],
    'queue depth': [
      'Does {nouns} bound the {tech} request queue depth? What is the behavior when '
      + 'the queue is full — drop, block, or error?',
    ],
  },
  realtime: {
    'connection limit': [
      'What is the per-server connection limit for {nouns} using {tech}? What happens '
      + 'when it is reached — silent drop or explicit error?',
    ],
    'message ordering': [
      'Does {nouns} on {tech} guarantee message ordering? Can two messages from the same '
      + 'client arrive out of order, and does the application handle it?',
    ],
    'reconnect storm': [
      'If the {tech} server for {nouns} restarts, do all clients reconnect simultaneously? '
      + 'Is there jitter in the reconnect backoff?',
    ],
    'memory leak': [
      'Are {tech} connections in {nouns} properly closed on client disconnect? '
      + 'Is there a resource leak when connections are abandoned (no close frame)?',
    ],
  },
  queue: {
    'consumer lag': [
      'Under what message rate does the {tech} consumer for {nouns} accumulate lag? '
      + 'What is the recovery time after a consumer restart?',
    ],
    'partition rebalance': [
      'Does a {tech} partition rebalance for {nouns} cause duplicate processing or '
      + 'message loss during the rebalance window?',
    ],
    'message ordering': [
      'Does {nouns} depend on {tech} message ordering across partitions? '
      + 'Is there a sequence number or deduplication key?',
    ],
    'at-least-once delivery': [
      'Does {nouns} handle {tech} duplicate delivery idempotently? '
      + 'What is the state left if a message is processed twice?',
    ],
  },
  task_queue: {
    'worker crash recovery': [
      'If a {tech} worker for {nouns} crashes mid-task, is the task requeued and retried '
      + 'safely, or is it silently dropped?',
    ],
    'task retry storm': [
      'Does the retry policy for {nouns} on {tech} use exponential backoff? '
      + 'Can a failing task cause a retry storm that saturates the queue?',
    ],
    'result backend expiry': [
      'Does {nouns} read results from {tech} within the result backend TTL? '
      + 'What happens when the result expires before it is read?',
    ],
    'lock contention': [
      'Are {tech} task locks in {nouns} scoped narrowly enough to avoid contention? '
      + 'What is the worst-case lock hold time?',
    ],
  },
  vector_db: {
    'collection consistency': [
      'Does {nouns} ensure {tech} writes are flushed before reading them back? '
      + 'Can a read-after-write return stale results?',
    ],
    'payload index': [
      'Are the {tech} payload indexes for {nouns} covering the filter fields used in searches? '
      + 'Can a missing index cause full-collection scans?',
    ],
    'search timeout': [
      'What is the timeout for {tech} similarity searches in {nouns}? '
      + 'At what collection size does search latency exceed the SLA?',
    ],
    'upsert ordering': [
      'If two concurrent upserts to {tech} in {nouns} use the same ID, which wins? '
      + 'Is the result deterministic, or can partial state be written?',
    ],
  },
  object_store: {
    'eventual consistency': [
      'Does {nouns} read from {tech} immediately after a write? '
      + 'Can eventual consistency cause {nouns} to see an old version?',
    ],
    'rate limiting': [
      'Does {nouns} handle {tech} rate limit errors (HTTP 503/429) with backoff? '
      + 'Can a burst cause a cascading retry loop?',
    ],
    'cost under load': [
      'What is the estimated {tech} cost for {nouns} at 10x current request volume? '
      + 'Is there a request pattern that causes unexpected cost amplification?',
    ],
    'multipart upload': [
      'Does {nouns} use multipart uploads for large objects to {tech}? '
      + 'What is the cleanup strategy for incomplete multipart uploads?',
    ],
  },
  auth: {
    'token expiry handling': [
      'Does {nouns} handle {tech} token expiry gracefully — refreshing silently or failing '
      + 'fast with a clear error rather than serving a stale authenticated response?',
    ],
    'secret rotation': [
      'Can the {tech} signing secret in {nouns} be rotated without downtime? '
      + 'Is there a grace period for tokens signed with the old secret?',
    ],
    'algorithm confusion': [
      'Does {nouns} pin the {tech} algorithm to a specific value? '
      + 'Can an attacker supply a token with `alg: none` or switch to a weak algorithm?',
    ],
    'revocation gap': [
      'How long does a revoked {tech} token remain valid in {nouns}? '
      + 'Is there a blocklist or short-TTL design to close the revocation gap?',
    ],
  },
  search: {
    'mapping explosion': [
      'Can {nouns} send dynamic fields to {tech} that cause mapping explosion? '
      + 'Is there a strict mapping with `dynamic: strict` or equivalent?',
    ],
    'shard allocation': [
      'Are {tech} shards for {nouns} sized appropriately for the expected document count? '
      + 'Can over-sharding cause excessive overhead?',
    ],
    'query timeout': [
      'Does {nouns} set a timeout on {tech} queries? '
      + 'What is the behavior when a query times out — error or partial results?',
    ],
    'index refresh lag': [
      'Does {nouns} read from {tech} immediately after indexing? '
      + 'Can the refresh interval cause stale search results?',
    ],
  },
  document_db: {
    'transaction isolation': [
      'Does the transaction in {nouns} on {tech} use the correct write concern and '
      + 'read concern to prevent dirty reads?',
    ],
    'index usage': [
      'Are the queries in {nouns} on {tech} using indexes? '
      + 'Can a collection scan under production data volume cause latency spikes?',
    ],
    'oplog lag': [
      'Can replica lag in {tech} cause {nouns} to read stale data from a secondary? '
      + 'Is there a read preference override for consistency-critical reads?',
    ],
    'write concern': [
      'Does {nouns} use an appropriate {tech} write concern for durability? '
      + 'What data is lost if the primary fails before replication?',
    ],
  },
};

// ---------------------------------------------------------------------------
// Noun extraction helpers
// ---------------------------------------------------------------------------

const _STOPWORDS = new Set([
  'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
  'of', 'with', 'by', 'from', 'is', 'it', 'this', 'that', 'was', 'are',
  'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
  'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can',
  'just', 'i', 'my', 'we', 'our', 'so', 'also', 'now', 'then', 'into',
  'onto', 'over', 'under', 'when', 'which', 'who', 'where', 'what',
  'how', 'if', 'as', 'about', 'up', 'out', 'off', 'some', 'new',
  'added', 'built', 'fixed', 'refactored', 'use', 'used', 'using',
  'via', 'get', 'set', 'run', 'make', 'put', 'call', 'send', 'read', 'write',
]);

const _COMPOUND_PATTERNS = [
  'session store', 'connection pool', 'message queue', 'event loop',
  'worker thread', 'background task', 'rate limit(?:er|ing)?',
  'circuit breaker', 'retry logic', 'health check', 'dead letter',
  'write ahead log', 'foreign key', 'primary key', 'api endpoint',
  'auth(?:entication|orization)? middleware', 'cache layer',
  'data model', 'object store', 'vector store', 'graph store',
];

const _COMPOUND_RE = new RegExp(
  '\\b(?:' + _COMPOUND_PATTERNS.join('|') + ')\\b', 'gi',
);

function _extractNouns(text) {
  const found = [];
  const lower = text.toLowerCase();

  // 1. Compound phrases first
  let m;
  const re = new RegExp(_COMPOUND_RE.source, _COMPOUND_RE.flags);
  while ((m = re.exec(lower)) !== null) {
    found.push(m[0]);
  }

  // 2. Remaining single words that are not stopwords or intent verbs
  const intentVerbs = new Set();
  for (const patterns of Object.values(INTENT_PATTERNS)) {
    for (const p of patterns) {
      if (!p.includes(' ')) intentVerbs.add(p);
    }
  }
  const techNames = new Set(Object.keys(TECH_KEYWORDS));

  const words = lower.match(/\b[a-z][a-z0-9_-]*\b/g) || [];
  for (const w of words) {
    if (!_STOPWORDS.has(w) && !intentVerbs.has(w) && !techNames.has(w) && w.length >= 3) {
      found.push(w);
    }
  }

  // Filter out single words already covered by compound phrases
  const compoundWords = new Set();
  for (const item of found) {
    if (item.includes(' ')) {
      for (const word of item.split(' ')) {
        compoundWords.add(word);
      }
    }
  }

  const seen = new Set();
  const result = [];
  for (const item of found) {
    if (!seen.has(item)) {
      if (!item.includes(' ') && compoundWords.has(item)) continue;
      seen.add(item);
      result.push(item);
    }
  }

  return result.slice(0, 6);
}

function _nounPhrase(nouns) {
  if (!nouns.length) return 'the changed component';
  if (nouns.length === 1) return nouns[0];
  if (nouns.length === 2) return `${nouns[0]} and ${nouns[1]}`;
  return `${nouns[0]}, ${nouns[1]}, and ${nouns[2]}`;
}

// ---------------------------------------------------------------------------
// Core parsing
// ---------------------------------------------------------------------------

function parseIntent(description) {
  const lower = description.toLowerCase();

  // Intent category
  let intentCategory = 'new_feature';
  const intentScores = {};
  for (const [category, patterns] of Object.entries(INTENT_PATTERNS)) {
    let score = 0;
    for (const pattern of patterns) {
      if (lower.includes(pattern)) {
        score += pattern.split(' ').length;
      }
    }
    if (score > 0) intentScores[category] = score;
  }

  if (Object.keys(intentScores).length > 0) {
    intentCategory = Object.keys(intentScores).reduce((a, b) =>
      intentScores[a] >= intentScores[b] ? a : b,
    );
  }

  // Technologies
  const technologies = [];
  for (const tech of Object.keys(TECH_KEYWORDS)) {
    if (lower.includes(tech)) technologies.push(tech);
  }

  // Concerns from matched technologies
  const concerns = [];
  const seenConcerns = new Set();
  for (const tech of technologies) {
    for (const concern of TECH_KEYWORDS[tech].concerns) {
      if (!seenConcerns.has(concern)) {
        concerns.push(concern);
        seenConcerns.add(concern);
      }
    }
  }

  // Nouns
  const nouns = _extractNouns(description);

  return {
    intentCategory,
    technologies,
    concerns,
    nouns,
    raw: description,
  };
}

// ---------------------------------------------------------------------------
// Question generation
// ---------------------------------------------------------------------------

const _EST_MINUTES_PER_QUESTION = 3;

function _makeId(questionText) {
  const h = crypto.createHash('sha256').update(questionText).digest('hex');
  return `NL-${h.slice(0, 6)}`;
}

function _renderTemplate(template, tech, techType, nouns) {
  const nounPhrase = _nounPhrase(nouns);
  return template
    .replace(/\{tech\}/g, tech)
    .replace(/\{nouns\}/g, nounPhrase)
    .replace(/\{tech_type\}/g, techType);
}

function generateFromDescription(description, maxQuestions = 5) {
  const intent = parseIntent(description);
  const category = intent.intentCategory;
  const technologies = intent.technologies;
  const nouns = intent.nouns;

  const domain = _DOMAIN_MAP[category] || 'D4';
  const mode = _MODE_MAP[category] || 'diagnose';

  const candidates = [];

  // Tech-specific questions (highest specificity)
  for (const tech of technologies) {
    const techType = TECH_KEYWORDS[tech].type;
    const typeTemplates = _TECH_TEMPLATES[techType] || {};
    const techConcerns = TECH_KEYWORDS[tech].concerns;

    for (const concern of techConcerns) {
      const concernTemplates = typeTemplates[concern] || [];
      for (const template of concernTemplates) {
        const questionText = _renderTemplate(template, tech, techType, nouns);
        const qid = _makeId(description + concern + template);
        const title = `${tech.toUpperCase()} ${concern} — ${_nounPhrase(nouns)}`;
        const effectiveDomain = (
          category === 'security' || concern.includes('auth') || concern.includes('permission')
        ) ? 'D2' : domain;

        candidates.push({
          id: qid, title, mode, domain: effectiveDomain,
          status: 'PENDING', priority: 'high', source: 'nl_entry',
          question: questionText,
          estimated_minutes: _EST_MINUTES_PER_QUESTION,
          _specificity: 3,
        });
      }
    }
  }

  // Generic intent-category questions
  const genericTemplates = _GENERIC_TEMPLATES[category] || _GENERIC_TEMPLATES.new_feature;
  for (const template of genericTemplates) {
    const questionText = _renderTemplate(template, '', '', nouns);
    const qid = _makeId(description + template);
    const title = `${category.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())} — ${_nounPhrase(nouns)}`;

    candidates.push({
      id: qid, title, mode, domain,
      status: 'PENDING',
      priority: technologies.length ? 'medium' : 'high',
      source: 'nl_entry',
      question: questionText,
      estimated_minutes: _EST_MINUTES_PER_QUESTION,
      _specificity: technologies.length ? 1 : 2,
    });
  }

  // Deduplicate by ID
  const seenIds = new Set();
  const deduped = [];
  for (const q of candidates) {
    if (!seenIds.has(q.id)) {
      seenIds.add(q.id);
      deduped.push(q);
    }
  }

  // Rank by specificity descending
  deduped.sort((a, b) => b._specificity - a._specificity);

  // Cap
  const result = deduped.slice(0, maxQuestions);

  // Strip internal field
  for (const q of result) {
    delete q._specificity;
  }

  return result;
}

// ---------------------------------------------------------------------------
// Preview formatting
// ---------------------------------------------------------------------------

function formatPreview(questions) {
  if (!questions.length) {
    return 'No questions generated — try a more specific description.';
  }

  const totalMinutes = questions.reduce((sum, q) => sum + (q.estimated_minutes || 0), 0);
  const lines = [
    `Generated ${questions.length} question${questions.length !== 1 ? 's' : ''} (~${totalMinutes} min):\n`,
  ];

  for (const q of questions) {
    const priority = q.priority || 'high';
    const mode = q.mode || 'diagnose';
    const domain = q.domain || 'D4';
    const questionText = q.question;

    const words = questionText.split(/\s+/);
    const wrappedLines = [];
    let current = '  ';
    for (const word of words) {
      if (current.length + word.length + 1 > 82 && current.trim()) {
        wrappedLines.push(current.trimEnd());
        current = '  ' + word + ' ';
      } else {
        current += word + ' ';
      }
    }
    if (current.trim()) wrappedLines.push(current.trimEnd());

    lines.push(`  [${priority}] ${q.id}  ${mode}/${domain}`);
    lines.push(...wrappedLines);
    lines.push('');
  }

  lines.push('Run /masonry-run to start the campaign.');
  return lines.join('\n');
}

module.exports = {
  INTENT_PATTERNS,
  TECH_KEYWORDS,
  parseIntent,
  generateFromDescription,
  formatPreview,
};
