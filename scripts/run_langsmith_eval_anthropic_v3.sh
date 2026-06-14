#!/usr/bin/env bash
# Ad-hoc v3 golden-set experiment using Anthropic (requires ANTHROPIC_API_KEY).
# Override model: LOG_TRIAGE_DEFAULT_MODEL=claude-sonnet-4-20250514 ./scripts/...
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate

MODEL="${LOG_TRIAGE_DEFAULT_MODEL:-claude-3-5-haiku-latest}"
PREFIX="${LOG_TRIAGE_LANGSMITH_EXPERIMENT_PREFIX:-log-triage-v3-anthropic}"

echo "LangSmith eval (Anthropic): model=${MODEL} prompt=v3 prefix=${PREFIX}"

LOG_TRIAGE_DEFAULT_PROMPT_VERSION=v3 \
LOG_TRIAGE_DEFAULT_MODEL="$MODEL" \
LOG_TRIAGE_LANGSMITH_EVAL_MAX_CASES=all \
OBS_BACKEND="${OBS_BACKEND:-langsmith}" \
  python -m llm_log_triage.langsmith_eval --sync-dataset --run \
  --max-cases all \
  --experiment-prefix "$PREFIX"
