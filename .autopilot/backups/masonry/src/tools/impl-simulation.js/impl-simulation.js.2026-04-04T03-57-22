'use strict';

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { callPython, httpRequest } = require('./impl-utils');
const { loadConfig } = require('./config');
const { GIT_DIFF_PATTERNS } = require('./impl-campaign');

function toolNlGenerate(args) {
  const { description, project_path, append = false } = args;
  if (!description) return { error: 'description is required' };

  if (append && project_path) {
    return callPython(`
from bl.nl_entry import quick_campaign
result = quick_campaign(args["description"], project_dir=args.get("project_path", "."))
print(json.dumps(result))  # noqa: mcp-stdout
`, args);
  }

  return callPython(`
from bl.nl_entry import generate_from_description, format_preview
qs = generate_from_description(args["description"])
print(json.dumps({"questions": qs, "preview": format_preview(qs), "count": len(qs)}))  # noqa: mcp-stdout
`, args);
}

function toolGitHypothesis(args) {
  const { project_path, commits = 5, max_questions = 10, dry_run = true } = args;

  let diff = '';
  try {
    diff = execSync(`git diff HEAD~${commits} HEAD --name-only`, {
      cwd: project_path, encoding: 'utf8', timeout: 5000,
    });
  } catch (_) {
    return { error: 'git diff failed — is this a git repository?', questions: [] };
  }

  const files = diff.trim().split('\n').filter(Boolean);
  if (!files.length) {
    return { questions: [], count: 0, message: 'No changed files in the last ' + commits + ' commits.' };
  }

  const questions = [];
  const seen = new Set();
  for (const file of files) {
    for (const pat of GIT_DIFF_PATTERNS) {
      if (pat.pattern.test(file)) {
        const key = `${pat.name}:${file}`;
        if (seen.has(key)) continue;
        seen.add(key);
        const text = pat.template.replace('{file}', file).replace('{pattern}', pat.name);
        const id = `GIT-${pat.name.slice(0, 4).toUpperCase()}-${questions.length + 1}`;
        questions.push({ id, text, domain: pat.domain, mode: pat.mode, source: 'git-hypothesis', file });
        if (questions.length >= max_questions) break;
      }
    }
    if (questions.length >= max_questions) break;
  }

  if (!dry_run && questions.length > 0) {
    const questionsFile = path.join(project_path, 'questions.md');
    if (fs.existsSync(questionsFile)) {
      const timestamp = new Date().toISOString().split('T')[0];
      let append = `\n## Wave GIT — ${timestamp} (git-hypothesis)\n\n`;
      for (const q of questions) {
        append += `### ${q.id} — ${q.text}\n\n**Status:** PENDING\n**Mode:** ${q.mode}\n**Domain:** ${q.domain}\n**Source:** git-hypothesis (${q.file})\n\n`;
      }
      fs.appendFileSync(questionsFile, append, 'utf8');
      return { questions, count: questions.length, appended: true, files_analyzed: files };
    }
  }

  return {
    questions, count: questions.length, dry_run, files_analyzed: files,
    patterns_matched: [...new Set(questions.map(q => q.id.split('-')[1]))],
  };
}

function toolRunSimulation(args) {
  const code = `
from pathlib import Path
import importlib.util, sys, io, json

project_path = Path(args["project_path"])
simulate_path = project_path / "simulate.py"

real_stdout = sys.stdout
fake_buf = io.BytesIO()
sys.stdout = io.TextIOWrapper(fake_buf, encoding="utf-8")
try:
    spec = importlib.util.spec_from_file_location("simulate_mcp", simulate_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
finally:
    sys.stdout = real_stdout

kwargs = {k: v for k, v in args.items() if k != "project_path"}
for k, v in kwargs.items():
    if hasattr(mod, k):
        setattr(mod, k, v)
records, failure_reason = mod.run_simulation()
result = mod.evaluate(records, failure_reason)
result["records"] = records
print(json.dumps(result))  # noqa: mcp-stdout
`;
  return callPython(code, args);
}

function toolSweep(args) {
  const { REPO_ROOT } = require('./impl-utils');
  const code = `
from pathlib import Path
import sys, json
sys.path.insert(0, ${JSON.stringify(REPO_ROOT)})
from bl.sweep import sweep

results = sweep(
    project_dir=Path(args["project_path"]),
    param_name=args["param_name"],
    values=args["values"],
    scenarios=args.get("scenarios"),
    base_params=args.get("base_params"),
)
print(json.dumps({"results": results, "count": len(results)}))  # noqa: mcp-stdout
`;
  return callPython(code, args);
}

function toolRunQuestion(args) {
  const { question_id } = args;
  if (!question_id) return { error: 'question_id is required' };

  return callPython(`
import os
os.chdir(args.get("project_path", "."))
from bl.questions import load_questions
from bl.runners import run_question, _register_builtins
_register_builtins()
qs = load_questions("questions.md")
q = next((q for q in qs if q.get("id") == args["question_id"]), None)
if q is None:
    print(json.dumps({"error": f"Question {args['question_id']!r} not found"}))  # noqa: mcp-stdout
    sys.exit(0)
result = run_question(q)
print(json.dumps({"question_id": args["question_id"], "result": result}))  # noqa: mcp-stdout
`, args);
}

async function toolRecall(args) {
  const { query, project, limit = 10 } = args;
  const cfg = loadConfig();
  const domain = `${project}-bricklayer`;
  const payload = JSON.stringify({ query, domain, limit });

  try {
    const resp = await Promise.race([
      httpRequest(`${cfg.recallHost}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(payload),
          ...(cfg.recallApiKey ? { Authorization: `Bearer ${cfg.recallApiKey}` } : {}),
        },
      }, payload),
      new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 5000)),
    ]);
    if (resp.status >= 400) return { error: 'recall_error', message: `Recall returned HTTP ${resp.status}` };
    const data = resp.body;
    return Array.isArray(data) ? data : data.results || data;
  } catch (err) {
    return { error: 'recall_unavailable', message: err.message || 'Could not reach Recall' };
  }
}

function toolRoute(args) {
  const { REPO_ROOT } = require('./impl-utils');
  return callPython(`
import sys, json
sys.path.insert(0, ${JSON.stringify(REPO_ROOT)})
try:
    from masonry.src.routing.router import route_request
    result = route_request(args["request"], project_path=args.get("project_path"))
    print(json.dumps(result))  # noqa: mcp-stdout
except Exception as e:
    print(json.dumps({"error": str(e), "target_agent": "user", "layer": "fallback", "confidence": 0, "reason": "Router unavailable"}))  # noqa: mcp-stdout
`, args);
}

module.exports = { toolNlGenerate, toolGitHypothesis, toolRunSimulation, toolSweep, toolRunQuestion, toolRecall, toolRoute };
