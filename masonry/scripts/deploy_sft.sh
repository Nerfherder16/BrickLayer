#!/bin/bash
# deploy_sft.sh — Re-register bricklayer-sft in Ollama from existing GGUF
#
# Run this on the machine that has Ollama (100.70.195.84) or on LXC 104
# if the GGUF lives there and you want to serve from there.
#
# Prerequisites:
#   - GGUF exists at ~/output/model.gguf (or adjust GGUF_PATH)
#   - ollama is installed and running
#
# Usage:
#   bash deploy_sft.sh
#   bash deploy_sft.sh /path/to/model.gguf   # override GGUF path

set -e

GGUF_PATH="${1:-$HOME/output/model.gguf}"
MODEL_NAME="bricklayer-sft"

if [ ! -f "$GGUF_PATH" ]; then
    echo "ERROR: GGUF not found at $GGUF_PATH"
    echo ""
    echo "Options:"
    echo "  1. If training output is on LXC 104:"
    echo "     scp root@192.168.50.104:~/output/model.gguf ~/output/model.gguf"
    echo ""
    echo "  2. If you need to re-run training:"
    echo "     ssh root@192.168.50.104"
    echo "     cd ~/bricklayer-sft  (or wherever finetune_lxc.py is)"
    echo "     python finetune_lxc.py --data sharegpt_train.jsonl --max-steps 500"
    echo "     python finetune_lxc.py --gguf-only --adapter ./output"
    echo "     scp ./output/model.gguf <ollama-host>:~/output/model.gguf"
    exit 1
fi

echo "[deploy_sft] GGUF found: $GGUF_PATH"
echo "[deploy_sft] Creating Modelfile..."

cat > /tmp/Modelfile_bricklayer_sft <<EOF
FROM ${GGUF_PATH}

SYSTEM """You are a BrickLayer research specialist. You evaluate hypotheses and claims about business models, technical systems, and architectural decisions. You respond only with structured JSON assessments."""

PARAMETER temperature 0.1
PARAMETER num_ctx 2048
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"
EOF

echo "[deploy_sft] Registering $MODEL_NAME in Ollama..."
ollama create "$MODEL_NAME" -f /tmp/Modelfile_bricklayer_sft

echo ""
echo "[deploy_sft] Verifying..."
ollama list | grep "$MODEL_NAME"

echo ""
echo "[deploy_sft] Done. Test with:"
echo "  ollama run $MODEL_NAME 'Assess: Does this system scale?'"
echo ""
echo "[deploy_sft] Then run eval:"
echo "  cd /path/to/Bricklayer2.0"
echo "  python masonry/scripts/eval_sft.py karen --eval-size 30 --compare"
