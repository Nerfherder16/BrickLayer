#!/usr/bin/env node
/**
 * masonry-content-guard.js
 * PreToolUse hook — combined Write/Edit gate (replaces masonry-secret-scanner.js
 * and masonry-config-protection.js, archived 2026-03-28).
 *
 * Pass 1 — Secret scan: blocks if secret patterns detected in written content.
 * Pass 2 — Lint config protection: blocks writes to lint config files unless
 *           LINT_CONFIG_OVERRIDE is present in the user message.
 *
 * Exit codes:
 *   0 — allow
 *   2 — block (secret detected OR lint config protected)
 */

'use strict';
const fs = require('fs');
const path = require('path');

// ─── Pass 1: Secret patterns ────────────────────────────────────────────────

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

const EXEMPT_PATTERNS = [/\.example$/, /\.sample$/, /test_/, /_test\./, /\.test\./, /mock_/, /_mock\./, /fixture/, /\.env\.example/];

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
        findings.push({ name, description, file: filePath || '(stdin)', line: i + 1, preview: line.trim().slice(0, 80) });
      }
    }
  }
  return findings;
}

// ─── Pass 2: Lint config protection ─────────────────────────────────────────

const LINT_CONFIG_PATTERNS = [
  /\.eslintrc(\.(js|cjs|json|yaml|yml))?$/,
  /\.prettierrc(\.(js|cjs|json|yaml|yml))?$/,
  /prettier\.config\.(js|cjs|mjs)$/,
  /ruff\.toml$/,
];
const PYPROJECT_LINT_SECTIONS = /\[tool\.(ruff|black|flake8|isort|pylint)\]/;

function isProtectedLintConfig(filePath, toolInput) {
  if (!filePath) return false;
  const basename = path.basename(filePath);
  if (LINT_CONFIG_PATTERNS.some(p => p.test(basename))) return true;
  if (/pyproject\.toml$/.test(filePath)) {
    const incoming = toolInput.content || toolInput.new_string || '';
    if (PYPROJECT_LINT_SECTIONS.test(incoming)) return true;
    try {
      const existing = fs.readFileSync(filePath, 'utf8');
      if (PYPROJECT_LINT_SECTIONS.test(existing)) return true;
    } catch (_) {}
  }
  return false;
}

// ─── Main ────────────────────────────────────────────────────────────────────

let input = '';
process.stdin.on('data', chunk => { input += chunk; });
process.stdin.on('end', () => {
  try {
    const hookData = JSON.parse(input);
    const { tool_name, tool_input } = hookData;

    if (!['Write', 'Edit'].includes(tool_name)) process.exit(0);

    const filePath = tool_input.file_path || tool_input.path || '';

    // ── Pass 1b: .env file protection (passive-frontend-v2) ─────────────────
    const basename = path.basename(filePath);
    if (/passive-frontend-v2/.test(filePath) && /^\.env(\..+)?$/.test(basename) && !/\.example$/.test(basename)) {
      process.stdout.write(JSON.stringify({
        decision: 'block',
        reason: '[masonry-content-guard] BLOCKED: Direct edits to .env files in passive-frontend-v2 are prohibited. Edit .env.local.example instead, or use ENV_OVERRIDE in your message to proceed.',
      }) + '\n');
      process.exit(2);
    }

    // ── Pass 1: secrets ──────────────────────────────────────────────────────
    if (!isExempt(filePath)) {
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
    }

    // ── Pass 2: lint config protection ──────────────────────────────────────
    if (isProtectedLintConfig(filePath, tool_input)) {
      const userMessage = (hookData.tool_context && hookData.tool_context.user_message) || '';
      if (!/LINT_CONFIG_OVERRIDE/i.test(userMessage)) {
        process.stdout.write(JSON.stringify({
          decision: 'block',
          reason: '[masonry-content-guard] BLOCKED: Write to lint config requires explicit override. Add # LINT_CONFIG_OVERRIDE to your message to proceed.',
        }) + '\n');
        process.exit(2);
      }
    }

    process.exit(0);
  } catch (_) {
    process.exit(0);
  }
});
