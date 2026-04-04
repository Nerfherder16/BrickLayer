---
name: fork
description: Fork the current session — save branch/commit context and print parallel session instructions
---

# Skill: fork

Save current session context and prepare for parallel work in a new session.

## What to do

1. **Capture current state**
   ```bash
   cd C:/Users/trg16/Dev/Bricklayer2.0
   git branch --show-current
   git log --oneline -3
   ```

2. **Write fork context to `.masonry/fork-context.md`**
   ```
   # Fork Context
   Date: <ISO date>
   Branch: <current branch>
   Last commits:
   <git log output>
   Active work: <brief description of what was being done>
   ```

3. **Print parallel session instructions**
   ```
   Fork saved. To continue in a parallel session:
   Branch: <branch>
   Run: claude --dangerously-skip-permissions
   Resume from: .masonry/fork-context.md
   ```
