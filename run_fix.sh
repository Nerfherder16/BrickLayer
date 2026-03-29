#!/bin/bash
python3 masonry/scripts/fix_recall_instructions.py > /tmp/fix_recall_result.txt 2>&1
echo "EXIT:$?" >> /tmp/fix_recall_result.txt
