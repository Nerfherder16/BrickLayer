#!/usr/bin/env node
"use strict";
/**
 * bin/masonry-mcp.js — Masonry MCP server (thin orchestrator)
 * All tool schemas and implementations live in masonry/src/tools/.
 */

const readline = require("readline");
const pkg = require("../package.json");

// ---------------------------------------------------------------------------
// Tool schema registry
// ---------------------------------------------------------------------------

const { TOOLS_CORE } = require("../src/tools/schema-core");
const { TOOLS_ADVANCED } = require("../src/tools/schema-advanced");
const extraTools = require("../src/tools/extra-tools");
const patternLifecycle = require("../src/tools/pattern-lifecycle");

const TOOLS = [
  ...TOOLS_CORE,
  ...TOOLS_ADVANCED,
  ...extraTools.schemas,
  ...patternLifecycle.schemas,
];

// ---------------------------------------------------------------------------
// Tool implementation modules
// ---------------------------------------------------------------------------

const campaign = require("../src/tools/impl-campaign");
const simulation = require("../src/tools/impl-simulation");
const patterns = require("../src/tools/impl-patterns");
const agents = require("../src/tools/impl-agents");
const consensus = require("../src/tools/impl-consensus");
const misc = require("../src/tools/impl-misc");
const { toolDoctor } = require("../src/tools/impl-doctor");

// ---------------------------------------------------------------------------
// Dispatch
// ---------------------------------------------------------------------------

async function processRequest(name, args) {
  switch (name) {
    // Campaign
    case "masonry_status":        return campaign.toolStatus(args);
    case "masonry_findings":      return campaign.toolFindings(args);
    case "masonry_questions":     return campaign.toolQuestions(args);
    case "masonry_run":           return campaign.toolRun(args);
    case "masonry_weights":       return campaign.toolWeights(args);
    case "masonry_fleet":         return campaign.toolFleet(args);
    // Simulation / research
    case "masonry_recall":        return await simulation.toolRecall(args);
    case "masonry_git_hypothesis":return simulation.toolGitHypothesis(args);
    case "masonry_nl_generate":   return simulation.toolNlGenerate(args);
    case "masonry_run_question":  return simulation.toolRunQuestion(args);
    case "masonry_run_simulation":return simulation.toolRunSimulation(args);
    case "masonry_sweep":         return simulation.toolSweep(args);
    case "masonry_route":         return simulation.toolRoute(args);
    // Patterns
    case "masonry_pattern_store": return await patterns.toolPatternStore(args);
    case "masonry_pattern_search":return await patterns.toolPatternSearch(args);
    case "masonry_pattern_decay":   return patterns.toolPatternDecay(args);
    case "masonry_pattern_promote": return patterns.toolPatternPromote(args);
    case "masonry_pattern_demote":  return patterns.toolPatternDemote(args);
    // Agents / swarm
    case "masonry_worker_status": return agents.toolWorkerStatus(args);
    case "masonry_task_assign":   return agents.toolTaskAssign(args);
    case "masonry_agent_health":  return agents.toolAgentHealth(args);
    case "masonry_wave_validate": return agents.toolWaveValidate(args);
    case "masonry_swarm_init":    return agents.toolSwarmInit(args);
    // Consensus
    case "masonry_consensus_check":   return consensus.toolConsensusCheck(args);
    case "masonry_review_consensus":  return consensus.toolReviewConsensus(args);
    // Misc
    case "masonry_doctor":            return await toolDoctor(args);
    case "masonry_verify_7point":     return misc.toolVerify7point(args);
    case "masonry_training_update":   return misc.toolTrainingUpdate(args);
    case "masonry_set_strategy":      return misc.toolSetStrategy(args);
    case "masonry_reasoning_store":   return misc.toolReasoningStore(args);
    case "masonry_reasoning_query":   return misc.toolReasoningQuery(args);
    case "masonry_graph_record":      return misc.toolGraphRecord(args);
    case "masonry_pagerank_run":      return misc.toolPageRankRun(args);
    case "masonry_claim_add":         return misc.toolClaimsAdd(args);
    case "masonry_claims_list":       return misc.toolClaimsList(args);
    case "masonry_claim_resolve":     return misc.toolClaimResolve(args);
    default: {
      // Overflow tools (extra-tools + pattern-lifecycle)
      try { return extraTools.handle(name, args); } catch (_) {}
      try { return patternLifecycle.handle(name, args); } catch (_) {}
      throw new Error(`Unknown tool: ${name}`);
    }
  }
}

// ---------------------------------------------------------------------------
// MCP protocol layer
// ---------------------------------------------------------------------------

function sendResponse(obj) {
  process.stdout.write(JSON.stringify(obj) + "\n");
}

function makeError(id, code, message) {
  return { jsonrpc: "2.0", id, error: { code, message } };
}

async function handleRequest(raw) {
  let msg;
  try { msg = JSON.parse(raw); } catch (_) {
    sendResponse(makeError(null, -32700, "Parse error"));
    return;
  }

  const { jsonrpc, id, method, params } = msg;
  if (jsonrpc !== "2.0") { sendResponse(makeError(id ?? null, -32600, "Invalid Request")); return; }
  if (id === undefined || id === null) return; // notifications — ignore

  switch (method) {
    case "initialize":
      sendResponse({ jsonrpc: "2.0", id, result: {
        protocolVersion: "2024-11-05",
        capabilities: { tools: {} },
        serverInfo: { name: "masonry-mcp", version: pkg.version },
      }});
      break;

    case "tools/list":
      sendResponse({ jsonrpc: "2.0", id, result: { tools: TOOLS } });
      break;

    case "tools/call": {
      const toolName = params && params.name;
      const toolArgs = (params && params.arguments) || {};
      if (!toolName) { sendResponse(makeError(id, -32602, "Missing tool name")); return; }
      try {
        const result = await processRequest(toolName, toolArgs);
        sendResponse({ jsonrpc: "2.0", id, result: { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] } });
      } catch (err) {
        sendResponse(makeError(id, -32603, err.message || "Tool execution error"));
      }
      break;
    }

    case "notifications/initialized":
      break;

    default:
      sendResponse(makeError(id, -32601, `Method not found: ${method}`));
  }
}

// ---------------------------------------------------------------------------
// Main — read stdin line by line
// ---------------------------------------------------------------------------

process.stderr.write(`masonry-mcp v${pkg.version} started\n`);

const rl = readline.createInterface({ input: process.stdin, output: null, terminal: false, crlfDelay: Infinity });

let pendingRequests = 0;
let stdinClosed = false;

rl.on("line", (line) => {
  const trimmed = line.trim();
  if (!trimmed) return;
  pendingRequests++;
  handleRequest(trimmed)
    .catch((err) => { process.stderr.write(`Unhandled error: ${err.message}\n`); })
    .finally(() => { pendingRequests--; if (stdinClosed && pendingRequests === 0) process.exit(0); });
});

rl.on("close", () => { stdinClosed = true; if (pendingRequests === 0) process.exit(0); });
