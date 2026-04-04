---
name: context7
description: Get up-to-date library documentation - use when coding with unfamiliar APIs or packages
---

# Context7 MCP

## Purpose
Pulls current, version-specific documentation directly into prompts.
Eliminates outdated info and hallucinated APIs.

## Key Tools
- `resolve-library-id` - Find Context7 ID for a package name
- `get-library-docs` - Get documentation for a library

## Workflow
1. First call `resolve-library-id` with package name
2. Then call `get-library-docs` with the resolved ID

## When to Use
- Working with unfamiliar npm/pip packages
- Need current API docs (not training data)
- User says "use context7" in prompt
- Avoiding hallucinated method names

## Supported Languages
JavaScript/TypeScript, Python, Java, Go, Rust, and more
