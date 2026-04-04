# Security Audit — BrickLayer 2.0
**Date:** 2026-04-04
**Auditor:** Claude (automated scan)
**Scope:** Full repository — Python (bl/, masonry/src/), JavaScript (masonry/src/hooks/, masonry/bin/), shell scripts, GitHub Actions workflows, configuration files. Excludes `projects/` vendored code except where directly relevant.

---

## Executive Summary

The BrickLayer 2.0 codebase is well-structured with good defensive defaults in new code (the masonry Phase 1-2 work added `fcntl` locking, input sanitization, and safe YAML loading). The critical risk is a committed `.env` file in `projects/passive-frontend-v2/` containing live third-party API credentials. The core BL engine has intentional `shell=True` usage in two runners that is an accepted design trade-off, but needs to be clearly scoped. No secrets were found in the main codebase beyond the `.env` issue and one explicit placeholder. CI/CD pipelines are clean.

---

## Critical Findings

### C1 — `.env` with live credentials committed to git
**File:** `projects/passive-frontend-v2/.env`
**CVSS:** 9.1 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N)

The file is tracked in git (`git ls-files` confirms) and contains:

| Credential | Value (truncated) | Risk |
|---|---|---|
| `VITE_SUPABASE_ANON_KEY` | JWT `eyJhbGc...` | Public-facing anon key — lower risk but rotatable |
| `ENCRYPTION_KEY` | Base64 AES-256 `yhZAGV...` | **High** — symmetric key for backup encryption |
| `PLAID_SECRET` | `12685c082c...` | **High** — Plaid sandbox but real credential |
| `DWOLLA_SECRET` | `JABD9eJO...` | **High** — Dwolla OAuth secret |
| `DWOLLA_WEBHOOK_SECRET` | `a8fua4nn...` | Webhook validation |
| `SIGNALWIRE_TOKEN` | `PTa7aba9d...` | **High** — telephony API token |

The `projects/passive-frontend-v2/.gitignore` does **not** exclude `.env`. The file has been committed and is in git history.

**Remediation (immediate):**
1. Rotate all credentials above — assume they are compromised since this is a git repo
2. Add `.env` to `projects/passive-frontend-v2/.gitignore`
3. Remove from git history: `git filter-repo --path projects/passive-frontend-v2/.env --invert-paths` (requires `git filter-repo` and a force-push; coordinate with all collaborators)
4. Add `.env` to the root `.gitignore` to prevent recurrence across all projects

---

## High Findings

### H1 — `shell=True` with campaign-controlled command in `subprocess_runner.py`
**File:** `bl/runners/subprocess_runner.py:123-125`
**CVSS:** 7.8 (AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H)

```python
result = subprocess.run(
    command,   # string assembled from question's "Test" field
    shell=True,
    cwd=str(cfg.autosearch_root),
)
```

The `command` string is parsed from the `Test:` field of a research question (read from `questions.md`). Any user or agent that can write to `questions.md` can inject arbitrary shell commands. This is intentional by design — the subprocess runner is explicitly a "run whatever command is in the question" mechanism — but it means the trust boundary is the question file, not the runner itself.

**Context:** The `cwd` is constrained to `cfg.autosearch_root`, which limits filesystem scope. The runner is not exposed over a network.

**Remediation:**
- Document the trust model explicitly: "questions.md is a trusted config file; arbitrary shell execution is intentional"
- Consider an allowlist of command prefixes (e.g., `python`, `pytest`, `git`) for the subprocess runner
- Add a `--sandbox` flag that wraps commands in `firejail` or `bubblewrap` for untrusted campaigns

---

### H2 — `shell=True` in `correctness.py` with string interpolation
**File:** `bl/runners/correctness.py:41-43, 64-66`
**CVSS:** 7.4 (AV:L/AC:H/PR:L/UI:N/S:U/C:H/I:H/A:H)

```python
pytest_cmd = f"pytest {paths} -v --tb=short -q{k_filter}"
cmd = f"python -m {pytest_cmd}"
result = subprocess.run(cmd, shell=True, ...)
```

`paths` is derived from the question content (via `_find_test_paths`). A path string containing shell metacharacters (e.g., `; rm -rf ~`) would execute as shell code. The `k_filter` is derived from a regex match on the question text, same risk.

**Remediation:** Replace `shell=True` + string with a list: `["python", "-m", "pytest"] + shlex.split(paths) + [...]`

---

### H3 — `rotate_supabase_backup_key.py` uses `shell=True` with `gh` CLI
**File:** `projects/passive-frontend-v2/scripts/rotate_supabase_backup_key.py:33`
**CVSS:** 7.0 (AV:L/AC:H/PR:H/UI:N/S:U/C:H/I:H/A:N)

```python
def run(cmd):
    return subprocess.check_output(cmd, shell=True, text=True).strip()
```

Called with strings like `run(f"gh secret set {key_name} --body {value} -R {repo}")`. If `key_name`, `value`, or `repo` ever contain shell metacharacters, injection is possible. This script runs in GitHub Actions with `GH_TOKEN` in scope.

**Remediation:** Use list form: `subprocess.check_output(["gh", "secret", "set", key_name, "--body", value, "-R", repo])`

---

## Medium Findings

### M1 — `bl/config.py` placeholder API key in source
**File:** `bl/config.py:31`
**CVSS:** 4.3 (AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:N/A:N)

```python
api_key="recall-admin-key-change-me",  # noqa: S105 — placeholder, overridden by project.json
```

The placeholder is intentional and overridden at runtime from `project.json`. Risk is low since it's a well-documented placeholder with a `noqa` annotation. However, if `project.json` is missing or fails to load, the default key is sent to the Recall API.

**Remediation:** Fail loudly if `project.json` is missing rather than falling back to the placeholder: `raise ValueError("api_key not configured — set in project.json")`.

---

### M2 — `masonry_build_guard.js` execSync with interpolated tag name
**File:** `masonry/src/hooks/masonry-build-guard.js:123`
**CVSS:** 4.5 (AV:L/AC:H/PR:L/UI:N/S:U/C:L/I:L/A:N)

```javascript
execSync(`git tag "${tagName}" -m "BrickLayer phase checkpoint: ${task.phase_end}"`, {
```

`tagName` is derived from task data. If a task's `phase_end` field contained a double-quote or shell metacharacter, this could break the command. Low likelihood since task data is internal.

**Remediation:** Use `spawnSync(["git", "tag", tagName, "-m", msg])` instead of `execSync` with a template string.

---

### M3 — No timeout on `httpx` calls in `bl/tracer.py`
**File:** `bl/tracer.py:62`
**CVSS:** 4.0 (AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:L)

```python
httpx.post(f"{RECALL_BASE}/memories", json=payload, timeout=RECALL_TIMEOUT)
```

`RECALL_TIMEOUT` is defined — this is fine. However, `bl/followup.py:148`, `bl/hypothesis.py:138`, and `bl/goal.py:210` make `httpx.post` calls where the timeout should be verified.

**Remediation:** Audit all `httpx` calls to confirm `timeout=` is always set. Consider a shared `httpx.Client` with a default timeout at the module level.

---

### M4 — SSRF potential in `bl/runners/performance.py`
**File:** `bl/runners/performance.py` (multiple lines)
**CVSS:** 4.0 (AV:N/AC:H/PR:L/UI:N/S:U/C:L/I:L/A:N)

The performance runner makes HTTP calls to configurable endpoints read from question data or config. If the Recall/Ollama base URL is user-controllable, SSRF to internal services is possible.

**Remediation:** Validate that URL schemes are `http`/`https` and optionally allowlist target hostnames.

---

## Low / Informational

### L1 — `masonry/src/routing/llm_router.py` — prompt injection mitigation is partial
The `_sanitize()` function (added in this PR) collapses whitespace and truncates to 500 chars. This reduces but does not eliminate prompt injection — a 500-char payload is sufficient for many injection attacks. The hallucination guard (validate target in registry) provides a second layer.

**Recommendation:** Consider wrapping the user request in a clearly delimited block: `[USER REQUEST START]\n{request_text}\n[USER REQUEST END]` to make instruction boundaries explicit to the LLM.

### L2 — `masonry/src/training/collector.py` — `COLD_START = 0.688` magic constant
Not a security issue but a correctness concern. The value 0.688 is hardcoded with no comment explaining its origin. If this is a historical baseline accuracy, document it.

### L3 — GitHub Actions uses `GITHUB_TOKEN` with `contents: write` + `pull-requests: write`
**File:** `.github/workflows/release-please.yml`
The release-please workflow requests broad write permissions. This is standard for release-please but worth noting — if the workflow is ever compromised, it can write to the repo and create PRs.

### L4 — `masonry/scripts/archive/` excluded from ruff but not reviewed
The archive scripts are excluded from linting. They may contain older patterns (hardcoded paths, shell injection) that are not caught. These are not production code but could be a source of confusion.

---

## Dependency Audit

### Python

```
masonry/pyproject.toml: dspy-ai, numpy, pyyaml, pytest
```

No `requirements.txt` at root — dependencies are ad-hoc installed in CI. This means no lock file and no reproducible builds.

**Recommendation:** Add `uv.lock` or `requirements.txt` with pinned versions. Run `pip-audit` or `safety check` in CI.

### JavaScript

`masonry/package.json` dependencies are present. The CI runs `npm ci` which uses the lockfile — good.

**Recommendation:** Add `npm audit` step to `node-ci.yml`.

---

## CI/CD Pipeline Review

| Check | Status |
|---|---|
| Secrets in workflow files | ✅ Only `GITHUB_TOKEN` via `secrets.*` — no hardcoded secrets |
| Action versions pinned | ✅ Updated to v6 (node22) in this PR |
| `pull_request` trigger scoped to base branches | ✅ Only `master`/`main` |
| Python test matrix | ✅ 3.11 and 3.12 |
| Node test matrix | ✅ 20.x and 22.x |
| Dependency install uses pip directly (not uv) | ⚠️ CI uses `pip install` — project standard is `uv`. Low risk but inconsistent |
| No `pip install --trusted-host` or insecure index | ✅ Clean |
| `release-please` has `contents: write` | ℹ️ Expected, document intentionally |

---

## Recommendations (Priority Order)

1. **Rotate all credentials in `projects/passive-frontend-v2/.env` immediately** — treat as compromised
2. **Add `.env` to `.gitignore`** at root and in `projects/passive-frontend-v2/`
3. **Remove `.env` from git history** using `git filter-repo`
4. **Fix `correctness.py` `shell=True`** — convert to list-form subprocess call (H2)
5. **Fix `rotate_supabase_backup_key.py` `shell=True`** — convert to list-form (H3)
6. **Add `npm audit` to `node-ci.yml`** and `pip-audit` to `python-ci.yml`
7. **Add a lock file** (`uv.lock` or pinned `requirements.txt`) for reproducible Python builds
8. **Fail loudly on missing `project.json`** rather than falling back to placeholder API key (M1)
9. **Document subprocess runner trust model** — the `shell=True` in `subprocess_runner.py` is intentional; make that explicit in code comments (H1)
10. **Consider delimiter-wrapped prompts** in `llm_router.py` for stronger injection resistance (L1)
