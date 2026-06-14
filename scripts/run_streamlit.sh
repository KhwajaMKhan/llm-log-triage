#!/usr/bin/env bash
# Streamlit UI for llm-log-triage.
#
# Usage (from repo root):
#   ./scripts/run_streamlit.sh
#
# App entrypoint: ui/streamlit_app.py
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

STREAMLIT="${ROOT}/.venv/bin/streamlit"
if [[ ! -x "$STREAMLIT" ]]; then
  echo "Missing .venv — run from repo root:" >&2
  echo "  python -m venv .venv && source .venv/bin/activate && pip install -e '.[dev,obs]'" >&2
  exit 1
fi

exec "$STREAMLIT" run ui/streamlit_app.py "$@"
