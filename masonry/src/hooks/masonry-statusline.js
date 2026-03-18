"use strict";
const fs = require("fs");
const path = require("path");
const os = require("os");
const { spawn, execSync } = require("child_process");

const C = {
  purple: "\x1b[38;2;139;92;246m",
  cyan: "\x1b[38;2;34;211;238m",
  orange: "\x1b[38;2;251;146;60m",
  pink: "\x1b[38;2;244;114;182m",
  green: "\x1b[38;2;52;211;153m",
  amber: "\x1b[38;2;245;158;11m",
  red: "\x1b[38;2;239;68;68m",
  dim: "\x1b[2m",
  reset: "\x1b[0m",
};
const c = (col, txt) => `${C[col]}${txt}${C.reset}`;
const dim = (txt) => `${C.dim}${txt}${C.reset}`;
const sep = dim("│");

function progressBar(pct) {
  const filled = Math.round((pct / 100) * 10);
  const col = pct >= 65 ? "pink" : pct >= 40 ? "orange" : "purple";
  return c(col, "█".repeat(filled)) + dim("░".repeat(10 - filled));
}

function loadConfig() {
  const DEFAULTS = {
    recallHost: process.env.RECALL_HOST || "http://100.70.195.84:8200",
    recallApiKey: process.env.RECALL_API_KEY || "",
    handoffThreshold: 70,
  };
  try {
    const p = path.join(os.homedir(), ".masonry", "config.json");
    if (fs.existsSync(p))
      return {
        ...DEFAULTS,
        ...JSON.parse(fs.readFileSync(p, "utf8")),
        recallApiKey: process.env.RECALL_API_KEY || "",
      };
  } catch (_) {}
  return DEFAULTS;
}

function recallDot(cfg) {
  const cacheFile = path.join(os.tmpdir(), "masonry-recall-status.json");
  try {
    if (fs.existsSync(cacheFile)) {
      const d = JSON.parse(fs.readFileSync(cacheFile, "utf8"));
      if (Date.now() - (d.ts || 0) < 30000)
        return d.ok ? c("green", "●") : c("red", "●");
    }
  } catch (_) {}
  // Spawn background check
  try {
    const script = path.join(
      os.homedir(),
      ".claude",
      "hud",
      "masonry-recall-check.js",
    );
    if (fs.existsSync(script)) {
      const child = spawn(
        process.execPath,
        [script, cfg.recallHost, cfg.recallApiKey || ""],
        { detached: true, stdio: "ignore" },
      );
      child.unref();
    }
  } catch (_) {}
  return dim("○");
}

function gitSegment(cwd) {
  try {
    const branch = execSync("git rev-parse --abbrev-ref HEAD", {
      cwd,
      stdio: "pipe",
      timeout: 2000,
    })
      .toString()
      .trim();
    const dirty = execSync("git status --porcelain", {
      cwd,
      stdio: "pipe",
      timeout: 2000,
    })
      .toString()
      .trim();
    const name = branch.length > 20 ? branch.slice(0, 20) : branch;
    return dim(name) + (dirty ? c("amber", "*") : "");
  } catch (_) {
    return "";
  }
}

function buildSegment(cwd) {
  try {
    const p = path.join(cwd, ".autopilot", "progress.json");
    if (!fs.existsSync(p)) return "";
    const data = JSON.parse(fs.readFileSync(p, "utf8"));
    const task = (data.tasks || []).find((t) => t.status === "IN_PROGRESS");
    if (!task) return "";
    return c("amber", `bld:#${task.id}`);
  } catch (_) {
    return "";
  }
}

function uiSegment(cwd) {
  try {
    const p = path.join(cwd, ".ui", "mode");
    if (!fs.existsSync(p)) return "";
    const mode = fs.readFileSync(p, "utf8").trim();
    if (!mode) return "";
    return c("cyan", `ui:${mode}`);
  } catch (_) {
    return "";
  }
}

function recallSegment(sessionId) {
  if (!sessionId) return "";
  try {
    const counterFile = path.join(
      os.tmpdir(),
      `masonry-recall-hits-${sessionId}.txt`,
    );
    if (!fs.existsSync(counterFile)) return "";
    const val = parseInt(fs.readFileSync(counterFile, "utf8").trim(), 10);
    if (!val || val <= 0) return "";
    // dim cyan: combine dim + 24-bit cyan
    return `\x1b[2m\x1b[38;2;34;211;238m↑${val} mem\x1b[0m`;
  } catch (_) {
    return "";
  }
}

function agentsSegment(state) {
  if (state.active_agents && Array.isArray(state.active_agents) && state.active_agents.length > 0) {
    return c("purple", `${state.active_agents.length} agents`);
  }
  if (state.active_agent) return dim(state.active_agent);
  return "";
}

// Read stdin synchronously — cross-platform (fd 0 works on Windows + Unix)
let stdinData = "";
try {
  const buf = Buffer.allocUnsafe(65536);
  const n = fs.readSync(0, buf, 0, buf.length, null);
  stdinData = buf.slice(0, n).toString("utf8");
} catch (_) {}
let input = {};
try {
  input = JSON.parse(stdinData);
} catch (_) {}

const ctxPct = Math.round(input.context_window?.used_percentage || 0);
const cfg = loadConfig();
const cwd = input.cwd || process.env.CLAUDE_PROJECT_DIR || process.cwd();
const sessionId = input.session_id || process.env.CLAUDE_SESSION_ID || "";
const brand = `🧱  ${c("purple", "masonry")}`;

let state = null;
try {
  const sf = path.join(cwd, "masonry-state.json");
  if (fs.existsSync(sf)) state = JSON.parse(fs.readFileSync(sf, "utf8"));
} catch (_) {}

const project = (state && state.project) || path.basename(cwd);
const bar = progressBar(ctxPct);
const ctxStr =
  ctxPct >= 65
    ? c("pink", `${ctxPct}%`)
    : ctxPct >= 40
      ? c("orange", `${ctxPct}%`)
      : c("purple", `${ctxPct}%`);
const recall = recallDot(cfg);

if (!state) {
  process.stdout.write(
    [
      brand,
      sep,
      dim(project),
      sep,
      gitSegment(cwd),
      recallSegment(sessionId),
      buildSegment(cwd),
      uiSegment(cwd),
      sep,
      dim("no campaign · /masonry-run to start"),
      sep,
      `${bar} ${ctxStr}`,
      sep,
      `${recall} ${dim("recall")}`,
    ]
      .filter(Boolean)
      .join("  ") + "\n",
  );
  process.exit(0);
}

const {
  mode = "?",
  wave = 0,
  q_current = 0,
  q_total = 0,
  verdicts = {},
} = state;
const v = [
  verdicts.HEALTHY > 0 ? c("green", `✓${verdicts.HEALTHY}`) : "",
  verdicts.WARNING > 0 ? c("amber", `⚠${verdicts.WARNING}`) : "",
  verdicts.FAILURE > 0 ? c("red", `✗${verdicts.FAILURE}`) : "",
]
  .filter(Boolean)
  .join(" ");

process.stdout.write(
  [
    brand,
    sep,
    dim(project),
    c("cyan", `${mode} · wave ${wave}`),
    sep,
    `Q${q_current}/${q_total}`,
    agentsSegment(state),
    sep,
    gitSegment(cwd),
    recallSegment(sessionId),
    buildSegment(cwd),
    uiSegment(cwd),
    sep,
    `${bar} ${ctxStr}`,
    v,
    sep,
    `${recall} ${dim("recall")}`,
  ]
    .filter(Boolean)
    .join("  ") + "\n",
);
process.exit(0);
