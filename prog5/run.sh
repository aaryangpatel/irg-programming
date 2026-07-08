#!/bin/bash
cd "$(dirname "$0")/.."
source .venv/bin/activate
source .env/irgprog.env 2>/dev/null || true

if [ ! -f prog4/bm25_full.run ]; then
  bash prog4/run.sh
fi

python prog5/run.py
