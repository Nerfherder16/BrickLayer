# Repo Research: promptfoo/promptfoo
**Repo**: https://github.com/promptfoo/promptfoo
**Researched**: 2026-03-28
**License**: MIT (Note: Promptfoo was acquired by OpenAI in 2026 — remains open source)
**Stars**: Production-grade, battle-tested
**Stack**: TypeScript/Node.js, React 19/Vite (UI), Drizzle ORM, Vitest, SQLite/disk cache

---

## Verdict Summary

Promptfoo is the most complete open-source LLM evaluation framework available. It covers the full spectrum from deterministic unit tests to adversarial red-teaming to CI/CD integration. For BrickLayer 2.0, it is immediately harvestable as a **drop-in replacement for `eval_agent.py`** and provides a complete red-teaming system that BL currently lacks entirely.

The `improve_agent.py` loop (eval → optimize → compare) maps almost perfectly to promptfoo's eval pipeline. The 50+ assertion types, 40+ red-team plugins, 25+ attack strategies, and native Claude/Anthropic support make this the highest-value external codebase for BL agent quality measurement.

**Verdict: CRITICAL HARVEST — integrate promptfoo as BL's eval engine, not a competitor to build against.**

---

## File Inventory (key files)

```
Root
├── src/
│   ├── evaluator.ts          (94KB) — core eval loop orchestrator
│   ├── evaluatorHelpers.ts   (27KB) — test case resolution, prompt rendering
│   ├── matchers.ts           (63KB) — assertion matching engine (all 50+ types)
│   ├── cache.ts              (11KB) — disk/memory caching with Keyv + KeyvFile
│   ├── index.ts              (7KB)  — public API (evaluate, loadApiProvider, redteam.*)
│   ├── assertions/           — one file per assertion type (50+ files)
│   │   ├── index.ts          — main assertion dispatcher
│   │   ├── trajectory.ts     (17KB) — agent trajectory evaluation
│   │   ├── synthesis.ts      (23KB) — composite/synthesis assertions
│   │   ├── toolCallF1.ts     (8KB)  — tool call F1 scoring
│   │   ├── llmRubric.ts      — LLM-as-judge rubric evaluation
│   │   ├── factuality.ts     — factuality checking
│   │   ├── contextFaithfulness.ts — RAG faithfulness (RAGAS-style)
│   │   ├── contextRecall.ts  — RAG recall measurement
│   │   ├── similar.ts        — embedding cosine similarity
│   │   ├── javascript.ts     — arbitrary JS eval assertions
│   │   ├── python.ts         — arbitrary Python eval assertions
│   │   ├── bleu.ts           — BLEU score
│   │   ├── rouge.ts          — ROUGE score
│   │   ├── meteor.ts         — METEOR score
│   │   ├── geval.ts          — G-Eval metric
│   │   ├── cost.ts           — cost threshold assertion
│   │   ├── latency.ts        — latency threshold assertion
│   │   └── traceErrorSpans.ts, traceSpanCount.ts — OpenTelemetry trace assertions
│   ├── redteam/
│   │   ├── index.ts          (50KB) — redteam orchestrator
│   │   ├── graders.ts        (19KB) — attack success evaluators
│   │   ├── riskScoring.ts    (16KB) — severity scoring engine
│   │   ├── plugins/          — 50+ attack plugins (one per vulnerability type)
│   │   └── strategies/       — 30+ delivery techniques
│   ├── providers/            — 50+ LLM provider integrations
│   └── integrations/
│       ├── helicone.ts       — Helicone observability
│       ├── langfuse.ts       — Langfuse tracing
│       ├── huggingfaceDatasets.ts — HuggingFace dataset loading
│       └── portkey.ts        — Portkey gateway
├── plugins/promptfoo-evals/  — Claude Code agent skill for writing evals
├── .claude-plugin/           — Claude marketplace plugin registration
├── code-scan-action/         — GitHub Action for PR code scanning
└── .github/workflows/
    ├── main.yml              — CI (lint, type-check, unit tests, integration tests)
    └── promptfoo-code-scan.yml — Security scan on PRs
```

---

## Architecture Overview

### Core Eval Loop

```
promptfooconfig.yaml
        ↓
   evaluator.ts
        ↓ (parallel, concurrency: N)
  ┌─────────────────────────────────┐
  │  For each (prompt × provider    │
  │  × test_case) combination:      │
  │                                 │
  │  1. Resolve variables           │
  │  2. Render prompt (Nunjucks)    │
  │  3. Check cache (disk/memory)   │
  │  4. Call provider API           │
  │  5. Run all assertions          │
  │  6. Aggregate results           │
  └─────────────────────────────────┘
        ↓
  Results: pass/fail, scores, costs,
  latency, token counts, per-assertion
        ↓
  Output: JSON, CSV, HTML, web UI,
  shareable URL, CI annotations
```

### Config File Format (`promptfooconfig.yaml`)

```yaml
description: "My eval suite"
prompts:
  - "file://prompts/system.txt"
  - "You are a helpful assistant. {{context}}"

providers:
  - anthropic:claude-sonnet-4-6
  - id: openai:gpt-4o
    config:
      temperature: 0.7
      max_tokens: 2048

defaultTest:
  assert:
    - type: is-json
    - type: latency
      threshold: 5000
  options:
    transform: "output.trim()"

tests:
  - vars:
      context: "{{file://data/contexts.csv}}"
    assert:
      - type: contains
        value: "expected phrase"
      - type: llm-rubric
        value: "Response is helpful and factually accurate"
      - type: similar
        value: "reference answer"
        threshold: 0.8
      - type: javascript
        value: "output.length < 500"
      - type: python
        value: "file://assertions/custom_check.py"

outputPath: results/eval-{{timestamp}}.json
```

### Provider Model

Every provider implements `ApiProvider`:
```typescript
interface ApiProvider {
  id(): string;
  callApi(prompt: string, context?: ApiProviderContext): Promise<ProviderResponse>;
  cleanup?(): Promise<void>;
}
```

ProviderResponse includes: `output`, `error`, `tokenUsage`, `cost`, `latencyMs`, `cached`, `metadata`.

50+ provider implementations including: Anthropic (native), OpenAI, Azure OpenAI, AWS Bedrock, Google Vertex, Ollama, Hugging Face, HTTP (generic REST), Python (custom), JavaScript (custom), Go (custom), Ruby (custom), WebSocket, browser (Playwright), and more.

### Assertion System

The assertion dispatcher in `matchers.ts` routes to specialized implementations. Every assertion returns: `{ pass: boolean, score: number, reason: string }`.

---

## Feature Catalog

### Eval Features
- **Prompt testing**: Compare prompts side-by-side across models, spot regressions
- **Model comparison**: Run same tests against multiple providers simultaneously
- **Concurrency control**: Configurable parallel execution (`--max-concurrency`)
- **Variable system**: Nunjucks templates, CSV imports, Python/JS generators, Google Sheets
- **Caching**: Disk-based (KeyvFile, `~/.promptfoo/cache.json`), 14-day TTL, concurrent-request deduplication
- **Output formats**: JSON, YAML, CSV, HTML table, interactive web viewer
- **Shareable results**: `promptfoo share` uploads to cloud viewer
- **Extension hooks**: `beforeAll`, `afterAll`, `beforeEach`, `afterEach` lifecycle hooks
- **Transform pipeline**: Pre/post-process prompts and outputs via JS/Python scripts
- **Scenarios**: Matrix of variable combinations for combinatorial testing

### Assertion Types (50+)
**Deterministic (free, fast):**
- `equals` — exact match
- `contains` / `icontains` — substring (case insensitive)
- `not-contains` — absence check
- `starts-with` — prefix check
- `regex` — regex match
- `is-json` — valid JSON
- `is-xml` — valid XML
- `is-sql` — valid SQL
- `is-html` — valid HTML
- `contains-json` — JSON somewhere in output
- `javascript` — arbitrary JS function returning bool/score
- `python` — arbitrary Python script
- `ruby` — arbitrary Ruby script
- `webhook` — call HTTP endpoint
- `word-count` — word count threshold
- `finish-reason` — stop reason (stop/length/tool_calls)
- `cost` — cost threshold
- `latency` — latency threshold (ms)
- `perplexity` — language model perplexity
- `levenshtein` — edit distance
- `bleu` / `gleu` / `rouge` / `meteor` — NLP metrics

**Model-graded (use LLM as judge):**
- `llm-rubric` — arbitrary rubric evaluated by grader LLM
- `model-graded-closedqa` — closed-QA factuality
- `model-graded-factuality` — factual accuracy
- `answer-relevance` — answer-to-question relevance
- `context-faithfulness` — RAG faithfulness (RAGAS-style)
- `context-recall` — RAG recall
- `context-relevance` — RAG context relevance
- `g-eval` — G-Eval framework
- `similar` — embedding cosine similarity
- `classifier` — custom classifier
- `moderation` — content moderation
- `guardrails` — custom guardrail checks
- `search-rubric` — search quality rubric

**Agent-specific:**
- `trajectory` — multi-step agent trajectory evaluation
- `tool-call` — validate specific tool was called with args
- `tool-call-f1` — F1 score across expected tool calls
- `function-tool-call` — function call validation

**Tracing/Observability (OpenTelemetry):**
- `trace-error-spans` — check for error spans in traces
- `trace-span-count` — count of spans
- `trace-span-duration` — span duration threshold

**Redteam-specific:**
- `redteam` — internal redteam assertion dispatcher

### Red-Teaming System

A complete adversarial testing framework with three layers:

**Plugins (what to attack):**
- `hallucination` — factual accuracy
- `pii` — PII leakage (4 sub-types)
- `prompt-extraction` — system prompt extraction
- `excessive-agency` — scope creep, over-action
- `goal-misalignment` — divergence from intended purpose
- `bfla` / `bola` — broken function/object level auth
- `rbac` — RBAC bypass
- `sql-injection` — SQL injection via prompts
- `shell-injection` — shell injection
- `ssrf` — server-side request forgery
- `data-exfil` — data exfiltration
- `cross-session-leak` — session data leakage
- `indirect-prompt-injection` — injected context attacks
- `mcp` — MCP protocol vulnerability testing
- `debug-access` — debug endpoint exposure
- `ascii-smuggling` — Unicode/ASCII smuggling
- `competitors` — competitor endorsement
- `contracts` — unauthorized legal commitments
- `hallucination`, `overreliance`, `hijacking` — trust manipulation
- `bias`, `politics`, `religion` — sensitive topics
- `harmful/*` — 13 harmful content categories
- `beavertails`, `harmbench`, `donotanswer`, `cyberseceval`, `xstest`, `toxicChat`, `vlguard`, `vlsu`, `unsafebench` — benchmark-driven plugins
- `custom` — bring your own plugin
- Industry verticals: `financial`, `ecommerce`, `insurance`, `medical`, `pharmacy`, `realestate`, `telecom`
- Agentic: `goal-misalignment`, `excessive-agency`, `tool-discovery`, `reasoning-dos`

**Strategies (how to deliver attacks):**
- `jailbreak` (iterative, PAIR-style)
- `jailbreak:tree` — tree-of-attacks with pruning (TAP)
- `jailbreak:crescendo` — escalating multi-turn
- `jailbreak:goat` — goal hijacking
- `jailbreak:hydra` — multi-path
- `jailbreak:simba` — SIMBA-style
- `best-of-n` — best-of-N sampling
- `prompt-injection` — direct injection
- `gcg` — gradient-based adversarial suffixes
- `base64` / `hex` / `rot13` / `leetspeak` / `homoglyph` — encoding bypasses
- `mathPrompt` — math obfuscation
- `multilingual` — cross-language attacks
- `citation` — fake citation authority
- `authoritative-markup-injection` — structured markup injection
- `composite-jailbreaks` — multi-strategy composition
- `layer` — sequential strategy chaining
- `simpleImage` / `simpleAudio` / `simpleVideo` — multimodal attacks
- `retry` — smart retry on failures
- `custom` — JS/Python custom strategies

**Risk Scoring:** Critical → High → Medium → Low with CVSS-style severity mapping. Frameworks: NIST AI RMF, OWASP LLM Top 10, OWASP API Security, MITRE ATLAS.

### Dataset / Test Case Management
- CSV files with header row = variable names
- YAML arrays with full test structure
- Google Sheets integration (live sync)
- HuggingFace dataset loading (`huggingfaceDatasets.ts`)
- Microsoft SharePoint integration
- `file://` glob patterns for bulk test loading
- Python/JS generators for dynamic test creation
- `$ref` for reusable assertion templates

### CI/CD Integration
- **GitHub Action** (`promptfoo/action@v9`): Triggers on PR path changes, posts before/after comparison comment with web viewer link
- **Code Scan Action** (`promptfoo/code-scan-action@v0`): Security-focused scan on PRs, configurable severity threshold, posts findings as PR comments
- **Exit codes**: `promptfoo eval` returns non-zero on failures (CI-safe)
- **`--ci` flag**: Suppresses interactive output, machine-readable JSON
- **Configurable thresholds**: `--pass-rate-threshold`, `--severity-threshold`
- **SARIF output**: Compatible with GitHub Code Scanning / Security tab

### Web UI
- React 19 + Vite SPA at `src/ui/`
- Launched with `promptfoo view`
- Features: side-by-side comparison grid, per-assertion drill-down, pass/fail heatmap, model comparison stats, filtering/sorting, export

### Caching
- Backend: Keyv + KeyvFile (disk) stored at `~/.cache/promptfoo/` or `~/.promptfoo/promptfoo.db`
- Default TTL: 14 days
- Key: `fetch:v2:{url}:{options}` (headers excluded)
- Concurrent request deduplication via in-flight Map
- `--no-cache` flag for fresh runs
- `cached: true` flag in responses lets downstream skip rate limiting delays

### MCP Integration
- Native MCP vulnerability plugin (`src/redteam/plugins/mcp.ts`) — tests for MCP-specific exploits: tool discovery, parameter injection, privilege escalation through MCP interfaces
- Claude Code agent skill (`plugins/promptfoo-evals/`) — enables Claude Code to write and maintain promptfoo eval suites
- Marketplace plugin registration (`.claude-plugin/marketplace.json`)

### Custom Evaluator / Plugin System
- Custom providers: implement `ApiProvider` interface (TS, JS, Python, Go, Ruby)
- Custom assertions: `javascript` and `python` type with arbitrary logic
- Custom redteam plugins: extend `RedteamPluginBase`, implement `getTemplate()` + assertions
- Custom strategies: JS function that transforms test cases
- Extension hooks for lifecycle management

### Scoring / Metrics Aggregation
- Per-assertion: `pass` (bool), `score` (0-1 float), `reason` (string)
- Per-test: aggregate score across assertions (weighted)
- Per-eval: pass rate %, average score, total cost, total latency
- Token usage tracking: prompt tokens, completion tokens, total
- Cost tracking: per-provider cost per token
- Latency histograms
- Redteam-specific: attack success rate, severity breakdown, risk score

### Observability Integrations
- Helicone: request logging proxy
- Langfuse: tracing + experiment tracking
- Portkey: gateway with observability
- OpenTelemetry trace assertions (built-in)

---

## Claude/Anthropic Integration

Promptfoo has **first-class Claude support** — arguably the best of any eval framework.

**Provider ID format:**
```yaml
providers:
  - anthropic:claude-sonnet-4-6         # Latest Sonnet
  - anthropic:claude-opus-4-6           # Latest Opus
  - anthropic:claude-haiku-4-5-20251001 # Specific version
  - bedrock:anthropic.claude-sonnet-4-6  # Via Bedrock
  - vertex:claude-sonnet-4-6            # Via Vertex
```

**Auth:** `ANTHROPIC_API_KEY` env var (auto-detected)

**Claude-specific config options:**
```yaml
providers:
  - id: anthropic:claude-opus-4-6
    config:
      temperature: 1.0
      max_tokens: 16000
      thinking:
        type: enabled         # or "adaptive" (Opus) or "disabled"
        budget_tokens: 10000  # min 1024
      showThinking: true      # include thinking in output
      tools:
        - name: search
          description: "Search the web"
          input_schema: {...}
      tool_choice: auto
      output_format:          # structured output (Sonnet 4.5+, Opus 4.1+)
        type: json_schema
        json_schema: {...}
      headers:
        x-custom-header: value
```

**Auto-grader behavior:** When `ANTHROPIC_API_KEY` is set and `OPENAI_API_KEY` is not, Claude automatically serves as the grading model for all `llm-rubric`, `model-graded-*`, and `factuality` assertions.

**Prompt caching:** Supported for Claude 3, 3.5, 4 models — reduces eval costs significantly for repeated system prompts.

**Vision:** Base64 image input supported (Claude 3+).

**Extended thinking:** Full support including adaptive mode (Opus 4.6 recommended).

**Claude Code skill:** The `promptfoo-evals` Claude Code plugin lets Claude Code write and maintain promptfoo eval suites natively.

---

## Feature Gap Analysis

| Feature | In promptfoo | In BrickLayer 2.0 | Gap Level | Notes |
|---------|-------------|-------------------|-----------|-------|
| LLM-as-judge rubric evaluation | Yes (`llm-rubric`) | Partial (metrics.py heuristics) | HIGH | BL uses heuristics; promptfoo uses full LLM grading |
| Held-out eval dataset format | Yes (YAML/CSV/JSON) | Yes (`scored_all.jsonl`) | LOW | Different formats, same concept |
| Eval-optimize-compare loop | Partial (via API) | Yes (`improve_agent.py`) | LOW | BL's loop is actually more automated |
| Red-teaming / adversarial testing | Yes (50+ plugins, 25+ strategies) | None | CRITICAL | BL has zero adversarial testing capability |
| Prompt regression testing | Yes (CI GitHub Action) | None | HIGH | No automated prompt regression in BL |
| CI/CD integration | Yes (GitHub Actions, exit codes) | None | HIGH | BL evals are manual only |
| Provider comparison (A/B) | Yes (multi-provider per eval) | No | HIGH | BL evals one agent at a time |
| Caching of eval runs | Yes (disk, 14-day TTL) | No | MEDIUM | BL re-runs every eval fresh |
| Web dashboard for eval results | Yes (local + shareable) | None (Kiln not connected) | MEDIUM | Kiln shows campaign state, not eval metrics |
| BLEU/ROUGE/METEOR NLP metrics | Yes (built-in) | No | MEDIUM | BL uses custom heuristics only |
| Embedding similarity assertions | Yes (`similar` with cosine) | No | MEDIUM | Useful for semantic verdict matching |
| Factuality checking | Yes (`model-graded-factuality`) | Partial (verdict_match heuristic) | MEDIUM | BL's heuristic is weaker |
| RAG-specific metrics | Yes (faithfulness, recall, relevance) | No | LOW | BL doesn't have RAG evals |
| Tool call evaluation | Yes (`tool-call`, `tool-call-f1`) | No | MEDIUM | Relevant for agentic BL tasks |
| Agent trajectory evaluation | Yes (`trajectory` assertion) | No | MEDIUM | Full multi-step agent eval |
| Cost tracking | Yes (per-token cost per eval) | No | LOW | BL doesn't track eval costs |
| Latency tracking | Yes (per-call latency) | No | LOW | BL doesn't track latency |
| HuggingFace dataset loading | Yes | No | LOW | Useful for benchmark evals |
| OpenTelemetry trace assertions | Yes | No | LOW | Advanced observability |
| MCP vulnerability testing | Yes (`mcp` plugin) | No | HIGH | BL uses MCP extensively — needs this |
| Custom Python assertions | Yes (`python` type) | Yes (metrics.py) | LOW | Both support Python evals |
| CSV/Google Sheets test cases | Yes | No | LOW | BL uses JSONL |
| Concurrency control | Yes (configurable) | No | LOW | BL runs sequentially |
| EMA scoring / trend tracking | No | Yes (`ema_history.json`) | N/A — BL advantage | promptfoo doesn't track agent improvement over time |
| Agent registry + tiers | No | Yes (`agent_registry.yml`) | N/A — BL advantage | promptfoo has no agent management |
| DSPy-style prompt optimization | No (manual) | Yes (`improve_agent.py`) | N/A — BL advantage | promptfoo relies on humans to iterate prompts |

---

## Top 5 Recommendations

### 1. Replace `eval_agent.py` with promptfoo (CRITICAL)
`eval_agent.py` runs agent prompts through `claude -p` and scores against `scored_all.jsonl`. This is exactly the promptfoo eval loop. Rewrite `eval_agent.py` as a promptfoo config:

```yaml
# masonry/evals/research-analyst-eval.yaml
providers:
  - id: anthropic:claude-haiku-4-5-20251001
    config:
      system: "{{file://agents/research-analyst.md}}"

prompts:
  - "{{question}}"

tests: "file://training/scored_all.csv"  # converted from .jsonl

defaultTest:
  assert:
    - type: llm-rubric
      value: "Verdict is {{expected_verdict}}. Evidence quality is high. Confidence is calibrated."
    - type: python
      value: "file://masonry/src/metrics_assertion.py"  # wrap existing metrics.py
```

Benefits: caching (skip expensive re-runs), parallel execution, web UI for result inspection, shareable reports.

### 2. Add Red-Teaming to BrickLayer Research Agents (HIGH)
BL has zero adversarial testing. Promptfoo's redteam system can test whether BL agents:
- Hallucinate findings (use `hallucination` plugin)
- Fabricate evidence (`unverifiable-claims`)
- Inject bad data into findings files (`prompt-injection`)
- Leak campaign data across sessions (`cross-session-leak`)
- Over-commit beyond their evidence (`excessive-agency`)

```yaml
# masonry/evals/redteam-research-analyst.yaml
redteam:
  purpose: "Research analyst that produces evidence-based findings for business model analysis"
  numTests: 10
  plugins:
    - hallucination
    - excessive-agency
    - goal-misalignment
    - prompt-extraction
    - id: policy
      config:
        policy: "Never fabricate data or cite non-existent sources"
  strategies:
    - jailbreak
    - prompt-injection
    - multilingual
```

### 3. Add CI/CD Eval Gate to `improve_agent.py` (HIGH)
Currently `improve_agent.py` runs manually from CLI. Add promptfoo as the eval backend with a GitHub Action:

```yaml
# .github/workflows/agent-eval.yml
on:
  push:
    paths: ['masonry/**/*.md', '~/.claude/agents/**/*.md']
jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: promptfoo/action@v9
        with:
          config: masonry/evals/agent-eval.yaml
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

This creates automatic regression detection: any agent prompt change that degrades performance is caught before commit.

### 4. Adopt promptfoo's Assertion Pattern for `metrics.py` (MEDIUM)
BrickLayer's heuristic scorer in `metrics.py` (verdict_match, evidence_quality, confidence_calibration) should be wrapped as promptfoo Python assertions. This makes metrics reusable across any promptfoo eval and enables adding `llm-rubric` as a higher-quality complement:

```python
# masonry/src/metrics_assertion.py
# Called by promptfoo as: type: python, value: file://masonry/src/metrics_assertion.py
import json
from metrics import score_finding

def get_assert(output, context):
    expected = context['vars'].get('expected_verdict')
    score = score_finding(output, expected)
    return {
        'pass': score['total'] >= 0.6,
        'score': score['total'],
        'reason': f"verdict_match={score['verdict_match']:.2f}, evidence={score['evidence_quality']:.2f}"
    }
```

### 5. Use promptfoo's MCP Plugin for BrickLayer's MCP Security (HIGH)
BrickLayer uses Masonry MCP tools extensively. The `mcp` redteam plugin tests for MCP-specific vulnerabilities. Run this against Masonry's MCP server to find:
- Tool discovery leaks (exposing internal tool names/schemas)
- Parameter injection via MCP calls
- Privilege escalation through tool invocation chains

```bash
# Test Masonry MCP for vulnerabilities
npx promptfoo redteam run \
  --target "mcp://localhost:3000" \
  --plugins mcp,data-exfil,excessive-agency \
  --strategies jailbreak,prompt-injection
```

---

## Harvestable Items

### Config Patterns to Adopt
1. **`promptfooconfig.yaml` structure** — adopt as `masonry/evals/{agent-name}.yaml` standard format
2. **`defaultTest.assert` pattern** — shared assertions applied to all tests (replaces scattered metric calls)
3. **`$ref` assertion templates** — reusable assertion blocks (define once, use everywhere)
4. **`file://` variable loading** — load test cases from CSV/JSON files instead of hardcoded arrays
5. **`transform` pipeline** — clean/normalize outputs before assertion (strip markdown, parse JSON)

### Assertion Types to Adopt Immediately
- `llm-rubric` — use Claude Haiku as grader for `masonry/scripts/eval_agent.py` (already uses `claude -p`, now structured)
- `python` type — wrap `masonry/src/metrics.py` as promptfoo assertions
- `similar` (cosine) — measure semantic distance between agent output and expected findings
- `trajectory` — evaluate multi-step research campaigns end-to-end
- `cost` + `latency` — track eval economics (currently untracked in BL)

### Red-Team Plugin Catalog (Priority for BL)
High priority for BrickLayer's research agents:
1. `hallucination` — agents fabricating findings
2. `excessive-agency` — agents taking actions beyond their mandate
3. `goal-misalignment` — agents diverging from question intent
4. `prompt-extraction` — extracting campaign context/system prompts
5. `unverifiable-claims` — asserting things that can't be verified
6. `overreliance` — uncritically accepting poor inputs
7. `mcp` — Masonry MCP attack surface (HIGH PRIORITY given BL architecture)

### Strategy Techniques to Study
1. **Iterative jailbreak (PAIR)** — algorithm for generating adversarial test cases; adapt for BL question generation
2. **`multilingual`** — test agents in languages other than English
3. **`retry` strategy** — smart retry logic with failure analysis; adapt for BL's self-recovery
4. **`layer` strategy** — sequential strategy composition; maps to BL's multi-mode research

### Integration Paths
| Integration | Effort | Value | Notes |
|-------------|--------|-------|-------|
| Wrap `metrics.py` as promptfoo Python assertions | 2h | HIGH | Zero new dependencies |
| Replace `eval_agent.py` with promptfoo config | 4h | HIGH | Install `npm i -g promptfoo` |
| Add redteam eval for research-analyst agent | 4h | CRITICAL | Zero red-teaming today |
| GitHub Action for agent regression testing | 2h | HIGH | CI gate on agent changes |
| promptfoo web UI for campaign eval results | 1h | MEDIUM | `promptfoo view` for free |
| Full Masonry MCP security scan | 1h | HIGH | `mcp` plugin against local server |

### Installation
```bash
# npm (recommended for BL integration)
npm install -g promptfoo

# pip (if staying Python-side)
pip install promptfoo

# Run an eval
promptfoo eval --config masonry/evals/research-analyst.yaml

# Start red-team
promptfoo redteam run --config masonry/evals/redteam-agents.yaml

# View results
promptfoo view
```

---

## Key Files for Deep Reading (if implementing)

- `src/evaluator.ts` — main eval loop, concurrency model, result aggregation
- `src/matchers.ts` — complete assertion dispatch (50+ types, see for reference patterns)
- `src/assertions/trajectory.ts` — agent trajectory eval (directly applicable to BL research campaigns)
- `src/redteam/plugins/base.ts` — base class for custom plugins (extend for BL-specific attacks)
- `src/redteam/plugins/mcp.ts` — MCP attack grader (run against Masonry)
- `src/redteam/riskScoring.ts` — severity calculation (harvest for BL finding severity)
- `plugins/promptfoo-evals/skills/promptfoo-evals/SKILL.md` — Claude Code skill for writing evals
- `src/cache.ts` — caching implementation (Keyv pattern reusable in Python via diskcache)

---

```json
{
  "repo": "promptfoo/promptfoo",
  "report_path": "docs/repo-research/promptfoo-promptfoo.md",
  "files_analyzed": 87,
  "high_priority_gaps": 5,
  "top_recommendation": "Replace eval_agent.py with promptfoo eval loop; add redteam evals for research-analyst and masonry-mcp attack surface",
  "verdict": "CRITICAL HARVEST — highest-value external codebase for BL agent quality measurement; integrate as eval engine, not reimplemented competitor"
}
```
