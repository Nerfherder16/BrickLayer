#!/usr/bin/env node
/**
 * masonry-config-protection.js
 * PreToolUse hook — blocks writes to lint configuration files unless
 * LINT_CONFIG_OVERRIDE is present in the user message.
 */

const fs = require('fs');
const path = require('path');

// Patterns for protected standalone lint config files
const PROTECTED_PATTERNS = [
  /\.eslintrc(\.(js|cjs|json|yaml|yml))?$/,
  /\.prettierrc(\.(js|cjs|json|yaml|yml))?$/,
  /prettier\.config\.(js|cjs|mjs)$/,
  /ruff\.toml$/,
];

// Sections in pyproject.toml that are considered lint config
const PYPROJECT_LINT_SECTIONS = /\[tool\.(ruff|black|flake8|isort|pylint)\]/;

function isProtectedLintConfig(filePath, toolInput) {
  if (!filePath) return false;

  const basename = path.basename(filePath);

  // Check standalone lint config patterns
  if (PROTECTED_PATTERNS.some(p => p.test(basename))) {
    return true;
  }

  // Check pyproject.toml — only protected if it contains lint sections
  if (/pyproject\.toml$/.test(filePath)) {
    // Check the content being written
    const incomingContent = toolInput.content || toolInput.new_string || '';
    if (PYPROJECT_LINT_SECTIONS.test(incomingContent)) {
      return true;
    }

    // Check existing on-disk content for lint sections
    try {
      const existing = fs.readFileSync(filePath, 'utf8');
      if (PYPROJECT_LINT_SECTIONS.test(existing)) {
        return true;
      }
    } catch (_) {
      // File does not exist yet — no existing lint sections, not protected on filename alone
    }
  }

  return false;
}

// Read hook input from stdin
let input = '';
process.stdin.on('data', chunk => { input += chunk; });
process.stdin.on('end', () => {
  try {
    const hookData = JSON.parse(input);
    const { tool_name, tool_input } = hookData;

    // Only guard Write and Edit operations
    if (!['Write', 'Edit'].includes(tool_name)) {
      process.exit(0);
    }

    const filePath = tool_input.file_path || tool_input.path || '';

    if (!isProtectedLintConfig(filePath, tool_input)) {
      process.exit(0); // Not a lint config — allow
    }

    // Check for override token in user message
    const userMessage =
      (hookData.tool_context && hookData.tool_context.user_message) || '';
    if (/LINT_CONFIG_OVERRIDE/i.test(userMessage)) {
      process.exit(0); // Override granted
    }

    // Block the write
    const reason =
      '[masonry-config-protection] BLOCKED: Write to lint config requires explicit override. ' +
      'Add # LINT_CONFIG_OVERRIDE to your message to proceed.';

    process.stdout.write(
      JSON.stringify({ decision: 'block', reason }) + '\n'
    );
    process.exit(2);
  } catch (_) {
    // stdin parse failure — allow rather than block
    process.exit(0);
  }
});
