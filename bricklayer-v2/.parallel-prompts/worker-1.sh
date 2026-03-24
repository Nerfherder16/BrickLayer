#!/bin/bash
cd 'C:/Users/trg16/Dev/Bricklayer2.0/bricklayer-v2'
export BL_WORKER_ID=1
git checkout bricklayer-v2/mar24-parallel 2>/dev/null || true
PROMPT=$(cat 'C:/Users/trg16/Dev/Bricklayer2.0/bricklayer-v2/.parallel-prompts/worker-1.txt')
claude --dangerously-skip-permissions "$PROMPT"
echo ''
echo 'Worker 1 finished. Press Enter to close.'
read