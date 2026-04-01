#!/usr/bin/env node
/**
 * masonry-secret-scanner.js
 * PreToolUse hook — blocks Write/Edit if secret patterns detected
 */

const SECRET_PATTERNS = [
  // 1. AWS Access Key ID
  { name: 'AWS_ACCESS_KEY', pattern: /AKIA[0-9A-Z]{16}/, description: 'AWS access key ID' },
  // 2. AWS Secret Access Key
  { name: 'AWS_SECRET_KEY', pattern: /(?:aws_secret|aws_secret_access_key)\s*[=:]\s*["']?[A-Za-z0-9+/]{40}["']?/i, description: 'AWS secret access key' },
  // 3. GitHub PAT (classic)
  { name: 'GITHUB_PAT', pattern: /ghp_[A-Za-z0-9]{36}/, description: 'GitHub Personal Access Token' },
  // 4. GitHub OAuth Token
  { name: 'GITHUB_OAUTH', pattern: /gho_[A-Za-z0-9]{36}/, description: 'GitHub OAuth token' },
  // 5. Anthropic API Key
  { name: 'ANTHROPIC_KEY', pattern: /sk-ant-[A-Za-z0-9\-_]{20,}/, description: 'Anthropic API key' },
  // 6. OpenAI API Key (sk- + exactly 48 alphanumeric chars)
  { name: 'OPENAI_KEY', pattern: /sk-[A-Za-z0-9]{48}/, description: 'OpenAI API key' },
  // 7. Stripe Secret Key
  { name: 'STRIPE_SECRET', pattern: /sk_(?:live|test)_[A-Za-z0-9]{24,}/, description: 'Stripe secret key' },
  // 8. Solana Private Key (base58, 64-byte keypair)
  { name: 'SOLANA_PRIVATE_KEY', pattern: /(?:private_key|secret_key|keypair)\s*[=:]\s*["']?[1-9A-HJ-NP-Za-km-z]{87,88}["']?/i, description: 'Solana private key' },
  // 9. Generic sk- prefix token (catch-all for other services)
  { name: 'GENERIC_SK', pattern: /(?<!\w)sk-[A-Za-z0-9\-_]{20,}(?!\w)/, description: 'Generic sk- API key' },
  // 10. PEM private key header
  { name: 'PEM_PRIVATE_KEY', pattern: /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/, description: 'PEM private key' },
  // 11. JWT secret in assignment
  { name: 'JWT_SECRET', pattern: /(?:jwt_secret|JWT_SECRET|secret_key)\s*[=:]\s*["'][A-Za-z0-9+/=]{20,}["']/, description: 'JWT secret' },
  // 12. Database URL with embedded credentials
  { name: 'DB_URL_WITH_CREDS', pattern: /(?:postgres|mysql|mongodb):\/\/[^:]+:[^@]+@/, description: 'Database URL with embedded credentials' },
];

// Files exempt from scanning (test fixtures, examples, mocks)
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
  if (!filePath) return false;
  return EXEMPT_PATTERNS.some(p => p.test(filePath));
}

function scanContent(content, filePath) {
  const findings = [];
  const lines = content.split('\n');

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    for (const { name, pattern, description } of SECRET_PATTERNS) {
      if (pattern.test(line)) {
        findings.push({
          pattern_type: name,
          description,
          file_path: filePath || '(stdin)',
          line_number: i + 1,
          line_preview: line.trim().substring(0, 80) + (line.trim().length > 80 ? '...' : ''),
        });
      }
    }
  }

  return findings;
}

// Read hook input from stdin
let input = '';
process.stdin.on('data', chunk => { input += chunk; });
process.stdin.on('end', () => {
  try {
    const hookData = JSON.parse(input);
    const { tool_name, tool_input } = hookData;

    // Only scan Write and Edit operations
    if (!['Write', 'Edit'].includes(tool_name)) {
      process.exit(0); // Allow
    }

    const filePath = tool_input.file_path || tool_input.path || '';

    // Skip exempt files
    if (isExempt(filePath)) {
      process.exit(0);
    }

    // Get content to scan
    let content = '';
    if (tool_name === 'Write') {
      content = tool_input.content || '';
    } else if (tool_name === 'Edit') {
      content = (tool_input.new_string || '') + '\n' + (tool_input.old_string || '');
    }

    const findings = scanContent(content, filePath);

    if (findings.length > 0) {
      for (const f of findings) {
        process.stderr.write(`[SECRET SCAN] Blocked: ${f.pattern_type} detected in ${f.file_path}:${f.line_number}\n`);
        process.stderr.write(`  Pattern: ${f.description}\n`);
        process.stderr.write(`  Line: ${f.line_preview}\n`);
        process.stderr.write(`  Remove the secret before committing.\n`);
      }
      process.exit(2); // Block
    }

    process.exit(0); // Allow
  } catch (e) {
    // Parse error — don't block
    process.exit(0);
  }
});
