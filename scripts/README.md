# Scripts

## Run interfaces

| Script | Purpose | Keys |
|--------|---------|------|
| [`run_streamlit.sh`](run_streamlit.sh) | Streamlit UI (`ui/streamlit_app.py`) | `OPENAI_API_KEY` (or `ANTHROPIC_API_KEY` for Claude models) |

```bash
cd llm-log-triage && source .venv/bin/activate
./scripts/run_streamlit.sh
```

## Manual eval scripts

Ad-hoc runs — **not** merge gates. CI: [`.github/workflows/README.md`](../.github/workflows/README.md).

| Script | Purpose | Keys |
|--------|---------|------|
| [`run_langsmith_eval_golden.sh`](run_langsmith_eval_golden.sh) | Full golden-set LangSmith experiment | `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`, `LANGCHAIN_API_KEY` |
| [`run_langsmith_eval_anthropic_v3.sh`](run_langsmith_eval_anthropic_v3.sh) | v3 + Anthropic model experiment | `ANTHROPIC_API_KEY`, `LANGCHAIN_API_KEY` |
| [`run_judge_eval.sh`](run_judge_eval.sh) | LLM-as-judge over golden set | `OPENAI_API_KEY` |

```bash
cd llm-log-triage && source .venv/bin/activate
./scripts/run_langsmith_eval_golden.sh
./scripts/run_judge_eval.sh
```

GitHub: **Actions → Manual LangSmith Eval** / **Manual Judge Eval**.
