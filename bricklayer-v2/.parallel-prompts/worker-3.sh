#!/bin/bash
cd 'C:/Users/trg16/Dev/Bricklayer2.0/bricklayer-v2'
export BL_WORKER_ID=3
git checkout bricklayer-v2/mar24-parallel 2>/dev/null || true
PROMPT=$(cat 'C:/Users/trg16/Dev/Bricklayer2.0/bricklayer-v2/.parallel-prompts/worker-3.txt')
claude --dangerously-skip-permissions "$PROMPT"
echo ''
echo 'Worker 3 finished. Press Enter to close.'
read