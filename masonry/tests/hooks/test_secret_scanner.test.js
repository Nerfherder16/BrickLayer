import { execFileSync } from "child_process";
import { join } from "path";
import { describe, it, expect } from "vitest";

const HOOK = join(process.cwd(), "src", "hooks", "masonry-content-guard.js");

/**
 * Run the hook with a synthetic tool payload.
 * Returns the exit code: 0 = allow, 2 = block.
 */
function runHook(toolName, toolInput) {
  try {
    execFileSync("node", [HOOK], {
      input: JSON.stringify({ tool_name: toolName, tool_input: toolInput }),
      stdio: ["pipe", "pipe", "pipe"],
    });
    return 0;
  } catch (e) {
    return e.status ?? 1;
  }
}

// ---------------------------------------------------------------------------
// Positive match tests — 12 patterns, one per pattern definition
// ---------------------------------------------------------------------------

describe("secret scanner — positive matches (should block)", () => {
  it("blocks AWS access key ID (AKIA...)", () => {
    const code = runHook("Write", {
      file_path: "config.js",
      content: 'const key = "AKIAIOSFODNN7EXAMPLE";',
    });
    expect(code).toBe(2);
  });

  it("blocks AWS secret access key assignment", () => {
    const code = runHook("Write", {
      file_path: "config.js",
      content: 'aws_secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY1234"',
    });
    expect(code).toBe(2);
  });

  it("blocks GitHub classic PAT (ghp_...)", () => {
    const code = runHook("Write", {
      file_path: "deploy.js",
      content: 'const token = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij";',
    });
    expect(code).toBe(2);
  });

  it("blocks GitHub OAuth token (gho_...)", () => {
    const code = runHook("Write", {
      file_path: "auth.js",
      content: 'const oauthToken = "gho_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij";',
    });
    expect(code).toBe(2);
  });

  it("blocks Anthropic API key (sk-ant-...)", () => {
    const code = runHook("Write", {
      file_path: "api.js",
      content: 'const apiKey = "sk-ant-api03-ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcd";',
    });
    expect(code).toBe(2);
  });

  it("blocks OpenAI API key (sk- + 48 chars)", () => {
    const code = runHook("Write", {
      file_path: "openai.js",
      content: 'const key = "sk-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx";',
    });
    expect(code).toBe(2);
  });

  it("blocks Stripe secret key (sk_live_...)", () => {
    const code = runHook("Write", {
      file_path: "payments.js",
      content: 'const stripe = "sk_' + 'live_ABCDEFGHIJKLMNOPQRSTUVWXYZabcd";',
    });
    expect(code).toBe(2);
  });

  it("blocks Solana private key assignment", () => {
    // 88-char valid base58 string (no 0, O, I, l chars)
    const solanaKey = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdef";
    const code = runHook("Write", {
      file_path: "wallet.js",
      content: `const private_key = "${solanaKey}";`,
    });
    expect(code).toBe(2);
  });

  it("blocks generic sk- prefixed token (not caught by more specific patterns)", () => {
    const code = runHook("Write", {
      file_path: "service.js",
      content: 'const token = "sk-someservice-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij12345";',
    });
    expect(code).toBe(2);
  });

  it("blocks PEM private key header", () => {
    const code = runHook("Write", {
      file_path: "tls.pem",
      content: "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA0Z3VS5JJcds3xHn/ygWep4",
    });
    expect(code).toBe(2);
  });

  it("blocks JWT secret assignment", () => {
    const code = runHook("Write", {
      file_path: "server.js",
      content: 'const JWT_SECRET = "mySuperSecretKey1234567890abcdef";',
    });
    expect(code).toBe(2);
  });

  it("blocks database URL with embedded credentials", () => {
    const code = runHook("Write", {
      file_path: "db.js",
      content: 'const url = "postgres://admin:secretpassword@localhost:5432/mydb";',
    });
    expect(code).toBe(2);
  });
});

// ---------------------------------------------------------------------------
// Negative match tests — similar-looking but not secrets (should allow)
// ---------------------------------------------------------------------------

describe("secret scanner — negative matches (should allow)", () => {
  it("allows placeholder AWS key text in documentation", () => {
    const code = runHook("Write", {
      file_path: "README.md",
      content: "Set AWS_ACCESS_KEY_ID to your access key value.",
    });
    expect(code).toBe(0);
  });

  it("allows short sk- string that does not meet length threshold", () => {
    const code = runHook("Write", {
      file_path: "config.js",
      content: 'const prefix = "sk-short";',
    });
    expect(code).toBe(0);
  });

  it("allows database URL without credentials (no user:pass@)", () => {
    const code = runHook("Write", {
      file_path: "config.js",
      content: 'const url = "postgres://localhost:5432/mydb";',
    });
    expect(code).toBe(0);
  });

  it("allows normal source code with no secrets", () => {
    const code = runHook("Write", {
      file_path: "utils.js",
      content: "function add(a, b) { return a + b; }\nmodule.exports = { add };",
    });
    expect(code).toBe(0);
  });

  it("allows Bash tool operations (not scanned)", () => {
    const code = runHook("Bash", {
      command: 'echo "sk-ant-api03-ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcd"',
    });
    expect(code).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// Exempt file path tests — should always allow regardless of content
// ---------------------------------------------------------------------------

describe("secret scanner — exempt file paths (should allow)", () => {
  it("allows test_ prefixed files even with secret-looking content", () => {
    const code = runHook("Write", {
      file_path: "tests/test_auth.js",
      content: 'const key = "AKIAIOSFODNN7EXAMPLE";',
    });
    expect(code).toBe(0);
  });

  it("allows .example files even with secret-looking content", () => {
    const code = runHook("Write", {
      file_path: ".env.example",
      content: 'AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\nAWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY1',
    });
    expect(code).toBe(0);
  });

  it("allows fixture files even with secret-looking content", () => {
    const code = runHook("Write", {
      file_path: "tests/fixtures/auth_response.json",
      content: '{ "token": "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij" }',
    });
    expect(code).toBe(0);
  });
});
