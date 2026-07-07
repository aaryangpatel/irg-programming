#!/bin/bash
cd "$(dirname "$0")/.."
source .venv/bin/activate
source .env/irgprog.env 2>/dev/null || true
python prog2/run.py
