# Repo Research Index

Comparative analysis of GitHub repos against BrickLayer 2.0 capabilities.
All findings feed into the BrickLayer roadmap.

## How to run a new research

Invoke the `repo-researcher` agent:
```
Act as the repo-researcher agent in ~/.claude/agents/repo-researcher.md.
repo_url: https://github.com/owner/repo
output_dir: C:/Users/trg16/Dev/Bricklayer2.0/docs/repo-research/
```

Or via Mortar: "research this repo: https://github.com/owner/repo"

---

## Researched Repos

| Repo | Date | Files | Agents | High Gaps | Top Recommendation |
|------|------|-------|--------|-----------|-------------------|
| [mk-knight23/AGENTS-COLLECTION](agents-collection.md) | 2026-03-28 | 3,475 | 700+ | 8 | Blind review system (3 reviewers + Devil's Advocate) |

---

## Cross-Repo Synthesis

*(Populated after 3+ repos are researched)*

Common patterns appearing in multiple repos will be promoted to the BrickLayer build queue.

---

## Build Queue (from repo research)

### HIGH Priority
- [ ] **Blind review system** — 3 parallel reviewers + Devil's Advocate agent; weighted consensus (from AGENTS-COLLECTION — ZEUS/TITAN)
- [ ] **Secret scanning hook** — `masonry-secret-scanner.js` PreToolUse with Gitleaks + Semgrep; critical given ADBP Solana keys (from AGENTS-COLLECTION — security-hooks)
- [ ] **Eval-Driven Development harness** — capability/regression/safety evals per agent + pass@1/pass@3/pass^3 metrics extending improve_agent.py (from AGENTS-COLLECTION — NEXUS/EDD)
- [ ] **Fail-closed defaults + confidence gating** in /verify — default verdict FAIL, only surface findings ≥80% confidence (from AGENTS-COLLECTION — TITAN/everything-cc)
- [ ] **PR-writer agent** — writes PR description, review checklist, links issues at /build completion (from AGENTS-COLLECTION — OpenClaw PR agent)
- [ ] **Named pipeline templates** — FEATURE-DEV/BUG-FIX/SECURITY-AUDIT as YAML files with typed agent handoffs (from AGENTS-COLLECTION — OpenClaw)
- [ ] **Dependency audit + file size enforcement hooks** — dep vuln scan on package.json/requirements.txt changes; hard block >300 lines (from AGENTS-COLLECTION — hooks-collection)

### MEDIUM Priority
- [ ] **LOKI Reflect phase** in research loop — spawn reflect agent between specialist verdict and writing finding; flags low-confidence verdicts as UNCERTAIN (from AGENTS-COLLECTION — ZEUS LOKI)
- [ ] **LSP/semantic code index** — unified symbol graph via pyright/tsserver/gopls; `masonry_lsp_query` MCP tool; replaces exhaustive file reads in developer/diagnose agents (from AGENTS-COLLECTION — lsp-index-engineer)
- [ ] **Context compression** — active summarization at 120K tokens targeting ≤500-token handoff summary (from AGENTS-COLLECTION — ZEUS 98.6% compression)
- [ ] **sequential-thinking MCP** — add `@modelcontextprotocol/server-sequential-thinking`; inject for `reasoning: deep` tasks (from AGENTS-COLLECTION — MCP configs)
- [ ] **Confidence-gated output** (>80% threshold) for code-reviewer and research-analyst
- [ ] **Golden examples in agent prompts** — add worked examples to spec-writer, question-designer-bl2, synthesizer
- [ ] **Dual verification** — separate REVIEWER (quality/style) and VERIFIER (spec compliance/correctness) agents in /build
- [ ] **Agentic identity trust** — Ed25519 keypairs per agent for delegation chain verification (from AGENTS-COLLECTION — agentic-identity-trust)
- [ ] **CI/CD templates** — Node.js/Python/Go GitHub Actions workflows with change-detection (dorny/paths-filter) (from AGENTS-COLLECTION — ci-cd-workflows)

### LOW Priority
- [ ] soul.md ethical constraint doc per agent (from AGENTS-COLLECTION — ClawSec)
- [ ] AARRR / PLFS growth + ethical scoring agent (from AGENTS-COLLECTION — PULSE)
- [ ] SRE incident responder agent with blameless postmortem template (from AGENTS-COLLECTION — NEW-AGENTS)
- [ ] Spatial computing agents — visionOS/XR/Metal GPU (from AGENTS-COLLECTION — AGENCY-SOURCE)
- [ ] Chinese platform marketing specialists (from AGENTS-COLLECTION — AGENCY-SOURCE/MARKETING)
- [ ] Semantic release automation from conventional commits (from AGENTS-COLLECTION — ci-cd-workflows)
- [ ] SBOM + license compliance in security pipeline (from AGENTS-COLLECTION — security-workflows)
