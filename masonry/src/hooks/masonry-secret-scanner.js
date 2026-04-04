#!/usr/bin/env node
/**
 * masonry-secret-scanner.js
 * PreToolUse hook — blocks Write/Edit operations that contain secret credentials.
 *
 * Scans the content being written for known secret patterns (API keys, tokens,
 * private keys, database URLs with embedded credentials, etc.).
 * Exempt file paths (test files, fixtures, .example files) are skipped.
 *
 * Exit codes:
 *   0 — allow (no secrets detected, or exempt path, or non-Write/Edit tool)
 *   2 — block (secret pattern detected)
 */

'use strict';
const path = require('path');

// ─── Secret patterns ─────────────────────────────────────────────────────────

const SECRET_PATTERNS = [
  { name: 'AWS_ACCESS_KEY',     pattern: /AKIA[0-9A-Z]{16}/,                                                                       description: 'AWS access key ID' },
  { name: 'AWS_SECRET_KEY',     pattern: /(?:aws_secret|aws_secret_access_key)\s*[=:]\s*["']?[A-Za-z0-9+/]{40}["']?/i,           description: 'AWS secret access key' },
  { name: 'GITHUB_PAT',         pattern: /ghp_[A-Za-z0-9]{36}/,                                                                    description: 'GitHub Personal Access Token' },
  { name: 'GITHUB_OAUTH',       pattern: /gho_[A-Za-z0-9]{36}/,                                                                    description: 'GitHub OAuth token' },
  { name: 'ANTHROPIC_KEY',      pattern: /sk-ant-[A-Za-z0-9\-_]{20,}/,                                                            description: 'Anthropic API key' },
  { name: 'OPENAI_KEY',         pattern: /sk-[A-Za-z0-9]{48}/,                                                                     description: 'OpenAI API key' },
  { name: 'STRIPE_SECRET',      pattern: /sk_(?:live|test)_[A-Za-z0-9]{24,}/,                                                     description: 'Stripe secret key' },
  { name: 'SOLANA_PRIVATE_KEY', pattern: /(?:private_key|secret_key|keypair)\s*[=:]\s*["']?[1-9A-HJ-NP-Za-km-z]{87,88}["']?/i, description: 'Solana private key' },
  { name: 'GENERIC_SK',         pattern: /(?<!\w)sk-[A-Za-z0-9\-_]{20,}(?!\w)/,                                                  description: 'Generic sk- API key' },
  { name: 'PEM_PRIVATE_KEY',    pattern: /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/,                                     description: 'PEM private key' },
  { name: 'JWT_SECRET',         pattern: /(?:jwt_secret|JWT_SECRET|secret_key)\s*[=:]\s*["'][A-Za-z0-9+/=]{20,}["']/,           description: 'JWT secret' },
  { name: 'DB_URL_WITH_CREDS',  pattern: /(?:postgres|mysql|mongodb):\/\/[^:]+:[^@]+@/,                                           description: 'Database URL with embedded credentials' },
];

const EXEMPT_PATTERNS = [
  /\.example$/,
  /\.sample$/,
  /test_/,
  /_test\./,
  /\.test\./,
  /mock_/,
  /_mock\./,
  /fixture/,
  /\.env\.example/,
];

function isExempt(filePath) {
  return filePath ? EXEMPT_PATTERNS.some(p => p.test(filePath)) : false;
}

function scanSecrets(content, filePath) {
  const findings = [];
  const lines = content.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    for (const { name, pattern, description } of SECRET_PATTERNS) {
      if (pattern.test(line)) {
        findings.push({
          name,
          description,
          file: filePath || '(stdin)',
          line: i + 1,
          preview: line.trim().slice(0, 80),
        });
      }
    }
  }
  return findings;
}

// ─── Main ────────────────────────────────────────────────────────────────────

let input = '';
process.stdin.on('data', chunk => { input += chunk; });
process.stdin.on('end', () => {
  try {
    const hookData = JSON.parse(input);
    const { tool_name, tool_input } = hookData;

    if (!['Write', 'Edit'].includes(tool_name)) {
      process.exit(0);
    }

    const filePath = tool_input.file_path || tool_input.path || '';

    if (isExempt(filePath)) {
      process.exit(0);
    }

    let content = '';
    if (tool_name === 'Write') {
      content = tool_input.content || '';
    } else {
      content = (tool_input.new_string || '') + '\n' + (tool_input.old_string || '');
    }

    const findings = scanSecrets(content, filePath);
    if (findings.length > 0) {
      for (const f of findings) {
        process.stderr.write(`[SECRET SCAN] Blocked: ${f.name} detected in ${f.file}:${f.line}\n`);
        process.stderr.write(`  Pattern: ${f.description}\n`);
        process.stderr.write(`  Line: ${f.preview}\n`);
        process.stderr.write(`  Remove the secret before writing.\n`);
      }
      process.exit(2);
    }

    process.exit(0);
  } catch (_) {
    process.exit(0);
  }
});
