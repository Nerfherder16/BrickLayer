---
name: playwright
description: Browser automation for testing, form filling, screenshots, web scraping
---

# Playwright MCP

## Key Tools
- `mcp__playwright__browser_navigate` - Go to URL
- `mcp__playwright__browser_snapshot` - Get accessibility tree (better than screenshot)
- `mcp__playwright__browser_click` - Click element by ref
- `mcp__playwright__browser_type` - Type into element
- `mcp__playwright__browser_fill_form` - Fill multiple form fields
- `mcp__playwright__browser_take_screenshot` - Capture page
- `mcp__playwright__browser_evaluate` - Run JavaScript
- `mcp__playwright__browser_wait_for` - Wait for text/element

## Workflow
1. Navigate to URL
2. Take snapshot to see elements with refs
3. Interact using refs from snapshot
4. Verify with screenshot

## Use Cases
- Testing FamilyHub tablet UI
- Automating web forms
- Scraping dynamic content
- E2E testing workflows
