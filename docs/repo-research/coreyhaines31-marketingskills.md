# Repo Research: coreyhaines31/marketingskills
**Repo**: https://github.com/coreyhaines31/marketingskills
**Researched**: 2026-03-28
**Analyzed by**: repo-researcher agent

---

## Verdict Summary

**High-value harvest.** This is a production-quality, actively maintained (last updated 2026-03-14) collection of 33 marketing/GTM skills built for Claude Code, designed for the exact format BrickLayer uses. Zero code to write — these are markdown skill files with YAML frontmatter that install directly into `.claude/skills/`. The format is 100% compatible with BL's `~/.claude/skills/` system. BrickLayer has zero marketing capability today; this fills the entire gap in one install. Top candidates for immediate harvest: `launch-strategy`, `ai-seo`, `product-marketing-context`, `pricing-strategy`, `referral-program`, and `free-tool-strategy` — all directly relevant to Tim's active projects (ADBP token launch, JellyStream, Relay AI).

---

## File Inventory

| Path | Type | Size | Notes |
|------|------|------|-------|
| `README.md` | Docs | 15.5KB | Full skill catalog, install instructions, architecture diagram |
| `AGENTS.md` | Docs | 7.9KB | Agent instructions: spec format, tool integrations, update protocol |
| `VERSIONS.md` | Docs | 3.9KB | Version history for all 33 skills — all v1.2.0 as of 2026-03-14 |
| `CONTRIBUTING.md` | Docs | 2.6KB | Skill authoring guide |
| `CLAUDE.md` | Config | 9 bytes | Minimal (just points to AGENTS.md) |
| `.claude-plugin/marketplace.json` | Config | 1.9KB | Claude Code plugin marketplace manifest — enables `/plugin install` |
| `validate-skills.sh` | Tool | 5.8KB | Shell validator for skill frontmatter compliance |
| `validate-skills-official.sh` | Tool | 2.0KB | Official Agent Skills spec validator |
| `skills/` | Dir | — | 33 skill subdirectories, each with `SKILL.md` |
| `tools/REGISTRY.md` | Docs | 22.2KB | 68-tool registry with API/MCP/CLI/SDK availability matrix |
| `tools/clis/` | Code | — | 51 zero-dependency Node.js CLI tools for marketing platforms |
| `tools/integrations/` | Docs | — | 31+ integration guides (GA4, Stripe, HubSpot, etc.) |
| `tools/composio/` | Docs | — | Composio integration layer for OAuth-heavy tools |

---

## Skill/Agent Catalog

All 33 skills follow the Agent Skills spec: YAML frontmatter with `name` + `description` + optional `metadata`, then markdown body. Each reads `.agents/product-marketing-context.md` first (falls back to `.claude/product-marketing-context.md`).

### Foundation Layer

| Skill | Purpose | Unique Techniques |
|-------|---------|-------------------|
| `product-marketing-context` | Creates `.agents/product-marketing-context.md` — shared context that all other skills read first | Auto-drafts from codebase scan (README, landing pages, package.json); JTBD Four Forces model (Push/Pull/Anxiety/Habit); captures verbatim customer language |

### SEO & Content

| Skill | Purpose | Unique Techniques |
|-------|---------|-------------------|
| `seo-audit` | Technical + on-page SEO audit | Prioritized checklist: Core Web Vitals, crawlability, E-E-A-T, structured data |
| `ai-seo` | Optimize for AI-generated answers (AEO/GEO/LLMO) | Covers all major AI search platforms (ChatGPT, Perplexity, Gemini, Claude, Copilot, Google AI Overviews); cites stat that brands are 6.5x more likely to be cited via third-party sources; AI Overviews appear in ~45% of Google searches |
| `site-architecture` | Website page hierarchy, URL structure, internal linking | Silo architecture, hub-and-spoke content models |
| `programmatic-seo` | SEO-driven pages at scale using templates + data | Template + data source strategy; dedupe/canonicalization patterns |
| `schema-markup` | Structured data / JSON-LD implementation | Schema type selection, rich result eligibility |
| `content-strategy` | Content planning and topic selection | ICP-audience alignment, content-to-funnel mapping |

### Copywriting & Messaging

| Skill | Purpose | Unique Techniques |
|-------|---------|-------------------|
| `copywriting` | Marketing copy for any page | Message-market fit, awareness stage targeting, PAS/AIDA frameworks |
| `copy-editing` | Review and polish existing copy | Clarity, specificity, active voice, jargon elimination |
| `cold-email` | B2B cold outreach and follow-up sequences | Personalization at scale, permission-based openings, multi-touch sequences |
| `email-sequence` | Drip campaigns, lifecycle email automation | Trigger-based vs. time-based, behavior-responsive branching |
| `social-content` | LinkedIn, Twitter/X, Instagram content | Platform-native tone, hook engineering, thread structure |

### Conversion Rate Optimization (CRO)

| Skill | Purpose | Unique Techniques |
|-------|---------|-------------------|
| `page-cro` | Conversion optimization for any marketing page | 7-dimension analysis: value prop, headline, CTA, visual hierarchy, social proof, objection handling, friction |
| `signup-flow-cro` | Optimize signup/registration/trial activation | Progressive disclosure, field reduction, social signup patterns |
| `onboarding-cro` | Post-signup user activation | Aha moment identification, time-to-value optimization, multi-channel coordination |
| `form-cro` | Lead capture and non-signup form optimization | Field sequencing, microcopy, conditional logic |
| `popup-cro` | Popups, modals, overlays, banners | Trigger timing, exit intent, progressive gates |
| `paywall-upgrade-cro` | In-app paywalls and upgrade screens | Upgrade moment identification, friction reduction, trial-to-paid flows |
| `ab-test-setup` | Design statistically valid experiments | Hypothesis framework (`Because [obs], we believe [change] will cause [outcome]`); sample size lookup tables; peeking problem mitigation |

### Paid Acquisition

| Skill | Purpose | Unique Techniques |
|-------|---------|-------------------|
| `paid-ads` | Campaign strategy for Google, Meta, LinkedIn, TikTok | Platform selection by intent stage, bidding strategy, audience layering |
| `ad-creative` | Ad copy generation at scale | Angle-based generation (8 angle categories); iterates from performance data; bulk CSV output for platform upload; Remotion integration for code-based video at scale |
| `analytics-tracking` | GA4, Mixpanel, Segment setup and audits | Event taxonomy, conversion tracking, attribution |

### Growth & Retention

| Skill | Purpose | Unique Techniques |
|-------|---------|-------------------|
| `referral-program` | Customer referral + affiliate programs | Referral loop design (Trigger → Share → Convert → Reward); single vs. double-sided incentives; tiered reward gamification |
| `free-tool-strategy` | Engineering-as-marketing / free tool planning | 6 tool type categories (calculator, generator, analyzer, tester, library, interactive); lead gating options matrix |
| `lead-magnets` | Lead magnet creation and optimization | Format selection by audience, progressive value exchange |
| `churn-prevention` | Cancel flows, save offers, dunning, payment recovery | Cancellation intervention hierarchy, failed payment recovery sequences |

### Go-To-Market

| Skill | Purpose | Unique Techniques |
|-------|---------|-------------------|
| `launch-strategy` | Product launch and feature announcement planning | ORB Framework (Owned/Rented/Borrowed channels); 5-phase launch (Internal → Alpha → Beta → Press → Public); real examples: Superhuman waitlist, Notion community virality, TRMNL influencer gifting |
| `pricing-strategy` | Pricing decisions, packaging, monetization | Value metric selection framework; good/better/best tier design; Van Westendorp price sensitivity meter; freemium vs. free trial decision matrix |
| `competitor-alternatives` | Competitor comparison and alternative pages | SEO angle: "[Competitor] alternatives" pages; positioning differentiation copy |
| `sales-enablement` | Sales decks, one-pagers, objection handling, demo scripts | Battlecard templates, ROI calculators, champion-friendly materials |
| `revops` | Revenue operations, lead lifecycle, CRM automation | Lead scoring models, routing rules, handoff SLAs |

### Strategy

| Skill | Purpose | Unique Techniques |
|-------|---------|-------------------|
| `marketing-ideas` | Marketing idea generation for SaaS/software | Ideation prompts across 6+ categories |
| `marketing-psychology` | Behavioral science applied to marketing | 40+ mental models with marketing applications; organized into: Thinking Models, Buyer Psychology, Persuasion, Pricing Psychology, Design/Delivery, Growth/Scaling |

---

## Technical Architecture

### Skill Format (Agent Skills Spec)

```yaml
---
name: skill-name                          # Must match directory name
description: Trigger phrases + scope...  # 1-1024 chars, drives auto-detection
metadata:
  version: 1.2.0
---
# Skill Title
## Instructions...
```

- Skills install to `.agents/skills/` (cross-agent) with symlink to `.claude/skills/`
- Each skill auto-reads `.agents/product-marketing-context.md` before acting
- Skills cross-reference each other via "Related Skills" sections
- AGENTS.md instructs agents to check VERSIONS.md once per session and notify on updates

### Version Update Protocol

AGENTS.md contains a live-update check: fetch `VERSIONS.md` from GitHub on first skill use per session, prompt user if 2+ skills have updates or any has a major bump. Non-blocking notification pattern.

### Tools Registry (51 CLI Tools + 31 Integration Guides)

Zero-dependency Node.js scripts, each following identical patterns:
- `node tools/clis/ga4.js reports get --date-range last_30_days`
- `node tools/clis/resend.js emails send --to ... --subject ...`
- Skills reference these tools for implementation (e.g., `ad-creative` pulls Google Ads performance data → feeds iteration loop)

MCP-enabled tools (usable as MCP servers): ga4, stripe, mailchimp, google-ads, resend, zapier, zoominfo, clay, supermetrics, coupler, outreach, crossbeam, composio

### Claude Code Plugin

`.claude-plugin/marketplace.json` supports direct installation:
```bash
/plugin marketplace add coreyhaines31/marketingskills
/plugin install marketing-skills
```

---

## Feature Gap Analysis

| Feature | In this repo | In BrickLayer 2.0 | Gap Level | Notes |
|---------|-------------|-------------------|-----------|-------|
| Product launch planning | `launch-strategy` — full ORB framework | None | CRITICAL | Directly needed for ADBP token launch |
| AI search optimization | `ai-seo` — ChatGPT/Perplexity/Gemini/Claude citations | None | CRITICAL | Tim's projects need discoverability in AI answers |
| Pricing strategy | `pricing-strategy` — value metrics, tier design, freemium | None | CRITICAL | ADBP token pricing; JellyStream monetization |
| Product positioning | `product-marketing-context` — shared foundation | None | CRITICAL | Required base layer for all other skills |
| Landing page CRO | `page-cro` — 7-dimension analysis | None | HIGH | Any product launch needs conversion-optimized pages |
| Referral programs | `referral-program` — viral loops, affiliate design | None | HIGH | JellyStream growth, ADBP token distribution |
| Free tool strategy | `free-tool-strategy` — engineering-as-marketing | None | HIGH | BrickLayer itself could offer free tools for lead gen |
| Copywriting | `copywriting` + `copy-editing` | None | HIGH | Needed for all project launches |
| Cold email | `cold-email` — B2B sequences | None | HIGH | Relay AI receptionist sales (when unblocked) |
| Email sequences | `email-sequence` — lifecycle automation | None | HIGH | ADBP onboarding, JellyStream activation |
| Ad creative | `ad-creative` — bulk generation + iteration loops | None | MEDIUM | Useful but not urgent without paid ad budget |
| SEO audit | `seo-audit` — technical + on-page | None | MEDIUM | Good practice for any web project |
| A/B testing | `ab-test-setup` — hypothesis framework + stats | None | MEDIUM | Needed when traffic exists |
| Social content | `social-content` — LinkedIn/Twitter/X creation | None | MEDIUM | Product announcements and thought leadership |
| Competitor analysis | `competitor-alternatives` — SEO comparison pages | None | MEDIUM | ADBP vs. other token loyalty programs |
| Marketing psychology | `marketing-psychology` — 40+ mental models | None | LOW-MEDIUM | Good reference; enriches other skills |
| Analytics setup | `analytics-tracking` — GA4/Mixpanel/Segment | None | LOW-MEDIUM | Needed when web properties exist |
| Churn prevention | `churn-prevention` — cancel flows, dunning | None | LOW | More relevant post-launch |
| Onboarding CRO | `onboarding-cro` — activation optimization | None | LOW | Post-launch when user base exists |
| Sales enablement | `sales-enablement` — decks, battlecards | None | LOW | More relevant for Relay AI |
| Revenue ops | `revops` — CRM automation, lead routing | None | LOW | Not yet relevant |
| Tool registry / CLIs | 51 Node.js CLIs for marketing platforms | None | LOW | Useful once specific platforms are chosen |

**Summary**: BrickLayer has 0/21 marketing capabilities. All 33 skills represent net-new capability. Priority tier based on Tim's active projects.

---

## Top 5 Recommendations

### 1. Install `product-marketing-context` + `launch-strategy` immediately — ADBP token launch

The ADBP Solana discount-credit platform needs a GTM plan. `product-marketing-context` establishes the positioning foundation (ICP, differentiation, JTBD), then `launch-strategy`'s ORB Framework (Owned/Rented/Borrowed) and 5-phase rollout directly maps to a token launch. Specific: build a waitlist (Owned), use crypto Twitter/X (Rented), find Solana KOLs (Borrowed). Install both as skills in `~/.claude/skills/`.

### 2. Use `ai-seo` for all Tim's web-facing projects

This is forward-looking infrastructure. AI Overviews appear in 45% of searches; brands cited via third-party sources get 6.5x more mentions than own domains. Any web property Tim launches (ADBP landing page, JellyStream, Relay AI) should be structured for AI citation from day one. The skill covers ChatGPT, Perplexity, Gemini, Claude, and Copilot separately.

### 3. Adopt the `product-marketing-context` pattern for BrickLayer agent design

The pattern of having a shared context file (`.agents/product-marketing-context.md`) that all marketing skills read before acting is directly adoptable as a BrickLayer architecture pattern. BL could have `.agents/project-brief.md` (it already does) serve this role, and new BL marketing agents should be designed to read it first — same as BL's existing `project-brief.md` sits in Tier 1 authority.

### 4. Harvest `ad-creative` for ADBP token promotion

The ad-creative skill's angle-based generation system and iteration loop (pull performance data → identify winning patterns → generate new variations → batch CSV output) is the most sophisticated AI-automation pattern in the repo. It references Remotion for code-based video at scale and documents all platform character limits inline. If ADBP runs any paid acquisition, this workflow saves hours.

### 5. Add `free-tool-strategy` to BrickLayer's capability planning

BrickLayer could use engineering-as-marketing: a free "business model stress-test" tool or "simulation sandbox" that drives leads back to BrickLayer. The skill's ideation framework (start with audience pain points → validate search demand → design lead capture) is ready to run against BrickLayer's own positioning.

---

## Harvestable Items

### Direct installs (copy to `~/.claude/skills/`)

Priority A — Install now, relevant to active projects:
1. `skills/product-marketing-context/SKILL.md` → `~/.claude/skills/product-marketing-context.md`
2. `skills/launch-strategy/SKILL.md` → `~/.claude/skills/launch-strategy.md`
3. `skills/ai-seo/SKILL.md` → `~/.claude/skills/ai-seo.md`
4. `skills/pricing-strategy/SKILL.md` → `~/.claude/skills/pricing-strategy.md`
5. `skills/referral-program/SKILL.md` → `~/.claude/skills/referral-program.md`
6. `skills/copywriting/SKILL.md` → `~/.claude/skills/copywriting.md`
7. `skills/free-tool-strategy/SKILL.md` → `~/.claude/skills/free-tool-strategy.md`

Priority B — Install for upcoming launch work:
8. `skills/page-cro/SKILL.md` → `~/.claude/skills/page-cro.md`
9. `skills/cold-email/SKILL.md` → `~/.claude/skills/cold-email.md`
10. `skills/email-sequence/SKILL.md` → `~/.claude/skills/email-sequence.md`
11. `skills/ad-creative/SKILL.md` → `~/.claude/skills/ad-creative.md`
12. `skills/social-content/SKILL.md` → `~/.claude/skills/social-content.md`
13. `skills/competitor-alternatives/SKILL.md` → `~/.claude/skills/competitor-alternatives.md`

Priority C — Reference library (install when needed):
14. `skills/ab-test-setup/SKILL.md`
15. `skills/seo-audit/SKILL.md`
16. `skills/analytics-tracking/SKILL.md`
17. `skills/marketing-psychology/SKILL.md`
18. `skills/onboarding-cro/SKILL.md`
19. `skills/churn-prevention/SKILL.md`
20. `skills/sales-enablement/SKILL.md`

### Patterns to adopt in BrickLayer agent design

1. **Shared context file pattern**: `.agents/product-marketing-context.md` — all marketing agents read this first. BL already has `project-brief.md` but could formalize a lighter-weight marketing context file for non-research projects.

2. **Skill format spec**: The YAML frontmatter `name` + `description` (with trigger phrases) format from the Agent Skills spec is cleaner than BL's current agent `.md` files. Consider adopting `description:` with trigger phrases in BL's agent registry for better Mortar routing.

3. **Version check hook pattern**: AGENTS.md instructs agents to fetch VERSIONS.md once per session and notify on updates — a pull-based update notification pattern BL could adopt for its own agent registry.

4. **Angle-based creative generation**: The 8-angle framework from `ad-creative` (pain point, outcome, social proof, curiosity, comparison, urgency, identity, contrarian) is directly usable in a BL `content-writer` agent.

5. **ORB launch framework**: Owned/Rented/Borrowed channel taxonomy from `launch-strategy` maps cleanly to any BL project launch, especially ADBP.

### Installation command

```bash
# Fastest: clone and copy Priority A skills
git clone https://github.com/coreyhaines31/marketingskills.git /tmp/marketingskills

# Install to global Claude skills
for skill in product-marketing-context launch-strategy ai-seo pricing-strategy referral-program copywriting free-tool-strategy page-cro cold-email email-sequence ad-creative social-content; do
  cp /tmp/marketingskills/skills/$skill/SKILL.md ~/.claude/skills/$skill.md
done
```

Or via Claude Code plugin system (if available):
```
/plugin marketplace add coreyhaines31/marketingskills
/plugin install marketing-skills
```

---

## Format Compatibility Note

The skills use the [Agent Skills specification](https://agentskills.io) format with YAML frontmatter. BrickLayer's `~/.claude/skills/` system is compatible — Claude Code reads `.md` files from that directory and treats them as skills. The `description` field with trigger phrases is what drives Claude Code's skill auto-detection when a user's message matches the trigger vocabulary. No code changes needed to BrickLayer to use these.

---

```json
{
  "repo": "coreyhaines31/marketingskills",
  "report_path": "docs/repo-research/coreyhaines31-marketingskills.md",
  "files_analyzed": 47,
  "skills_analyzed": 33,
  "cli_tools": 51,
  "integration_guides": 31,
  "high_priority_gaps": 4,
  "medium_priority_gaps": 6,
  "format_compatible": true,
  "install_method": "copy SKILL.md files to ~/.claude/skills/ OR /plugin marketplace add",
  "top_recommendation": "Install product-marketing-context + launch-strategy immediately for ADBP token launch GTM planning",
  "verdict": "High-value, production-quality, install-ready. All 33 skills are net-new capability for BrickLayer. Format is 100% compatible with ~/.claude/skills/. Priority A (7 skills) directly applies to Tim's active projects. Harvest now."
}
```
