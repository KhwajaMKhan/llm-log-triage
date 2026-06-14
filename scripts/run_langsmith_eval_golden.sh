#!/usr/bin/env bash
# Ad-hoc LangSmith experiment on log-triage-golden-set-v3 (NOT a CI merge gate).
# Same scorer as pytest; optional tracing to LangSmith.
#
# Usage:
#   ./scripts/run_langsmith_eval_golden.sh
#   LOG_TRIAGE_DEFAULT_MODEL=claude-3-5-haiku-latest ./scripts/run_langsmith_eval_golden.sh
#   LOG_TRIAGE_DEFAULT_PROMPT_VERSION=v1 ./scripts/run_langsmith_eval_golden.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate

PROMPT="${LOG_TRIAGE_DEFAULT_PROMPT_VERSION:-v3}"
MODEL="${LOG_TRIAGE_DEFAULT_MODEL:-gpt-4o-mini}"
PREFIX="${LOG_TRIAGE_LANGSMITH_EXPERIMENT_PREFIX:-log-triage-${PROMPT}}"
MAX="${LOG_TRIAGE_LANGSMITH_EVAL_MAX_CASES:-all}"

echo "LangSmith eval: prompt=${PROMPT} model=${MODEL} max_cases=${MAX} prefix=${PREFIX}"

LOG_TRIAGE_DEFAULT_PROMPT_VERSION="$PROMPT" \
LOG_TRIAGE_DEFAULT_MODEL="$MODEL" \
LOG_TRIAGE_LANGSMITH_EVAL_MAX_CASES="$MAX" \
OBS_BACKEND="${OBS_BACKEND:-langsmith}" \
  python -m llm_log_triage.langsmith_eval --sync-dataset --run \
  --max-cases "$MAX" \
  --experiment-prefix "$PREFIX"
