#!/bin/bash
# Prog 6: Learning-to-Rank with RankLib (Java).
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate

python prog6/run.py
