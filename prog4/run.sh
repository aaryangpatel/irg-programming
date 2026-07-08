#!/bin/bash
cd "$(dirname "$0")/.."
source .venv/bin/activate

TREC_EVAL_DIR="$(pwd)/tools/trec_eval"
TREC_EVAL="$TREC_EVAL_DIR/trec_eval"

if [ ! -x "$TREC_EVAL" ]; then
  echo "Building trec_eval..."
  mkdir -p tools
  if [ ! -d "$TREC_EVAL_DIR/.git" ]; then
    git clone --branch version-10.0-rc2 --depth 1 https://github.com/usnistgov/trec_eval.git "$TREC_EVAL_DIR"
  fi
  make -C "$TREC_EVAL_DIR"
fi

python prog4/run.py
