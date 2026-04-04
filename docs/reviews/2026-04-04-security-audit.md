# Security Audit — BrickLayer 2.0 + Masonry
**Date:** 2026-04-04
**Auditor:** Claude (automated scan + manual review)
**Scope:** `bl/` and `masonry/` only. `projects/` excluded per owner request.

---

## Executive Summary

The BrickLayer/Masonry codebase is in good shape. No hardcoded secrets were found. All `httpx` calls have explicit timeouts. The `spawn()` calls in masonry hooks use array form (not shell strings) and are safe. The three real findings are: intentional-but-undocumented `shell=True` in the subprocess/correctness runners (design decision that needs a trust boundary comment), hardcoded Tailscale IP fallbacks scattered across ~15 files (leaks internal topology in a public repo), and one `execSync` with interpolated data in the build guard. Everything else scanned clean.

---

## Findings

### M1 — `correctness.py`: `shell=True` with regex-extracted paths
**File:** `bl/runners/correctness.py:41-43, 64-66`
**Severity:** Medium
**Exploitable by:** Anyone who can write to `questions.md`

```python
pytest_cmd = f"pytest {paths} -v --tb=short -q{k_filter}"
cmd = f"python -m {pytest_cmd}"
result = subprocess.run(cmd, shell=True, ...)
```

`paths` is extracted from the question's `test` field via regex. The pattern `[^\s\`]` blocks whitespace and backticks but not semicolons, `&&`, `||`, or `$()`. A question with `Test: pytest tests/foo.py;malicious_cmd` would execute both commands. The `k_filter` is safe — its regex stops at `"`.

`subprocess_runner.py` has the same pattern but is explicitly designed to run arbitrary commands from the Test field — that one is intentional.

**Fix:**
```python
import shlex
cmd_parts = ["python", "-m", "pytest"] + shlex.split(paths) + ["-v", "--tb=short", "-q"]
if k_filter:
    cmd_parts += ["-k", k_match.group(1)]
result = subprocess.run(cmd_parts, capture_output=True, text=True, timeout=300, cwd=...)
```

---

### M2 — Hardcoded Tailscale IP in ~15 files
**Files:** `masonry/src/hooks/masonry-prompt-inject.js`, `masonry/src/hooks/session/context-data.js`, `masonry/src/core/config.js`, `masonry/src/reasoning/graph.py`, `masonry/src/reasoning/pagerank.py`, and ~10 others
**Severity:** Medium (information disclosure in a public repo)

```javascript
const RECALL_HOST = process.env.RECALL_HOST || 'http://100.70.195.84:8200';
```

`100.70.195.84` is the internal Tailscale IP for the Recall VM. Having it hardcoded in a public repo leaks internal network topology and makes rotating the endpoint require touching 15+ files.

**Fix:** Centralise in `masonry/src/core/config.js` (already the canonical config) and change the default to `localhost`. All hook files should import from config rather than re-declaring the fallback:

```javascript
// masonry/src/core/config.js — single source of truth
recallHost: process.env.RECALL_HOST || 'http://localhost:8200',
ollamaHost: process.env.OLLAMA_HOST || 'http://localhost:11434',
```

---

### L1 — `masonry-build-guard.js`: `execSync` with interpolated tag name
**File:** `masonry/src/hooks/masonry-build-guard.js:123`
**Severity:** Low
**Exploitable by:** Malformed content in `progress.json`'s `phase_end` field

```javascript
execSync(`git tag "${tagName}" -m "BrickLayer phase checkpoint: ${task.phase_end}"`, {
```

A `phase_end` value containing `"` could break out of the shell argument. In practice `progress.json` is written by the build system, so real-world risk is low.

**Fix:**
```javascript
const { spawnSync } = require('child_process');
spawnSync('git', ['tag', tagName, '-m', `BrickLayer phase checkpoint: ${task.phase_end}`], {
  cwd: sessionCwd, stdio: 'pipe'
});
```

---

### L2 — `subprocess_runner.py`: `shell=True` undocumented trust model
**File:** `bl/runners/subprocess_runner.py:123-125`
**Severity:** Low / informational

The subprocess runner intentionally executes arbitrary shell commands from the `Test:` field of research questions. This is correct by design. The trust boundary is `questions.md`. It should be explicitly documented so future contributors don't expose it to untrusted sources:

```python
# SECURITY: shell=True is intentional. This runner treats questions.md as
# a trusted config file. Never call run_subprocess() with untrusted question data.
result = subprocess.run(command, shell=True, ...)
```

---

### L3 — `masonry/src/routing/semantic.py`: hardcoded Ollama IP
**File:** `masonry/src/routing/semantic.py:31`
**Severity:** Low (same class as M2)

```python
or "http://100.70.195.84:11434"
```

**Fix:** `os.environ.get("OLLAMA_HOST", "http://localhost:11434")`

---

## What Scanned Clean

| Area | Result |
|---|---|
| Hardcoded secrets / API keys in `bl/` or `masonry/` | ✅ None found |
| `bl/config.py` placeholder key | ✅ Documented `noqa: S105`, overridden at runtime |
| `yaml.load` unsafe deserialization | ✅ No occurrences — all safe_load |
| `pickle.load` on untrusted data | ✅ No occurrences |
| `eval()` / `exec()` in production code | ✅ No occurrences |
| `httpx` calls missing timeouts | ✅ All use explicit `_TIMEOUT` (30–120s) |
| masonry `spawn()` injection | ✅ All hooks use array form — no shell string interpolation |
| CI/CD secrets exposure | ✅ Only `secrets.GITHUB_TOKEN` via Actions context |
| Path traversal | ✅ File paths from trusted config only |
| SQL/NoSQL injection | ✅ No direct DB queries in scope |

---

## Recommendations (Priority Order)

1. **Fix `correctness.py`** — swap `shell=True` + f-string for `shlex.split` list form (M1)
2. **Centralise Recall/Ollama host** — remove ~15 hardcoded `100.70.195.84` fallbacks, import from `masonry/src/core/config.js`, default to `localhost` (M2)
3. **Fix `masonry-build-guard.js`** — `execSync` → `spawnSync` array form (L1)
4. **Document `subprocess_runner.py` trust model** — add security comment (L2)
5. **Fix `semantic.py` Ollama URL** — use env var with localhost fallback (L3)
