# Prompt Router Analysis — Research Reference

Source: C:/Users/trg16/Dev/Bricklayer2.0/masonry/src/hooks/masonry-prompt-router.js

## What It Does

The prompt router is a UserPromptSubmit hook that:
1. Intercepts every user prompt before Claude sees it
2. Detects intent via regex pattern matching (INTENT_RULES array)
3. Classifies effort (low/medium/high/max) via additional regex
4. Injects a one-line routing hint: `→ Mortar: routing to {agent} [effort:X]`

**Critical note:** It only injects text into the context — it does NOT force routing. Claude reads the hint and may or may not honor it.

## Intent Rule Coverage

The router covers 9 intent categories:
1. Campaign / research loop → Trowel
2. Security audit → security agent
3. Architecture / design → architect + design-reviewer
4. UI / design → uiux-master
5. Debugging → diagnose-analyst → fix-implementer
6. Build / implement → developer + test-writer + code-reviewer
7. Git → git-nerd
8. Refactoring → refactorer
9. Documentation / roadmap → karen
10. Research / analysis (generic) → research-analyst + competitive-analyst

## Gap Analysis

**Not covered by router:**
- Simple questions / lookups (falls through to no routing hint)
- Multi-part prompts that span multiple intent categories
- Follow-up prompts in an existing conversation (context-dependent routing)
- Prompts shorter than 20 chars or starting with `/`

## Skip Conditions

The router exits silently (no hint) when:
- Prompt is empty, a slash command, or < 20 chars
- CWD contains `program.md` + `questions.md` (inside BL research loop)
- `masonry-state.json` has `mode` set (active campaign)
- Intent is unclear AND effort is "medium" (default, no signal)

## Signal Injection Mechanism

Output format:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "content": "→ Mortar: routing to {agent} [effort:X] — {note}"
  }
}
```

This content is injected into the conversation context. Claude sees it as part of the system context before processing the user prompt.

## Structural Weakness

The router uses **first-match** logic. If a prompt matches an early rule (e.g., "ui"), it never checks if it also matches later rules (e.g., "build"). Multi-intent prompts get single-agent routing hints, potentially missing required specialists.

## Why Routing Hints May Be Ignored

1. **Context window position**: The hint appears as a brief system context addition. In long conversations with rich history, this hint may be weighted less heavily than conversation history.
2. **No penalty for non-compliance**: Claude receives the hint but faces no consequence for ignoring it.
3. **"Trivial" override**: CLAUDE.md says "direct action when trivial" — Claude can classify any task as trivial to justify inline execution.
4. **Conversation mode vs. campaign mode**: In casual conversation, routing feels unnecessary. In campaign mode, routing is expected. The distinction may not be clear to Claude without explicit mode indicators.
