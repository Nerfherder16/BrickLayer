# Skill Description Audit
**Date:** 2026-04-06
**Scope:** `~/.claude/skills/` — all 62 skill files (directory-based SKILL.md + flat .md files)
**Method:** Read-only static analysis via `ls`, `wc`, and system-reminder observation

---

## 1. Total Skill Count

```
Total skill entries on disk: 62
  └── Directory-based (SKILL.md): 47  (each dir has one SKILL.md)
  └── Flat .md files:             15  (e.g., architecture.md, hats.md, etc.)
```

---

## 2. Skill File Size Inventory

### Top 10 Largest SKILL.md Files

| Skill | Lines | Chars | Est. Tokens |
|-------|-------|-------|-------------|
| `ui-design-system` | 1,169 | 30,834 | **7,708** |
| `build` | 529 | 21,821 | **5,455** |
| `pdf` | 414 | 9,291 | 2,323 |
| `hats.md` (flat) | 226 | 9,443 | 2,361 |
| `docx` | 230 | 6,198 | 1,549 |
| `visual-recap` | 153 | 6,630 | 1,658 |
| `hook-perf-audit` | 164 | 6,358 | 1,589 |
| `visual-plan` | 150 | 6,161 | 1,540 |
| `debug` | 168 | 5,845 | 1,461 |
| `homelab-deploy` | 159 | 5,155 | 1,289 |

### Bottom 5 Smallest

| Skill | Lines | Chars | Est. Tokens |
|-------|-------|-------|-------------|
| `status.md` (flat) | 23 | 569 | 142 |
| `fork.md` (flat) | 35 | 824 | 206 |
| `architecture.md` (flat) | 15 | 924 | 231 |
| `playwright` | 28 | 920 | 230 |
| `context7` | 27 | 802 | 200 |

### Totals Across All Skill Files

| Metric | Value |
|--------|-------|
| Total files on disk | 62 |
| Total chars (all SKILL.md + flat .md) | 259,444 |
| **Estimated tokens if ALL loaded** | **~64,861** |

---

## 3. How Claude Code Loads Skill Descriptions

### What the System-Reminder Shows

Observation from the live system-reminder in this session: Claude Code injects a skill listing block that looks like:

```
- skill-name: description (truncated ~45-50 chars)...
```

The system-reminder in this session showed **115 total entries** across two listing blocks:
- Block 1: ~53 entries from global + local skills (with full or truncated descriptions)
- Block 2: ~62 entries repeating global skills (apparent duplicate injection from global + project-local registration)

Unique skills in the listing: **~70** (some skills appear twice due to both global `~/.claude/skills/` and project-local `.claude/skills/` registration).

### How Descriptions Are Loaded

Each skill's `SKILL.md` begins with YAML front matter:
```yaml
---
name: skill-name
description: "Short description here"
---
```

Claude Code reads only the `description` field for the system-reminder listing. The full SKILL.md body is **not** loaded into the system prompt — it is only loaded when the Skill tool is invoked.

This means:
- **Per-skill cost in the system-reminder:** ~70–90 chars per entry (name + truncated description)
- **Full SKILL.md cost:** Only incurred when the skill is invoked (on-demand)

---

## 4. Token Estimates

### System-Reminder Skill Listing (Always-On Cost)

| Metric | Value |
|--------|-------|
| Total entries in system-reminder | ~115 (with duplicates) |
| Unique entries | ~70 |
| Average chars per entry | ~81 (name + description) |
| Total chars for listing | ~9,315 |
| **Estimated tokens for listing** | **~2,328** |

This is the always-on cost. It fires every session regardless of which skills are used.

### On-Demand SKILL.md Cost (Per Invocation)

When a skill is invoked via the Skill tool, the full SKILL.md is loaded. Costs:

| Scenario | Tokens |
|----------|--------|
| Simple skill (playwright, context7) | ~200–230 |
| Medium skill (debug, plan, anchor) | ~750–1,750 |
| Large skill (build, ui-design-system) | **5,455 / 7,708** |
| All skills loaded simultaneously | **~64,861** |

---

## 5. Observations and Risks

### Risk 1: Duplicate Injection in System-Reminder (~35% waste)

The system-reminder in this session showed 115 entries for ~70 unique skills. Approximately 45 entries are duplicates from skills registered in both `~/.claude/skills/` (global) and `.claude/skills/` (project-local). This means ~35% of the skill listing tokens are redundant.

**Estimated wasted tokens:** ~810 tokens per session from duplicate listing.

### Risk 2: `ui-design-system` and `build` Are Outliers

These two skills are 4–8x larger than average:

| Skill | Tokens | Ratio to Avg (1,360) |
|-------|--------|----------------------|
| `ui-design-system` | 7,708 | 5.7x |
| `build` | 5,455 | 4.0x |

If both are invoked in the same session, they consume ~13,163 tokens of context. Together they account for ~20% of the total capacity of all 62 skills combined.

### Risk 3: Flat `.md` Skills vs. Directory Skills

15 of 62 skill files are flat `.md` files (no YAML front matter directory structure). These include:
- `architecture.md` (924 chars)
- `hats.md` (9,443 chars — largest flat file, larger than most SKILL.md files)
- `competitive-positioning.md`, `copywriting.md`, `gtm.md`, etc.

If flat `.md` files are loaded differently than directory-based SKILL.md files, their descriptions may not appear truncated in the system-reminder, causing unexpected full-file injection.

### Risk 4: Total Cumulative Load

In a session that uses many skills (e.g., a `/build` run that invokes `build`, `plan`, `debug`, `context7`, `playwright`):

| Component | Tokens |
|-----------|--------|
| System-reminder listing | ~2,328 |
| `build` SKILL.md | ~5,455 |
| `plan` SKILL.md | ~1,775 |
| `debug` SKILL.md | ~1,461 |
| `context7` SKILL.md | ~200 |
| `playwright` SKILL.md | ~230 |
| **Total** | **~11,449** |

This is before any hook injections. Combined with the worst-case hook injection estimate (~4,400 tokens for session-open), a heavy session can consume **~15,000+ tokens of system/context overhead** before any user code or task content.

---

## 6. Summary of Findings

| Finding | Severity | Tokens Impacted |
|---------|----------|-----------------|
| Duplicate skill listing in system-reminder | WARNING | ~810/session |
| `ui-design-system` size outlier | SUGGESTION | 7,708 when invoked |
| `build` size outlier | SUGGESTION | 5,455 when invoked |
| `hats.md` flat file is largest flat skill | INFO | ~2,361 when loaded |
| Total always-on skill listing cost | INFO | ~2,328/session |
| Total all-skills-loaded worst case | INFO | ~64,861 (theoretical) |

---

## 7. Recommendations

1. **De-duplicate skill registration** — skills in both `~/.claude/skills/` and `.claude/skills/` appear twice in the system-reminder. Consider a dedup pass when building the listing, saving ~810 tokens per session.

2. **Split `ui-design-system` SKILL.md** — at 1,169 lines / 7,708 tokens, this is more than the entire rest of the skills combined for its invocation cost. Consider splitting into a small entry-point skill + separate reference docs that are only fetched when needed.

3. **Trim `build` SKILL.md** — at 529 lines it is the second-largest skill. The pipeline description may be excessively detailed for the entry-point file.

4. **Standardize flat `.md` skills** — the 15 flat `.md` files lack SKILL.md structure. Their descriptions in the system-reminder may not be truncated the same way, causing inconsistent injection behavior.
