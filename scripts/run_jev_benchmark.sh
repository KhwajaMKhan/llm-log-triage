#!/usr/bin/env bash
# Jev vs llm-log-triage benchmark — optional, uses live APIs.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source .venv/bin/activate
export OBS_BACKEND=none
python scripts/jev_benchmark/run_lab.py --lanes ABC "$@"
