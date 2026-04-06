#!/usr/bin/env node
/**
 * registry-list.js
 * List agents from agent_registry.yml, optionally filtered by tier or mode.
 *
 * Usage:
 *   node registry-list.js [--tier <tier>] [--mode <mode>] [--project-dir <path>]
 *
 * stdout: JSON array of agent objects on success, or {"error":"..."} on failure.
 * exit 0: success, exit 1: failure.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import yaml from 'js-yaml';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function parseArgs(argv) {
  const args = { tier: null, mode: null, projectDir: null };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--tier' && argv[i + 1]) {
      args.tier = argv[++i];
    } else if (argv[i] === '--mode' && argv[i + 1]) {
      args.mode = argv[++i];
    } else if (argv[i] === '--project-dir' && argv[i + 1]) {
      args.projectDir = argv[++i];
    }
  }
  return args;
}

function resolveRegistryPath(projectDir) {
  if (projectDir) {
    return path.join(projectDir, 'masonry', 'agent_registry.yml');
  }
  // __dirname is masonry/src/engine/cli — go up 3 levels to masonry/
  return path.resolve(__dirname, '..', '..', '..', 'agent_registry.yml');
}

function buildAgent(raw) {
  return {
    id: raw.name ?? null,
    tier: raw.tier ?? null,
    mode: raw.modes ?? raw.mode ?? null,
    description: raw.description ?? null,
    capabilities: raw.capabilities ?? null,
  };
}

function agentMatchesTier(agent, tier) {
  return agent.tier === tier;
}

function agentMatchesMode(agent, mode) {
  const modeField = agent.mode;
  if (Array.isArray(modeField)) {
    return modeField.includes(mode);
  }
  if (typeof modeField === 'string') {
    return modeField === mode;
  }
  return false;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const registryPath = resolveRegistryPath(args.projectDir);

  if (!fs.existsSync(registryPath)) {
    process.stdout.write(JSON.stringify({ error: `registry not found at ${registryPath}` }) + '\n');
    process.exit(1);
  }

  let doc;
  try {
    const raw = fs.readFileSync(registryPath, 'utf8');
    doc = yaml.load(raw);
  } catch (err) {
    process.stdout.write(JSON.stringify({ error: `failed to parse registry: ${err.message}` }) + '\n');
    process.exit(1);
  }

  const agentList = doc?.agents;
  if (!Array.isArray(agentList)) {
    process.stdout.write(JSON.stringify({ error: 'registry has no agents list' }) + '\n');
    process.exit(1);
  }

  let agents = agentList.map(buildAgent);

  if (args.tier) {
    agents = agents.filter((a) => agentMatchesTier(a, args.tier));
  }

  if (args.mode) {
    agents = agents.filter((a) => agentMatchesMode(a, args.mode));
  }

  process.stdout.write(JSON.stringify(agents) + '\n');
  process.exit(0);
}

main();
