#!/usr/bin/env node
/**
 * route.js
 * Wrap the routing pipeline and output a single JSON routing decision.
 *
 * Usage:
 *   node masonry/src/engine/cli/route.js --prompt "<text>" [--project-dir <path>]
 *
 * stdout: JSON routing decision on success, {"error":"..."} on bad invocation.
 * exit 0: success (including no-match), exit 1: unexpected error only.
 *
 * All debug / status output goes to stderr so stdout stays clean JSON.
 */

"use strict";

const path = require("path");
const { detectIntentAsync } = require("../../hooks/session/registry-router.js");

// ---------------------------------------------------------------------------
// Arg parsing
// ---------------------------------------------------------------------------

function parseArgs(argv) {
  const args = { prompt: null, projectDir: null };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--prompt" && argv[i + 1]) {
      args.prompt = argv[++i];
    } else if (argv[i] === "--project-dir" && argv[i + 1]) {
      args.projectDir = argv[++i];
    }
  }
  return args;
}

// ---------------------------------------------------------------------------
// Result mapping
// ---------------------------------------------------------------------------

/**
 * Map a detectIntentAsync result object to the CLI output shape.
 * @param {object} result - result from detectIntentAsync (non-null)
 * @returns {{ agent: string, confidence: number, layer: string, note: string }}
 */
function mapResult(result) {
  let layer;
  if (result.registryMatch) {
    layer = "L1a";
  } else if (result.semanticMatch) {
    layer = "L2";
  } else {
    layer = "L1b";
  }

  return {
    agent: result.route ?? null,
    confidence: result.semanticMatch
      ? parseFloat((result.note.match(/sim=([\d.]+)/)?.[1] ?? "0"))
      : 1.0,
    layer,
    note: result.note ?? "",
  };
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

async function main() {
  const args = parseArgs(process.argv.slice(2));

  if (!args.prompt) {
    process.stdout.write(JSON.stringify({ error: "--prompt is required" }) + "\n");
    process.exit(1);
  }

  let result;
  try {
    result = await detectIntentAsync(args.prompt);
  } catch (err) {
    process.stderr.write("[route.js] detectIntentAsync threw: " + err.message + "\n");
    result = null;
  }

  if (!result) {
    process.stdout.write(
      JSON.stringify({ agent: null, confidence: 0, layer: null, note: "no match" }) + "\n"
    );
    process.exit(0);
  }

  process.stdout.write(JSON.stringify(mapResult(result)) + "\n");
  process.exit(0);
}

main().catch((err) => {
  process.stderr.write("[route.js] fatal: " + err.message + "\n");
  process.stdout.write(JSON.stringify({ error: "unexpected error: " + err.message }) + "\n");
  process.exit(1);
});
