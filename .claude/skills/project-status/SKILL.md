---
name: project-status
description: >-
  Generate a live project status report for the BrickLayer monorepo.
  Reads actual file system and git state — never guesses.
---

# Skill: project-status

Generate a live project status report for the BrickLayer monorepo.
Reads actual file system and git state — never guesses.

## What to do

1. **Read git state**
   ```bash
   cd C:/Users/trg16/Dev/Bricklayer2.0
   git branch -a --sort=-committerdate
   git log --all --oneline --decorate | head -20
   git status --short | grep -v "^?" | head -20
   ```

2. **Scan project directories** — for each dir that has a `project-brief.md`:
   ```bash
   for dir in recall recall-2.0 recall-arch-frontier recall-competitive adbp bricklayer-meta projects/bl2; do
     pending=$(grep -c "Status.*PENDING" "$dir/questions.md" 2>/dev/null || echo 0)
     last=$(git log --oneline -1 -- "$dir/" 2>/dev/null)
     echo "$dir: $pending PENDING | $last"
   done
   ```

3. **Rewrite `PROJECT_STATUS.md`** at `C:/Users/trg16/Dev/Bricklayer2.0/PROJECT_STATUS.md`
   Use the same format as the existing file. Update:
   - Branch table (which branches exist locally vs remote)
   - Per-project status (PENDING count, last commit, next action)
   - "What's not built yet" table from ROADMAP.md
   - Cleanup checklist (anything untracked, unpushed, stale)

4. **Print a summary** — 10 lines max covering:
   - Active projects with PENDING counts
   - Branches that need pushing
   - Top cleanup item
   - What to work on next

## Format rules
- Emoji status: 🟢 active/healthy · 🟡 paused/needs attention · 🔵 ready to start · ⚪ dormant/archive
- Always show PENDING question count — that's the pulse of a campaign
- Always flag unpushed branches — losing work is the biggest risk
- Keep "What BL 2.0 Has" section current — Tim forgets what's been built
