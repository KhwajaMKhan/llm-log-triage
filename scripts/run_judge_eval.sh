#!/usr/bin/env bash
# Ad-hoc LLM-as-judge eval (NOT a CI merge gate). ~2 LLM calls per golden-set case.
# Writes docs/eval-runs/judge-latest.json
#
# Usage:
#   ./scripts/run_judge_eval.sh
#   LOG_TRIAGE_JUDGE_MODEL=claude-3-5-haiku-latest ./scripts/run_judge_eval.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate

OBS_BACKEND="${OBS_BACKEND:-none}" \
  pytest tests/test_judge.py -m judge -v --tb=short "$@"

echo "Report: docs/eval-runs/judge-latest.json"
