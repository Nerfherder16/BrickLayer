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
| [mk-knight23/AGENTS-COLLECTION](agents-collection.md) | 2026-03-28 | 100+ | 70+ | 12 | Fail-closed /verify + confidence gating |

---

## Cross-Repo Synthesis

*(Populated after 3+ repos are researched)*

Common patterns appearing in multiple repos will be promoted to the BrickLayer build queue.

---

## Build Queue (from repo research)

### HIGH Priority
- [ ] Fail-closed defaults + confidence gating in /verify (from AGENTS-COLLECTION)
- [ ] PR-writer agent (from AGENTS-COLLECTION — OpenClaw PR agent pattern)
- [ ] File size + dependency audit hooks (from AGENTS-COLLECTION — hooks-collection)
- [ ] Named pipeline templates (from AGENTS-COLLECTION — OpenClaw FEATURE-DEV/BUG-FIX/SECURITY-AUDIT)
- [ ] sequential-thinking MCP + pass^N evals (from AGENTS-COLLECTION — NEXUS/EDD)

### MEDIUM Priority
- [ ] Confidence-gated output (>80% threshold) for code-reviewer
- [ ] Golden examples in spec-writer, question-designer-bl2, synthesizer prompts
- [ ] Devil's Advocate as required /build pipeline stage
- [ ] LOKI RARV loop in developer agent (Reason→Act→Reflect→Verify per tool call)
- [ ] Dual verification — separate REVIEWER and VERIFIER agents

### LOW Priority
- [ ] soul.md ethical constraint doc per agent (from AGENTS-COLLECTION — ClawSec)
- [ ] AARRR growth agent (from AGENTS-COLLECTION — PULSE)
- [ ] SRE incident responder agent (from AGENTS-COLLECTION — NEW-AGENTS)
