# Spec: Fix qwen3:14b LLM Timeout Instability in Recall

## Overview
Recall's LLM pipeline (qwen3:14b via Ollama) is timing out at 74% — 71 of 96 recent calls timed out.
This degrades the observer, signal detector, and consolidation pipeline, causing partial/stub memories and fail-open writes.
The fix requires: diagnosing root cause (GPU memory, concurrency, timeout config), then implementing targeted remediations.

## Source Location
- Local source: `/mnt/c/Users/trg16/Dev/Recall/src`
- jcodemunch repo: `local/src-3944fe64`
- VM: `sshpass -p 'lacetimcat1216' ssh nerfherder@100.70.195.84`
- Deploy: scp file to VM /tmp, sudo cp to /opt/recall/app/src/<path>, then sudo docker compose restart worker api

## Tasks

### T1: Diagnose — Ollama GPU/memory and timeout config [INDEPENDENT]
- SSH into VM, check Ollama logs for model load/unload events, OOM errors, queue depth
- Check GPU memory: nvidia-smi or docker stats
- Check current LLM timeout value in src/core/config.py and src/core/llm.py
- Check keepalive worker is actually running: look for ollama_keepalive_sent in worker logs
- Check Ollama concurrency: how many simultaneous requests does it handle?
- Output: root cause diagnosis

### T2: Diagnose — LLM call concurrency in the application [INDEPENDENT]
- Use jcodemunch to trace all call sites of get_llm() in the codebase
- Map which workers/routes call LLM and whether they are serialized or concurrent
- Check if ARQ worker concurrency allows N workers to each make LLM calls simultaneously
- Output: concurrency map — max simultaneous LLM calls possible under normal load

### T3: Fix — LLM timeout and retry config [BLOCKED BY T1]
- Raise LLM timeout if current value is too short for qwen3:14b (14B models need 15-45s)
- Add exponential backoff retry (2-3 attempts) for timeout errors
- Add llm_timeout_seconds config setting if not already tunable
- Update src/core/llm.py to use new timeout

### T4: Fix — LLM concurrency semaphore [BLOCKED BY T2]
- Add a global asyncio semaphore to cap simultaneous Ollama calls (max 2-3 concurrent)
- Place in src/core/llm.py as module-level semaphore
- All LLM call sites acquire the semaphore

### T5: Fix — Observer fail-closed on LLM unavailable [INDEPENDENT]
- In src/workers/observer.py _run_extraction: skip storage on LLM timeout after retries
- Currently stores partial/empty memories on LLM failure
- Change: log observer_skipped_llm_unavailable and return without storing

### T6: Fix — Keepalive interval tuning [INDEPENDENT]
- Verify keepalive worker is hitting correct Ollama endpoint
- Reduce keepalive interval from 5min to 2min for qwen3:14b to prevent model eviction
- Verify in worker logs

### T7: Deploy and verify [BLOCKED BY T3, T4, T5, T6]
- Deploy all changed files to VM
- Monitor recall_llm_requests_total metric for 10 minutes
- Verify timeout rate drops below 20%

## Success Criteria
- LLM timeout rate < 20% (from current 74%)
- Observer no longer stores stub/partial memories on LLM failure
- No more than 3 concurrent LLM calls to Ollama at once
- Keepalive confirmed working with appropriate interval

## Files Likely Changed
- src/core/llm.py
- src/core/config.py
- src/workers/observer.py
- src/workers/main.py
