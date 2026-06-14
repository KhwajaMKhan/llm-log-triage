# Scripts

Helper scripts for local runs. **CI merge gates** are GitHub Actions — see [`.github/workflows/README.md`](../.github/workflows/README.md).

## Run interfaces

| Script | Purpose | Keys |
|--------|---------|------|
| [`run_streamlit.sh`](run_streamlit.sh) | Streamlit UI (`ui/streamlit_app.py`) | Matching key for selected model (see [README model table](../README.md#pick-a-model-4-supported)) |

```bash
cd llm-log-triage && source .venv/bin/activate
./scripts/run_streamlit.sh
```

## Manual eval scripts

Ad-hoc runs — **not** merge gates.

| Script | Purpose | Keys |
|--------|---------|------|
| [`run_langsmith_eval_golden.sh`](run_langsmith_eval_golden.sh) | Full golden-set LangSmith experiment | Matching key for `LOG_TRIAGE_DEFAULT_MODEL` + `LANGCHAIN_API_KEY` |
| [`run_langsmith_eval_anthropic_v3.sh`](run_langsmith_eval_anthropic_v3.sh) | v3 + Claude (`claude-sonnet-4-6`) | `ANTHROPIC_API_KEY`, `LANGCHAIN_API_KEY` |
| [`run_judge_eval.sh`](run_judge_eval.sh) | LLM-as-judge over golden set | Matching key for `LOG_TRIAGE_DEFAULT_MODEL` (judge uses same model by default) |

```bash
cd llm-log-triage && source .venv/bin/activate
./scripts/run_langsmith_eval_golden.sh
./scripts/run_judge_eval.sh
```

GitHub equivalents: **Actions → Manual LangSmith Eval** / **Manual Judge Eval** (see [README workflows](../README.md#github-actions-workflows)).
