#!/usr/bin/env node
"use strict";
/**
 * bin/masonry-setup.js — Masonry plugin installer
 *
 * Installs Masonry into Claude Code's plugin system the same way OMC is installed:
 *   1. Write ~/.masonry/config.json
 *   2. Create a directory junction from the plugin cache path → masonry source root
 *   3. Register in ~/.claude/plugins/installed_plugins.json
 *   4. Add "masonry@masonry" to enabledPlugins in ~/.claude/settings.json
 *   5. Write statusLine command to ~/.claude/settings.json
 *   6. Smoke-check Recall connectivity
 *
 * Usage:
 *   node bin/masonry-setup.js [--recall-url <url>] [--api-key <key>] [--dry-run]
 *   node bin/masonry-setup.js --uninstall
 */

const fs = require("fs");
const path = require("path");
const os = require("os");
const readline = require("readline");

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------
const MASONRY_ROOT = path.resolve(__dirname, "..");
const MASONRY_DIR = path.join(os.homedir(), ".masonry");
const CONFIG_FILE = path.join(MASONRY_DIR, "config.json");

const CLAUDE_DIR = path.join(os.homedir(), ".claude");
const SETTINGS_FILE = path.join(CLAUDE_DIR, "settings.json");
const PLUGINS_DIR = path.join(CLAUDE_DIR, "plugins");
const INSTALLED_FILE = path.join(PLUGINS_DIR, "installed_plugins.json");

// Plugin identity — matches enabledPlugins key format: {pluginName}@{marketplace}
const MARKETPLACE = "masonry";
const PLUGIN_NAME = "masonry";
const PLUGIN_VERSION = require("../package.json").version;
const PLUGIN_KEY = `${PLUGIN_NAME}@${MARKETPLACE}`;

// Where Claude Code expects to find the plugin files
const CACHE_PATH = path.join(
  PLUGINS_DIR,
  "cache",
  MARKETPLACE,
  PLUGIN_NAME,
  PLUGIN_VERSION,
);

// StatusLine script
const STATUSLINE_SCRIPT = path
  .join(MASONRY_ROOT, "src", "hooks", "masonry-statusline.js")
  .replace(/\\/g, "/");

// ---------------------------------------------------------------------------
// ANSI helpers
// ---------------------------------------------------------------------------
const CLR = {
  purple: "\x1b[38;2;139;92;246m",
  cyan: "\x1b[38;2;34;211;238m",
  green: "\x1b[38;2;52;211;153m",
  amber: "\x1b[38;2;245;158;11m",
  red: "\x1b[38;2;239;68;68m",
  dim: "\x1b[2m",
  bold: "\x1b[1m",
  reset: "\x1b[0m",
};
const c = (col, t) => `${CLR[col]}${t}${CLR.reset}`;
const dim = (t) => `${CLR.dim}${t}${CLR.reset}`;
const bold = (t) => `${CLR.bold}${t}${CLR.reset}`;

function log(msg) {
  process.stdout.write(`  ${msg}\n`);
}
function ok(msg) {
  log(`${c("green", "✓")} ${msg}`);
}
function warn(msg) {
  log(`${c("amber", "⚠")} ${msg}`);
}
function err(msg) {
  log(`${c("red", "✗")} ${msg}`);
}
function info(msg) {
  log(`${dim("·")} ${msg}`);
}
function hdr(msg) {
  process.stdout.write(`\n${c("purple", "🧱")}  ${bold(msg)}\n`);
}

// ---------------------------------------------------------------------------
// Arg parsing
// ---------------------------------------------------------------------------
function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--recall-url" && argv[i + 1]) {
      args.recallUrl = argv[++i];
    }
    if (argv[i] === "--api-key" && argv[i + 1]) {
      args.apiKey = argv[++i];
    }
    if (argv[i] === "--ollama-url" && argv[i + 1]) {
      args.ollamaUrl = argv[++i];
    }
    if (argv[i] === "--ollama-model" && argv[i + 1]) {
      args.ollamaModel = argv[++i];
    }
    if (argv[i] === "--dry-run") {
      args.dryRun = true;
    }
    if (argv[i] === "--uninstall") {
      args.uninstall = true;
    }
  }
  return args;
}

// ---------------------------------------------------------------------------
// Readline
// ---------------------------------------------------------------------------
function ask(rl, question) {
  return new Promise((resolve) =>
    rl.question(question, (ans) => resolve(ans.trim())),
  );
}

// ---------------------------------------------------------------------------
// JSON helpers
// ---------------------------------------------------------------------------
function readJson(file, fallback = {}) {
  try {
    if (fs.existsSync(file)) return JSON.parse(fs.readFileSync(file, "utf8"));
  } catch (_e) {}
  return fallback;
}

function writeJson(file, data, dryRun = false) {
  if (dryRun) {
    info(`[dry-run] would write ${path.basename(file)}`);
    return;
  }
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(data, null, 2) + "\n", "utf8");
}

// ---------------------------------------------------------------------------
// Step 2: Install into Claude Code plugin cache via directory junction
// A junction makes CACHE_PATH point to MASONRY_ROOT so Claude Code can find
// .claude-plugin/plugin.json and hooks/hooks.json at the expected cache path.
// ---------------------------------------------------------------------------
function installPluginCache(dryRun) {
  if (dryRun) {
    info(`[dry-run] would create junction: ${CACHE_PATH} → ${MASONRY_ROOT}`);
    return true;
  }

  // Remove existing cache entry if it exists
  try {
    if (fs.existsSync(CACHE_PATH)) {
      fs.rmSync(CACHE_PATH, { recursive: true, force: true });
    }
  } catch (_e) {}

  // Ensure parent directory exists
  fs.mkdirSync(path.dirname(CACHE_PATH), { recursive: true });

  try {
    // Use junction type on Windows — works without admin, unlike symlinks
    fs.symlinkSync(MASONRY_ROOT, CACHE_PATH, "junction");
    return true;
  } catch (e) {
    warn(`Could not create junction (${e.message}) — falling back to copy`);
    // Fallback: copy key files
    try {
      fs.mkdirSync(CACHE_PATH, { recursive: true });
      copyDir(MASONRY_ROOT, CACHE_PATH, [
        ".claude-plugin",
        "hooks",
        "skills",
        "src",
        "package.json",
      ]);
      return true;
    } catch (e2) {
      err(`Plugin cache install failed: ${e2.message}`);
      return false;
    }
  }
}

function copyDir(src, dest, items) {
  for (const item of items) {
    const srcPath = path.join(src, item);
    const destPath = path.join(dest, item);
    if (!fs.existsSync(srcPath)) continue;
    const stat = fs.statSync(srcPath);
    if (stat.isDirectory()) {
      fs.mkdirSync(destPath, { recursive: true });
      for (const child of fs.readdirSync(srcPath)) {
        copyDir(srcPath, destPath, [child]);
      }
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

// ---------------------------------------------------------------------------
// Step 3: Register in installed_plugins.json
// ---------------------------------------------------------------------------
function registerPlugin(dryRun) {
  const installed = readJson(INSTALLED_FILE, { version: 2, plugins: {} });
  if (!installed.plugins) installed.plugins = {};

  installed.plugins[PLUGIN_KEY] = [
    {
      scope: "user",
      installPath: CACHE_PATH,
      version: PLUGIN_VERSION,
      installedAt: new Date().toISOString(),
      lastUpdated: new Date().toISOString(),
    },
  ];

  writeJson(INSTALLED_FILE, installed, dryRun);
}

// ---------------------------------------------------------------------------
// Step 4+5: Update settings.json
// ---------------------------------------------------------------------------
function updateSettings(dryRun) {
  const settings = readJson(SETTINGS_FILE, {});

  // enabledPlugins
  if (!settings.enabledPlugins) settings.enabledPlugins = {};
  settings.enabledPlugins[PLUGIN_KEY] = true;

  // statusLine — point directly at source (not cache path) so it stays live
  settings.statusLine = {
    type: "command",
    command: `node ${STATUSLINE_SCRIPT}`,
    padding: 1,
  };

  // Remove any manually-injected masonry hooks from previous install attempts
  // (hooks are now handled by the plugin system via hooks/hooks.json)
  const masonryFwd = MASONRY_ROOT.replace(/\\/g, "/");
  for (const event of Object.keys(settings.hooks || {})) {
    settings.hooks[event] = (settings.hooks[event] || []).filter(
      (entry) => !entry?.hooks?.some((h) => h?.command?.includes(masonryFwd)),
    );
    // Remove empty event arrays
    if (settings.hooks[event].length === 0) delete settings.hooks[event];
  }

  writeJson(SETTINGS_FILE, settings, dryRun);
}

// ---------------------------------------------------------------------------
// Uninstall
// ---------------------------------------------------------------------------
function uninstall(dryRun) {
  // Remove cache junction/copy
  if (!dryRun) {
    try {
      if (fs.existsSync(CACHE_PATH)) {
        fs.rmSync(CACHE_PATH, { recursive: true, force: true });
        ok(`Removed plugin cache: ${CACHE_PATH}`);
      }
    } catch (e) {
      warn(`Could not remove cache: ${e.message}`);
    }
  }

  // Remove from installed_plugins.json
  const installed = readJson(INSTALLED_FILE, { version: 2, plugins: {} });
  if (installed.plugins?.[PLUGIN_KEY]) {
    delete installed.plugins[PLUGIN_KEY];
    writeJson(INSTALLED_FILE, installed, dryRun);
    ok("Removed from installed_plugins.json");
  }

  // Remove from settings.json
  const settings = readJson(SETTINGS_FILE, {});
  if (settings.enabledPlugins?.[PLUGIN_KEY]) {
    delete settings.enabledPlugins[PLUGIN_KEY];
  }
  const cmd = settings.statusLine?.command || "";
  if (cmd.includes("masonry-statusline")) delete settings.statusLine;
  // Remove any residual hook entries
  const masonryFwd = MASONRY_ROOT.replace(/\\/g, "/");
  for (const event of Object.keys(settings.hooks || {})) {
    settings.hooks[event] = (settings.hooks[event] || []).filter(
      (entry) => !entry?.hooks?.some((h) => h?.command?.includes(masonryFwd)),
    );
    if (settings.hooks[event].length === 0) delete settings.hooks[event];
  }
  writeJson(SETTINGS_FILE, settings, dryRun);
  ok("Removed from settings.json");
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
async function main() {
  const cliArgs = parseArgs(process.argv.slice(2));

  hdr("masonry setup");
  process.stdout.write("\n");

  // --- Uninstall ---
  if (cliArgs.uninstall) {
    hdr("uninstalling masonry");
    uninstall(cliArgs.dryRun);
    info("~/.masonry/config.json preserved (delete manually if desired)");
    process.stdout.write("\n");
    return;
  }

  // --- Interactive prompts ---
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });
  const existingCfg = readJson(CONFIG_FILE, {});

  const recallUrlDefault =
    existingCfg.recallHost || "http://100.70.195.84:8200";
  const ollamaUrlDefault =
    existingCfg.ollamaHost || "http://192.168.50.62:11434";
  const ollamaModelDefault = existingCfg.ollamaModel || "qwen3:14b";
  const apiKeyDefault =
    process.env.RECALL_API_KEY || existingCfg.recallApiKey || "";

  let recallUrl, apiKey, ollamaUrl, ollamaModel;
  const allProvided = cliArgs.recallUrl && cliArgs.apiKey;

  if (allProvided) {
    recallUrl = cliArgs.recallUrl;
    apiKey = cliArgs.apiKey;
    ollamaUrl = cliArgs.ollamaUrl || ollamaUrlDefault;
    ollamaModel = cliArgs.ollamaModel || ollamaModelDefault;
  } else {
    info(`Masonry root:  ${dim(MASONRY_ROOT)}`);
    info(`Plugin cache:  ${dim(CACHE_PATH)}`);
    info(`Settings:      ${dim(SETTINGS_FILE)}`);
    process.stdout.write("\n");

    process.stdout.write(c("cyan", "  Recall\n"));
    recallUrl =
      cliArgs.recallUrl ||
      (await ask(rl, `  URL [${recallUrlDefault}]: `)) ||
      recallUrlDefault;
    const apiKeyDisplay = apiKeyDefault
      ? `${apiKeyDefault.slice(0, 4)}…`
      : "(empty)";
    apiKey =
      cliArgs.apiKey ||
      (await ask(rl, `  API key [${apiKeyDisplay}]: `)) ||
      apiKeyDefault;

    process.stdout.write("\n");
    process.stdout.write(c("cyan", "  Ollama\n"));
    ollamaUrl =
      cliArgs.ollamaUrl ||
      (await ask(rl, `  URL [${ollamaUrlDefault}]: `)) ||
      ollamaUrlDefault;
    ollamaModel =
      cliArgs.ollamaModel ||
      (await ask(rl, `  Model [${ollamaModelDefault}]: `)) ||
      ollamaModelDefault;
  }

  rl.close();
  process.stdout.write("\n");

  // --- Step 1: Config ---
  hdr("step 1 · config");
  const newCfg = {
    recallHost: recallUrl,
    recallApiKey: apiKey,
    ollamaHost: ollamaUrl,
    ollamaModel: ollamaModel,
    handoffThreshold: existingCfg.handoffThreshold ?? 70,
  };
  writeJson(CONFIG_FILE, newCfg, cliArgs.dryRun);
  ok(`Wrote ~/.masonry/config.json`);
  info(`  recall: ${recallUrl}  ollama: ${ollamaUrl} (${ollamaModel})`);

  // --- Step 2: Plugin cache ---
  hdr("step 2 · plugin cache (junction)");
  info(`${CACHE_PATH}`);
  info(`  → ${MASONRY_ROOT}`);
  const cached = installPluginCache(cliArgs.dryRun);
  if (cached) ok("Plugin cache created");

  // --- Step 3: installed_plugins.json ---
  hdr("step 3 · plugin registry");
  registerPlugin(cliArgs.dryRun);
  ok(`Registered ${PLUGIN_KEY} in installed_plugins.json`);

  // --- Step 4+5: settings.json ---
  hdr("step 4 · settings.json");
  updateSettings(cliArgs.dryRun);
  ok(`enabledPlugins: ${PLUGIN_KEY} = true`);
  ok(`statusLine: node ${STATUSLINE_SCRIPT}`);
  ok("Cleaned residual hook entries from previous installs");

  // --- Step 5: Recall connectivity ---
  hdr("step 5 · connectivity check");
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 3000);
    const headers = apiKey ? { Authorization: `Bearer ${apiKey}` } : {};
    const res = await fetch(`${recallUrl}/health`, {
      signal: controller.signal,
      headers,
    });
    clearTimeout(timer);
    if (res.ok) {
      ok(`Recall reachable at ${recallUrl}`);
    } else {
      warn(`Recall responded ${res.status}`);
    }
  } catch (_e) {
    warn(`Recall not reachable — hooks will degrade gracefully`);
  }

  // --- Done ---
  process.stdout.write("\n");
  hdr("done");
  process.stdout.write("\n");
  ok("Masonry installed. Restart Claude Code to activate.\n");
  process.stdout.write(
    `  ${dim("Start a campaign:")}  ${c("cyan", "cd")} your-project && ${c("cyan", "/masonry-run")}\n` +
      `  ${dim("Uninstall:")}         ${c("cyan", "node")} ${MASONRY_ROOT.replace(/\\/g, "/")}/bin/masonry-setup.js ${dim("--uninstall")}\n\n`,
  );
}

main().catch((e) => {
  err(`Setup failed: ${e.message}`);
  process.exit(1);
});
