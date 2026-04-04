---
name: status
description: Show current BrickLayer session status — branch, active campaign, pending question count, agent spawns, session time
---

# Skill: status

Display the current BrickLayer session status line.

## What to do

Run the statusline script and print the output:

```bash
node C:/Users/trg16/Dev/Bricklayer2.0/masonry/src/hooks/masonry-statusline.mjs
```

If the script fails, fall back to:
```bash
cd C:/Users/trg16/Dev/Bricklayer2.0
git branch --show-current
grep -c "Status.*PENDING" questions.md 2>/dev/null || echo "No active campaign"
```
